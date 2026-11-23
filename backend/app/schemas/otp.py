import re
from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
    TypeAdapter,
    field_validator,
)

from app.schemas.auth import RegisterRequest


def normalize_target(channel, value):
    if channel == "EMAIL":
        return str(TypeAdapter(EmailStr).validate_python(value.strip().lower()))
    raise ValueError("Only email OTP is supported")


class OTPRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    purpose: Literal["REGISTER", "RESET_PASSWORD"]
    channel: Literal["EMAIL"] = "EMAIL"
    target: str = Field(min_length=3, max_length=255)

    @field_validator("target")
    @classmethod
    def email(cls, value):
        return normalize_target("EMAIL", value)


class OTPVerify(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    challenge_id: UUID
    code: SecretStr = Field(min_length=6, max_length=6)

    @field_validator("code")
    @classmethod
    def digits(cls, value):
        if not re.fullmatch(r"[0-9]{6}", value.get_secret_value()):
            raise ValueError("Use six digits")
        return value


class VerifiedAction(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    verification_token: SecretStr = Field(min_length=64, max_length=64)

    @field_validator("verification_token")
    @classmethod
    def token_format(cls, value):
        if not re.fullmatch(r"[0-9a-f]{64}", value.get_secret_value()):
            raise ValueError("Invalid verification token")
        return value


class OTPRegister(VerifiedAction):
    full_name: str = Field(min_length=1, max_length=150)
    password: SecretStr = Field(min_length=9, max_length=128)

    @field_validator("full_name")
    @classmethod
    def name(cls, value):
        if not value.strip():
            raise ValueError("Name required")
        return value.strip()

    @field_validator("password")
    @classmethod
    def password_policy(cls, value):
        return RegisterRequest.strong_password(value)


class OTPReset(VerifiedAction):
    new_password: SecretStr = Field(min_length=9, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_policy(cls, value):
        return RegisterRequest.strong_password(value)


class OTPLogin(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    identifier: str = Field(min_length=3, max_length=255)
    password: SecretStr = Field(min_length=1, max_length=128)

    @field_validator("identifier")
    @classmethod
    def normalize(cls, value):
        return normalize_target("EMAIL", value)
