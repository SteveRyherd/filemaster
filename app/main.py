"""Main FastAPI application."""

from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session
from secrets import token_hex
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import json

from .modules import discover_modules
from .models import ClientRequest, Module, AccessLog
from .utils.database import SessionLocal, init_db
from .utils.file_orchestrator import FileOrchestrator
from .settings import Settings

app = FastAPI(title="FileMaster")
app.mount("/static", StaticFiles(directory="static"), name="static")


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class RequestCreate(BaseModel):
    nickname: str | None = None
    expires_days: int | None = None


class ModuleAttach(BaseModel):
    kind: str
    label: str | None = None
    description: str | None = None
    required: bool = True


class ModuleStatus(BaseModel):
    id: int
    kind: str
    label: str | None
    completed: bool
    completed_at: datetime | None = None


class RequestStatus(BaseModel):
    id: int
    token: str
    modules: list[ModuleStatus]
    completed_at: datetime | None = None


settings: Settings


def load_modules() -> None:
    """Discover modules and initialize the database."""
    discover_modules()
    init_db()


@app.on_event("startup")
async def startup_event() -> None:
    """Load configuration and then initialize modules."""
    global settings
    settings = Settings()
    app.state.settings = settings
    app.state.orchestrator = FileOrchestrator(settings.UPLOAD_FOLDER)
    load_modules()


@app.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    """Serve the landing page."""
    return HTMLResponse(Path("static/index.html").read_text())


@app.get("/admin/new_request", response_class=HTMLResponse)
async def new_request_page() -> HTMLResponse:
    """Serve the new request creation page."""
    return HTMLResponse(Path("static/new_request.html").read_text())


@app.get("/customer", response_class=HTMLResponse)
async def customer_interface() -> HTMLResponse:
    """Serve the customer interface."""
    return HTMLResponse(Path("static/customer.html").read_text())


@app.get("/customer/{token}")
async def get_customer_request(token: str, db: Session = Depends(get_db)):
    """Get request data for customer view."""
    req = db.query(ClientRequest).filter(ClientRequest.token == token).first()
    if not req:
        raise HTTPException(status_code=404, detail="Invalid token")
    
    # Check expiration
    if req.expires_at and req.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Request has expired")
    
    # Update last accessed
    req.last_accessed = datetime.utcnow()
    
    # Log access
    access_log = AccessLog(
        request_id=req.id,
        action="view",
        ip_address="0.0.0.0",  # TODO: Get real IP
        user_agent="Unknown"   # TODO: Get from request
    )
    db.add(access_log)
    db.commit()
    
    modules = [
        {
            "id": m.id,
            "kind": m.kind,
            "label": m.label,
            "description": m.description,
            "required": m.required,
            "completed": m.completed,
            "completed_at": m.completed_at
        }
        for m in sorted(req.modules, key=lambda x: x.sort_order)
    ]
    
    return {
        "nickname": req.nickname,
        "modules": modules,
        "expires_at": req.expires_at
    }


@app.get("/customer/module/{module_id}/form", response_class=HTMLResponse)
async def get_module_form(module_id: int, db: Session = Depends(get_db)):
    """Get the HTML form for a specific module."""
    module = db.get(Module, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    
    from .modules import registry
    handler = registry.get(module.kind)
    if not handler:
        raise HTTPException(status_code=404, detail="Handler not found")
    
    # For now, return a simple form based on module type
    # In the future, this would call handler.render_form(module)
    if module.kind == "ssn":
        form_html = f"""
        <form onsubmit="return window.submitModuleForm(event, {module.id})" class="space-y-4">
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                    Social Security Number
                </label>
                <input type="text" 
                       name="ssn"
                       pattern="\\d{{3}}-\\d{{2}}-\\d{{4}}" 
                       placeholder="123-45-6789"
                       value="{module.result_data.get('ssn', '') if module.result_data else ''}"
                       class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                       required>
                <p class="text-xs text-gray-500 mt-1">Your SSN is encrypted and stored securely</p>
            </div>
            <div class="flex justify-end space-x-3 pt-4">
                <button type="button" onclick="document.querySelector('[x-data]').__x.$data.activeModule = null" 
                        class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
                    Cancel
                </button>
                <button type="submit" 
                        class="px-4 py-2 automotive-gradient text-white rounded-lg hover:opacity-90">
                    Save
                </button>
            </div>
        </form>
        """
    else:
        form_html = f"""
        <div class="text-center py-8">
            <p class="text-gray-500">Form for {module.kind} module coming soon...</p>
        </div>
        """
    
    return HTMLResponse(form_html)


@app.get("/modules")
async def list_modules() -> list[str]:
    """List registered module keys."""
    from .modules import registry

    return list(registry.keys())


@app.post("/requests", response_model=RequestStatus)
def create_request(data: RequestCreate, db: Session = Depends(get_db)):
    expires_at = None
    if data.expires_days:
        expires_at = datetime.utcnow() + timedelta(days=data.expires_days)
    req = ClientRequest(token=token_hex(16), nickname=data.nickname, expires_at=expires_at)
    db.add(req)
    db.commit()
    db.refresh(req)
    return RequestStatus(
        id=req.id, token=req.token, modules=[], completed_at=req.completed_at
    )


@app.post("/requests/{request_id}/modules", response_model=ModuleStatus)
def attach_module(
    request_id: int, data: ModuleAttach, db: Session = Depends(get_db)
) -> ModuleStatus:
    req = db.get(ClientRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    module = Module(
        request=req,
        kind=data.kind,
        label=data.label,
        description=data.description,
        required=data.required,
    )
    db.add(module)
    db.commit()
    db.refresh(module)
    return ModuleStatus(
        id=module.id,
        kind=module.kind,
        label=module.label,
        completed=module.completed,
        completed_at=module.completed_at,
    )


@app.get("/requests/{request_id}", response_model=RequestStatus)
def get_request(request_id: int, db: Session = Depends(get_db)):
    req = db.get(ClientRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    modules = [
        ModuleStatus(
            id=m.id,
            kind=m.kind,
            label=m.label,
            completed=m.completed,
            completed_at=m.completed_at,
        )
        for m in req.modules
    ]
    return RequestStatus(
        id=req.id, token=req.token, modules=modules, completed_at=req.completed_at
    )


@app.post("/modules/{module_id}/submit", response_model=ModuleStatus)
def submit_module(module_id: int, data: dict, db: Session = Depends(get_db)):
    module = db.get(Module, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    from .modules import registry

    handler = registry.get(module.kind)
    if not handler:
        raise HTTPException(status_code=404, detail="Handler not found")

    validated = handler.validate(data)
    orchestrator: FileOrchestrator = app.state.orchestrator
    
    # Save returns the data to store (may include file paths)
    result_data = handler.save(module.request, validated, orchestrator)
    
    # Store the result data returned by handler
    module.result_data = result_data if result_data is not None else validated
    module.completed = True
    module.completed_at = datetime.utcnow()

    # Log the submission
    access_log = AccessLog(
        request_id=module.request_id,
        module_id=module.id,
        action="submit",
        ip_address="0.0.0.0",  # TODO: Get real IP
        user_agent="Unknown"   # TODO: Get from request
    )
    db.add(access_log)

    if module.request and all(m.completed for m in module.request.modules):
        module.request.completed_at = datetime.utcnow()
        db.add(module.request)

    db.add(module)
    db.commit()
    db.refresh(module)

    return ModuleStatus(
        id=module.id,
        kind=module.kind,
        label=module.label,
        completed=module.completed,
        completed_at=module.completed_at,
    )
