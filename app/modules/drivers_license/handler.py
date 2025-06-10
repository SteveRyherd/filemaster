"""Handler for the Driver's License module."""

from pydantic import BaseModel, Field
from typing import Optional
import uuid
from pathlib import Path

from ...models import ClientRequest, Module
from .. import ModuleHandler
from ...utils.file_orchestrator import FileOrchestrator


class DriversLicenseModel(BaseModel):
    """Schema for driver's license upload."""
    
    front_image: str = Field(..., description="Front of license file path")
    back_image: str = Field(..., description="Back of license file path")
    notes: Optional[str] = Field(None, max_length=500)
    
    # Extracted data (optional, for future OCR)
    license_number: Optional[str] = None
    full_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    expiration_date: Optional[str] = None
    address: Optional[str] = None


class DriversLicenseModuleHandler(ModuleHandler):
    key = "drivers_license"
    name = "Driver's License"
    
    def get_fields(self) -> list[dict]:
        """Return field configuration for form rendering."""
        return [
            {
                "name": "front_image",
                "type": "file",
                "label": "Front of License",
                "required": True,
                "accept": "image/*,.pdf",
                "help_text": "Upload a clear photo of the front of your driver's license"
            },
            {
                "name": "back_image", 
                "type": "file",
                "label": "Back of License",
                "required": True,
                "accept": "image/*,.pdf",
                "help_text": "Upload a clear photo of the back of your driver's license"
            },
            {
                "name": "notes",
                "type": "textarea",
                "label": "Additional Notes",
                "required": False,
                "placeholder": "Any additional information (optional)",
                "rows": 3
            }
        ]
    
    def validate(self, data: dict) -> dict:
        """Validate without file data - files handled separately."""
        # Only validate non-file fields
        validated = {}
        if "notes" in data:
            validated["notes"] = data["notes"][:500]  # Truncate to max length
        return validated
    
    def save(
        self,
        request: ClientRequest,
        data: dict,
        orchestrator: FileOrchestrator,
        files: dict = None
    ) -> dict:
        """Save license images and return stored data."""
        result = data.copy()
        
        if files:
            # Generate unique filenames
            if "front_image" in files:
                front_file = files["front_image"]
                ext = Path(front_file.filename).suffix
                front_filename = f"{uuid.uuid4()}_front{ext}"
                front_path = orchestrator.save(
                    front_file, 
                    request.token, 
                    str(self.key), 
                    front_filename
                )
                result["front_image"] = str(front_path.relative_to(orchestrator.base_path))
            
            if "back_image" in files:
                back_file = files["back_image"]
                ext = Path(back_file.filename).suffix
                back_filename = f"{uuid.uuid4()}_back{ext}"
                back_path = orchestrator.save(
                    back_file,
                    request.token,
                    str(self.key),
                    back_filename
                )
                result["back_image"] = str(back_path.relative_to(orchestrator.base_path))
        
        return result
    
    def render_admin_view(self, module: Module) -> str:
        """Render the admin view for this module."""
        data = module.result_data or {}
        
        html = f"""
        <div class="space-y-4">
            <h3 class="font-semibold">Driver's License</h3>
        """
        
        if data.get("front_image"):
            html += f"""
            <div>
                <p class="text-sm text-gray-600 mb-1">Front of License:</p>
                <a href="/admin/download/{module.request.token}/{self.key}/{Path(data['front_image']).name}" 
                   class="text-blue-600 hover:underline">Download Front</a>
            </div>
            """
        
        if data.get("back_image"):
            html += f"""
            <div>
                <p class="text-sm text-gray-600 mb-1">Back of License:</p>
                <a href="/admin/download/{module.request.token}/{self.key}/{Path(data['back_image']).name}"
                   class="text-blue-600 hover:underline">Download Back</a>
            </div>
            """
        
        if data.get("notes"):
            html += f"""
            <div>
                <p class="text-sm text-gray-600 mb-1">Notes:</p>
                <p class="text-sm">{data['notes']}</p>
            </div>
            """
        
        html += "</div>"
        return html


handler = DriversLicenseModuleHandler()