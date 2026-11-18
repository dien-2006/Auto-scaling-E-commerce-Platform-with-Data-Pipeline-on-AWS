from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Shop


class SellerShopRepository:
    def __init__(self, session: Session, owner_id: int):
        self.session = session
        self.owner_id = owner_id

    def owned(self, *, write: bool = False) -> Shop | None:
        query = select(Shop).where(Shop.owner_user_id == self.owner_id)
        if write:
            query = query.with_for_update()
        return self.session.scalar(query)

    def add(self, values: dict) -> Shop:
        row = Shop(owner_user_id=self.owner_id, shop_status="PENDING", **values)
        self.session.add(row)
        self.session.flush()
        return row

    def remove(self, row: Shop) -> None:
        self.session.delete(row)
        self.session.flush()
