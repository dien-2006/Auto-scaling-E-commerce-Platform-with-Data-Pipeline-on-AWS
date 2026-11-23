from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class ShopCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    shop_name: str = Field(min_length=1, max_length=150)
    shop_slug: str = Field(min_length=1, max_length=160, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str | None = Field(default=None, max_length=5000)
    contact_email: EmailStr | None = Field(default=None, max_length=255)

    @field_validator("shop_name", "shop_slug", "description", "contact_email", mode="before")
    @classmethod
    def trim(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class ShopPatch(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    shop_name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=5000)
    contact_email: EmailStr | None = Field(default=None, max_length=255)

    @field_validator("shop_name", "description", "contact_email", mode="before")
    @classmethod
    def trim(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def nonempty_patch(self):
        if not self.model_fields_set or (
            "shop_name" in self.model_fields_set and self.shop_name is None
        ):
            raise ValueError("Provide editable fields and a non-null shop name")
        return self


class ShopPrivate(BaseModel):
    shop_id: str
    owner_user_id: str
    shop_name: str
    shop_slug: str
    description: str | None
    contact_email: str | None
    logo_url: str | None = None
    shop_status: Literal["PENDING", "APPROVED", "REJECTED", "LOCKED"]
    created_at: datetime
    updated_at: datetime


class ShopResponse(BaseModel):
    data: ShopPrivate
