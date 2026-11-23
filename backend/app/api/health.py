from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.core.errors import APIError
from app.schemas.errors import ErrorResponse

router = APIRouter(prefix="/health", tags=["Health"])


class LiveStatus(BaseModel):
    status: Literal["ok"] = "ok"


class ReadyStatus(BaseModel):
    status: Literal["ready"] = "ready"


@router.get("/live", response_model=LiveStatus)
async def live() -> LiveStatus:
    return LiveStatus()


@router.get("/ready", response_model=ReadyStatus, responses={503: {"model": ErrorResponse}})
def ready(request: Request) -> ReadyStatus:
    # Sync route runs DB I/O in FastAPI's worker thread, not the ASGI event loop.
    if not request.app.state.database.ready():
        raise APIError(503, "DEPENDENCY_UNAVAILABLE", "Dịch vụ chưa sẵn sàng")
    return ReadyStatus()
