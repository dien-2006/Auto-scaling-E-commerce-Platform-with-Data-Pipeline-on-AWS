import logging
import re
from time import perf_counter
from uuid import uuid4

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.errors import error_response
from app.core.metrics import HTTPMetrics

REQUEST_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
logger = logging.getLogger("marketplace.requests")


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp, metrics: HTTPMetrics | None = None) -> None:
        self.app = app
        self.metrics = metrics

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        supplied = Headers(scope=scope).get("x-request-id", "")
        request_id = supplied if REQUEST_ID.fullmatch(supplied) else str(uuid4())
        scope.setdefault("state", {})["request_id"] = request_id
        started_at = perf_counter()
        response_started = False
        status_code = 500

        async def send_response(message: Message) -> None:
            nonlocal response_started, status_code
            if message["type"] == "http.response.start":
                response_started = True
                status_code = message["status"]
                headers = MutableHeaders(scope=message)
                headers["X-Request-ID"] = request_id
                headers["Cache-Control"] = "no-store"
            await send(message)

        try:
            await self.app(scope, receive, send_response)
        except Exception:
            if response_started:
                raise
            response = error_response(500, "INTERNAL_ERROR", "Đã xảy ra lỗi hệ thống", request_id)
            await response(scope, receive, send_response)
        finally:
            route = getattr(scope.get("route"), "path", "<unmatched>")
            elapsed = perf_counter() - started_at
            if self.metrics is not None:
                self.metrics.observe(scope["method"], route, status_code, elapsed)
            logger.info(
                "request_completed",
                extra={
                    "request_id": request_id,
                    "method": scope["method"],
                    "route": route,
                    "status_code": status_code,
                    "duration_ms": round(elapsed * 1000, 2),
                },
            )
