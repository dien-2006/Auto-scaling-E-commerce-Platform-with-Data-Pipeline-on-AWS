from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import event
from sqlalchemy.exc import SQLAlchemyError
from test_checkout_postgres import checkout_db as checkout_db  # noqa: F401
from test_checkout_postgres import client_for, csrf
from test_checkout_postgres import world as world  # noqa: F401

from app.db.session import get_session
from app.models import Shop, User


@pytest.fixture
def admin_world(world):
    cfg, db, r = world
    prefix = uuid4().hex
    with db.sessions.begin() as s:
        ids = [*r["buyers"], *[s.get(Shop, sid).owner_user_id for sid in r["shops"]]]
        for index, uid in enumerate(ids):
            user = s.get(User, uid)
            user.full_name = f"{prefix} User {index}"
            user.phone = f"{prefix[:8]}-{index}"
            if index < 2:
                user.user_role = "ADMIN"
        s.get(User, ids[3]).user_status = "LOCKED"
    return cfg, db, r, ids, prefix


def change(c, uid, status):
    return c.patch(
        f"/api/v1/admin/users/{uid}/status", json={"user_status": status}, headers=csrf(c)
    )


def test_search_pagination_projection_and_readonly(admin_world):
    cfg, db, _, ids, prefix = admin_world
    statements = []

    def record(conn, cursor, statement, params, context, executemany):
        statements.append(statement)

    event.listen(db.engine, "before_cursor_execute", record)
    try:
        with client_for(cfg, ids[0]) as c:

            def observed_session():
                with db.sessions() as session:
                    yield session

            c.app.dependency_overrides[get_session] = observed_session
            pages = [
                c.get("/api/v1/admin/users", params={"q": prefix, "page_size": 2, "page": p})
                for p in [1, 2]
            ]
            assert all(r.status_code == 200 for r in pages)
            assert pages[0].headers["cache-control"] == "no-store"
            rows = [r for response in pages for r in response.json()["items"]]
            assert {row["user_id"] for row in rows} == {str(uid) for uid in ids}
            assert [int(row["user_id"]) for row in rows] == sorted(ids, reverse=True)
            assert all(
                set(row)
                == {
                    "user_id",
                    "email",
                    "full_name",
                    "phone",
                    "user_role",
                    "user_status",
                    "created_at",
                }
                for row in rows
            )
            assert (
                c.get("/api/v1/admin/users", params={"q": prefix, "status": "LOCKED"}).json()[
                    "total"
                ]
                == 1
            )
            assert c.get("/api/v1/admin/users?q=%25_").json()["total"] == 0
            assert (
                c.get("/api/v1/admin/users", params={"q": prefix, "page": 2147483647}).json()[
                    "items"
                ]
                == []
            )
            for field in [rows[0]["email"], rows[0]["phone"]]:
                found = c.get("/api/v1/admin/users", params={"q": field}).json()
                assert any(row["user_id"] == rows[0]["user_id"] for row in found["items"])
        assert any("SET TRANSACTION READ ONLY" in q for q in statements)
        assert not any("password_hash" in q for q in statements)
        assert not any(
            q.lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE")) for q in statements
        )
    finally:
        event.remove(db.engine, "before_cursor_execute", record)


def test_lock_unlock_existing_token_and_preserve_shop(admin_world):
    cfg, db, r, ids, _ = admin_world
    with client_for(cfg, ids[0]) as admin, client_for(cfg, ids[2]) as target:
        assert target.get("/api/v1/auth/me").status_code == 200
        for _ in range(2):
            response = change(admin, ids[2], "LOCKED")
            assert (
                response.status_code == 200 and response.json()["data"]["user_status"] == "LOCKED"
            )
            assert "password_hash" not in response.text
        assert target.get("/api/v1/auth/me").status_code == 403
        assert target.get("/api/v1/seller/orders").status_code == 403
        for _ in range(2):
            assert change(admin, ids[2], "ACTIVE").status_code == 200
        assert target.get("/api/v1/auth/me").status_code == 200
    with db.sessions() as s:
        assert s.get(Shop, r["shops"][0]).shop_status == "APPROVED"
        assert s.get(User, ids[2]).user_role == "USER"


def test_role_status_guest_csrf_and_missing_user(admin_world):
    cfg, db, _, ids, _ = admin_world
    with client_for(cfg, ids[2]) as c:
        assert c.get("/api/v1/admin/users").status_code == 403
        assert change(c, ids[3], "ACTIVE").status_code == 403
    with client_for(cfg, ids[0]) as c:
        assert (
            c.patch(
                f"/api/v1/admin/users/{ids[2]}/status", json={"user_status": "LOCKED"}
            ).status_code
            == 403
        )
        assert (
            c.patch(
                f"/api/v1/admin/users/{ids[2]}/status",
                json={"user_status": "LOCKED"},
                headers=csrf(c) | {"Origin": "https://hostile.invalid"},
            ).status_code
            == 403
        )
        assert change(c, 9223372036854775807, "ACTIVE").status_code == 404
        with db.sessions.begin() as s:
            s.get(User, ids[0]).user_role = "USER"
        assert c.get("/api/v1/admin/users").status_code == 403
        assert change(c, ids[2], "LOCKED").status_code == 403
        with db.sessions.begin() as s:
            user = s.get(User, ids[0])
            user.user_role = "ADMIN"
            user.user_status = "LOCKED"
        assert c.get("/api/v1/admin/users").status_code == 403
        assert change(c, ids[2], "LOCKED").status_code == 403
        c.cookies.clear()
        assert c.get("/api/v1/admin/users").status_code == 401


@pytest.mark.parametrize(
    "query", ["status=OTHER", "page=0", "page_size=101", "extra=1", "q=" + "a" * 201]
)
def test_query_validation(admin_world, query):
    cfg, _, _, ids, _ = admin_world
    with client_for(cfg, ids[0]) as c:
        assert c.get("/api/v1/admin/users?" + query).status_code == 422


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"user_status": "OTHER"},
        {"user_status": True},
        {"user_status": "LOCKED", "user_role": "ADMIN"},
        {"user_status": "ACTIVE", "email": "changed@example.com"},
    ],
)
def test_mass_assignment_and_validation(admin_world, body):
    cfg, _, _, ids, _ = admin_world
    with client_for(cfg, ids[0]) as c:
        assert (
            c.patch(f"/api/v1/admin/users/{ids[2]}/status", json=body, headers=csrf(c)).status_code
            == 422
        )


def test_commit_failure_rolls_back(admin_world):
    cfg, db, _, ids, _ = admin_world

    def fail(session):
        raise SQLAlchemyError("private DSN")

    def broken():
        with db.sessions() as s:
            event.listen(s, "before_commit", fail)
            yield s

    with client_for(cfg, ids[0]) as c:
        headers = csrf(c)
        c.app.dependency_overrides[get_session] = broken
        result = c.patch(
            f"/api/v1/admin/users/{ids[2]}/status", json={"user_status": "LOCKED"}, headers=headers
        )
        assert result.status_code == 503 and "private DSN" not in result.text
    with db.sessions() as s:
        assert s.get(User, ids[2]).user_status == "ACTIVE"


def test_concurrent_admins_same_target_no_deadlock(admin_world):
    cfg, db, _, ids, _ = admin_world
    barrier = Barrier(2)

    def run(index):
        with client_for(cfg, ids[index]) as c:
            headers = csrf(c)
            barrier.wait(timeout=10)
            return c.patch(
                f"/api/v1/admin/users/{ids[2]}/status",
                json={"user_status": "LOCKED"},
                headers=headers,
            ).status_code

    with ThreadPoolExecutor(2) as pool:
        assert list(pool.map(run, range(2))) == [200, 200]
    with db.sessions() as s:
        assert s.get(User, ids[2]).user_status == "LOCKED"


def test_admin_accounts_are_readonly_including_self_and_locked_admin(admin_world):
    cfg, db, _, ids, _ = admin_world
    with client_for(cfg, ids[0]) as c:
        for uid in ids[:2]:
            for target in ["ACTIVE", "LOCKED"]:
                result = change(c, uid, target)
                assert result.status_code == 403
                assert result.json()["error"]["code"] == "ADMIN_PROTECTED"
        with db.sessions.begin() as s:
            s.get(User, ids[1]).user_status = "LOCKED"
        assert change(c, ids[1], "ACTIVE").status_code == 403
    with db.sessions() as s:
        assert s.get(User, ids[0]).user_status == "ACTIVE"
        assert s.get(User, ids[1]).user_status == "LOCKED"
