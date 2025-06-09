import os
import uuid
from typing import Dict, Any
try:
    from flask import current_app
except Exception:
    current_app = None
from werkzeug.utils import secure_filename
from .base import BaseModuleHandler, ModuleResult


class InsuranceCardResult(ModuleResult):
    def validate(self):
        if 'front_file' not in self.data or 'back_file' not in self.data:
            raise ValueError("Both front and back images are required")


class InsuranceCardModuleHandler(BaseModuleHandler):
    # Expanded to match file handler capabilities
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'heic', 'pdf'}
    ALLOWED_MIMETYPES = {
        'image/png', 'image/jpeg', 'image/jpg', 'image/gif', 
        'image/heic', 'application/pdf'
    }

    @property
    def module_type(self) -> str:
        return 'insurance_card'

    @property
    def template_name(self) -> str:
        return 'insurance_card.html'

    def get_result_schema(self) -> Dict[str, Any]:
        file_schema = {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "original_filename": {"type": "string"},
                "file_size": {"type": "integer"}
            }
        }
        return {
            "type": "object",
            "properties": {
                "front_file": file_schema,
                "back_file": file_schema,
                "notes": {"type": "string"}
            },
            "required": ["front_file", "back_file"]
        }

    def create_result(self, request_data) -> InsuranceCardResult:
        front_file = request_data.files.get('front_file')
        back_file = request_data.files.get('back_file')
        notes = request_data.form.get('notes', '')

        if not front_file or front_file.filename == '':
            raise ValueError("Front image is required")
        if not back_file or back_file.filename == '':
            raise ValueError("Back image is required")

        front_data = self._process_file(front_file, 'front')
        back_data = self._process_file(back_file, 'back')

        return InsuranceCardResult({
            'front_file': front_data,
            'back_file': back_data,
            'notes': notes
        })

    def _process_file(self, file, prefix: str) -> Dict[str, Any]:
        mimetype = getattr(file, 'mimetype', getattr(file, 'content_type', ''))
        if not self._allowed_file(file.filename, mimetype):
            raise ValueError(
                f"{prefix.title()} file type not allowed. "
                f"Filename: {file.filename}, Mimetype: {mimetype}. "
                f"Allowed extensions: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )

        upload_folder = (
            current_app.config['UPLOAD_FOLDER']
            if current_app else os.getenv('UPLOAD_FOLDER', 'uploads')
        )
        os.makedirs(upload_folder, exist_ok=True)

        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{prefix}_{filename}"
        file_path = os.path.join(upload_folder, unique_filename)
        if hasattr(file, 'save'):
            file.save(file_path)
        else:
            file.file.seek(0)
            with open(file_path, 'wb') as f:
                f.write(file.file.read())

        return {
            'file_path': unique_filename,
            'original_filename': file.filename,
            'file_size': os.path.getsize(file_path)
        }

    def get_display_data(self, module) -> Dict[str, Any]:
        data = super().get_display_data(module)
        if data.get('front_file'):
            data['front_file']['download_url'] = f"/uploads/{data['front_file']['file_path']}"
        if data.get('back_file'):
            data['back_file']['download_url'] = f"/uploads/{data['back_file']['file_path']}"
        return data

    def _allowed_file(self, filename: str, mimetype: str) -> bool:
        if not filename or '.' not in filename:
            return False
        extension = filename.rsplit('.', 1)[1].lower()
        # Check extension OR mimetype (more flexible)
        extension_ok = extension in self.ALLOWED_EXTENSIONS
        mimetype_ok = mimetype in self.ALLOWED_MIMETYPES
        return extension_ok and mimetype_ok
