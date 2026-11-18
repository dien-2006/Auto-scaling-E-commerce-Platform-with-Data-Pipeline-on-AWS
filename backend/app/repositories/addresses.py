from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import Address


class AddressRepository:
    def __init__(self, session: Session, user_id: int):
        self.session = session
        self.user_id = user_id

    def list(self) -> list[Address]:
        return list(
            self.session.scalars(
                select(Address)
                .where(Address.user_id == self.user_id)
                .order_by(Address.is_default.desc(), Address.address_id.desc())
            )
        )

    def get(self, address_id: int) -> Address | None:
        return self.session.scalar(
            select(Address)
            .where(Address.address_id == address_id, Address.user_id == self.user_id)
            .with_for_update()
        )

    def clear_default(self) -> None:
        # Caller holds the owner user row lock; clear before setting the new row
        # to satisfy the existing partial unique index, even during ORM flush.
        self.session.execute(
            update(Address)
            .where(Address.user_id == self.user_id, Address.is_default.is_(True))
            .values(is_default=False)
        )

    def add(self, values: dict) -> Address:
        address = Address(user_id=self.user_id, **values)
        self.session.add(address)
        return address
