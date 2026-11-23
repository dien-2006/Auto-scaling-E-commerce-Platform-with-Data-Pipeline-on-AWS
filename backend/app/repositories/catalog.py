from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.engine import RowMapping
from sqlalchemy.orm import Session

from app.models import Category, Shop


class CatalogRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def active_categories(self) -> Sequence[RowMapping]:
        # One bounded-by-catalog query, not one query per child. Never read products/users here.
        statement = (
            select(
                Category.category_id,
                Category.parent_category_id,
                Category.category_name,
                Category.category_slug,
                Category.is_active,
            )
            .where(Category.is_active.is_(True))
            .order_by(Category.category_name.asc(), Category.category_id.asc())
        )
        return self.session.execute(statement).mappings().all()

    def public_shop(self, slug: str) -> RowMapping | None:
        # Logo keys are used only by the service to sign a URL, never returned to clients.
        statement = select(
            Shop.shop_id, Shop.shop_name, Shop.shop_slug, Shop.description, Shop.logo_key
        ).where(
            Shop.shop_slug == slug, Shop.shop_status == "APPROVED"
        )
        return self.session.execute(statement).mappings().one_or_none()
