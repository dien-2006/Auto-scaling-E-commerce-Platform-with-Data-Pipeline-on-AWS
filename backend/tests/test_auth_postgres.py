"""Auth writes are opt-in and restricted to a disposable marketplace_test PostgreSQL."""

import os
import secrets
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text

from app.core.config import Settings
from app.core.errors import APIError
from app.core.security import verify_password
from app.db.base import Base
from app.db.session import Database
from app.main import create_app
from app.models import User
from app.repositories.users import UserRepository
from app.schemas.auth import RegisterRequest
from app.services.auth import AuthService


@pytest.fixture(scope="module")
def auth_database():
    if os.environ.get("MARKETPLACE_TEST_DB_NAME") != "marketplace_test":
        pytest.skip("Requires disposable marketplace_test PostgreSQL, never existing data")
    cfg = Settings(
        environment="test",
        public_origin="http://testserver",
        jwt_secret=secrets.token_urlsafe(48),
        db_host=os.environ["MARKETPLACE_TEST_DB_HOST"],
        db_port=int(os.environ["MARKETPLACE_TEST_DB_PORT"]),
        db_name="marketplace_test",
        db_user=os.environ["MARKETPLACE_TEST_DB_USER"],
        db_password=os.environ["MARKETPLACE_TEST_DB_PASSWORD"],
    )
    db = Database(cfg)
    with db.engine.begin() as connection:
        assert connection.scalar(text("SELECT current_database()")) == "marketplace_test"
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS marketplace"))
        Base.metadata.create_all(connection)  # Disposable test database only.
    yield cfg, db
    db.close()


def payload():
    return {
        "email": f"auth-{uuid4().hex}@example.com",
        "password": "  Mật khẩu đủ dài 1!  ",
        "full_name": " Người dùng thử ",
        "phone": "+84 901234567",
    }


def csrf(client):
    token = client.get("/api/v1/auth/csrf").json()["data"]["csrf_token"]
    return {"Origin": "http://testserver", "X-CSRF-Token": token}


def test_registration_login_me_and_database_hash(auth_database):
    cfg, db = auth_database
    data = payload()
    with TestClient(create_app(cfg)) as client:
        headers = csrf(client)
        created = client.post("/api/v1/auth/register", json=data, headers=headers)
        assert created.status_code == 201
        user = created.json()["data"]
        assert user["user_role"] == "USER" and user["user_status"] == "ACTIVE"
        assert user["full_name"] == "Người dùng thử"
        assert "password" not in created.text and "token" not in created.text
        assert "marketplace_access" not in client.cookies
        repeated = client.post(
            "/api/v1/auth/register", json=data | {"email": data["email"].upper()}, headers=headers
        )
        assert repeated.status_code == 409 and repeated.json()["error"]["code"] == "EMAIL_EXISTS"
        for login in (
            {"email": data["email"], "password": "wrong-password-123"},
            {"email": f"missing-{uuid4().hex}@example.com", "password": data["password"]},
        ):
            failed = client.post("/api/v1/auth/login", json=login, headers=headers)
            assert failed.status_code == 401
            assert failed.json()["error"]["code"] == "INVALID_CREDENTIALS"
        result = client.post(
            "/api/v1/auth/login",
            json={"email": data["email"].upper(), "password": data["password"]},
            headers=headers,
        )
        assert result.status_code == 200
        assert client.get("/api/v1/auth/me").json()["data"] == user
        # A separate application instance accepts the same signed cookie, no process session.
        with TestClient(create_app(cfg)) as replica:
            replica.cookies.update(client.cookies)
            assert replica.get("/api/v1/auth/me").json()["data"] == user
        with db.sessions() as session:
            stored = session.get(User, int(user["user_id"]))
            assert stored.password_hash.startswith("$argon2id$")
            assert verify_password(stored.password_hash, data["password"])
            assert not verify_password(stored.password_hash, data["password"].strip())
        assert client.post("/api/v1/auth/logout", headers=csrf(client)).status_code == 204
        assert client.get("/api/v1/auth/me").status_code == 401


def test_lock_and_current_role_after_token_issue(auth_database):
    cfg, db = auth_database
    data = payload()
    with TestClient(create_app(cfg)) as client:
        headers = csrf(client)
        user = client.post("/api/v1/auth/register", json=data, headers=headers).json()["data"]
        result = client.post(
            "/api/v1/auth/login",
            json={"email": data["email"], "password": data["password"]},
            headers=headers,
        )
        assert result.status_code == 200
        with db.sessions.begin() as session:
            stored = session.get(User, int(user["user_id"]))
            stored.user_role = "ADMIN"
        assert client.get("/api/v1/auth/me").json()["data"]["user_role"] == "ADMIN"
        with db.sessions.begin() as session:
            session.get(User, int(user["user_id"])).user_status = "LOCKED"
        assert client.get("/api/v1/auth/me").json()["error"]["code"] == "USER_LOCKED"
        result = client.post(
            "/api/v1/auth/login",
            json={"email": data["email"], "password": data["password"]},
            headers=csrf(client),
        )
        assert result.status_code == 403
        # Logout is allowed even for locked users and clears cookies without a user query.
        assert client.post("/api/v1/auth/logout", headers=csrf(client)).status_code == 204


def test_concurrent_case_insensitive_registration(auth_database):
    cfg, db = auth_database
    data = payload()

    def register(index):
        with TestClient(create_app(cfg)) as client:
            body = data | {"email": data["email"].upper() if index else data["email"]}
            return client.post("/api/v1/auth/register", json=body, headers=csrf(client)).status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(register, range(2))) == [201, 409]
    with db.sessions() as session:
        assert (
            session.scalar(
                select(func.count())
                .select_from(User)
                .where(func.lower(User.email) == data["email"])
            )
            == 1
        )


def test_validation_csrf_and_rollback(auth_database):
    cfg, db = auth_database
    data = payload()
    with TestClient(create_app(cfg)) as client:
        headers = csrf(client)
        for extra in ({"user_role": "ADMIN"}, {"full_name": " "}, {"phone": "bad"}):
            response = client.post("/api/v1/auth/register", json=data | extra, headers=headers)
            assert response.status_code == 422
            assert data["password"] not in response.text
        response = client.post(
            "/api/v1/auth/register", json=data, headers=headers | {"Origin": "https://evil.test"}
        )
        assert response.status_code == 403

    class FailingRepository(UserRepository):
        def add(self, **kwargs):
            super().add(**kwargs)
            raise APIError(503, "DEPENDENCY_UNAVAILABLE", "Test rollback")

    with db.sessions() as session:
        with pytest.raises(APIError):
            AuthService(FailingRepository(session)).register(RegisterRequest(**data))
    with db.sessions() as session:
        assert session.scalar(select(User).where(User.email == data["email"])) is None
