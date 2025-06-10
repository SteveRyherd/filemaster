"""Main FastAPI application."""

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from secrets import token_hex

from .modules import discover_modules
from .models import ClientRequest, Module
from .utils.database import SessionLocal, init_db
from .settings import Settings

app = FastAPI(title="FileMaster")


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class RequestCreate(BaseModel):
    nickname: str | None = None


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


class RequestStatus(BaseModel):
    id: int
    token: str
    modules: list[ModuleStatus]


settings: Settings


async def load_modules() -> None:
    """Discover modules and initialize the database."""
    discover_modules()
    init_db()


@app.on_event("startup")
async def startup_event() -> None:
    """Load configuration and then initialize modules."""
    global settings
    settings = Settings()
    app.state.settings = settings
    await load_modules()


@app.get("/")
async def root() -> dict[str, str]:
    """Basic root endpoint."""
    return {"message": "Welcome to FileMaster"}


@app.get("/modules")
async def list_modules() -> list[str]:
    """List registered module keys."""
    from .modules import registry

    return list(registry.keys())


@app.post("/requests", response_model=RequestStatus)
def create_request(data: RequestCreate, db: Session = Depends(get_db)):
    req = ClientRequest(token=token_hex(16), nickname=data.nickname)
    db.add(req)
    db.commit()
    db.refresh(req)
    return RequestStatus(id=req.id, token=req.token, modules=[])


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
        )
        for m in req.modules
    ]
    return RequestStatus(id=req.id, token=req.token, modules=modules)
