"""Utility functions to inspect stored module data."""

from __future__ import annotations

from typing import Any, Dict

from sqlalchemy.orm import Session

from ..models import Module


def get_module_data(db: Session, module_id: int) -> Dict[str, Any] | None:
    """Return the stored ``result_data`` for a module by ID."""
    module = db.get(Module, module_id)
    return module.result_data if module else None


def get_request_data(db: Session, request_id: int) -> Dict[int, Dict[str, Any]]:
    """Return a mapping of module ID to ``result_data`` for a request."""
    modules = (
        db.query(Module)
        .filter(Module.request_id == request_id)
        .order_by(Module.sort_order)
        .all()
    )
    return {mod.id: mod.result_data for mod in modules}
