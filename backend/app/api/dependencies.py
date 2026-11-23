"""Dependencies for future protected routes; transactions cover policy and service work."""

import hmac
import re
from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.errors import APIError
from app.core.security import Security, get_security
from app.db.session import get_session
from app.models import User
from app.repositories.access import AccessRepository
from app.services.access import AccessPolicy, Principal


def current_subject(request: Request, security: Annotated[Security, Depends(get_security)]) -> int:
    subject = security.subject(request)
    credential = getattr(request.state, "auth_credential", None)
    if request.app.state.settings.otp_enabled or credential is not None:
        try:
            with request.app.state.database.sessions() as session:
                session.execute(text("SET TRANSACTION READ ONLY"))
                password_hash = session.scalar(
                    select(User.password_hash).where(User.user_id == subject)
                )
                if (
                    not isinstance(credential, str)
                    or not re.fullmatch(r"[a-f0-9]{64}", credential)
                    or not password_hash
                    or not hmac.compare_digest(credential, security.credential_stamp(password_hash))
                ):
                    raise APIError(
                        401, "INVALID_TOKEN", "Phiên đăng nhập đã thay đổi. Vui lòng đăng nhập lại"
                    )
        except SQLAlchemyError as exc:
            raise APIError(
                503, "DEPENDENCY_UNAVAILABLE", "Không kiểm tra được phiên đăng nhập"
            ) from exc
    return subject


def csrf_guard(request: Request, security: Annotated[Security, Depends(get_security)]) -> None:
    security.check_csrf(request)


def get_access(
    subject: Annotated[int, Depends(current_subject)],
    session: Annotated[Session, Depends(get_session)],
) -> Generator[AccessPolicy]:
    try:
        with session.begin():
            session.execute(text("SET TRANSACTION READ ONLY"))
            yield AccessPolicy(AccessRepository(session), subject)
    except SQLAlchemyError as exc:
        raise APIError(503, "DEPENDENCY_UNAVAILABLE", "Dịch vụ chưa sẵn sàng") from exc


def get_write_access(
    subject: Annotated[int, Depends(current_subject)],
    _csrf: Annotated[None, Depends(csrf_guard)],
    session: Annotated[Session, Depends(get_session)],
) -> Generator[AccessPolicy]:
    try:
        with session.begin():
            yield AccessPolicy(AccessRepository(session, write=True), subject)
    except SQLAlchemyError as exc:
        raise APIError(503, "DEPENDENCY_UNAVAILABLE", "Dịch vụ chưa sẵn sàng") from exc


ReadAccess = Annotated[AccessPolicy, Depends(get_access, scope="function")]
WriteAccess = Annotated[AccessPolicy, Depends(get_write_access, scope="function")]


def require_admin(access: ReadAccess) -> Principal:
    return access.admin()


def require_buyer(access: ReadAccess) -> Principal:
    return access.buyer()
