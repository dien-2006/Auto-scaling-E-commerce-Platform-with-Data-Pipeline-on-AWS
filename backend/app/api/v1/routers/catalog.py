from collections.abc import Generator
from typing import Annotated

from fastapi import APIRouter, Depends, Path
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, TimeoutError
from sqlalchemy.orm import Session

from app.core.errors import APIError
from app.db.session import get_session
from app.repositories.catalog import CatalogRepository
from app.schemas.catalog import CategoryList, ShopResponse
from app.schemas.errors import ErrorResponse
from app.services.catalog import CatalogService

router = APIRouter(tags=["Public catalog"], responses={503: {"model": ErrorResponse}})


def read_session(
    session: Annotated[Session, Depends(get_session)],
) -> Generator[Session]:
    try:
        session.execute(text("SET TRANSACTION READ ONLY"))
        yield session
    except (OperationalError, TimeoutError) as exc:
        raise APIError(503, "DEPENDENCY_UNAVAILABLE", "Dịch vụ chưa sẵn sàng") from exc


def get_catalog_service(
    session: Annotated[Session, Depends(read_session)],
) -> CatalogService:
    return CatalogService(CatalogRepository(session))


@router.get("/categories", response_model=CategoryList)
def categories(service: Annotated[CatalogService, Depends(get_catalog_service)]) -> CategoryList:
    """Active category tree; inactive ancestors hide their entire branch. Not paginated."""
    return service.categories()


@router.get("/shops/{shop_slug}", response_model=ShopResponse)
def shop(
    shop_slug: Annotated[str, Path(min_length=1, max_length=160)],
    service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> ShopResponse:
    """Approved public shop profile. Hidden/nonexistent shops share the same 404 response."""
    return service.shop(shop_slug)
