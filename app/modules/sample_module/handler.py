"""Sample module handler implementation."""

from pydantic import BaseModel, Field

from ...models import ClientRequest
from .. import ModuleHandler


class SampleModel(BaseModel):
    """Schema for sample module fields."""

    text: str = Field(..., title="Sample Text")


class SampleModuleHandler(ModuleHandler):
    key = "sample"
    name = "Sample Module"

    def get_fields(self) -> list[BaseModel]:
        return [SampleModel]

    def validate(self, data: dict) -> dict:
        return SampleModel(**data).dict()

    def save(self, request: ClientRequest, data: dict) -> None:
        # Placeholder: In a real module, persist data to DB or filesystem
        print(f"Saving data for request {request.id}: {data}")


handler = SampleModuleHandler()
