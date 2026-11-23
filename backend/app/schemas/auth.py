import unicodedata
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, field_validator


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    email: EmailStr = Field(max_length=255)
    # Login checks existing hashes, not today's registration complexity policy.
    password: SecretStr = Field(min_length=1, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value


class RegisterRequest(LoginRequest):
    password: SecretStr = Field(min_length=9, max_length=128)
    full_name: str = Field(min_length=1, max_length=150)
    phone: str | None = Field(default=None, min_length=3, max_length=30, pattern=r"^\+?[0-9 ()-]+$")

    @field_validator("password")
    @classmethod
    def strong_password(cls, value: SecretStr) -> SecretStr:
        password = value.get_secret_value()
        if not (
            any("A" <= c <= "Z" for c in password)
            and any("0" <= c <= "9" for c in password)
            and any(unicodedata.category(c)[0] in {"P", "S"} for c in password)
        ):
            raise ValueError("Password requires uppercase, number and special character")
        return value

    @field_validator("full_name", "phone", mode="before")
    @classmethod
    def trim_profile(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class OwnedShop(BaseModel):
    shop_id: str
    shop_status: Literal["PENDING", "APPROVED", "REJECTED", "LOCKED"]


class UserPrivate(BaseModel):
    user_id: str
    email: str | None
    full_name: str
    phone: str | None
    user_role: Literal["USER", "ADMIN"]
    user_status: Literal["ACTIVE", "LOCKED"]
    owned_shop: OwnedShop | None = None


class AuthResponse(BaseModel):
    data: UserPrivate


class CSRFData(BaseModel):
    csrf_token: str


class CSRFResponse(BaseModel):
    data: CSRFData
