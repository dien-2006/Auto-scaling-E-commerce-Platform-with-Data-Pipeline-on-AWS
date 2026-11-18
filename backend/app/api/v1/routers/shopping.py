from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response
from sqlalchemy.orm import Session

from app.api.dependencies import ReadAccess, WriteAccess, csrf_guard
from app.api.v1.routers.catalog import read_session
from app.repositories.shopping import CouponRepository, ReviewRepository
from app.schemas.shopping import CouponCode, CouponQuote, ReviewCreate, ReviewData, ReviewPage
from app.services.shopping import CouponService, ReviewService

router = APIRouter(tags=["Coupons and product reviews"])
ResourceID = Annotated[int, Path(ge=1, le=9223372036854775807)]


@router.post("/coupons/quote", response_model=CouponQuote)
def coupon_quote(
    payload: CouponCode,
    access: ReadAccess,
    response: Response,
    _csrf: Annotated[None, Depends(csrf_guard)],
):
    buyer = access.buyer()
    response.headers["Cache-Control"] = "no-store"
    return CouponService(CouponRepository(access.repository.session)).quote(
        payload.code, buyer.user_id, payload.direct_item, payload.selected_product_ids
    )


@router.get("/products/{product_id}/reviews", response_model=ReviewPage)
def product_reviews(
    product_id: ResourceID,
    response: Response,
    session: Annotated[Session, Depends(read_session)],
    page: Annotated[int, Query(ge=1, le=2147483647)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 10,
):
    response.headers["Cache-Control"] = "no-store"
    return ReviewService(ReviewRepository(session)).public(product_id, page, page_size)


@router.get("/order-items/{item_id}/review", response_model=dict[str, ReviewData | None])
def my_review(item_id: ResourceID, access: ReadAccess, response: Response):
    response.headers["Cache-Control"] = "no-store"
    buyer = access.buyer()
    return {
        "data": ReviewService(ReviewRepository(access.repository.session)).mine(
            item_id, buyer.user_id
        )
    }


@router.post("/order-items/{item_id}/review", response_model=dict[str, ReviewData], status_code=201)
def create_review(
    item_id: ResourceID, payload: ReviewCreate, access: WriteAccess, response: Response
):
    response.headers["Cache-Control"] = "no-store"
    buyer = access.buyer()
    return {
        "data": ReviewService(ReviewRepository(access.repository.session)).create(
            item_id, buyer.user_id, payload
        )
    }
