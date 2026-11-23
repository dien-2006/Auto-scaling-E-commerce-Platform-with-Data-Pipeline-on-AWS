from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.checkout import CheckoutItem


class CouponCode(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    code: str = Field(min_length=1, max_length=50)
    direct_item: CheckoutItem | None = None
    selected_product_ids: list[str] | None = Field(default=None, min_length=1, max_length=1000)


class CouponQuote(BaseModel):
    code: str
    subtotal: Decimal
    discount_amount: Decimal
    total_amount: Decimal


class ReviewCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    rating: int = Field(strict=True, ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)


class ReviewData(BaseModel):
    review_id: str
    rating: int
    comment: str | None
    created_at: datetime


class ReviewPage(BaseModel):
    items: list[ReviewData]
    total: int
    average_rating: Decimal | None
    page: int
    page_size: int
