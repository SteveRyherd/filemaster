from __future__ import annotations

from pathlib import Path
from typing import Iterable

from fastapi import UploadFile


class FileOrchestrator:
    """Handle file storage operations for modules."""

    def __init__(self, base_path: str) -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _resolve(self, parts: Iterable[str]) -> Path:
        return self.base_path.joinpath(*parts)

    def save(self, upload: UploadFile, *parts: str) -> Path:
        """Save an uploaded file and return the stored path."""
        target_dir = self._resolve(parts[:-1]) if parts else self.base_path
        target_dir.mkdir(parents=True, exist_ok=True)
        filename = parts[-1] if parts else upload.filename
        file_path = target_dir / filename
        with file_path.open("wb") as fh:
            fh.write(upload.file.read())
        return file_path

    def retrieve(self, *parts: str) -> bytes:
        """Retrieve a file's bytes from storage."""
        return self.path(*parts).read_bytes()

    def delete(self, *parts: str) -> None:
        """Remove a stored file if it exists."""
        file_path = self.path(*parts)
        if file_path.exists():
            file_path.unlink()

    def path(self, *parts: str) -> Path:
        """Return the resolved path for the given file."""
        return self._resolve(parts)
