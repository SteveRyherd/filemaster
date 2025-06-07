from abc import ABC, abstractmethod
from typing import Dict, Any
from flask import render_template


class ModuleResult:
    """Wrapper for module result data with validation."""

    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.validate()

    def validate(self):
        """Override in subclasses for specific validation."""
        pass

    def to_dict(self) -> Dict[str, Any]:
        return self.data


class BaseModuleHandler(ABC):
    """Base class for all module handlers."""

    @property
    @abstractmethod
    def module_type(self) -> str:
        """Return the module type this handler supports."""
        pass

    @property
    @abstractmethod
    def template_name(self) -> str:
        """Return the template name for rendering this module."""
        pass

    @abstractmethod
    def get_result_schema(self) -> Dict[str, Any]:
        """Return JSON schema for validating result data."""
        pass

    @abstractmethod
    def create_result(self, request_data) -> ModuleResult:
        """Create a ModuleResult from request data."""
        pass

    def validate_request(self, request_data) -> tuple[bool, str]:
        """Validate the incoming request data."""
        try:
            result = self.create_result(request_data)
            return True, ""
        except ValueError as e:
            return False, str(e)

    def process_submission(self, module, request_data) -> bool:
        """Process the module submission."""
        try:
            result = self.create_result(request_data)
            module.update_results(result.to_dict())
            module.completed = True
            return True
        except Exception:
            return False

    def render(self, module):
        """Render the module form."""
        return render_template(f'modules/{self.template_name}', module=module)

    def get_display_data(self, module) -> Dict[str, Any]:
        """Get formatted data for display in admin views."""
        return module.result_data or {}
