import io
import json
import logging
from uuid import UUID

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from app.core.config import Settings
from app.core.errors import APIError
from app.core.logging import JsonFormatter
from app.main import create_app


@pytest.fixture
def client():
    app = create_app(Settings(environment="test"))

    class Payload(BaseModel):
        password: str = Field(min_length=20)

    @app.post("/test/validate")
    async def validate(payload: Payload):
        return {"ok": True}

    @app.get("/test/crash")
    async def crash():
        raise RuntimeError("secret-password-and-database-url")

    @app.get("/test/domain")
    async def domain():
        raise APIError(409, "OUT_OF_STOCK", "Không đủ tồn kho")

    @app.get("/test/auth")
    async def auth():
        raise HTTPException(
            status_code=401,
            detail="private-internal-detail",
            headers={"WWW-Authenticate": "Bearer"},
        )

    with TestClient(app) as test_client:
        yield test_client


def test_liveness_and_readiness_are_distinct(client):
    live = client.get("/health/live")
    assert live.status_code == 200
    assert live.json() == {"status": "ok"}
    ready = client.get("/health/ready")
    assert ready.status_code == 503
    assert ready.json()["error"]["code"] == "DEPENDENCY_UNAVAILABLE"


@pytest.mark.parametrize("supplied", ["request-123", "", "bad id", "x" * 65])
def test_request_id_is_validated_and_correlates_with_error(client, supplied):
    response = client.get("/unknown", headers={"X-Request-ID": supplied})
    request_id = response.headers["X-Request-ID"]
    if supplied == "request-123":
        assert request_id == supplied
    else:
        UUID(request_id)
    assert response.status_code == 404
    assert response.json()["error"]["request_id"] == request_id
    assert response.headers["Cache-Control"] == "no-store"


def test_method_not_allowed_preserves_allow_header(client):
    response = client.post("/health/live")
    assert response.status_code == 405
    assert "GET" in response.headers["allow"]
    assert response.json()["error"]["code"] == "METHOD_NOT_ALLOWED"


def test_validation_does_not_echo_password_or_context(client):
    response = client.post("/test/validate", json={"password": "sensitive-value"})
    assert response.status_code == 422
    assert response.json()["error"]["message"] == "Dữ liệu không hợp lệ"
    assert "sensitive-value" not in response.text
    assert response.json()["error"]["details"] == [
        {"field": "body.password", "reason": "string_too_short"}
    ]


def test_internal_errors_do_not_leak_exception_or_debug_page(client):
    response = client.get("/test/crash")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert "secret-password" not in response.text
    assert "RuntimeError" not in response.text
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]


def test_domain_error_and_http_auth_error(client):
    domain = client.get("/test/domain")
    assert domain.status_code == 409
    assert domain.json()["error"]["code"] == "OUT_OF_STOCK"
    auth = client.get("/test/auth")
    assert auth.status_code == 401
    assert auth.headers["WWW-Authenticate"] == "Bearer"
    assert "private-internal-detail" not in auth.text


def test_openapi_contains_health_and_error_models(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "/health/live" in schema["paths"]
    assert "503" in schema["paths"]["/health/ready"]["get"]["responses"]
    assert "ErrorResponse" in schema["components"]["schemas"]
    assert client.get("/docs").status_code == 200


def test_production_disables_public_documentation():
    with TestClient(create_app(Settings(environment="production"))) as client:
        assert client.get("/docs").status_code == 404
        assert client.get("/openapi.json").status_code == 404
        assert client.get("/health/live").status_code == 200


def test_request_logging_omits_query_headers_body_and_concrete_path(client):
    # Use a temporary handler because configure_logging intentionally keeps one handler.
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("marketplace")
    logger.addHandler(handler)
    try:
        response = client.post(
            "/unknown-sensitive-path?token=private-query",
            headers={"Authorization": "Bearer private-header"},
            json={"password": "private-body"},
        )
        record = json.loads(stream.getvalue().strip())
        assert record["route"] == "<unmatched>"
        assert record["status_code"] == 404
        assert record["request_id"] == response.headers["X-Request-ID"]
        assert "private-query" not in stream.getvalue()
        assert "private-header" not in stream.getvalue()
        assert "private-body" not in stream.getvalue()
        assert "unknown-sensitive-path" not in stream.getvalue()
    finally:
        logger.removeHandler(handler)
