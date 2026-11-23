from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import event
from sqlalchemy.exc import SQLAlchemyError
from test_checkout_postgres import checkout, client_for, csrf, payload
from test_checkout_postgres import checkout_db as checkout_db  # noqa: F401
from test_checkout_postgres import world as world  # noqa: F401
from test_seller_products_postgres import seller_world as seller_world  # noqa: F401

from app.db.session import get_session
from app.models import Inventory, Product, Shop, ShopOrder, User


@pytest.fixture
def placed(seller_world):
    cfg, db, r, owners, _ = seller_world
    with client_for(cfg, r["buyers"][0]) as c:
        response = checkout(c, payload(r))
        assert response.status_code == 201
    order = response.json()["data"]
    return cfg, db, r, owners, order


def change(c, sid, target, expected="PENDING"):
    return c.patch(
        f"/api/v1/seller/orders/{sid}/status",
        json={"expected_status": expected, "status": target},
        headers=csrf(c),
    )


def cancel(c, order, sid):
    return c.post(f"/api/v1/orders/{order}/shop-orders/{sid}/cancel", headers=csrf(c))


def test_list_projection_snapshots_and_state_machine(placed):
    cfg, db, r, owners, order = placed
    sid = order["shop_orders"][0]["shop_order_id"]
    with db.sessions.begin() as s:
        s.get(Product, r["products"][0]).product_name = "Changed name"
    with client_for(cfg, owners[0]) as c:
        result = c.get("/api/v1/seller/orders?page_size=1&status=PENDING")
        assert result.status_code == 200 and result.headers["cache-control"] == "no-store"
        assert result.json()["total"] == 1
        assert "phone" not in result.text and "recipient_name" not in result.text
        detail = c.get(f"/api/v1/seller/orders/{sid}").json()["data"]
        assert len(detail["items"]) == 1 and detail["items"][0]["product_name"] != "Changed name"
        assert detail["subtotal"] == "12.34" and detail["order_id"] == order["order_id"]
        assert "total_amount" not in detail and "buyer_user_id" not in detail
        assert change(c, sid, "SHIPPING").status_code == 409
        for source, target in [
            ("PENDING", "CONFIRMED"),
            ("CONFIRMED", "SHIPPING"),
            ("SHIPPING", "COMPLETED"),
        ]:
            assert change(c, sid, target, source).json()["data"]["order_status"] == target
            assert change(c, sid, target, source).status_code == 200
        assert change(c, sid, "CANCELLED", "COMPLETED").status_code == 409
        assert c.get("/api/v1/seller/orders?status=PENDING").json()["total"] == 0
        assert c.get("/api/v1/seller/orders?page=2147483647").json()["items"] == []
    with db.sessions() as s:
        assert s.get(Inventory, r["products"][0]).quantity == 9


def test_buyer_cancel_repeat_isolated_shop_and_hidden_catalog(placed):
    cfg, db, r, _, order = placed
    sid = order["shop_orders"][0]["shop_order_id"]
    with db.sessions.begin() as s:
        s.get(Product, r["products"][0]).is_active = False
        s.get(Shop, r["shops"][0]).shop_status = "LOCKED"
    with client_for(cfg, r["buyers"][0]) as c:
        for _ in range(2):
            assert cancel(c, order["order_id"], sid).json()["data"]["order_status"] == "CANCELLED"
    with db.sessions() as s:
        assert s.get(Inventory, r["products"][0]).quantity == 10
        assert s.get(Inventory, r["products"][1]).quantity == 9
        assert (
            s.get(ShopOrder, int(order["shop_orders"][1]["shop_order_id"])).order_status
            == "PENDING"
        )


@pytest.mark.parametrize("actor", ["buyer", "seller", "both"])
def test_simultaneous_cancellations_restore_once(placed, actor):
    cfg, db, r, owners, order = placed
    sid = order["shop_orders"][0]["shop_order_id"]
    barrier = Barrier(2)

    def run(index):
        buyer = actor == "buyer" or (actor == "both" and index == 0)
        with client_for(cfg, r["buyers"][0] if buyer else owners[0]) as c:
            headers = csrf(c)
            barrier.wait(timeout=10)
            if buyer:
                return c.post(
                    f"/api/v1/orders/{order['order_id']}/shop-orders/{sid}/cancel", headers=headers
                ).status_code
            return c.patch(
                f"/api/v1/seller/orders/{sid}/status",
                headers=headers,
                json={"expected_status": "PENDING", "status": "CANCELLED"},
            ).status_code

    with ThreadPoolExecutor(2) as pool:
        assert list(pool.map(run, range(2))) == [200, 200]
    with db.sessions() as s:
        assert s.get(Inventory, r["products"][0]).quantity == 10


def test_confirm_vs_buyer_cancel(placed):
    cfg, db, r, owners, order = placed
    sid = order["shop_orders"][0]["shop_order_id"]
    barrier = Barrier(2)

    def run(index):
        with client_for(cfg, owners[0] if index == 0 else r["buyers"][0]) as c:
            barrier.wait(timeout=10)
            return (
                change(c, sid, "CONFIRMED") if index == 0 else cancel(c, order["order_id"], sid)
            ).status_code

    with ThreadPoolExecutor(2) as pool:
        result = list(pool.map(run, range(2)))
    assert sorted(result) == [200, 409]
    with db.sessions() as s:
        state = s.get(ShopOrder, int(sid)).order_status
        assert s.get(Inventory, r["products"][0]).quantity == (10 if state == "CANCELLED" else 9)


def test_locked_shop_can_cancel_confirmed_buyer_cannot(placed):
    cfg, db, r, owners, order = placed
    sid = order["shop_orders"][0]["shop_order_id"]
    with client_for(cfg, owners[0]) as c:
        assert change(c, sid, "CONFIRMED").status_code == 200
    with db.sessions.begin() as s:
        s.get(Shop, r["shops"][0]).shop_status = "LOCKED"
    with client_for(cfg, r["buyers"][0]) as c:
        assert cancel(c, order["order_id"], sid).status_code == 409
    with client_for(cfg, owners[0]) as c:
        assert c.get("/api/v1/seller/orders").status_code == 200
        assert change(c, sid, "CANCELLED", "PENDING").status_code == 409
        assert change(c, sid, "CANCELLED", "CONFIRMED").status_code == 200
    with db.sessions() as s:
        assert s.get(Inventory, r["products"][0]).quantity == 10


def test_idor_validation_guest_csrf_and_locked_user(placed):
    cfg, db, r, owners, order = placed
    sid = order["shop_orders"][0]["shop_order_id"]
    with db.sessions.begin() as s:
        s.get(User, owners[1]).user_role = "ADMIN"
    with client_for(cfg, owners[1]) as c:
        assert c.get(f"/api/v1/seller/orders/{sid}").status_code == 404
        assert change(c, sid, "CANCELLED").status_code == 404
    with client_for(cfg, r["buyers"][1]) as c:
        assert cancel(c, order["order_id"], sid).status_code == 404
    with client_for(cfg, r["buyers"][0]) as c:
        assert cancel(c, "9223372036854775807", sid).status_code == 404
        assert (
            c.post(f"/api/v1/orders/{order['order_id']}/shop-orders/{sid}/cancel").status_code
            == 403
        )
    with client_for(cfg, owners[0]) as c:
        assert c.get("/api/v1/seller/orders?status=INVALID").status_code == 422
        assert c.get("/api/v1/seller/orders?other=1").status_code == 422
        assert (
            c.patch(
                f"/api/v1/seller/orders/{sid}/status",
                headers=csrf(c),
                json={"status": "CONFIRMED", "expected_status": "PENDING", "subtotal": 0},
            ).status_code
            == 422
        )
        with db.sessions.begin() as s:
            s.get(User, owners[0]).user_status = "LOCKED"
        assert c.get("/api/v1/seller/orders").status_code == 403
        assert change(c, sid, "CANCELLED").status_code == 403
        c.cookies.clear()
        assert c.get("/api/v1/seller/orders").status_code == 401


@pytest.mark.parametrize("mode", ["missing", "overflow", "commit"])
def test_restoration_failure_is_atomic(placed, mode):
    cfg, db, r, owners, order = placed
    sid = order["shop_orders"][0]["shop_order_id"]
    if mode != "commit":
        with db.sessions.begin() as s:
            row = s.get(Inventory, r["products"][0])
            if mode == "missing":
                s.delete(row)
            else:
                row.quantity = 2147483647

    def fail(session):
        raise SQLAlchemyError("private DSN")

    def broken():
        with db.sessions() as s:
            event.listen(s, "before_commit", fail)
            yield s

    with client_for(cfg, owners[0]) as c:
        headers = csrf(c)
        if mode == "commit":
            c.app.dependency_overrides[get_session] = broken
        result = c.patch(
            f"/api/v1/seller/orders/{sid}/status",
            headers=headers,
            json={"expected_status": "PENDING", "status": "CANCELLED"},
        )
        assert result.status_code == (503 if mode == "commit" else 409)
        assert "private DSN" not in result.text
    with db.sessions() as s:
        assert s.get(ShopOrder, int(sid)).order_status == "PENDING"
        if mode == "commit":
            assert s.get(Inventory, r["products"][0]).quantity == 9


def test_complete_transition_matrix_and_buyer_terminal_states(placed):
    cfg, db, r, owners, order = placed
    sid = order["shop_orders"][0]["shop_order_id"]
    states = ["PENDING", "CONFIRMED", "SHIPPING", "COMPLETED", "CANCELLED"]
    allowed = {
        ("PENDING", "CONFIRMED"),
        ("CONFIRMED", "SHIPPING"),
        ("SHIPPING", "COMPLETED"),
        ("PENDING", "CANCELLED"),
        ("CONFIRMED", "CANCELLED"),
    }
    with client_for(cfg, owners[0]) as c:
        for source in states:
            for target in states:
                with db.sessions.begin() as s:
                    s.get(ShopOrder, int(sid)).order_status = source
                    s.get(Inventory, r["products"][0]).quantity = 9
                result = change(c, sid, target, source)
                valid = source == target or (source, target) in allowed
                assert result.status_code == (200 if valid else 409), (source, target)
                with db.sessions() as s:
                    assert s.get(ShopOrder, int(sid)).order_status == (target if valid else source)
                    restored = source != target and valid and target == "CANCELLED"
                    assert s.get(Inventory, r["products"][0]).quantity == (10 if restored else 9)
    with client_for(cfg, r["buyers"][0]) as c:
        for source in states:
            with db.sessions.begin() as s:
                s.get(ShopOrder, int(sid)).order_status = source
            assert cancel(c, order["order_id"], sid).status_code == (
                200 if source in {"PENDING", "CANCELLED"} else 409
            )


@pytest.mark.parametrize("opponent", ["inventory", "checkout"])
def test_cancel_races_other_stock_writes(placed, opponent):
    cfg, db, r, owners, order = placed
    sid = order["shop_orders"][0]["shop_order_id"]
    barrier = Barrier(2)

    def run(index):
        user = (
            r["buyers"][0]
            if index == 0
            else (owners[0] if opponent == "inventory" else r["buyers"][1])
        )
        with client_for(cfg, user) as c:
            headers = csrf(c)
            barrier.wait(timeout=10)
            if index == 0:
                return c.post(
                    f"/api/v1/orders/{order['order_id']}/shop-orders/{sid}/cancel", headers=headers
                ).status_code
            if opponent == "checkout":
                return checkout(c, payload(r, 1)).status_code
            return c.post(
                f"/api/v1/seller/products/{r['products'][0]}/inventory/adjustments",
                json={"delta": 2},
                headers=headers | {"X-Expected-Quantity": "9"},
            ).status_code

    with ThreadPoolExecutor(2) as pool:
        cancelled, other = list(pool.map(run, range(2)))
    assert cancelled == 200
    assert other in ([200, 409] if opponent == "inventory" else [201])
    with db.sessions() as s:
        expected = 9 if opponent == "checkout" else (12 if other == 200 else 10)
        assert s.get(Inventory, r["products"][0]).quantity == expected


def test_seller_detail_reads_only_supported_order_columns_and_buyer_name(placed):
    cfg, db, r, owners, order = placed
    sid = order["shop_orders"][0]["shop_order_id"]
    statements = []

    def record_query(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(db.engine, "before_cursor_execute", record_query)
    try:
        with client_for(cfg, owners[0]) as c:
            response = c.get(f"/api/v1/seller/orders/{sid}")
            assert response.status_code == 200
            data = response.json()["data"]
            with db.sessions() as s:
                assert data["buyer_name"] == s.get(User, r["buyers"][0]).full_name
            assert data["recipient_name"] == order["recipient_name"]
            assert data["phone"] == order["phone"]
            assert "buyer_user_id" not in data and "email" not in data
            assert "shipping_discount_amount" not in " ".join(statements)
        with client_for(cfg, owners[1]) as c:
            response = c.get(f"/api/v1/seller/orders/{sid}")
            assert response.status_code == 404
            assert "buyer_name" not in response.text
    finally:
        event.remove(db.engine, "before_cursor_execute", record_query)
