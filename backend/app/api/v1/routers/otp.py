from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response
from sqlalchemy.orm import Session

from app.api.dependencies import csrf_guard
from app.core.client_ip import otp_client_ip
from app.core.security import Security, get_security
from app.db.session import get_session
from app.schemas.otp import OTPLogin, OTPRegister, OTPRequest, OTPReset, OTPVerify
from app.services.otp import OTPService, send_pending
from app.services.otp_delivery import configured

router = APIRouter(prefix="/auth", tags=["OTP verification"])


@router.get("/otp-options")
def options(request: Request, response: Response):
    settings = request.app.state.settings
    response.headers["Cache-Control"] = "no-store"
    return {
        "enabled": settings.otp_enabled,
        "email": settings.otp_enabled and configured(settings, "EMAIL"),
        "sms": False,
    }


@router.post("/otp-request", status_code=202, dependencies=[Depends(csrf_guard)])
def issue(
    data: OTPRequest,
    request: Request,
    response: Response,
    tasks: BackgroundTasks,
    session: Annotated[Session, Depends(get_session)],
):
    result, pending = OTPService(
        session, request.app.state.settings, request.app.state.database.otp_store
    ).issue(data, otp_client_ip(request))
    if pending:
        tasks.add_task(
            send_pending, request.app.state.database.otp_store, request.app.state.settings, pending
        )
    response.headers["Cache-Control"] = "no-store"
    return {"data": result}


@router.post("/otp-verify", dependencies=[Depends(csrf_guard)])
def verify(
    data: OTPVerify,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(get_session)],
    security: Annotated[Security, Depends(get_security)],
):
    result = OTPService(
        session, request.app.state.settings, request.app.state.database.otp_store
    ).verify(data)
    response.headers["Cache-Control"] = "no-store"
    return {"data": result}


@router.post("/otp-register", dependencies=[Depends(csrf_guard)])
def register_verified(
    data: OTPRegister,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(get_session)],
):
    result = OTPService(
        session, request.app.state.settings, request.app.state.database.otp_store
    ).complete(data, "REGISTER")
    response.headers["Cache-Control"] = "no-store"
    return {"data": result}


@router.post("/password-reset", dependencies=[Depends(csrf_guard)])
def reset_verified(
    data: OTPReset,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(get_session)],
    security: Annotated[Security, Depends(get_security)],
):
    result = OTPService(
        session, request.app.state.settings, request.app.state.database.otp_store
    ).complete(data, "RESET_PASSWORD")
    security.clear_cookies(response)
    response.headers["Cache-Control"] = "no-store"
    return {"data": result}


@router.post("/otp-login", dependencies=[Depends(csrf_guard)])
def login(
    data: OTPLogin,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(get_session)],
    security: Annotated[Security, Depends(get_security)],
):
    user, password_hash = OTPService(
        session, request.app.state.settings, request.app.state.database.otp_store
    ).login(data)
    security.login_cookies(response, int(user.user_id), security.credential_stamp(password_hash))
    response.headers["Cache-Control"] = "no-store"
    return {"data": user}
