from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.cart import CartAdd

PaymentMethod = Literal["COD", "BANK_TRANSFER", "MOMO", "VNPAY"]
ShippingMethod = Literal["STANDARD", "EXPRESS", "COCOEXPRESS"]


class ShopCoupon(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    shop_id: int = Field(ge=1, le=9223372036854775807)
    code: str = Field(min_length=1, max_length=50)

    @field_validator("shop_id", mode="before")
    @classmethod
    def exact_id(cls, value):
        return CartAdd.exact_id(value)


class CouponSelection(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    coco_coupon_code: str | None = Field(default=None, min_length=1, max_length=50)
    shipping_coupon_code: str | None = Field(default=None, min_length=1, max_length=50)
    shop_coupons: list[ShopCoupon] = Field(default_factory=list, max_length=1000)

    @model_validator(mode="after")
    def unique_shops(self):
        if len({c.shop_id for c in self.shop_coupons}) != len(self.shop_coupons):
            raise ValueError("Only one coupon per shop")
        codes = [c.code for c in self.shop_coupons]
        if self.coco_coupon_code:
            codes.append(self.coco_coupon_code)
        if self.shipping_coupon_code:
            codes.append(self.shipping_coupon_code)
        if len(codes) != len(set(codes)):
            raise ValueError("Coupons must be distinct")
        return self


class OptionsQuoteRequest(CouponSelection):
    shipping_method: ShippingMethod
    payment_method: PaymentMethod = "COD"


class AppliedCoupon(BaseModel):
    code: str
    shop_id: str | None
    discount_amount: Decimal
    coupon_type: Literal["GOODS", "SHIPPING"] = "GOODS"


class ShippingCost(BaseModel):
    shop_id: str
    method: ShippingMethod
    fee: Decimal


class OptionsQuote(BaseModel):
    subtotal: Decimal
    discount_amount: Decimal
    shipping_fee: Decimal
    shipping_discount_amount: Decimal = Decimal("0.00")
    total_amount: Decimal
    applied_coupons: list[AppliedCoupon]
    shipping: list[ShippingCost]


class ShippingOption(BaseModel):
    code: ShippingMethod
    label: str
    fee_per_shop: Decimal | None
    enabled: bool
    reason: str | None


class PaymentOption(BaseModel):
    code: PaymentMethod
    label: str
    enabled: bool
    reason: str | None


class CheckoutOptions(BaseModel):
    enabled: bool
    bank: dict[str, str] | None
    shipping_methods: list[ShippingOption]
    payment_methods: list[PaymentOption]
