import os
import uuid
from datetime import datetime, timedelta

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from fastapi_models import Base, engine, SessionLocal, ClientRequest, Module, AccessLog
from handlers.file_handler import FileModuleHandler
from handlers.form_handler import FormModuleHandler
from handlers.drivers_license_handler import DriversLicenseModuleHandler
from handlers.insurance_card_handler import InsuranceCardModuleHandler

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Ensure upload directory exists
app.state.upload_folder = os.getenv("UPLOAD_FOLDER", "uploads")
os.makedirs(app.state.upload_folder, exist_ok=True)

# Create DB tables if needed
Base.metadata.create_all(bind=engine)

MODULE_HANDLERS = {
    'file': FileModuleHandler(),
    'form': FormModuleHandler(),
    'drivers_license': DriversLicenseModuleHandler(),
    'insurance_card': InsuranceCardModuleHandler(),
}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/create_dummy", response_class=HTMLResponse)
async def create_dummy(request: Request, days: int | None = None, db: Session = Depends(get_db)):
    expires_at = datetime.utcnow() + timedelta(days=days) if days else None
    token = uuid.uuid4().hex
    req = ClientRequest(token=token, expires_at=expires_at)
    mod1 = Module(request=req, kind='file', description='Upload proof of income')
    mod2 = Module(request=req, kind='form', description='Provide credit score')
    mod3 = Module(request=req, kind='drivers_license', description="Upload your driver's license")
    mod4 = Module(request=req, kind='insurance_card', description='Upload your insurance card')
    db.add_all([req, mod1, mod2, mod3, mod4])
    db.commit()
    return HTMLResponse(
        f"Created request with token: {token}<br>Visit <a href='/request/{token}'>/request/{token}</a>"
    )


@app.get("/uploads/{filename}")
async def uploaded_file(filename: str):
    file_path = os.path.join(app.state.upload_folder, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, filename=filename)


@app.get("/request/{token}", response_class=HTMLResponse)
async def view_request(request: Request, token: str, module: int | None = None, db: Session = Depends(get_db)):
    req_db = db.query(ClientRequest).filter_by(token=token).first()
    if not req_db:
        raise HTTPException(status_code=404, detail="Request not found")
    if req_db.expires_at and datetime.utcnow() > req_db.expires_at:
        raise HTTPException(status_code=404, detail="Request expired")

    selected = None
    if module:
        selected = db.query(Module).get(module)
    if not selected:
        selected = next((m for m in req_db.modules if not m.completed), None)

    module_html = None
    if selected:
        handler = MODULE_HANDLERS.get(selected.kind)
        if not handler:
            raise HTTPException(status_code=400, detail="Unknown module type")
        module_html = handler.render(selected, request)

    db.add(
        AccessLog(
            request_id=req_db.id,
            module_id=selected.id if selected else None,
            ip_address=request.client.host,
            action="view_request",
        )
    )
    db.commit()

    return templates.TemplateResponse(
        "request.html",
        {"request": request, "req": req_db, "selected": selected, "module_html": module_html},
    )


@app.post("/module/{module_id}")
async def handle_module(request: Request, module_id: int, db: Session = Depends(get_db)):
    module = db.query(Module).get(module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    handler = MODULE_HANDLERS.get(module.kind)
    if not handler:
        raise HTTPException(status_code=400, detail="Unknown module type")
    form = await request.form()
    class RequestData:
        def __init__(self, form):
            self.form = {k: v for k, v in form.items() if not hasattr(v, "filename")}
            self.files = {k: v for k, v in form.items() if hasattr(v, "filename")}
    if not handler.process_submission(module, RequestData(form)):
        raise HTTPException(status_code=400, detail="Invalid submission")
    db.add(
        AccessLog(
            request_id=module.request_id,
            module_id=module.id,
            ip_address=request.client.host,
            action="module_completed",
        )
    )
    db.commit()
    return RedirectResponse(url=f"/request/{module.request.token}", status_code=303)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7777)
