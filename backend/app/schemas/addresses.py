from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator, model_validator


class AddressCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    recipient_name: str = Field(min_length=1, max_length=150)
    phone: str = Field(min_length=3, max_length=30, pattern=r"^\+?[0-9 ()-]+$")
    address_line: str = Field(min_length=1, max_length=2000)
    ward: str | None = Field(default=None, min_length=1, max_length=120)
    district: str | None = Field(default=None, min_length=1, max_length=120)
    city: str = Field(min_length=1, max_length=120)
    is_default: StrictBool = False

    @field_validator(
        "recipient_name", "phone", "address_line", "ward", "district", "city", mode="before"
    )
    @classmethod
    def trim(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class AddressPatch(AddressCreate):
    recipient_name: str | None = Field(default=None, min_length=1, max_length=150)
    phone: str | None = Field(default=None, min_length=3, max_length=30, pattern=r"^\+?[0-9 ()-]+$")
    address_line: str | None = Field(default=None, min_length=1, max_length=2000)
    city: str | None = Field(default=None, min_length=1, max_length=120)

    @model_validator(mode="after")
    def nonempty_patch(self):
        if not self.model_fields_set:
            raise ValueError("Provide at least one address field")
        for name in ("recipient_name", "phone", "address_line", "city"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError("Required address fields cannot be null")
        return self


class AddressData(BaseModel):
    address_id: str
    recipient_name: str
    phone: str
    address_line: str
    ward: str | None
    district: str | None
    city: str
    is_default: bool
    created_at: datetime


class AddressResponse(BaseModel):
    data: AddressData


class AddressItems(BaseModel):
    items: list[AddressData]


class AddressList(BaseModel):
    data: AddressItems
