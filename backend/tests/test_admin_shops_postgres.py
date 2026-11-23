from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import event, func, select
from sqlalchemy.exc import SQLAlchemyError
from test_checkout_postgres import checkout, client_for, csrf, payload
from test_checkout_postgres import checkout_db as checkout_db  # noqa: F401
from test_checkout_postgres import world as world  # noqa: F401

from app.db.session import get_session
from app.models import Inventory, Order, Shop, ShopOrder, User


@pytest.fixture
def admin_shops(world):
    cfg, db, r = world
    prefix = uuid4().hex
    with db.sessions.begin() as s:
        s.get(User, r["buyers"][1]).user_role = "ADMIN"
        owners = []
        for i, sid in enumerate(r["shops"]):
            shop = s.get(Shop, sid)
            owners.append(shop.owner_user_id)
            shop.shop_name = f"{prefix} {i}"
            shop.contact_email = f"{prefix}-{i}@example.com"
            shop.logo_key = "private-key"
    return cfg, db, r, owners, prefix


def change(c, sid, target, expected="PENDING"):
    return c.patch(
        f"/api/v1/admin/shops/{sid}/status",
        headers=csrf(c),
        json={"expected_status": expected, "shop_status": target},
    )


def test_list_search_pagination_projection_readonly(admin_shops):
    cfg, db, r, _, prefix = admin_shops
    statements = []

    def record(conn, cursor, statement, params, context, executemany):
        statements.append(statement)

    def observed_session():
        with db.sessions() as s:
            yield s

    with client_for(cfg, r["buyers"][1]) as c:
        c.app.dependency_overrides[get_session] = observed_session
        event.listen(db.engine, "before_cursor_execute", record)
        try:
            response = c.get("/api/v1/admin/shops", params={"q": prefix, "page_size": 1})
            assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
            data = response.json()
            assert data["total"] == 2 and len(data["items"]) == 1
            assert data["items"][0]["shop_id"] == str(max(r["shops"]))
            assert data["items"][0]["logo_url"] is None
            assert "logo_key" not in response.text and "private-key" not in response.text
            assert "password_hash" not in response.text
            assert any("SET TRANSACTION READ ONLY" in q for q in statements)
            assert sum("FROM marketplace.shops" in q for q in statements) == 2
            assert not any(
                q.lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE")) for q in statements
            )
        finally:
            event.remove(db.engine, "before_cursor_execute", record)
        assert (
            c.get("/api/v1/admin/shops", params={"q": prefix, "status": "PENDING"}).json()["items"]
            == []
        )
        assert (
            c.get("/api/v1/admin/shops", params={"q": prefix, "page": 2147483647}).json()["items"]
            == []
        )
        assert c.get("/api/v1/admin/shops?q=%25_").json()["total"] == 0
        for value in [data["items"][0]["contact_email"], data["items"][0]["shop_slug"]]:
            assert c.get("/api/v1/admin/shops", params={"q": value}).json()["total"] == 1


def test_full_transition_matrix_no_unlock_and_noop_timestamp(admin_shops):
    cfg, db, r, _, _ = admin_shops
    sid = r["shops"][0]
    states = ["PENDING", "APPROVED", "REJECTED", "LOCKED"]
    allowed = {("PENDING", "APPROVED"), ("PENDING", "REJECTED"), ("APPROVED", "LOCKED")}
    with client_for(cfg, r["buyers"][1]) as c:
        for source in states:
            for target in states:
                with db.sessions.begin() as s:
                    shop = s.get(Shop, sid)
                    shop.shop_status = source
                with db.sessions() as s:
                    stamp = s.get(Shop, sid).updated_at
                response = change(c, sid, target, source)
                valid = source == target or (source, target) in allowed
                assert response.status_code == (200 if valid else 409), (source, target)
                with db.sessions() as s:
                    shop = s.get(Shop, sid)
                    assert shop.shop_status == (target if valid else source)
                    if source == target:
                        assert shop.updated_at == stamp
        with db.sessions.begin() as s:
            s.get(Shop, sid).shop_status = "PENDING"
        assert change(c, sid, "APPROVED", "APPROVED").status_code == 409
        assert change(c, sid, "APPROVED").status_code == 200
        assert change(c, sid, "APPROVED").status_code == 200
        assert change(c, sid, "REJECTED").status_code == 409


def test_lock_blocks_new_checkout_catalog_but_preserves_old_orders(admin_shops):
    cfg, db, r, owners, _ = admin_shops
    with client_for(cfg, r["buyers"][0]) as buyer:
        result = checkout(buyer, payload(r))
        assert result.status_code == 201
        order = result.json()["data"]
    with client_for(cfg, r["buyers"][1]) as admin:
        assert change(admin, r["shops"][0], "LOCKED", "APPROVED").status_code == 200
        assert checkout(admin, payload(r, 1)).status_code == 403
        assert admin.get(f"/api/v1/products/{r['products'][0]}").status_code == 404
    with client_for(cfg, owners[0]) as seller:
        sid = order["shop_orders"][0]["shop_order_id"]
        assert seller.get(f"/api/v1/seller/orders/{sid}").status_code == 200
        assert (
            seller.patch(
                f"/api/v1/seller/orders/{sid}/status",
                headers=csrf(seller),
                json={"expected_status": "PENDING", "status": "CONFIRMED"},
            ).status_code
            == 200
        )
        assert (
            seller.patch(
                f"/api/v1/seller/products/{r['products'][0]}",
                headers=csrf(seller),
                json={"price": "1"},
            ).status_code
            == 403
        )
        assert (
            seller.post(
                f"/api/v1/seller/products/{r['products'][0]}/inventory/adjustments",
                headers=csrf(seller) | {"X-Expected-Quantity": "9"},
                json={"delta": 1},
            ).status_code
            == 403
        )
    with db.sessions() as s:
        assert s.get(Inventory, r["products"][0]).quantity == 9
        assert s.get(Inventory, r["products"][1]).quantity == 9
        assert s.get(ShopOrder, int(sid)).order_status == "CONFIRMED"


def test_lock_races_checkout_without_partial_order_or_oversell(admin_shops):
    cfg, db, r, _, _ = admin_shops
    barrier = Barrier(2)

    def run(index):
        with client_for(cfg, r["buyers"][index]) as c:
            barrier.wait(timeout=10)
            return (
                checkout(c, payload(r))
                if index == 0
                else change(c, r["shops"][0], "LOCKED", "APPROVED")
            ).status_code

    with ThreadPoolExecutor(2) as pool:
        ordered, locked = list(pool.map(run, range(2)))
    assert ordered in [201, 409] and locked == 200
    with db.sessions() as s:
        assert s.get(Shop, r["shops"][0]).shop_status == "LOCKED"
        assert s.scalar(
            select(func.count()).select_from(Order).where(Order.buyer_user_id == r["buyers"][0])
        ) == (1 if ordered == 201 else 0)
        for pid in r["products"]:
            assert s.get(Inventory, pid).quantity == (9 if ordered == 201 else 10)


def test_approve_vs_reject_concurrently(admin_shops):
    cfg, db, r, _, _ = admin_shops
    with db.sessions.begin() as s:
        s.get(Shop, r["shops"][0]).shop_status = "PENDING"
    barrier = Barrier(2)

    def run(target):
        with client_for(cfg, r["buyers"][1]) as c:
            barrier.wait(timeout=10)
            return change(c, r["shops"][0], target).status_code

    with ThreadPoolExecutor(2) as pool:
        assert sorted(pool.map(run, ["APPROVED", "REJECTED"])) == [200, 409]


def test_permissions_seller_no_self_approval_revoked_role_and_csrf(admin_shops):
    cfg, db, r, owners, _ = admin_shops
    with client_for(cfg, owners[0]) as c:
        assert c.get("/api/v1/admin/shops").status_code == 403
        assert change(c, r["shops"][0], "APPROVED").status_code == 403
        assert (
            c.patch(
                "/api/v1/seller/shop", headers=csrf(c), json={"shop_status": "APPROVED"}
            ).status_code
            == 422
        )
    with client_for(cfg, r["buyers"][1]) as c:
        assert (
            c.patch(
                f"/api/v1/admin/shops/{r['shops'][0]}/status",
                json={"expected_status": "APPROVED", "shop_status": "LOCKED"},
            ).status_code
            == 403
        )
        assert change(c, 9223372036854775807, "APPROVED").status_code == 404
        with db.sessions.begin() as s:
            s.get(User, r["buyers"][1]).user_role = "USER"
        assert c.get("/api/v1/admin/shops").status_code == 403
        assert change(c, r["shops"][0], "LOCKED", "APPROVED").status_code == 403
        with db.sessions.begin() as s:
            user = s.get(User, r["buyers"][1])
            user.user_role = "ADMIN"
            user.user_status = "LOCKED"
        assert c.get("/api/v1/admin/shops").status_code == 403
        c.cookies.clear()
        assert c.get("/api/v1/admin/shops").status_code == 401


@pytest.mark.parametrize(
    "query", ["status=OTHER", "page=0", "page_size=101", "extra=1", "q=" + "a" * 201]
)
def test_query_validation(admin_shops, query):
    cfg, _, r, _, _ = admin_shops
    with client_for(cfg, r["buyers"][1]) as c:
        assert c.get("/api/v1/admin/shops?" + query).status_code == 422


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"expected_status": "PENDING", "shop_status": "OTHER"},
        {"shop_status": "APPROVED"},
        {"expected_status": "PENDING", "shop_status": "APPROVED", "owner_user_id": "1"},
    ],
)
def test_body_validation(admin_shops, body):
    cfg, _, r, _, _ = admin_shops
    with client_for(cfg, r["buyers"][1]) as c:
        assert (
            c.patch(
                f"/api/v1/admin/shops/{r['shops'][0]}/status", headers=csrf(c), json=body
            ).status_code
            == 422
        )


def test_commit_failure_rolls_back_status(admin_shops):
    cfg, db, r, _, _ = admin_shops

    def fail(session):
        raise SQLAlchemyError("private DSN")

    def broken():
        with db.sessions() as s:
            event.listen(s, "before_commit", fail)
            yield s

    with client_for(cfg, r["buyers"][1]) as c:
        headers = csrf(c)
        c.app.dependency_overrides[get_session] = broken
        response = c.patch(
            f"/api/v1/admin/shops/{r['shops'][0]}/status",
            headers=headers,
            json={"expected_status": "APPROVED", "shop_status": "LOCKED"},
        )
        assert response.status_code == 503 and "private DSN" not in response.text
    with db.sessions() as s:
        assert s.get(Shop, r["shops"][0]).shop_status == "APPROVED"
