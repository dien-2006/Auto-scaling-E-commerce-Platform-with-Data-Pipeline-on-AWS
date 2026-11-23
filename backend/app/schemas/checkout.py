import re
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.cart import CartAdd
from app.schemas.checkout_options import (
    AppliedCoupon,
    CouponSelection,
    PaymentMethod,
    ShippingMethod,
)


class CheckoutItem(CartAdd):
    expected_unit_price: Decimal = Field(ge=0, max_digits=14, decimal_places=2)

    @field_validator("expected_unit_price", mode="before")
    @classmethod
    def exact_price(cls, value: object) -> object:
        if not isinstance(value, str) or not re.fullmatch(
            r"(?:0|[1-9]\d{0,11})(?:\.\d{1,2})?", value
        ):
            raise ValueError("Use a nonnegative decimal price string")
        return value


class CheckoutRequest(CouponSelection):
    purchase_mode: Literal["CART", "BUY_NOW", "SELECTED_CART"] = "CART"
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    address_id: int = Field(ge=1, le=9223372036854775807)
    payment_method: PaymentMethod
    shipping_method: ShippingMethod | None = None
    expected_shipping_fee: Decimal | None = Field(
        default=None, ge=0, max_digits=14, decimal_places=2
    )
    expected_shipping_discount: Decimal | None = Field(
        default=None, ge=0, max_digits=14, decimal_places=2
    )
    items: list[CheckoutItem] = Field(min_length=1, max_length=1000)
    coupon_code: str | None = Field(default=None, min_length=1, max_length=50)
    expected_coupon_discount: Decimal | None = Field(
        default=None, ge=0, max_digits=14, decimal_places=2
    )

    @field_validator(
        "expected_coupon_discount",
        "expected_shipping_fee",
        "expected_shipping_discount",
        mode="before",
    )
    @classmethod
    def discount_string(cls, value):
        return CheckoutItem.exact_price(value) if value is not None else None

    @field_validator("coupon_code")
    @classmethod
    def coupon_trim(cls, value: str | None):
        if value is not None and not value.strip():
            raise ValueError("Coupon cannot be blank")
        return value.strip() if value else None

    @field_validator("address_id", mode="before")
    @classmethod
    def exact_id(cls, value: object) -> object:
        return CartAdd.exact_id(value)

    @model_validator(mode="after")
    def unique_products(self):
        if self.purchase_mode == "BUY_NOW" and len(self.items) != 1:
            raise ValueError("Buy now requires exactly one product")
        if self.coupon_code and (
            self.coco_coupon_code or self.shipping_coupon_code or self.shop_coupons
        ):
            raise ValueError("Do not mix legacy and scoped coupons")
        if not self.shipping_method and (
            self.coco_coupon_code or self.shipping_coupon_code or self.shop_coupons
        ):
            raise ValueError("Shipping selection required for scoped coupons")
        if len({item.product_id for item in self.items}) != len(self.items):
            raise ValueError("Product IDs must be unique")
        return self


class OrderLineData(BaseModel):
    order_item_id: str
    product_id: str
    product_name: str
    unit_price: Decimal
    quantity: int
    line_total: Decimal


class ShopOrderData(BaseModel):
    shop_order_id: str
    shop_id: str
    shop_name: str
    order_status: Literal["PENDING", "CONFIRMED", "SHIPPING", "COMPLETED", "CANCELLED"]
    subtotal: Decimal
    shipping_method: ShippingMethod | None = None
    shipping_fee: Decimal = Decimal("0.00")
    items: list[OrderLineData]


class OrderDetailData(BaseModel):
    order_id: str
    total_amount: Decimal
    discount_amount: Decimal = Decimal("0.00")
    shipping_fee: Decimal = Decimal("0.00")
    shipping_discount_amount: Decimal = Decimal("0.00")
    payment_method: PaymentMethod
    payment_status: Literal["PENDING", "SUCCESS", "FAILED", "REFUNDED"] | None = None
    applied_coupons: list[AppliedCoupon] = Field(default_factory=list)
    created_at: datetime
    recipient_name: str
    phone: str
    shipping_address: str
    shop_orders: list[ShopOrderData]


class CheckoutResponse(BaseModel):
    data: OrderDetailData


class CheckoutStatusResponse(BaseModel):
    data: OrderDetailData | None
