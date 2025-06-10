"""Main FastAPI application."""

from fastapi import FastAPI

from .modules import discover_modules

app = FastAPI(title="FileMaster")


@app.on_event("startup")
async def load_modules() -> None:
    """Discover and initialize modules on startup."""
    discover_modules()


@app.get("/")
async def root() -> dict[str, str]:
    """Basic root endpoint."""
    return {"message": "Welcome to FileMaster"}


@app.get("/modules")
async def list_modules() -> list[str]:
    """List registered module keys."""
    from .modules import registry

    return list(registry.keys())
