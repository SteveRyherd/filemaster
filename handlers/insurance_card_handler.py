import os
import uuid
from typing import Dict, Any
from flask import current_app
from werkzeug.utils import secure_filename
from .base import BaseModuleHandler, ModuleResult


class InsuranceCardResult(ModuleResult):
    def validate(self):
        if 'front_file' not in self.data or 'back_file' not in self.data:
            raise ValueError("Both front and back images are required")


class InsuranceCardModuleHandler(BaseModuleHandler):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
    ALLOWED_MIMETYPES = {'image/png', 'image/jpeg', 'application/pdf'}

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

        if not front_file or not back_file:
            raise ValueError("Both front and back images are required")

        front_data = self._process_file(front_file, 'front')
        back_data = self._process_file(back_file, 'back')

        return InsuranceCardResult({
            'front_file': front_data,
            'back_file': back_data,
            'notes': notes
        })

    def _process_file(self, file, prefix: str) -> Dict[str, Any]:
        if not self._allowed_file(file.filename, file.mimetype):
            raise ValueError(f"{prefix.title()} file type not allowed")

        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)

        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{prefix}_{filename}"
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)

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
        return extension in self.ALLOWED_EXTENSIONS and mimetype in self.ALLOWED_MIMETYPES
