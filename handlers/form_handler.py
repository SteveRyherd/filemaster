from typing import Dict, Any
from .base import BaseModuleHandler, ModuleResult


class FormResult(ModuleResult):
    def validate(self):
        if 'answer' not in self.data or not self.data['answer'].strip():
            raise ValueError("Answer is required")


class FormModuleHandler(BaseModuleHandler):
    @property
    def module_type(self) -> str:
        return 'form'

    @property
    def template_name(self) -> str:
        return 'form.html'

    def get_result_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "answer": {"type": "string", "maxLength": 5000}
            },
            "required": ["answer"]
        }

    def create_result(self, request_data) -> FormResult:
        answer = request_data.form.get('answer', '').strip()
        if not answer:
            raise ValueError("Answer is required")
        if len(answer) > 5000:
            raise ValueError("Answer too long (max 5000 characters)")
        return FormResult({'answer': answer})
