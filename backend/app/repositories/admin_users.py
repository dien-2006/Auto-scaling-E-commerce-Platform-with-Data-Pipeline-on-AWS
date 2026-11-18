from datetime import UTC

from sqlalchemy import func, or_, select, update

from app.models import User
from app.schemas.admin_users import AdminUser, AdminUserList


class AdminUserRepository:
    # Select only the response fields; never fetch password_hash for administration.
    columns = (
        User.user_id,
        User.email,
        User.full_name,
        User.phone,
        User.user_role,
        User.user_status,
        User.created_at,
    )

    def __init__(self, session):
        self.session = session

    @staticmethod
    def project(row):
        return AdminUser(
            **{
                **row,
                "user_id": str(row["user_id"]),
                "created_at": row["created_at"].astimezone(UTC),
            }
        )

    def list(self, query):
        predicates = []
        if query.status:
            predicates.append(User.user_status == query.status)
        if query.q.strip():
            term = query.q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            pattern = f"%{term}%"
            predicates.append(
                or_(
                    *(
                        column.ilike(pattern, escape="\\")
                        for column in (User.email, User.full_name, User.phone)
                    )
                )
            )
        total = self.session.scalar(select(func.count()).select_from(User).where(*predicates))
        rows = self.session.execute(
            select(*self.columns)
            .where(*predicates)
            .order_by(User.created_at.desc(), User.user_id.desc())
            .offset((query.page - 1) * query.page_size)
            .limit(query.page_size)
        ).mappings()
        return AdminUserList(
            items=[self.project(row) for row in rows],
            page=query.page,
            page_size=query.page_size,
            total=total or 0,
        )

    def get(self, user_id, *, write=False):
        query = select(*self.columns).where(User.user_id == user_id)
        if write:
            query = query.with_for_update()
        return self.session.execute(query).mappings().one_or_none()

    def status(self, user_id, target):
        self.session.execute(
            update(User)
            .where(User.user_id == user_id)
            .values(user_status=target, updated_at=func.now())
            .execution_options(synchronize_session=False)
        )
        return self.project(self.get(user_id))
