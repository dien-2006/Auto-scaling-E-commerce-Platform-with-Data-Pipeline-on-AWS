"""Transaction, rollback and concurrency tests only on disposable PostgreSQL16."""

import os
import secrets
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from psycopg.errors import SerializationFailure
from sqlalchemy import delete, event, func, select, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from app.core.config import Settings
from app.core.security import PASSWORD_HASHER, Security
from app.db.base import Base
from app.db.locks import CATEGORY_LOCK_ID, CATEGORY_LOCK_NAMESPACE
from app.db.session import Database, get_session
from app.main import create_app
from app.models import (
    Address,
    Cart,
    CartItem,
    Category,
    Inventory,
    Order,
    Product,
    Shop,
    ShopOrder,
    User,
)
from app.repositories.checkout import CheckoutRepository


@pytest.fixture(scope="module")
def checkout_db():
    if os.environ.get("MARKETPLACE_TEST_DB_NAME") != "marketplace_test":
        pytest.skip("Requires isolated marketplace_test PostgreSQL")
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
        Base.metadata.create_all(conn)
    yield cfg, db
    db.close()


@pytest.fixture
def world(checkout_db):
    cfg, db = checkout_db
    with db.sessions.begin() as s:
        users = [
            User(email=f"{uuid4().hex}@example.com", password_hash="unused", full_name=f"Test {i}")
            for i in range(4)
        ]
        s.add_all(users)
        s.flush()
        buyers = [users[0].user_id, users[1].user_id]
        shops = [
            Shop(
                owner_user_id=u.user_id,
                shop_name=f"Shop {i}",
                shop_slug=uuid4().hex,
                shop_status="APPROVED",
            )
            for i, u in enumerate(users[2:])
        ]
        parent = Category(category_name="Parent", category_slug=uuid4().hex)
        s.add_all([*shops, parent])
        s.flush()
        child = Category(
            category_name="Child", category_slug=uuid4().hex, parent_category_id=parent.category_id
        )
        s.add(child)
        s.flush()
        products = [
            Product(
                shop_id=shop.shop_id,
                category_id=child.category_id,
                sku=uuid4().hex,
                product_name=f"Original {i}",
                price=price,
            )
            for i, (shop, price) in enumerate(zip(shops, ["12.34", "5.67"], strict=True))
        ]
        s.add_all(products)
        s.flush()
        addresses = [
            Address(
                user_id=uid,
                recipient_name=f"Buyer {i}",
                phone="0901234567",
                address_line="12 Nguyen Hue",
                ward="Ward",
                city="City",
            )
            for i, uid in enumerate(buyers)
        ]
        carts = [Cart(user_id=uid) for uid in buyers]
        s.add_all([*addresses, *carts])
        s.flush()
        s.add_all([Inventory(product_id=p.product_id, quantity=10) for p in products])
        s.add_all(
            [
                CartItem(cart_id=c.cart_id, product_id=p.product_id, quantity=1)
                for c in carts
                for p in products
            ]
        )
        r = {
            "buyers": buyers,
            "products": [p.product_id for p in products],
            "shops": [shop.shop_id for shop in shops],
            "addresses": [a.address_id for a in addresses],
            "carts": [c.cart_id for c in carts],
            "parent": parent.category_id,
        }
    return cfg, db, r


def client_for(cfg, uid):
    client = TestClient(create_app(cfg))
    sec = Security(cfg)
    client.cookies.set(sec.access_cookie, sec.issue_access(uid))
    return client


def csrf(client):
    token = client.get("/api/v1/auth/csrf").json()["data"]["csrf_token"]
    return {"Origin": "http://testserver", "X-CSRF-Token": token}


def payload(r, index=0):
    return {
        "address_id": str(r["addresses"][index]),
        "payment_method": "COD",
        "items": [
            {"product_id": str(pid), "quantity": 1, "expected_unit_price": price}
            for pid, price in zip(r["products"], ["12.34", "5.67"], strict=True)
        ],
    }


def checkout(client, data, key=None):
    return client.post(
        "/api/v1/orders/checkout",
        json=data,
        headers=csrf(client) | {"Idempotency-Key": str(key or uuid4())},
    )


def assert_unchanged(db, r):
    with db.sessions() as s:
        for pid in r["products"]:
            assert s.get(Inventory, pid).quantity == 10
        assert (
            s.scalar(
                select(func.count()).select_from(Order).where(Order.buyer_user_id.in_(r["buyers"]))
            )
            == 0
        )
        assert (
            s.scalar(
                select(func.count()).select_from(CartItem).where(CartItem.cart_id.in_(r["carts"]))
            )
            == 4
        )


def test_multishop_atomic_totals_composite_fk_and_replay_snapshots(world):
    cfg, db, r = world
    key = uuid4()
    data = payload(r)
    with client_for(cfg, r["buyers"][0]) as client:
        response = checkout(client, data, key)
        assert response.status_code == 201
        order = response.json()["data"]
        assert order["total_amount"] == "18.01" and len(order["shop_orders"]) == 2
        assert order["shipping_address"] == "12 Nguyen Hue, Ward, City" and order[
            "created_at"
        ].endswith("Z")
        assert response.headers["cache-control"] == "no-store"
        assert [s["order_status"] for s in order["shop_orders"]] == ["PENDING", "PENDING"]
        for shop in order["shop_orders"]:
            assert len(shop["items"]) == 1 and shop["subtotal"] == shop["items"][0]["line_total"]
        with db.sessions.begin() as s:
            assert s.get(Inventory, r["products"][0]).quantity == 9
            assert (
                s.scalar(
                    select(func.count())
                    .select_from(CartItem)
                    .where(CartItem.cart_id == r["carts"][0])
                )
                == 0
            )
            address = s.get(Address, r["addresses"][0])
            s.delete(address)
            p = s.get(Product, r["products"][0])
            p.product_name = "Changed"
            p.price = "99.00"
            p.is_active = False
            s.get(Shop, r["shops"][0]).shop_status = "LOCKED"
        # Replay ignores changed address/cart/catalog and a different valid retry payload.
        retry = checkout(client, payload(r, 1), key)
        assert retry.status_code == 200 and retry.json()["data"] == order
        assert checkout(client, data).status_code == 409
        with db.sessions() as s:
            assert s.get(Inventory, r["products"][0]).quantity == 9
            assert (
                s.scalar(
                    select(func.count())
                    .select_from(Order)
                    .where(Order.buyer_user_id == r["buyers"][0])
                )
                == 1
            )


def test_same_key_concurrent_replicas_create_exactly_one_order(world):
    cfg, db, r = world
    key = uuid4()
    barrier = Barrier(4)

    def run(_):
        with client_for(cfg, r["buyers"][0]) as c:
            headers = csrf(c) | {"Idempotency-Key": str(key)}
            barrier.wait(timeout=10)
            result = c.post("/api/v1/orders/checkout", json=payload(r), headers=headers)
            return result.status_code, result.json()["data"]["order_id"]

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(run, range(4)))
    assert sorted(status for status, _ in results) == [200, 200, 200, 201]
    assert len({oid for _, oid in results}) == 1
    with db.sessions() as s:
        assert s.get(Inventory, r["products"][0]).quantity == 9
        oid = int(results[0][1])
        assert (
            s.scalar(select(func.count()).select_from(ShopOrder).where(ShopOrder.order_id == oid))
            == 2
        )


def test_two_buyers_compete_for_last_unit(world):
    cfg, db, r = world
    barrier = Barrier(2)
    with db.sessions.begin() as s:
        s.execute(
            delete(CartItem).where(
                CartItem.cart_id.in_(r["carts"]), CartItem.product_id == r["products"][1]
            )
        )
        s.get(Inventory, r["products"][0]).quantity = 1

    def run(index):
        with client_for(cfg, r["buyers"][index]) as c:
            data = payload(r, index)
            data["items"] = data["items"][:1]
            headers = csrf(c) | {"Idempotency-Key": str(uuid4())}
            barrier.wait(timeout=10)
            return c.post("/api/v1/orders/checkout", json=data, headers=headers).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(run, [0, 1]))
    assert sorted(statuses) == [201, 409]
    with db.sessions() as s:
        assert s.get(Inventory, r["products"][0]).quantity == 0
        assert (
            s.scalar(
                select(func.count()).select_from(Order).where(Order.buyer_user_id.in_(r["buyers"]))
            )
            == 1
        )
        assert (
            s.scalar(
                select(func.count()).select_from(CartItem).where(CartItem.cart_id.in_(r["carts"]))
            )
            == 1
        )


def test_key_scope_per_buyer(world):
    cfg, db, r = world
    key = uuid4()
    orders = []
    for i in [0, 1]:
        with client_for(cfg, r["buyers"][i]) as c:
            result = checkout(c, payload(r, i), key)
            assert result.status_code == 201
            orders.append(result.json()["data"]["order_id"])
    assert len(set(orders)) == 2


@pytest.mark.parametrize(
    "kind",
    [
        "price",
        "quantity",
        "subset",
        "foreign_address",
        "hidden",
        "parent",
        "shop",
        "stock",
        "missing_stock",
        "self",
    ],
)
def test_checkout_guards_rollback_without_partial_orders(world, kind):
    cfg, db, r = world
    data = payload(r)
    expected = 409
    if kind == "price":
        data["items"][0]["expected_unit_price"] = "1.00"
    elif kind == "quantity":
        data["items"][0]["quantity"] = 2
    elif kind == "subset":
        data["items"] = data["items"][:1]
    elif kind == "foreign_address":
        data["address_id"] = str(r["addresses"][1])
        expected = 404
    else:
        with db.sessions.begin() as s:
            if kind == "hidden":
                s.get(Product, r["products"][0]).is_active = False
            elif kind == "parent":
                s.get(Category, r["parent"]).is_active = False
            elif kind == "shop":
                s.get(Shop, r["shops"][0]).shop_status = "LOCKED"
            elif kind == "stock":
                s.get(Inventory, r["products"][0]).quantity = 0
            elif kind == "missing_stock":
                s.delete(s.get(Inventory, r["products"][0]))
            elif kind == "self":
                s.get(Shop, r["shops"][0]).owner_user_id = r["buyers"][0]
                expected = 403
    with client_for(cfg, r["buyers"][0]) as c:
        result = checkout(c, data)
        assert result.status_code == expected
        if kind == "price":
            assert result.json()["error"]["code"] == "PRICE_CHANGED"
    with db.sessions() as s:
        assert (
            s.scalar(
                select(func.count()).select_from(Order).where(Order.buyer_user_id == r["buyers"][0])
            )
            == 0
        )
        assert (
            s.scalar(
                select(func.count()).select_from(CartItem).where(CartItem.cart_id == r["carts"][0])
            )
            == 2
        )
        assert s.get(Inventory, r["products"][1]).quantity == 10


def test_mid_transaction_and_commit_failures_rollback_then_same_key_succeeds(world, monkeypatch):
    cfg, db, r = world
    key = uuid4()
    original = CheckoutRepository.decrease_stock

    def fail(repository, pid, quantity):
        original(repository, pid, quantity)
        raise SQLAlchemyError("private DSN")

    with client_for(cfg, r["buyers"][0]) as c:
        monkeypatch.setattr(CheckoutRepository, "decrease_stock", fail)
        result = checkout(c, payload(r), key)
        assert result.status_code == 503 and "private" not in result.text
        assert_unchanged(db, r)
        monkeypatch.setattr(CheckoutRepository, "decrease_stock", original)

        def before_commit(_):
            raise SQLAlchemyError("private commit details")

        def override():
            with db.sessions() as s:
                event.listen(s, "before_commit", before_commit)
                yield s

        c.app.dependency_overrides[get_session] = override
        result = checkout(c, payload(r), key)
        assert result.status_code == 503 and "private" not in result.text
        assert_unchanged(db, r)
        c.app.dependency_overrides.clear()
        assert checkout(c, payload(r), key).status_code == 201


def test_serialization_retry_uses_same_transaction_intent(world):
    cfg, db, r = world
    calls = []

    def before_commit(_):
        calls.append(1)
        if len(calls) == 1:
            raise OperationalError(None, None, SerializationFailure("retry test"))

    def override():
        with db.sessions() as s:
            event.listen(s, "before_commit", before_commit)
            yield s

    with client_for(cfg, r["buyers"][0]) as c:
        c.app.dependency_overrides[get_session] = override
        result = checkout(c, payload(r))
        assert result.status_code == 201 and len(calls) == 2
    with db.sessions() as s:
        assert s.get(Inventory, r["products"][0]).quantity == 9


def test_auth_csrf_uuid_and_locked_account(world):
    cfg, db, r = world
    with TestClient(create_app(cfg)) as guest:
        assert checkout(guest, payload(r)).status_code == 401
    with client_for(cfg, r["buyers"][0]) as c:
        assert (
            c.post(
                "/api/v1/orders/checkout",
                json=payload(r),
                headers={"Idempotency-Key": str(uuid4())},
            ).status_code
            == 403
        )
        assert (
            c.post("/api/v1/orders/checkout", json=payload(r), headers=csrf(c)).status_code == 422
        )
        assert (
            c.post(
                "/api/v1/orders/checkout",
                json=payload(r),
                headers=csrf(c) | {"Idempotency-Key": "invalid"},
            ).status_code
            == 422
        )
        with db.sessions.begin() as s:
            s.get(User, r["buyers"][0]).user_status = "LOCKED"
        assert checkout(c, payload(r)).status_code == 403
    assert_unchanged(db, r)


def test_numeric_total_overflow_is_business_error_not_partial_write(world):
    cfg, db, r = world
    data = payload(r)
    with db.sessions.begin() as s:
        s.get(Product, r["products"][0]).price = "999999999999.99"
        s.get(Inventory, r["products"][0]).quantity = 2147483647
        row = s.scalar(
            select(CartItem).where(
                CartItem.cart_id == r["carts"][0], CartItem.product_id == r["products"][0]
            )
        )
        row.quantity = 2147483647
    data["items"][0].update(quantity=2147483647, expected_unit_price="999999999999.99")
    with client_for(cfg, r["buyers"][0]) as c:
        assert checkout(c, data).status_code == 409
    with db.sessions() as s:
        assert s.get(Inventory, r["products"][0]).quantity == 2147483647
        assert (
            s.scalar(
                select(func.count()).select_from(Order).where(Order.buyer_user_id == r["buyers"][0])
            )
            == 0
        )


@pytest.mark.parametrize("kind", ["shop", "price", "stock", "category", "cart"])
def test_concurrent_state_changes_are_rechecked_after_locks(world, kind):
    cfg, db, r = world
    reached = Event()
    blocker = db.sessions()
    blocker.begin()
    if kind in {"shop", "price"}:
        blocker.scalar(select(Shop).where(Shop.shop_id == r["shops"][0]).with_for_update())
        if kind == "shop":
            blocker.get(Shop, r["shops"][0]).shop_status = "LOCKED"
        else:
            blocker.get(Product, r["products"][0]).price = "99.00"
    elif kind == "stock":
        blocker.scalar(
            select(Inventory).where(Inventory.product_id == r["products"][0]).with_for_update()
        ).quantity = 0
    elif kind == "cart":
        blocker.scalar(select(User).where(User.user_id == r["buyers"][0]).with_for_update())
        blocker.scalar(
            select(CartItem).where(
                CartItem.cart_id == r["carts"][0], CartItem.product_id == r["products"][0]
            )
        ).quantity = 2
    else:
        blocker.execute(
            text("SELECT pg_advisory_xact_lock(:namespace,:key)"),
            {"namespace": CATEGORY_LOCK_NAMESPACE, "key": CATEGORY_LOCK_ID},
        )
        blocker.get(Category, r["parent"]).is_active = False
    blocker.flush()
    table = {
        "shop": "marketplace.shops",
        "price": "marketplace.shops",
        "stock": "marketplace.inventory",
        "category": "pg_advisory_xact_lock_shared",
        "cart": "marketplace.users",
    }[kind]

    def before_cursor(_conn, _cursor, statement, _parameters, _context, _many):
        if table in statement and ("FOR UPDATE" in statement or kind == "category"):
            reached.set()

    try:
        with client_for(cfg, r["buyers"][0]) as c:
            event.listen(c.app.state.database.engine, "before_cursor_execute", before_cursor)
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(checkout, c, payload(r))
                try:
                    assert reached.wait(timeout=5)
                    assert not future.done()
                finally:
                    blocker.commit()
                result = future.result(timeout=10)
                assert result.status_code == 409
    finally:
        blocker.close()


def test_new_nine_character_password_and_legacy_login(checkout_db):
    cfg, db = checkout_db
    with TestClient(create_app(cfg)) as c:
        email = f"{uuid4().hex}@example.com"
        data = {"email": email, "password": "Abcde1!xy", "full_name": "New user"}
        assert c.post("/api/v1/auth/register", json=data, headers=csrf(c)).status_code == 201
        assert (
            c.post(
                "/api/v1/auth/login",
                json={"email": email, "password": data["password"]},
                headers=csrf(c),
            ).status_code
            == 200
        )
    legacy_email = f"{uuid4().hex}@example.com"
    with db.sessions.begin() as s:
        s.add(
            User(
                email=legacy_email,
                password_hash=PASSWORD_HASHER.hash("legacy-password"),
                full_name="Legacy",
            )
        )
    with TestClient(create_app(cfg)) as c:
        assert (
            c.post(
                "/api/v1/auth/login",
                json={"email": legacy_email, "password": "legacy-password"},
                headers=csrf(c),
            ).status_code
            == 200
        )


@pytest.mark.parametrize("empty_cart", [False, True])
def test_direct_buy_only_selected_product_preserves_cart_and_replay(world, empty_cart):
    from sqlalchemy import delete

    cfg, db, r = world
    if empty_cart:
        with db.sessions.begin() as s:
            s.execute(delete(CartItem).where(CartItem.cart_id == r["carts"][0]))
    data = payload(r)
    data["purchase_mode"] = "BUY_NOW"
    data["items"] = [data["items"][0] | {"quantity": 2}]
    key = uuid4()
    with client_for(cfg, r["buyers"][0]) as c:
        response = checkout(c, data, key)
        assert response.status_code == 201
        order = response.json()["data"]
        assert order["total_amount"] == "24.68"
        assert len(order["shop_orders"]) == 1
        assert len(order["shop_orders"][0]["items"]) == 1
        assert order["shop_orders"][0]["items"][0]["quantity"] == 2
        assert checkout(c, data, key).json()["data"] == order
    with db.sessions() as s:
        assert s.get(Inventory, r["products"][0]).quantity == 8
        assert s.get(Inventory, r["products"][1]).quantity == 10
        items = list(s.scalars(select(CartItem).where(CartItem.cart_id == r["carts"][0])))
        assert len(items) == (0 if empty_cart else 2)
        assert all(item.quantity == 1 for item in items)


def test_direct_buy_checks_stock_price_and_single_item_without_touching_cart(world):
    cfg, db, r = world
    data = payload(r) | {"purchase_mode": "BUY_NOW"}
    with client_for(cfg, r["buyers"][0]) as c:
        assert checkout(c, data).status_code == 422
        data["items"] = [data["items"][0] | {"quantity": 11}]
        assert checkout(c, data).json()["error"]["code"] == "OUT_OF_STOCK"
        data["items"] = [data["items"][0] | {"quantity": 1, "expected_unit_price": "0.01"}]
        assert checkout(c, data).json()["error"]["code"] == "PRICE_CHANGED"
    assert_unchanged(db, r)


def test_selected_cart_only_consumes_selected_rows_and_stock(world):
    cfg, db, r = world
    data = payload(r) | {"purchase_mode": "SELECTED_CART"}
    data["items"] = [data["items"][0]]
    key = uuid4()
    with client_for(cfg, r["buyers"][0]) as c:
        result = checkout(c, data, key)
        assert result.status_code == 201
        assert result.json()["data"]["total_amount"] == "12.34"
        assert len(result.json()["data"]["shop_orders"]) == 1
        assert checkout(c, data, key).status_code == 200
    with db.sessions() as s:
        remaining = list(s.scalars(select(CartItem).where(CartItem.cart_id == r["carts"][0])))
        assert len(remaining) == 1 and remaining[0].product_id == r["products"][1]
        assert s.get(Inventory, r["products"][0]).quantity == 9
        assert s.get(Inventory, r["products"][1]).quantity == 10


def test_selected_cart_rejects_quantity_tampering_without_removal(world):
    cfg, db, r = world
    data = payload(r) | {"purchase_mode": "SELECTED_CART"}
    data["items"] = [data["items"][0] | {"quantity": 2}]
    with client_for(cfg, r["buyers"][0]) as c:
        assert checkout(c, data).json()["error"]["code"] == "CART_CHANGED"
    assert_unchanged(db, r)
