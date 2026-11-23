from datetime import UTC

from sqlalchemy import func, or_, select, update

from app.models import Shop
from app.schemas.admin_shops import AdminShopList
from app.schemas.seller_shop import ShopPrivate


class AdminShopRepository:
    columns = (
        Shop.shop_id,
        Shop.owner_user_id,
        Shop.shop_name,
        Shop.shop_slug,
        Shop.description,
        Shop.contact_email,
        Shop.shop_status,
        Shop.created_at,
        Shop.updated_at,
    )

    def __init__(self, session):
        self.session = session

    @staticmethod
    def project(row):
        return ShopPrivate(
            **{
                **row,
                "shop_id": str(row["shop_id"]),
                "owner_user_id": str(row["owner_user_id"]),
                "created_at": row["created_at"].astimezone(UTC),
                "updated_at": row["updated_at"].astimezone(UTC),
            },
            logo_url=None,
        )

    def list(self, query):
        predicates = []
        if query.status:
            predicates.append(Shop.shop_status == query.status)
        if query.q.strip():
            term = query.q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            predicates.append(
                or_(
                    *(
                        column.ilike(f"%{term}%", escape="\\")
                        for column in (Shop.shop_name, Shop.shop_slug, Shop.contact_email)
                    )
                )
            )
        total = self.session.scalar(select(func.count()).select_from(Shop).where(*predicates))
        rows = self.session.execute(
            select(*self.columns)
            .where(*predicates)
            .order_by(Shop.created_at.desc(), Shop.shop_id.desc())
            .offset((query.page - 1) * query.page_size)
            .limit(query.page_size)
        ).mappings()
        return AdminShopList(
            items=[self.project(row) for row in rows],
            page=query.page,
            page_size=query.page_size,
            total=total or 0,
        )

    def get(self, shop_id, *, write=False):
        query = select(*self.columns).where(Shop.shop_id == shop_id)
        if write:
            query = query.with_for_update()
        return self.session.execute(query).mappings().one_or_none()

    def transition(self, shop_id, expected, target):
        return (
            self.session.execute(
                update(Shop)
                .where(Shop.shop_id == shop_id, Shop.shop_status == expected)
                .values(shop_status=target, updated_at=func.now())
                .execution_options(synchronize_session=False)
            ).rowcount
            == 1
        )
