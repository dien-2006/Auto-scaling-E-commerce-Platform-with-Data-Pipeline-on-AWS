from pydantic import BaseModel


class ErrorDetail(BaseModel):
    field: str
    reason: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail]
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorBody
