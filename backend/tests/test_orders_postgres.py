"""Buyer history uses real disposable PostgreSQL fixtures, never the application DB."""

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, select
from test_checkout_postgres import checkout, client_for, payload
from test_checkout_postgres import checkout_db as checkout_db  # noqa: F401
from test_checkout_postgres import world as world  # noqa: F401

from app.main import create_app
from app.models import Address, Inventory, Order, Product, Shop, ShopOrder, User


def test_history_snapshots_mixed_status_and_locked_shop(world):
    cfg, db, r = world
    with client_for(cfg, r["buyers"][0]) as client:
        original = checkout(client, payload(r)).json()["data"]
        oid = original["order_id"]
        with db.sessions.begin() as s:
            s.delete(s.get(Address, r["addresses"][0]))
            product = s.get(Product, r["products"][0])
            product.product_name, product.price, product.is_active = "Changed", "88.88", False
            shop = s.get(Shop, r["shops"][0])
            shop.shop_name, shop.shop_status = "Renamed shop", "LOCKED"
            rows = s.scalars(
                select(ShopOrder).where(ShopOrder.order_id == int(oid)).order_by(ShopOrder.shop_id)
            ).all()
            rows[0].order_status, rows[1].order_status = "SHIPPING", "CANCELLED"
        response = client.get(f"/api/v1/orders/{oid}")
        assert response.status_code == 200
        detail = response.json()["data"]
        for field in ["recipient_name", "phone", "shipping_address", "total_amount"]:
            assert detail[field] == original[field]
        assert detail["shop_orders"][0]["items"] == original["shop_orders"][0]["items"]
        assert [row["order_status"] for row in detail["shop_orders"]] == ["SHIPPING", "CANCELLED"]
        assert detail["shop_orders"][0]["shop_name"] == "Renamed shop"
        history = client.get("/api/v1/orders").json()
        assert history["total"] == 1 and history["page_size"] == 24
        summary = history["items"][0]
        assert summary["total_amount"] == "18.01" and summary["created_at"].endswith("Z")
        assert "order_status" not in summary and "recipient_name" not in summary
        assert "items" not in summary["shop_orders"][0]
        for forbidden in [
            "buyer_user_id",
            "idempotency_key",
            "owner_user_id",
            "password_hash",
            "image_key",
        ]:
            assert forbidden not in response.text and forbidden not in str(history)
        assert response.headers["cache-control"] == "no-store"
        assert client.get("/api/v1/orders").headers["cache-control"] == "no-store"
        with db.sessions() as s:
            assert s.get(Inventory, r["products"][0]).quantity == 9


def test_other_buyer_and_admin_cannot_read_foreign_order(world):
    cfg, db, r = world
    with client_for(cfg, r["buyers"][0]) as owner:
        oid = checkout(owner, payload(r)).json()["data"]["order_id"]
    for role in ["USER"]:
        with db.sessions.begin() as s:
            s.get(User, r["buyers"][1]).user_role = role
        with client_for(cfg, r["buyers"][1]) as foreign:
            assert foreign.get("/api/v1/orders").json()["items"] == []
            a = foreign.get(f"/api/v1/orders/{oid}")
            b = foreign.get("/api/v1/orders/9223372036854775807")
            assert a.status_code == b.status_code == 404
            assert a.json()["error"]["code"] == b.json()["error"]["code"] == "NOT_FOUND"


def test_own_admin_order_and_unauthenticated_locked_user(world):
    cfg, db, r = world
    with client_for(cfg, r["buyers"][0]) as client:
        oid = checkout(client, payload(r)).json()["data"]["order_id"]
        with db.sessions.begin() as s:
            s.get(User, r["buyers"][0]).user_role = "ADMIN"
        assert client.get(f"/api/v1/orders/{oid}").status_code == 403
        assert client.get("/api/v1/orders").status_code == 403
        with db.sessions.begin() as s:
            s.get(User, r["buyers"][0]).user_status = "LOCKED"
        for path in ["/api/v1/orders", f"/api/v1/orders/{oid}"]:
            assert client.get(path).status_code == 403
    with TestClient(create_app(cfg)) as guest:
        assert guest.get("/api/v1/orders").status_code == 401
        assert guest.get(f"/api/v1/orders/{oid}").status_code == 401


def test_stable_pagination_and_constant_query_count_readonly(world):
    cfg, db, r = world
    ids = []
    with client_for(cfg, r["buyers"][0]) as client:
        # Multiple real checkouts from different buyers, then fixtures duplicate only
        # order snapshots for pagination (all writes in guarded marketplace_test).
        oid = int(checkout(client, payload(r)).json()["data"]["order_id"])
        with db.sessions.begin() as s:
            original = s.get(Order, oid)
            from uuid import uuid4

            for _ in range(3):
                order = Order(
                    buyer_user_id=r["buyers"][0],
                    idempotency_key=uuid4(),
                    recipient_name=original.recipient_name,
                    phone=original.phone,
                    shipping_address=original.shipping_address,
                    total_amount="18.01",
                    payment_method="COD",
                    created_at=datetime(2026, 1, 1, tzinfo=UTC),
                )
                s.add(order)
                s.flush()
                ids.append(str(order.order_id))
                for shop, price in zip(r["shops"], ["12.34", "5.67"], strict=True):
                    s.add(ShopOrder(order_id=order.order_id, shop_id=shop, subtotal=price))
            original.created_at = datetime(2026, 1, 1, tzinfo=UTC)
            ids.insert(0, str(oid))
        statements = []
        app = client.app

        def capture(conn, cursor, statement, parameters, context, executemany):
            statements.append(statement)

        event.listen(app.state.database.engine, "before_cursor_execute", capture)
        try:
            first = client.get("/api/v1/orders?page_size=2").json()
            selects = sum(sql.lstrip().upper().startswith("SELECT") for sql in statements)
            assert any("SET TRANSACTION READ ONLY" in sql for sql in statements)
            assert selects == 4  # principal, count, page, all shop summaries
            assert [row["order_id"] for row in first["items"]] == list(reversed(ids))[:2]
            statements.clear()
            second = client.get("/api/v1/orders?page=2&page_size=2").json()
            assert [row["order_id"] for row in second["items"]] == list(reversed(ids))[2:]
            assert sum(sql.lstrip().upper().startswith("SELECT") for sql in statements) == selects
            assert client.get("/api/v1/orders?page=3&page_size=2").json() == {
                "items": [],
                "page": 3,
                "page_size": 2,
                "total": 4,
            }
        finally:
            event.remove(app.state.database.engine, "before_cursor_execute", capture)


@pytest.mark.parametrize(
    "query",
    [
        "page=0",
        "page=-1",
        "page=2147483648",
        "page_size=0",
        "page_size=101",
        "page=abc",
        "buyer_user_id=1",
        "status=PENDING",
    ],
)
def test_order_query_validation(world, query):
    cfg, _, r = world
    with client_for(cfg, r["buyers"][0]) as client:
        assert client.get(f"/api/v1/orders?{query}").status_code == 422


@pytest.mark.parametrize("oid", ["0", "-1", "9223372036854775808", "abc"])
def test_order_path_validation(world, oid):
    cfg, _, r = world
    with client_for(cfg, r["buyers"][0]) as client:
        assert client.get(f"/api/v1/orders/{oid}").status_code == 422
