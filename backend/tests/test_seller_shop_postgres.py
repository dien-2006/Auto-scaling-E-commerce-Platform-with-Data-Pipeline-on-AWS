"""Seller registration/profile checks run only on guarded disposable PostgreSQL16."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, func, select
from sqlalchemy.exc import SQLAlchemyError
from test_checkout_postgres import checkout_db as checkout_db  # noqa: F401
from test_checkout_postgres import client_for, csrf

from app.db.session import get_session
from app.main import create_app
from app.models import Shop, User


@pytest.fixture
def sellers(checkout_db):
    cfg, db = checkout_db
    with db.sessions.begin() as s:
        users = [
            User(
                email=f"{uuid4().hex}@example.com",
                password_hash="unused",
                full_name="Owner",
                user_role=role,
            )
            for role in ["USER", "USER", "ADMIN"]
        ]
        s.add_all(users)
        s.flush()
        ids = [u.user_id for u in users]
    return cfg, db, ids


def body(**changes):
    return {
        "shop_name": " Shop name ",
        "shop_slug": f"shop-{uuid4().hex}",
        "description": " Description ",
        "contact_email": "shop@example.com",
        **changes,
    }


def create(client, data=None):
    return client.post("/api/v1/seller/shop", json=data or body(), headers=csrf(client))


def test_registration_profile_readonly_and_public_projection(sellers):
    cfg, db, ids = sellers
    with client_for(cfg, ids[0]) as c:
        assert c.get("/api/v1/seller/shop").status_code == 404
        response = create(c)
        assert response.status_code == 201
        shop = response.json()["data"]
        assert shop["shop_status"] == "PENDING" and shop["owner_user_id"] == str(ids[0])
        assert shop["shop_name"] == "Shop name" and shop["description"] == "Description"
        assert shop["logo_url"] is None and shop["created_at"].endswith("Z")
        assert set(shop) == {
            "shop_id",
            "owner_user_id",
            "shop_name",
            "shop_slug",
            "description",
            "contact_email",
            "logo_url",
            "shop_status",
            "created_at",
            "updated_at",
        }
        assert response.headers["cache-control"] == "no-store"
        assert c.get(f"/api/v1/shops/{shop['shop_slug']}").status_code == 404
        statements = []

        def capture(conn, cursor, sql, parameters, context, executemany):
            statements.append(sql)

        event.listen(c.app.state.database.engine, "before_cursor_execute", capture)
        try:
            get = c.get("/api/v1/seller/shop")
            assert get.status_code == 200 and get.json()["data"] == shop
            assert any("SET TRANSACTION READ ONLY" in sql for sql in statements)
            assert get.headers["cache-control"] == "no-store"
        finally:
            event.remove(c.app.state.database.engine, "before_cursor_execute", capture)
        again = create(c)
        assert again.status_code == 409 and again.json()["error"]["code"] == "SHOP_EXISTS"
        with db.sessions.begin() as s:
            s.get(Shop, int(shop["shop_id"])).shop_status = "APPROVED"
            s.get(Shop, int(shop["shop_id"])).logo_key = "private/key"
        public = c.get(f"/api/v1/shops/{shop['shop_slug']}")
        assert public.status_code == 200
        assert "contact_email" not in public.text and "owner_user_id" not in public.text
        assert "private/key" not in c.get("/api/v1/seller/shop").text


@pytest.mark.parametrize("status", ["PENDING", "APPROVED", "REJECTED", "LOCKED"])
def test_owner_can_read_and_patch_profile_without_status_change(sellers, status):
    cfg, db, ids = sellers
    with client_for(cfg, ids[0]) as c:
        shop = create(c).json()["data"]
        with db.sessions.begin() as s:
            s.get(Shop, int(shop["shop_id"])).shop_status = status
        assert c.get("/api/v1/seller/shop").json()["data"]["shop_status"] == status
        result = c.patch(
            "/api/v1/seller/shop",
            json={"shop_name": " New name ", "description": None, "contact_email": None},
            headers=csrf(c),
        )
        assert result.status_code == 200
        updated = result.json()["data"]
        assert updated["shop_name"] == "New name" and updated["description"] is None
        assert updated["contact_email"] is None and updated["shop_status"] == status
        assert updated["shop_slug"] == shop["shop_slug"]
        assert updated["updated_at"] >= shop["updated_at"]
        assert c.get("/api/v1/seller/shop").json()["data"] == updated


def test_admin_and_other_owner_never_impersonate(sellers):
    cfg, _, ids = sellers
    with client_for(cfg, ids[0]) as owner:
        shop = create(owner).json()["data"]
    for uid in ids[1:2]:
        with client_for(cfg, uid) as foreign:
            assert foreign.get("/api/v1/seller/shop").status_code == 404
            assert (
                foreign.patch(
                    "/api/v1/seller/shop", json={"shop_name": "Foreign"}, headers=csrf(foreign)
                ).status_code
                == 404
            )
            assert (
                foreign.patch(
                    f"/api/v1/seller/shop/{shop['shop_id']}",
                    json={"shop_name": "Foreign"},
                    headers=csrf(foreign),
                ).status_code
                == 405
            )
            own = create(foreign).json()["data"]
            assert own["owner_user_id"] == str(uid) and own["shop_id"] != shop["shop_id"]
    with client_for(cfg, ids[0]) as owner:
        assert owner.get("/api/v1/seller/shop").json()["data"]["shop_name"] == "Shop name"


@pytest.mark.parametrize(
    "extra",
    [
        {"owner_user_id": "1"},
        {"shop_status": "APPROVED"},
        {"shop_id": "1"},
        {"logo_key": "private/key"},
        {"logo_url": "https://example.com/logo"},
        {"user_role": "ADMIN"},
    ],
)
def test_mass_assignment_rejected_on_create_and_patch(sellers, extra):
    cfg, db, ids = sellers
    with client_for(cfg, ids[0]) as c:
        assert create(c, body(**extra)).status_code == 422
        assert (
            c.patch(
                "/api/v1/seller/shop", json={"shop_name": "Test", **extra}, headers=csrf(c)
            ).status_code
            == 422
        )
    with db.sessions() as s:
        assert (
            s.scalar(select(func.count()).select_from(Shop).where(Shop.owner_user_id == ids[0]))
            == 0
        )


@pytest.mark.parametrize(
    "data",
    [
        {"shop_name": "   "},
        {"shop_name": "x" * 151},
        {"shop_slug": "Uppercase"},
        {"shop_slug": "../other"},
        {"shop_slug": "double--dash"},
        {"shop_slug": "x" * 161},
        {"contact_email": "bad"},
        {"description": "x" * 5001},
    ],
)
def test_create_validation(sellers, data):
    cfg, _, ids = sellers
    with client_for(cfg, ids[0]) as c:
        assert create(c, body(**data)).status_code == 422


@pytest.mark.parametrize(
    "data",
    [
        {},
        {"shop_name": None},
        {"shop_slug": "changed"},
        {"shop_name": "  "},
        {"description": "x" * 5001},
    ],
)
def test_patch_validation(sellers, data):
    cfg, _, ids = sellers
    with client_for(cfg, ids[0]) as c:
        assert c.patch("/api/v1/seller/shop", json=data, headers=csrf(c)).status_code == 422


def test_guest_csrf_and_locked_user(sellers):
    cfg, db, ids = sellers
    with TestClient(create_app(cfg)) as guest:
        assert guest.get("/api/v1/seller/shop").status_code == 401
        assert create(guest).status_code == 401
    with client_for(cfg, ids[0]) as c:
        for method in ["POST", "PATCH"]:
            assert (
                c.request(
                    method,
                    "/api/v1/seller/shop",
                    json=body() if method == "POST" else {"shop_name": "Other"},
                ).status_code
                == 403
            )
            assert (
                c.request(
                    method,
                    "/api/v1/seller/shop",
                    json=body() if method == "POST" else {"shop_name": "Other"},
                    headers=csrf(c) | {"Origin": "https://hostile.invalid"},
                ).status_code
                == 403
            )
        with db.sessions.begin() as s:
            s.get(User, ids[0]).user_status = "LOCKED"
        assert c.get("/api/v1/seller/shop").status_code == 403
        assert create(c).status_code == 403
        assert (
            c.patch("/api/v1/seller/shop", json={"shop_name": "Other"}, headers=csrf(c)).status_code
            == 403
        )


@pytest.mark.parametrize("same_owner", [True, False])
def test_concurrent_registration_across_app_instances(sellers, same_owner):
    cfg, db, ids = sellers
    barrier = Barrier(2)
    slug = f"race-{uuid4().hex}"

    def worker(uid):
        with client_for(cfg, uid) as c:
            headers = csrf(c)
            barrier.wait(timeout=10)
            return c.post("/api/v1/seller/shop", json=body(shop_slug=slug), headers=headers)

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(worker, [ids[0], ids[0] if same_owner else ids[1]]))
    assert sorted(r.status_code for r in responses) == [201, 409]
    conflict = next(r for r in responses if r.status_code == 409)
    assert conflict.json()["error"]["code"] == ("SHOP_EXISTS" if same_owner else "SLUG_EXISTS")
    with db.sessions() as s:
        assert (
            s.scalar(select(func.count()).select_from(Shop).where(Shop.owner_user_id.in_(ids))) == 1
        )


def test_commit_failure_rolls_back_create_and_patch(sellers):
    cfg, db, ids = sellers
    with client_for(cfg, ids[0]) as c:

        def fail(_):
            raise SQLAlchemyError("private DSN connection details")

        def broken_session():
            with db.sessions() as s:
                event.listen(s, "before_commit", fail)
                yield s

        c.app.dependency_overrides[get_session] = broken_session
        result = create(c)
        assert result.status_code == 503 and "private DSN" not in result.text
        with db.sessions() as s:
            assert (
                s.scalar(select(func.count()).select_from(Shop).where(Shop.owner_user_id == ids[0]))
                == 0
            )
        c.app.dependency_overrides.clear()
        shop = create(c).json()["data"]
        c.app.dependency_overrides[get_session] = broken_session
        result = c.patch("/api/v1/seller/shop", json={"shop_name": "Lost update"}, headers=csrf(c))
        assert result.status_code == 503 and "private DSN" not in result.text
        with db.sessions() as s:
            assert s.get(Shop, int(shop["shop_id"])).shop_name == "Shop name"
