import os
import uuid
from typing import Dict, Any
try:
    from flask import current_app
except Exception:
    current_app = None
from werkzeug.utils import secure_filename
from .base import BaseModuleHandler, ModuleResult


class FileResult(ModuleResult):
    def validate(self):
        if 'file_path' not in self.data:
            raise ValueError("file_path is required")
        if 'original_filename' not in self.data:
            raise ValueError("original_filename is required")


class FileModuleHandler(BaseModuleHandler):
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'heic'}
    ALLOWED_MIMETYPES = {'application/pdf', 'image/png', 'image/jpeg', 'text/plain'}

    @property
    def module_type(self) -> str:
        return 'file'

    @property
    def template_name(self) -> str:
        return 'file.html'

    def get_result_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "original_filename": {"type": "string"},
                "file_size": {"type": "integer"},
                "mimetype": {"type": "string"}
            },
            "required": ["file_path", "original_filename"]
        }

    def create_result(self, request_data) -> FileResult:
        file = request_data.files.get('file')
        if not file or file.filename == '':
            raise ValueError("No file selected")

        mimetype = getattr(file, 'mimetype', getattr(file, 'content_type', ''))
        if not self._allowed_file(file.filename, mimetype):
            raise ValueError(f"File type not allowed. Supported: {', '.join(self.ALLOWED_EXTENSIONS)}")

        upload_folder = (
            current_app.config['UPLOAD_FOLDER']
            if current_app else os.getenv('UPLOAD_FOLDER', 'uploads')
        )
        os.makedirs(upload_folder, exist_ok=True)

        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(upload_folder, unique_filename)
        if hasattr(file, 'save'):
            file.save(file_path)
        else:
            # Starlette UploadFile provides a file-like object
            file.file.seek(0)
            with open(file_path, 'wb') as f:
                f.write(file.file.read())

        return FileResult({
            'file_path': unique_filename,
            'original_filename': file.filename,
            'file_size': os.path.getsize(file_path),
            'mimetype': mimetype
        })

    def get_display_data(self, module) -> Dict[str, Any]:
        data = super().get_display_data(module)
        if data.get('file_path'):
            data['download_url'] = f"/uploads/{data['file_path']}"
        return data

    def _allowed_file(self, filename: str, mimetype: str) -> bool:
        if not filename or '.' not in filename:
            return False
        extension = filename.rsplit('.', 1)[1].lower()
        return extension in self.ALLOWED_EXTENSIONS and mimetype in self.ALLOWED_MIMETYPES
