from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Shop, User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def by_email(self, email: str) -> User | None:
        return self.session.scalar(
            select(User).where(func.lower(User.email) == email).with_for_update()
        )

    def by_id(self, user_id: int) -> User | None:
        return self.session.get(User, user_id)

    def owned_shop(self, user_id: int) -> Shop | None:
        return self.session.scalar(select(Shop).where(Shop.owner_user_id == user_id))

    def add(
        self, *, email: str | None, password_hash: str, full_name: str, phone: str | None
    ) -> User:
        user = User(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            phone=phone,
            user_role="USER",
            user_status="ACTIVE",
        )
        self.session.add(user)
        self.session.flush()  # Existing unique LOWER(email) index resolves concurrent registration.
        return user
