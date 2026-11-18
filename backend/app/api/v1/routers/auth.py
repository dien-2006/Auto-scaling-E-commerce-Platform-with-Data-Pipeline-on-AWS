from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.api.dependencies import csrf_guard, current_subject
from app.core.security import Security, get_security
from app.db.session import get_session
from app.repositories.users import UserRepository
from app.schemas.auth import AuthResponse, CSRFData, CSRFResponse, LoginRequest, RegisterRequest
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])
SecurityDep = Annotated[Security, Depends(get_security)]


def service(request: Request, session: Annotated[Session, Depends(get_session)]) -> AuthService:
    return AuthService(UserRepository(session), request.app.state.settings)


ServiceDep = Annotated[AuthService, Depends(service)]


@router.get("/csrf", response_model=CSRFResponse)
def csrf(request: Request, response: Response, security: SecurityDep) -> CSRFResponse:
    token = security.set_csrf(response, request.cookies.get(security.access_cookie, ""))
    return CSRFResponse(data=CSRFData(csrf_token=token))


@router.post(
    "/register", status_code=201, response_model=AuthResponse, dependencies=[Depends(csrf_guard)]
)
def register(data: RegisterRequest, auth: ServiceDep) -> AuthResponse:
    return AuthResponse(data=auth.register(data))


@router.post("/login", response_model=AuthResponse, dependencies=[Depends(csrf_guard)])
def login(
    data: LoginRequest, response: Response, security: SecurityDep, auth: ServiceDep
) -> AuthResponse:
    user = auth.login(data)
    security.login_cookies(
        response,
        int(user.user_id),
        security.credential_stamp(auth.login_hash) if security.settings.otp_enabled else None,
    )
    return AuthResponse(data=user)


@router.post("/logout", status_code=204, dependencies=[Depends(csrf_guard)])
def logout(security: SecurityDep) -> Response:
    response = Response(status_code=204)
    security.clear_cookies(response)
    return response


@router.get("/me", response_model=AuthResponse)
def me(user_id: Annotated[int, Depends(current_subject)], auth: ServiceDep) -> AuthResponse:
    return AuthResponse(data=auth.me(user_id))
