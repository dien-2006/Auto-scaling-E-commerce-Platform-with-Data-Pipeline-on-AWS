from sqlalchemy import func, select, update

from app.models import User


class AdminGrantRepository:
    def __init__(self, session):
        self.session = session

    def find(self, email, *, write=False):
        query = select(User.user_id, User.email, User.full_name, User.user_role, User.user_status)
        query = query.where(func.lower(User.email) == email)
        if write:
            query = query.with_for_update()
        return self.session.execute(query).mappings().one_or_none()

    def grant(self, user_id):
        return (
            self.session.execute(
                update(User)
                .where(
                    User.user_id == user_id, User.user_role == "USER", User.user_status == "ACTIVE"
                )
                .values(user_role="ADMIN", updated_at=func.now())
                .execution_options(synchronize_session=False)
            ).rowcount
            == 1
        )
