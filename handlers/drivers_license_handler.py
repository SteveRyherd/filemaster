from .insurance_card_handler import InsuranceCardModuleHandler, InsuranceCardResult
from .base import ModuleResult


class DriversLicenseResult(ModuleResult):
    def validate(self):
        if 'front_file' not in self.data or 'back_file' not in self.data:
            raise ValueError("Both front and back images are required")
        # Additional validation could go here


class DriversLicenseModuleHandler(InsuranceCardModuleHandler):
    @property
    def module_type(self) -> str:
        return 'drivers_license'

    @property
    def template_name(self) -> str:
        return 'drivers_license.html'

    def create_result(self, request_data) -> DriversLicenseResult:
        parent_result = super().create_result(request_data)
        return DriversLicenseResult(parent_result.data)
