from collections.abc import Generator
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.dependencies import ReadAccess, csrf_guard, current_subject
from app.core.errors import APIError
from app.db.session import get_session
from app.models import User
from app.repositories.access import AccessRepository
from app.schemas.admin_users import (
    AdminUserList,
    AdminUserQuery,
    AdminUserResponse,
    UserStatusChange,
)
from app.schemas.products import PositiveID
from app.services.access import AccessPolicy
from app.services.admin_users import AdminUserService

router = APIRouter(prefix="/admin/users", tags=["Admin users"])


def admin_user_write(
    user_id: PositiveID,
    subject: Annotated[int, Depends(current_subject)],
    _csrf: Annotated[None, Depends(csrf_guard)],
    session: Annotated[Session, Depends(get_session)],
) -> Generator[AccessPolicy]:
    try:
        with session.begin():
            # Reject unauthorized callers before taking locks on other accounts.
            AccessPolicy(AccessRepository(session), subject).admin()
            # Actor and target must be locked in ID order, unlike a one-user mutation.
            session.execute(
                select(User.user_id)
                .where(User.user_id.in_([subject, user_id]))
                .order_by(User.user_id)
                .with_for_update()
            ).all()
            access = AccessPolicy(AccessRepository(session, write=True), subject)
            access.admin()  # Recheck role/status after any wait for concurrent changes.
            yield access
    except SQLAlchemyError as exc:
        raise APIError(503, "DEPENDENCY_UNAVAILABLE", "Dịch vụ chưa sẵn sàng") from exc


@router.get("", response_model=AdminUserList)
def users(query: Annotated[AdminUserQuery, Query()], access: ReadAccess, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return AdminUserService(access).list(query)


@router.patch("/{user_id}/status", response_model=AdminUserResponse)
def status(
    user_id: PositiveID,
    payload: UserStatusChange,
    access: Annotated[AccessPolicy, Depends(admin_user_write, scope="function")],
    response: Response,
):
    response.headers["Cache-Control"] = "no-store"
    return AdminUserResponse(data=AdminUserService(access).change(user_id, payload.user_status))
