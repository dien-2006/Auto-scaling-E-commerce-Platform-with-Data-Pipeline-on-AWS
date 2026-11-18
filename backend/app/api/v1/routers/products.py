from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.api.v1.routers.catalog import read_session
from app.repositories.products import ProductRepository
from app.schemas.errors import ErrorResponse
from app.schemas.products import (
    BestsellerList,
    DealList,
    DealSummary,
    ProductList,
    ProductQuery,
    ProductResponse,
)
from app.services.products import ProductService
from app.services.storage import Storage

router = APIRouter(tags=["Public products"], responses={503: {"model": ErrorResponse}})


def get_product_service(
    session: Annotated[Session, Depends(read_session)], storage: Storage
) -> ProductService:
    return ProductService(ProductRepository(session), storage)


@router.get("/products", response_model=ProductList)
def products(
    query: Annotated[ProductQuery, Query()],
    service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductList:
    """Public catalog; literal case-insensitive name search and active category descendants."""
    return service.list(query)


@router.get("/deals/today", response_model=DealList)
def deals(service: Annotated[ProductService, Depends(get_product_service)]) -> DealList:
    from app.services.products import summary

    return DealList(
        items=[
            DealSummary(
                **summary(row, service.storage).model_dump(),
                original_price=row["original_price"],
                sale_price=row["sale_price"],
                discount_percent=row["discount_percent"],
                coupon_code=row["coupon_code"],
                ends_at=row["ends_at"],
            )
            for row in service.repository.deals()
        ]
    )


@router.get("/products/bestsellers", response_model=BestsellerList)
def bestsellers(service: Annotated[ProductService, Depends(get_product_service)]) -> BestsellerList:
    from app.services.products import summary

    rows, ranked = service.repository.bestsellers()
    return BestsellerList(items=[summary(row, service.storage) for row in rows], ranked=ranked)


@router.get("/products/{product_id}", response_model=ProductResponse)
def product(
    product_id: Annotated[int, Path(ge=1, le=9223372036854775807)],
    service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductResponse:
    """Hidden products and products in non-approved shops return the same 404 as missing IDs."""
    return service.detail(product_id)
