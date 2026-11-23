from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator

Quantity = Annotated[StrictInt, Field(ge=1, le=2147483647)]


class CartQuantity(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    quantity: Quantity


class CartAdd(CartQuantity):
    product_id: int = Field(ge=1, le=9223372036854775807)

    @field_validator("product_id", mode="before")
    @classmethod
    def exact_id(cls, value: object) -> object:
        if isinstance(value, bool) or isinstance(value, float):
            raise ValueError("Use an exact integer product ID")
        return value


UnavailableReason = Literal[
    "HIDDEN_PRODUCT",
    "SHOP_UNAVAILABLE",
    "CATEGORY_UNAVAILABLE",
    "SELF_PURCHASE",
    "MISSING_INVENTORY",
    "OUT_OF_STOCK",
    "INSUFFICIENT_STOCK",
]


class CartLine(BaseModel):
    cart_item_id: str
    product_id: str
    product_name: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal
    available_quantity: int
    is_available: bool
    unavailable_reason: UnavailableReason | None
    primary_image_url: str | None = None


class CartShop(BaseModel):
    shop_id: str
    shop_name: str
    shop_slug: str
    items: list[CartLine]
    subtotal: Decimal


class CartData(BaseModel):
    shops: list[CartShop]
    total_amount: Decimal


class CartResponse(BaseModel):
    data: CartData
