"""Module discovery and registry."""

from __future__ import annotations

import importlib
import pkgutil
from typing import Dict, TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:  # pragma: no cover - import for type checking only
    from ..models import ClientRequest
    from ..utils.file_orchestrator import FileOrchestrator


class ModuleHandler:
    """Minimal interface for module handlers."""

    key: str
    name: str

    def get_fields(self) -> list[BaseModel]:
        raise NotImplementedError

    def validate(self, data: dict) -> dict:
        raise NotImplementedError

    def save(
        self,
        request: "ClientRequest",
        data: dict,
        orchestrator: "FileOrchestrator",
    ) -> None:
        raise NotImplementedError


registry: Dict[str, ModuleHandler] = {}


def discover_modules() -> None:
    """Discover and register modules available in the modules package."""
    registry.clear()
    package = __name__
    for finder, name, ispkg in pkgutil.iter_modules(__path__):
        if not ispkg:
            continue
        module_name = f"{package}.{name}.handler"
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            continue
        handler = getattr(module, "handler", None)
        if handler and hasattr(handler, "key"):
            registry[handler.key] = handler
