from sqlalchemy import func, select, update

from app.models import Inventory


class InventoryRepository:
    def __init__(self, session):
        self.session = session

    def get(self, product_id: int, *, write: bool):
        query = select(Inventory).where(Inventory.product_id == product_id)
        if write:
            query = query.with_for_update()
        return self.session.scalar(query)

    def adjust(self, product_id: int, expected: int, delta: int):
        # Service already holds the row lock and has checked the numeric bounds.
        # The predicate is a final guard against an accidental stale overwrite.
        return (
            self.session.execute(
                update(Inventory)
                .where(Inventory.product_id == product_id, Inventory.quantity == expected)
                .values(quantity=Inventory.quantity + delta, updated_at=func.now())
                .returning(Inventory.quantity, Inventory.updated_at)
                .execution_options(synchronize_session=False)
            )
            .mappings()
            .one_or_none()
        )
