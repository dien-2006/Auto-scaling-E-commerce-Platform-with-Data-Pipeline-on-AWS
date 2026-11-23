import re
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


class QuoteDirectItem(CartAdd):
    expected_unit_price: Decimal = Field(ge=0, max_digits=14, decimal_places=2)

    @field_validator("expected_unit_price", mode="before")
    @classmethod
    def exact_price(cls, value):
        if not isinstance(value, str) or not re.fullmatch(
            r"(?:0|[1-9]\d{0,11})(?:\.\d{1,2})?", value
        ):
            raise ValueError("Use a nonnegative decimal price string")
        return value


class OptionsQuoteRequest(CouponSelection):
    shipping_method: ShippingMethod
    payment_method: PaymentMethod = "COD"
    direct_item: QuoteDirectItem | None = None
    selected_product_ids: list[str] | None = Field(default=None, min_length=1, max_length=1000)

    @field_validator("selected_product_ids")
    @classmethod
    def selected_ids(cls, values):
        if values is None:
            return values
        if len(set(values)) != len(values):
            raise ValueError("Selected product IDs must be unique")
        for value in values:
            if not re.fullmatch(r"[1-9]\d{0,18}", value) or int(value) > 9223372036854775807:
                raise ValueError("Use a positive BIGINT product ID string")
        return values

    @model_validator(mode="after")
    def purchase_scope(self):
        if self.direct_item is not None and self.selected_product_ids is not None:
            raise ValueError("Choose buy now or selected cart, not both")
        return self


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
