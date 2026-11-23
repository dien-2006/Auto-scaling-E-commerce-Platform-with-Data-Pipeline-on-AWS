"""Writes only in explicitly configured disposable marketplace_test PostgreSQL."""

import os
import secrets
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, func, select, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings
from app.core.security import Security
from app.db.base import Base
from app.db.session import Database, get_session
from app.main import create_app
from app.models import Address, Order, User

PAYLOAD = {
    "recipient_name": " Mai ",
    "phone": "0901234567",
    "address_line": "12 Nguyễn Huệ",
    "city": "Hà Nội",
    "is_default": True,
}


@pytest.fixture(scope="module")
def address_db():
    if os.environ.get("MARKETPLACE_TEST_DB_NAME") != "marketplace_test":
        pytest.skip("Requires disposable marketplace_test PostgreSQL")
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
    with db.engine.begin() as conn:
        assert conn.scalar(text("SELECT current_database()")) == "marketplace_test"
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS marketplace"))
        Base.metadata.create_all(conn)  # Only this guarded disposable DB.
    yield cfg, db
    db.close()


@pytest.fixture
def world(address_db):
    cfg, db = address_db
    with db.sessions.begin() as session:
        users = [
            User(
                email=f"{uuid4().hex}@example.com",
                password_hash="unused",
                full_name="Test",
                user_role=role,
            )
            for role in ["USER", "USER", "ADMIN"]
        ]
        session.add_all(users)
        session.flush()
        ids = [user.user_id for user in users]
    yield cfg, db, ids


def client_for(cfg, uid):
    client = TestClient(create_app(cfg))
    sec = Security(cfg)
    client.cookies.set(sec.access_cookie, sec.issue_access(uid))
    return client


def csrf(client):
    token = client.get("/api/v1/auth/csrf").json()["data"]["csrf_token"]
    return {"Origin": "http://testserver", "X-CSRF-Token": token}


def test_crud_defaults_privacy_snapshot(world):
    cfg, db, ids = world
    with client_for(cfg, ids[0]) as client:
        assert client.get("/api/v1/addresses").json() == {"data": {"items": []}}
        headers = csrf(client)
        first = client.post("/api/v1/addresses", json=PAYLOAD, headers=headers)
        assert first.status_code == 201
        a = first.json()["data"]
        assert a["recipient_name"] == "Mai" and "user_id" not in a
        assert first.headers["cache-control"] == "no-store"
        second = client.post(
            "/api/v1/addresses", json=PAYLOAD | {"recipient_name": "Second"}, headers=headers
        )
        b = second.json()["data"]
        rows = client.get("/api/v1/addresses").json()["data"]["items"]
        assert rows[0]["address_id"] == b["address_id"] and sum(r["is_default"] for r in rows) == 1
        with db.sessions.begin() as session:
            order = Order(
                buyer_user_id=ids[0],
                idempotency_key=uuid4(),
                payment_method="COD",
                total_amount="0",
                recipient_name="Original",
                phone="0900000000",
                shipping_address="Immutable snapshot",
            )
            session.add(order)
            session.flush()
            order_id = order.order_id
        patched = client.patch(
            f"/api/v1/addresses/{a['address_id']}",
            json={"is_default": True, "ward": "Phường A"},
            headers=headers,
        )
        assert patched.status_code == 200 and patched.json()["data"]["is_default"]
        for row in [a, b]:
            assert (
                client.delete(f"/api/v1/addresses/{row['address_id']}", headers=headers).status_code
                == 204
            )
        assert client.get("/api/v1/addresses").json()["data"]["items"] == []
        with db.sessions() as session:
            assert session.get(Order, order_id).shipping_address == "Immutable snapshot"
            assert session.get(Order, order_id).recipient_name == "Original"


def test_auth_ownership_validation(world):
    cfg, db, ids = world
    with TestClient(create_app(cfg)) as guest:
        assert guest.get("/api/v1/addresses").status_code == 401
        assert guest.post("/api/v1/addresses", json=PAYLOAD).status_code == 401
    with client_for(cfg, ids[0]) as client:
        assert client.post("/api/v1/addresses", json=PAYLOAD).status_code == 403
        headers = csrf(client)
        created = client.post("/api/v1/addresses", json=PAYLOAD, headers=headers).json()["data"]
        assert (
            client.post(
                "/api/v1/addresses", json=PAYLOAD | {"user_id": ids[1]}, headers=headers
            ).status_code
            == 422
        )
        assert (
            client.patch(
                f"/api/v1/addresses/{created['address_id']}", json={}, headers=headers
            ).status_code
            == 422
        )
    for uid in ids[1:2]:  # Other USER has no ownership bypass.
        with client_for(cfg, uid) as other:
            assert other.get("/api/v1/addresses").json()["data"]["items"] == []
            for resource in [created["address_id"], "9223372036854775807"]:
                path = f"/api/v1/addresses/{resource}"
                assert (
                    other.patch(path, json={"is_default": True}, headers=csrf(other)).status_code
                    == 404
                )
                assert other.delete(path, headers=csrf(other)).status_code == 404
    with db.sessions.begin() as session:
        session.get(User, ids[0]).user_status = "LOCKED"
    with client_for(cfg, ids[0]) as locked:
        assert locked.get("/api/v1/addresses").status_code == 403
        assert (
            locked.delete(
                f"/api/v1/addresses/{created['address_id']}", headers=csrf(locked)
            ).status_code
            == 403
        )


def test_concurrent_create_and_switch_default_across_replicas(world):
    cfg, db, ids = world

    def create(_):
        with client_for(cfg, ids[0]) as client:
            response = client.post("/api/v1/addresses", json=PAYLOAD, headers=csrf(client))
            assert response.status_code == 201
            return response.json()["data"]["address_id"]

    with ThreadPoolExecutor(max_workers=4) as pool:
        addresses = list(pool.map(create, range(4)))

    def switch(address_id):
        with client_for(cfg, ids[0]) as client:
            return client.patch(
                f"/api/v1/addresses/{address_id}", json={"is_default": True}, headers=csrf(client)
            ).status_code

    with ThreadPoolExecutor(max_workers=4) as pool:
        assert list(pool.map(switch, addresses)) == [200] * 4
    with db.sessions() as session:
        assert (
            session.scalar(
                select(func.count())
                .select_from(Address)
                .where(Address.user_id == ids[0], Address.is_default.is_(True))
            )
            == 1
        )


def test_commit_failure_rolls_back_default_and_insert(world):
    cfg, db, ids = world
    with client_for(cfg, ids[0]) as client:
        headers = csrf(client)
        first = client.post("/api/v1/addresses", json=PAYLOAD, headers=headers).json()["data"]

        def fail(_):
            raise SQLAlchemyError("private connection information")

        def override():
            with db.sessions() as session:
                event.listen(session, "before_commit", fail)
                yield session

        client.app.dependency_overrides[get_session] = override
        result = client.post("/api/v1/addresses", json=PAYLOAD, headers=headers)
        assert result.status_code == 503 and "private" not in result.text
        client.app.dependency_overrides.clear()
        rows = client.get("/api/v1/addresses").json()["data"]["items"]
        assert (
            len(rows) == 1
            and rows[0]["address_id"] == first["address_id"]
            and rows[0]["is_default"]
        )
