from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.schemas.errors import ErrorBody, ErrorDetail, ErrorResponse


class APIError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(code)
        self.status_code = status_code
        self.code = code
        self.message = message


def error_response(
    status_code: int,
    code: str,
    message: str,
    request_id: str,
    details: list[ErrorDetail] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    payload = ErrorResponse(
        error=ErrorBody(code=code, message=message, details=details or [], request_id=request_id)
    )
    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(),
        headers={**(headers or {}), "X-Request-ID": request_id, "Cache-Control": "no-store"},
    )


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(APIError)
    async def api_error(request: Request, exc: APIError) -> JSONResponse:
        return error_response(exc.status_code, exc.code, exc.message, request.state.request_id)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Never return input, ctx or the original error message: they can contain secrets.
        details = [
            ErrorDetail(field=".".join(map(str, item["loc"])), reason=item["type"])
            for item in exc.errors()
        ]
        return error_response(
            422,
            "VALIDATION_ERROR",
            "Dữ liệu không hợp lệ",
            request.state.request_id,
            details,
        )

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        codes = {
            400: ("INVALID_REQUEST", "Yêu cầu không hợp lệ"),
            401: ("AUTH_REQUIRED", "Vui lòng đăng nhập"),
            403: ("FORBIDDEN", "Bạn không có quyền truy cập"),
            404: ("NOT_FOUND", "Không tìm thấy tài nguyên"),
            405: ("METHOD_NOT_ALLOWED", "Phương thức không được hỗ trợ"),
        }
        code, message = codes.get(exc.status_code, ("REQUEST_ERROR", "Không thể xử lý yêu cầu"))
        return error_response(
            exc.status_code, code, message, request.state.request_id, headers=exc.headers
        )
