from decimal import Decimal
from typing import Literal, Self

from pydantic import AnyHttpUrl, EmailStr, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MARKETPLACE_", extra="forbid", hide_input_in_errors=True
    )

    environment: Literal["local", "test", "production"] = "local"
    otp_enabled: bool = False
    otp_redis_url: SecretStr | None = None
    otp_secret: SecretStr | None = Field(default=None, min_length=32, max_length=512)
    otp_email_provider: Literal["disabled", "smtp", "ses"] = "disabled"
    otp_sms_provider: Literal["disabled", "sns"] = "disabled"
    otp_from_email: EmailStr | None = Field(default=None, max_length=255)
    otp_aws_region: str = Field(default="ap-southeast-1", pattern=r"^[a-z0-9-]{1,50}$")
    smtp_host: str | None = None
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_security: Literal["STARTTLS", "TLS"] = "STARTTLS"
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    public_origin: AnyHttpUrl | None = None
    additional_origins: list[AnyHttpUrl] = Field(default_factory=list, max_length=10)
    jwt_secret: SecretStr | None = Field(default=None, min_length=32, max_length=512)
    proxy_secret: SecretStr | None = Field(default=None, min_length=32, max_length=512)
    jwt_issuer: str = Field(default="marketplace", min_length=1, max_length=200)
    jwt_audience: str = Field(default="marketplace-web", min_length=1, max_length=200)
    db_host: str = Field(default="postgres", min_length=1)
    db_port: int = Field(default=5432, ge=1, le=65535)
    db_name: str | None = Field(default=None, min_length=1)
    db_user: str | None = Field(default=None, min_length=1)
    db_password: SecretStr | None = None
    db_pool_size: int = Field(default=5, ge=1, le=50)
    db_max_overflow: int = Field(default=5, ge=0, le=50)
    db_pool_timeout: int = Field(default=5, ge=1, le=30)
    db_connect_timeout: int = Field(default=3, ge=1, le=15)
    db_statement_timeout_ms: int = Field(default=3000, ge=100, le=30000)
    s3_bucket: str | None = Field(
        default=None, min_length=3, max_length=63, pattern=r"^[a-z0-9][a-z0-9.-]*[a-z0-9]$"
    )
    s3_region: str = Field(default="ap-southeast-1", pattern=r"^[a-z0-9-]{1,50}$")
    s3_endpoint_url: AnyHttpUrl | None = None
    s3_public_base_url: AnyHttpUrl | None = None
    s3_path_style: bool = False
    checkout_options_enabled: bool = False
    shipping_standard_fee: Decimal | None = Field(
        default=Decimal("25000"), ge=0, max_digits=14, decimal_places=2
    )
    shipping_express_fee: Decimal | None = Field(
        default=Decimal("40000"), ge=0, max_digits=14, decimal_places=2
    )
    shipping_cocoexpress_fee: Decimal | None = Field(
        default=Decimal("60000"), ge=0, max_digits=14, decimal_places=2
    )
    bank_name: str | None = Field(default=None, min_length=1, max_length=100)
    bank_account_number: str | None = Field(default=None, min_length=1, max_length=50)
    bank_account_holder: str | None = Field(default=None, min_length=1, max_length=150)

    @field_validator("s3_bucket", "s3_endpoint_url", "s3_public_base_url", mode="before")
    @classmethod
    def absent_storage(cls, value: object) -> object:
        return None if value == "" else value

    @field_validator("s3_endpoint_url", "s3_public_base_url")
    @classmethod
    def storage_url(cls, value: AnyHttpUrl | None) -> AnyHttpUrl | None:
        if value and (
            value.scheme != "https"
            or value.username
            or value.password
            or value.query
            or value.fragment
        ):
            raise ValueError("Storage URL must use HTTPS without credentials, query or fragment")
        return value

    @model_validator(mode="after")
    def storage_configuration(self) -> Self:
        if (self.s3_endpoint_url or self.s3_public_base_url) and not self.s3_bucket:
            raise ValueError("Storage URL requires a bucket")
        return self

    @field_validator("jwt_secret", "proxy_secret", mode="before")
    @classmethod
    def absent_auth_secret(cls, value: object) -> object:
        return None if value == "" else value

    @field_validator("public_origin")
    @classmethod
    def exact_origin(cls, value: AnyHttpUrl | None) -> AnyHttpUrl | None:
        if value and (
            value.username
            or value.password
            or value.path not in (None, "/")
            or value.query is not None
            or value.fragment is not None
        ):
            raise ValueError("Use an exact origin without credentials, path, query or fragment")
        return value

    @field_validator("additional_origins")
    @classmethod
    def exact_additional_origins(cls, values: list[AnyHttpUrl]) -> list[AnyHttpUrl]:
        for value in values:
            cls.exact_origin(value)
        return values

    @model_validator(mode="after")
    def production_origin(self) -> Self:
        if self.otp_enabled:
            if not self.otp_secret or not self.jwt_secret or not self.otp_redis_url:
                raise ValueError("OTP requires dedicated OTP and JWT secrets and a Redis URL")
            secret = self.otp_secret.get_secret_value()
            if len(set(secret)) < 10 or "replace" in secret.lower():
                raise ValueError("OTP secret must be randomly generated")
        if self.jwt_secret is not None:
            secret = self.jwt_secret.get_secret_value()
            if len(set(secret)) < 10 or "replace" in secret.lower():
                raise ValueError("JWT secret must be a randomly generated secret")
            if self.public_origin is None:
                raise ValueError("Authentication requires an exact public origin")
        credentials = (self.db_name, self.db_user, self.db_password)
        if any(value is not None for value in credentials) and not all(
            value is not None for value in credentials
        ):
            raise ValueError("Database name, user and password must be configured together")
        if self.db_password is not None and not self.db_password.get_secret_value():
            raise ValueError("Database password must not be empty")
        if self.environment == "production" and self.public_origin:
            if self.public_origin.scheme != "https":
                raise ValueError("Production origin must use HTTPS")
        if self.environment == "production" and any(
            origin.scheme != "https" for origin in self.additional_origins
        ):
            raise ValueError("Production additional origins must use HTTPS")
        return self
