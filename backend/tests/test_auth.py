import secrets
import time
from types import SimpleNamespace

import jwt
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import Response

from app.api.v1.routers.auth import service
from app.core.config import Settings
from app.core.errors import APIError
from app.core.security import PASSWORD_HASHER, Security, verify_password
from app.main import create_app
from app.schemas.auth import LoginRequest, RegisterRequest, UserPrivate


def settings(**extra):
    return Settings(
        environment="test",
        public_origin="http://testserver",
        jwt_secret=secrets.token_urlsafe(48),
        **extra,
    )


def request(cookies=None, headers=None):
    pairs = [(key.encode(), value.encode()) for key, value in (headers or {}).items()]
    if cookies:
        pairs.append((b"cookie", "; ".join(f"{k}={v}" for k, v in cookies.items()).encode()))
    return Request({"type": "http", "headers": pairs})


def test_csrf_explicit_additional_origin_still_requires_bound_token():
    sec = Security(settings(additional_origins=["http://localhost:3001"]))
    access = sec.issue_access(1)
    token = sec.issue_csrf(access)
    cookies = {sec.access_cookie: access, sec.csrf_cookie: token}
    for source in [sec.origin, "http://localhost:3001"]:
        sec.check_csrf(request(cookies, {"origin": source, "x-csrf-token": token}))
        sec.check_csrf(request(cookies, {"referer": source + "/dang-nhap", "x-csrf-token": token}))
    for source in [
        "http://localhost:3002",
        "http://localhost:3001.evil.test",
        "https://evil.test",
        "null",
    ]:
        with pytest.raises(APIError):
            sec.check_csrf(request(cookies, {"origin": source, "x-csrf-token": token}))
    with pytest.raises(APIError):
        sec.check_csrf(
            request(cookies, {"origin": "http://localhost:3001", "x-csrf-token": sec.issue_csrf()})
        )


@pytest.mark.parametrize(
    "value",
    [
        "http://localhost:3001/path",
        "http://user:pass@localhost:3001",
        "http://localhost:3001?token=x",
        "http://localhost:3001#x",
        "*",
        "null",
    ],
)
def test_additional_origins_must_be_exact(value):
    with pytest.raises(ValidationError):
        settings(additional_origins=[value])


def test_production_additional_origins_require_https():
    with pytest.raises(ValidationError):
        Settings(
            environment="production",
            public_origin="https://coco.test",
            additional_origins=["http://localhost:3001"],
        )
    cfg = Settings(
        environment="production",
        public_origin="https://coco.test",
        additional_origins=["https://seller.coco.test"],
    )
    assert str(cfg.additional_origins[0]) == "https://seller.coco.test/"


def test_password_validation_and_no_mass_assignment():
    data = RegisterRequest(
        email="  USER@Example.COM ", password="  Mật khẩu đủ dài 1!  ", full_name="  Người dùng  "
    )
    assert str(data.email) == "user@example.com"
    assert data.full_name == "Người dùng"
    assert data.password.get_secret_value() == "  Mật khẩu đủ dài 1!  "
    hashed = PASSWORD_HASHER.hash(data.password.get_secret_value())
    assert hashed.startswith("$argon2id$")
    assert verify_password(hashed, data.password.get_secret_value())
    assert not verify_password(hashed, "sai-mat-khau")
    assert not verify_password("corrupt-hash", "some-password")
    for extras in ({"user_role": "ADMIN"}, {"user_status": "ACTIVE"}, {"owner_user_id": "1"}):
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="a@example.com", password="Valid-password-123", full_name="User", **extras
            )
    for password in ("", "x" * 129):
        with pytest.raises(ValidationError):
            LoginRequest(email="a@example.com", password=password)


@pytest.mark.parametrize(
    "change",
    [
        {"exp": 1},
        {"iat": int(time.time()) + 1000},
        {"iss": "other"},
        {"aud": "other"},
        {"sub": "0"},
        {"sub": "9223372036854775808"},
        {"sub": 1},
        {"sub": "01"},
        {"exp": int(time.time()) + 86400},
        {"iat": "1"},
        {"aud": ["marketplace-web"]},
    ],
)
def test_reject_bad_claims(change):
    security = Security(settings())
    now = int(time.time())
    claims = {
        "sub": "9007199254740993",
        "iat": now,
        "exp": now + 900,
        "iss": "marketplace",
        "aud": "marketplace-web",
    } | change
    token = jwt.encode(claims, security.key, algorithm="HS256")
    with pytest.raises(APIError) as exc:
        security.subject(request({security.access_cookie: token}))
    assert exc.value.status_code == 401


def test_jwt_algorithm_signature_required_claims_and_bigint():
    security = Security(settings())
    token = security.issue_access(9007199254740993)
    assert security.subject(request({security.access_cookie: token})) == 9007199254740993
    claims = jwt.decode(token, options={"verify_signature": False})
    assert set(claims) == {"sub", "iat", "exp", "iss", "aud"}
    invalid = [
        jwt.encode(claims, security.key, algorithm="HS384"),
        jwt.encode(claims, secrets.token_urlsafe(48), algorithm="HS256"),
        jwt.encode(claims, key="", algorithm="none"),
    ]
    for missing in claims:
        invalid.append(
            jwt.encode(
                {k: v for k, v in claims.items() if k != missing}, security.key, algorithm="HS256"
            )
        )
    for value in invalid:
        with pytest.raises(APIError):
            security.subject(request({security.access_cookie: value}))
    with pytest.raises(APIError) as exc:
        security.subject(request(headers={"authorization": f"Bearer {token}"}))
    assert exc.value.code == "AUTH_REQUIRED"


@pytest.mark.parametrize(
    "origin",
    [
        "null",
        "https://evil.test",
        "http://testserver.evil.test",
        "http://testserver/",
        "http://testserver:81",
    ],
)
def test_csrf_requires_exact_origin(origin):
    sec = Security(settings())
    token = sec.issue_csrf()
    with pytest.raises(APIError) as exc:
        sec.check_csrf(request({sec.csrf_cookie: token}, {"origin": origin, "x-csrf-token": token}))
    assert exc.value.code == "CSRF_FAILED"


def test_csrf_signature_binding_expiration_and_referer():
    sec = Security(settings())
    access = sec.issue_access(1)
    token = sec.issue_csrf(access)
    cookies = {sec.access_cookie: access, sec.csrf_cookie: token}
    sec.check_csrf(request(cookies, {"origin": sec.origin, "x-csrf-token": token}))
    sec.check_csrf(request(cookies, {"referer": sec.origin + "/page", "x-csrf-token": token}))
    forged_payload = f"{int(time.time()) - 3601}." + "a" * 48
    expired = forged_payload + "." + sec._signature(forged_payload, access)
    for cookie, header, current_access in [
        (token, token, ""),
        (token, token + "x", access),
        (token, sec.issue_csrf(access), access),
        (expired, expired, access),
        ("é", token, access),
    ]:
        with pytest.raises(APIError):
            sec.check_csrf(
                request(
                    {sec.csrf_cookie: cookie, sec.access_cookie: current_access},
                    {"origin": sec.origin, "x-csrf-token": header},
                )
            )


def test_production_cookies_and_logout():
    sec = Security(
        Settings(
            environment="production",
            public_origin="https://example.com",
            jwt_secret=secrets.token_urlsafe(48),
        )
    )
    response = Response()
    sec.login_cookies(response, 1)
    cookies = response.headers.getlist("set-cookie")
    assert len(cookies) == 2
    assert all("Secure" in c and "SameSite=lax" in c and "Path=/" in c for c in cookies)
    assert "__Host-marketplace_access=" in cookies[0] and "HttpOnly" in cookies[0]
    assert "__Host-marketplace_csrf=" in cookies[1] and "HttpOnly" not in cookies[1]
    assert all("Domain=" not in c for c in cookies)
    response = Response()
    sec.clear_cookies(response)
    assert all("Max-Age=0" in c for c in response.headers.getlist("set-cookie"))


def test_logout_expired_access_and_forged_csrf():
    cfg = settings()
    sec = Security(cfg)
    expired = jwt.encode(
        {"sub": "1", "iat": 1, "exp": 901, "iss": "marketplace", "aud": "marketplace-web"},
        sec.key,
        algorithm="HS256",
    )
    with TestClient(create_app(cfg)) as client:
        client.cookies.set(sec.access_cookie, expired)
        token = client.get("/api/v1/auth/csrf").json()["data"]["csrf_token"]
        headers = {"Origin": sec.origin, "X-CSRF-Token": token}
        assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
        payload = f"{int(time.time())}." + "a" * 48
        forged = payload + "." + "0" * 64
        client.cookies.set(sec.csrf_cookie, forged)
        response = client.post(
            "/api/v1/auth/logout", headers={"Origin": sec.origin, "X-CSRF-Token": forged}
        )
        assert response.status_code == 403


def test_routes_csrf_before_service_cookie_rotation_and_logout():
    cfg = settings()
    app = create_app(cfg)
    user = UserPrivate(
        user_id="1",
        email="a@example.com",
        full_name="Name",
        phone=None,
        user_role="USER",
        user_status="ACTIVE",
    )
    calls = []

    def login(_data):
        calls.append("login")
        return user

    app.dependency_overrides[service] = lambda: SimpleNamespace(
        login=login, register=lambda _: user, me=lambda _: user
    )
    with TestClient(app) as client:
        payload = {"email": "a@example.com", "password": "Valid-password-123"}
        assert client.post("/api/v1/auth/login", json=payload).status_code == 403
        assert calls == []
        csrf = client.get("/api/v1/auth/csrf").json()["data"]["csrf_token"]
        headers = {"Origin": "http://testserver", "X-CSRF-Token": csrf}
        result = client.post(
            "/api/v1/auth/register", json=payload | {"full_name": "Name"}, headers=headers
        )
        assert result.status_code == 201 and "marketplace_access" not in client.cookies
        result = client.post("/api/v1/auth/login", json=payload, headers=headers)
        assert result.status_code == 200
        assert "token" not in result.text and "hash" not in result.text
        assert result.headers["cache-control"] == "no-store"
        assert "HttpOnly" in result.headers.get_list("set-cookie")[0]
        assert client.get("/api/v1/auth/me").json()["data"]["user_id"] == "1"
        assert client.post("/api/v1/auth/logout", headers=headers).status_code == 403
        headers["X-CSRF-Token"] = client.cookies["marketplace_csrf"]
        result = client.post("/api/v1/auth/logout", headers=headers)
        assert result.status_code == 204 and not result.content
        assert "marketplace_access" not in client.cookies
        assert client.get("/api/v1/auth/me").status_code == 401


def test_missing_config_fails_closed_and_secret_validation():
    with TestClient(create_app(Settings(environment="test"))) as client:
        assert client.get("/api/v1/auth/csrf").status_code == 503
        assert client.get("/health/live").status_code == 200
    for secret in ("short", "a" * 48, "replace_with_your_random_secret_0123456789"):
        with pytest.raises(ValidationError):
            Settings(jwt_secret=secret, public_origin="http://testserver")
