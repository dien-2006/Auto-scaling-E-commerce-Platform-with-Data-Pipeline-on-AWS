from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request, Response
from sqlalchemy.orm import Session

from app.api.dependencies import ReadAccess, csrf_guard, current_subject
from app.db.session import get_session
from app.repositories.checkout import CheckoutRepository
from app.repositories.shopping import CouponRepository
from app.schemas.checkout import CheckoutRequest, CheckoutResponse, CheckoutStatusResponse
from app.schemas.checkout_options import CheckoutOptions, OptionsQuote, OptionsQuoteRequest
from app.services.checkout import CheckoutService
from app.services.checkout_options import CheckoutOptionsService

router = APIRouter(tags=["Buyer checkout"])


@router.get("/checkout/options", response_model=CheckoutOptions)
def checkout_options(access: ReadAccess, request: Request, response: Response):
    access.buyer()
    response.headers["Cache-Control"] = "no-store"
    return CheckoutOptionsService(request.app.state.settings).options()


@router.post("/checkout/quote", response_model=OptionsQuote)
def options_quote(
    payload: OptionsQuoteRequest,
    access: ReadAccess,
    request: Request,
    response: Response,
    _csrf: Annotated[None, Depends(csrf_guard)],
):
    buyer = access.buyer()
    response.headers["Cache-Control"] = "no-store"
    return CheckoutOptionsService(request.app.state.settings).quote(
        payload, CouponRepository(access.repository.session), buyer.user_id
    )


@router.get("/orders/checkout-status", response_model=CheckoutStatusResponse)
def checkout_status(
    access: ReadAccess,
    response: Response,
    key: Annotated[UUID, Header(alias="Idempotency-Key")],
):
    repository = CheckoutRepository(access.repository.session, access.buyer().user_id)
    previous = repository.existing(key)
    response.headers["Cache-Control"] = "no-store"
    return CheckoutStatusResponse(data=repository.detail(previous) if previous else None)


@router.post("/orders/checkout", response_model=CheckoutResponse, status_code=201)
def checkout(
    payload: CheckoutRequest,
    response: Response,
    request: Request,
    key: Annotated[UUID, Header(alias="Idempotency-Key")],
    subject: Annotated[int, Depends(current_subject)],
    _csrf: Annotated[None, Depends(csrf_guard)],
    session: Annotated[Session, Depends(get_session)],
):
    data, replay = CheckoutService(session, subject, request.app.state.settings).checkout(
        payload, key
    )
    response.status_code = 200 if replay else 201
    response.headers["Cache-Control"] = "no-store"
    return CheckoutResponse(data=data)
