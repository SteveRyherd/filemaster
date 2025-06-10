"""Main FastAPI application."""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session
from secrets import token_hex
from datetime import datetime, timedelta
from pathlib import Path

from .modules import discover_modules
from .models import ClientRequest, Module
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


@app.get("/")
async def root() -> dict[str, str]:
    """Basic root endpoint."""
    return {"message": "Welcome to FileMaster"}


@app.get("/admin/new_request", response_class=HTMLResponse)
async def new_request_page() -> HTMLResponse:
    """Serve the new request creation page."""
    return HTMLResponse(Path("static/new_request.html").read_text())


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
    handler.save(module.request, validated, orchestrator)

    module.result_data = validated
    module.completed = True
    module.completed_at = datetime.utcnow()

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
