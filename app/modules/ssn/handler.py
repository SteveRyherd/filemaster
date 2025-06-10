"""Handler for the SSN module."""

from pydantic import BaseModel, Field

from ...models import ClientRequest
from .. import ModuleHandler
from ...settings import Settings
from ...utils import encryption


class SSNModel(BaseModel):
    """Schema for an SSN field."""

    ssn: str = Field(
        ..., title="Social Security Number", pattern=r"^\d{3}-\d{2}-\d{4}$"
    )


class SSNModuleHandler(ModuleHandler):
    key = "ssn"
    name = "Social Security Number"

    def get_fields(self) -> list[BaseModel]:
        return [SSNModel]

    def validate(self, data: dict) -> dict:
        return SSNModel(**data).dict()

    def save(self, request: ClientRequest, data: dict) -> None:
        key = Settings().ENCRYPTION_KEY.encode()
        encrypted = encryption.encrypt(data["ssn"], key)
        data["ssn"] = encrypted.decode()


handler = SSNModuleHandler()
