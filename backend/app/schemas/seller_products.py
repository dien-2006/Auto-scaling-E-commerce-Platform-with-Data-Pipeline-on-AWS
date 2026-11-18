from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.products import PositiveID, ProductDetail

Money = Annotated[Decimal, Field(ge=0, max_digits=14, decimal_places=2)]


class ProductCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    sku: str = Field(min_length=1, max_length=64)
    category_id: PositiveID
    product_name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    price: Money
    initial_quantity: int = Field(strict=True, ge=0, le=2147483647)

    @field_validator("sku", "product_name", "description", mode="before")
    @classmethod
    def trim(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("price", mode="before")
    @classmethod
    def decimal_string(cls, value: object) -> object:
        if not isinstance(value, str):
            raise ValueError("Price must be a decimal string")
        return value


class ProductPatch(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    sku: str | None = Field(default=None, min_length=1, max_length=64)
    category_id: PositiveID | None = None
    product_name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    price: Money | None = None

    _trim = field_validator("sku", "product_name", "description", mode="before")(
        ProductCreate.trim.__func__
    )
    _price = field_validator("price", mode="before")(ProductCreate.decimal_string.__func__)

    @model_validator(mode="after")
    def nonempty(self):
        if not self.model_fields_set or any(
            getattr(self, key) is None for key in self.model_fields_set - {"description"}
        ):
            raise ValueError("Provide editable, non-null fields")
        return self


class SellerQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    q: str = Field(default="", max_length=200)
    is_active: bool | None = None
    page: int = Field(default=1, ge=1, le=2147483647)
    page_size: int = Field(default=24, ge=1, le=100)


class SellerProduct(ProductDetail):
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SellerProductResponse(BaseModel):
    data: SellerProduct


class SellerProductList(BaseModel):
    items: list[SellerProduct]
    page: int
    page_size: int
    total: int
    image_upload_enabled: bool = False
