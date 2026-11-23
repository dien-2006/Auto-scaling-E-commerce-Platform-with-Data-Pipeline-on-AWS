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
from app.models import Inventory, Product, Shop, User


def path(pid):
    return f"/api/v1/seller/products/{pid}/inventory"


def adjust(c, pid, delta=2, expected="10"):
    return c.post(
        path(pid) + "/adjustments",
        json={"delta": delta},
        headers=csrf(c) | {"X-Expected-Quantity": expected},
    )


def test_adjust_read_stale_bounds_hidden(seller_world):
    cfg, db, r, owners, _ = seller_world
    pid = r["products"][0]
    with client_for(cfg, owners[0]) as c:
        result = c.get(path(pid))
        assert result.status_code == 200
        assert result.headers["cache-control"] == "no-store"
        assert set(result.json()["data"]) == {"product_id", "quantity", "updated_at"}
        assert result.json()["data"]["product_id"] == str(pid)
        assert adjust(c, pid).json()["data"]["quantity"] == 12
        assert adjust(c, pid).status_code == 409
        assert adjust(c, pid, -13, "12").json()["error"]["code"] == "INVALID_STOCK"
        assert adjust(c, pid, 2147483647, "12").status_code == 409
        assert adjust(c, pid, -12, "12").json()["data"]["quantity"] == 0
        with db.sessions.begin() as s:
            s.get(Product, pid).is_active = False
        assert adjust(c, pid, 1, "0").status_code == 200
    with db.sessions() as s:
        assert s.get(Inventory, pid).quantity == 1
        assert not s.get(Product, pid).is_active


@pytest.mark.parametrize("value", ["-1", "01", "+1", "1.0", "2147483648", "", "1,1"])
def test_invalid_precondition(seller_world, value):
    cfg, _, r, owners, _ = seller_world
    with client_for(cfg, owners[0]) as c:
        assert adjust(c, r["products"][0], expected=value).status_code == 422


@pytest.mark.parametrize(
    "body",
    [
        {"delta": 0},
        {"delta": True},
        {"delta": 1.0},
        {"delta": "1"},
        {"delta": 2147483648},
        {"delta": 1, "quantity": 3},
    ],
)
def test_invalid_delta(seller_world, body):
    cfg, _, r, owners, _ = seller_world
    with client_for(cfg, owners[0]) as c:
        assert (
            c.post(
                path(r["products"][0]) + "/adjustments",
                json=body,
                headers=csrf(c) | {"X-Expected-Quantity": "10"},
            ).status_code
            == 422
        )


def test_ownership_csrf_missing_row_and_locked_user(seller_world):
    cfg, db, r, owners, _ = seller_world
    pid = r["products"][0]
    with db.sessions.begin() as s:
        s.get(User, owners[1]).user_role = "ADMIN"
    with client_for(cfg, owners[1]) as c:
        assert c.get(path(pid)).status_code == 404
        assert adjust(c, pid).status_code == 404
    with client_for(cfg, owners[0]) as c:
        assert c.post(path(pid) + "/adjustments", json={"delta": 2}).status_code == 403
        with db.sessions.begin() as s:
            s.delete(s.get(Inventory, pid))
        assert c.get(path(pid)).json()["error"]["code"] == "INVENTORY_UNAVAILABLE"
        assert adjust(c, pid).status_code == 409
        with db.sessions.begin() as s:
            assert s.get(Inventory, pid) is None
            s.get(User, owners[0]).user_status = "LOCKED"
        assert c.get(path(pid)).status_code == 403
        assert adjust(c, pid).status_code == 403
        c.cookies.clear()
        assert c.get(path(pid)).status_code == 401


@pytest.mark.parametrize("status", ["PENDING", "REJECTED", "LOCKED"])
def test_unapproved(seller_world, status):
    cfg, db, r, owners, _ = seller_world
    with db.sessions.begin() as s:
        s.get(Shop, r["shops"][0]).shop_status = status
    with client_for(cfg, owners[0]) as c:
        assert c.get(path(r["products"][0])).status_code == 403
        assert adjust(c, r["products"][0]).status_code == 403


def test_commit_failure_rolls_back(seller_world):
    cfg, db, r, owners, _ = seller_world

    def fail(session):
        raise SQLAlchemyError("private DSN")

    def broken():
        with db.sessions() as s:
            event.listen(s, "before_commit", fail)
            yield s

    with client_for(cfg, owners[0]) as c:
        headers = csrf(c) | {"X-Expected-Quantity": "10"}
        c.app.dependency_overrides[get_session] = broken
        result = c.post(path(r["products"][0]) + "/adjustments", json={"delta": 2}, headers=headers)
        assert result.status_code == 503 and "private DSN" not in result.text
    with db.sessions() as s:
        assert s.get(Inventory, r["products"][0]).quantity == 10


def test_concurrent_adjustments(seller_world):
    cfg, db, r, owners, _ = seller_world
    barrier = Barrier(2)

    def run(_):
        with client_for(cfg, owners[0]) as c:
            barrier.wait(timeout=10)
            return adjust(c, r["products"][0]).status_code

    with ThreadPoolExecutor(2) as pool:
        assert sorted(pool.map(run, range(2))) == [200, 409]
    with db.sessions() as s:
        assert s.get(Inventory, r["products"][0]).quantity == 12


def test_checkout_racing_adjustment(seller_world):
    cfg, db, r, owners, _ = seller_world
    barrier = Barrier(2)

    def run(index):
        with client_for(cfg, owners[0] if index == 0 else r["buyers"][0]) as c:
            barrier.wait(timeout=10)
            return (
                adjust(c, r["products"][0]) if index == 0 else checkout(c, payload(r))
            ).status_code

    with ThreadPoolExecutor(2) as pool:
        stock_status, order_status = list(pool.map(run, range(2)))
    assert stock_status in [200, 409] and order_status == 201
    with db.sessions() as s:
        assert s.get(Inventory, r["products"][0]).quantity == (11 if stock_status == 200 else 9)
        assert s.get(Inventory, r["products"][1]).quantity == 9
