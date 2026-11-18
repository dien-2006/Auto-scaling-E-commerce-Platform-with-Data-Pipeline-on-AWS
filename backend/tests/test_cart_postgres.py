"""Cart writes use an isolated PostgreSQL database; never production fixtures."""

import os
import secrets
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
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
from app.models import Cart, Category, Inventory, Product, Shop, User


@pytest.fixture(scope="module")
def cart_db():
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
        Base.metadata.create_all(conn)  # Explicitly guarded disposable test DB only.
    yield cfg, db
    db.close()


@pytest.fixture
def world(cart_db):
    cfg, db = cart_db
    with db.sessions.begin() as session:
        users = [
            User(
                email=f"{uuid4().hex}@example.com",
                password_hash="unused",
                full_name="Test",
                user_role=role,
            )
            for role in ["USER", "USER", "USER", "ADMIN"]
        ]
        session.add_all(users)
        session.flush()
        ids = [row.user_id for row in users]
        shops = [
            Shop(
                owner_user_id=uid,
                shop_name=f"Shop {index}",
                shop_slug=uuid4().hex,
                shop_status="APPROVED",
            )
            for index, uid in enumerate(ids[1:3])
        ]
        parent = Category(category_name="Parent", category_slug=uuid4().hex)
        session.add_all([*shops, parent])
        session.flush()
        child = Category(
            category_name="Child", category_slug=uuid4().hex, parent_category_id=parent.category_id
        )
        session.add(child)
        session.flush()
        products = [
            Product(
                shop_id=shop.shop_id,
                category_id=child.category_id,
                sku=uuid4().hex,
                product_name=f"Test {i}",
                price=price,
            )
            for i, (shop, price) in enumerate(
                zip(shops, [Decimal("199000.25"), Decimal("10.50")], strict=True)
            )
        ]
        session.add_all(products)
        session.flush()
        session.add_all([Inventory(product_id=p.product_id, quantity=10) for p in products])
        resources = {
            "products": [p.product_id for p in products],
            "shops": [s.shop_id for s in shops],
            "parent": parent.category_id,
        }
    return cfg, db, ids, resources


def client_for(cfg, uid):
    client = TestClient(create_app(cfg))
    sec = Security(cfg)
    client.cookies.set(sec.access_cookie, sec.issue_access(uid))
    return client


def csrf(client):
    token = client.get("/api/v1/auth/csrf").json()["data"]["csrf_token"]
    return {"Origin": "http://testserver", "X-CSRF-Token": token}


def add(client, product, quantity=1):
    return client.post(
        "/api/v1/cart/items",
        json={"product_id": str(product), "quantity": quantity},
        headers=csrf(client),
    )


def test_empty_get_never_creates_cart_and_multishop_totals(world):
    cfg, db, ids, r = world
    with client_for(cfg, ids[0]) as client:
        assert client.get("/api/v1/cart").json() == {"data": {"shops": [], "total_amount": "0.00"}}
        with db.sessions() as session:
            assert session.scalar(select(Cart.cart_id).where(Cart.user_id == ids[0])) is None
        assert add(client, r["products"][0], 2).status_code == 200
        assert add(client, r["products"][0], 1).status_code == 200
        result = add(client, r["products"][1], 2)
        assert result.status_code == 200 and result.headers["cache-control"] == "no-store"
        cart = result.json()["data"]
        assert len(cart["shops"]) == 2 and cart["total_amount"] == "597021.75"
        first = cart["shops"][0]["items"][0]
        assert first["quantity"] == 3 and first["line_total"] == "597000.75"
        assert first["primary_image_url"] is None and first["is_available"]
        assert "owner_user_id" not in result.text and "password_hash" not in result.text
        item = first["cart_item_id"]
        changed = client.patch(
            f"/api/v1/cart/items/{item}", json={"quantity": 1}, headers=csrf(client)
        )
        assert changed.status_code == 200 and changed.json()["data"]["total_amount"] == "199021.25"
        assert client.delete(f"/api/v1/cart/items/{item}", headers=csrf(client)).status_code == 204
        assert len(client.get("/api/v1/cart").json()["data"]["shops"]) == 1
        with db.sessions() as session:
            assert session.get(Inventory, r["products"][0]).quantity == 10


def test_concurrent_upsert_is_one_line_no_lost_increment(world):
    cfg, db, ids, r = world

    def increment(_):
        with client_for(cfg, ids[0]) as client:
            return add(client, r["products"][0]).status_code

    with ThreadPoolExecutor(max_workers=4) as pool:
        assert list(pool.map(increment, range(4))) == [200] * 4
    with client_for(cfg, ids[0]) as client:
        cart = client.get("/api/v1/cart").json()["data"]
        assert len(cart["shops"][0]["items"]) == 1 and cart["shops"][0]["items"][0]["quantity"] == 4
    with db.sessions() as session:
        assert (
            session.scalar(select(func.count()).select_from(Cart).where(Cart.user_id == ids[0]))
            == 1
        )
        assert session.get(Inventory, r["products"][0]).quantity == 10


def test_concurrent_add_checks_accumulated_quantity_without_reserving(world):
    cfg, db, ids, r = world

    def increment(_):
        with client_for(cfg, ids[0]) as client:
            return add(client, r["products"][0], 4).status_code

    with ThreadPoolExecutor(max_workers=4) as pool:
        statuses = list(pool.map(increment, range(4)))
    assert sorted(statuses) == [200, 200, 409, 409]
    with db.sessions() as session:
        assert session.get(Inventory, r["products"][0]).quantity == 10


def test_ownership_auth_csrf_and_no_admin_bypass(world):
    cfg, db, ids, r = world
    with TestClient(create_app(cfg)) as guest:
        assert guest.get("/api/v1/cart").status_code == 401
    with client_for(cfg, ids[0]) as client:
        assert (
            client.post(
                "/api/v1/cart/items", json={"product_id": str(r["products"][0]), "quantity": 1}
            ).status_code
            == 403
        )
        item = add(client, r["products"][0]).json()["data"]["shops"][0]["items"][0]["cart_item_id"]
    for uid in [ids[2]]:
        with client_for(cfg, uid) as other:
            assert other.get("/api/v1/cart").json()["data"]["shops"] == []
            assert (
                other.patch(
                    f"/api/v1/cart/items/{item}", json={"quantity": 2}, headers=csrf(other)
                ).status_code
                == 404
            )
            assert (
                other.delete(f"/api/v1/cart/items/{item}", headers=csrf(other)).status_code == 404
            )
    with client_for(cfg, ids[1]) as owner:
        assert add(owner, r["products"][0]).status_code == 403
    with db.sessions.begin() as session:
        session.get(User, ids[0]).user_status = "LOCKED"
    with client_for(cfg, ids[0]) as locked:
        assert locked.get("/api/v1/cart").status_code == 403
        assert add(locked, r["products"][0]).status_code == 403


@pytest.mark.parametrize(
    ("kind", "reason"),
    [
        ("product", "HIDDEN_PRODUCT"),
        ("shop", "SHOP_UNAVAILABLE"),
        ("parent", "CATEGORY_UNAVAILABLE"),
        ("stock", "OUT_OF_STOCK"),
        ("missing_inventory", "MISSING_INVENTORY"),
    ],
)
def test_unavailable_rows_stay_removable_and_cannot_add(world, kind, reason):
    cfg, db, ids, r = world
    with client_for(cfg, ids[0]) as client:
        item = add(client, r["products"][0]).json()["data"]["shops"][0]["items"][0]["cart_item_id"]
        with db.sessions.begin() as session:
            if kind == "product":
                session.get(Product, r["products"][0]).is_active = False
            elif kind == "shop":
                session.get(Shop, r["shops"][0]).shop_status = "LOCKED"
            elif kind == "parent":
                session.get(Category, r["parent"]).is_active = False
            elif kind == "stock":
                session.get(Inventory, r["products"][0]).quantity = 0
            else:
                session.delete(session.get(Inventory, r["products"][0]))
        line = client.get("/api/v1/cart").json()["data"]["shops"][0]["items"][0]
        assert not line["is_available"] and line["unavailable_reason"] == reason
        assert add(client, r["products"][0]).status_code in {404, 409}
        assert client.delete(f"/api/v1/cart/items/{item}", headers=csrf(client)).status_code == 204


def test_prices_stock_refresh_and_reduction_to_valid_quantity(world):
    cfg, db, ids, r = world
    with client_for(cfg, ids[0]) as client:
        item = add(client, r["products"][0], 5).json()["data"]["shops"][0]["items"][0][
            "cart_item_id"
        ]
        with db.sessions.begin() as session:
            session.get(Product, r["products"][0]).price = Decimal("12.34")
            session.get(Inventory, r["products"][0]).quantity = 2
        line = client.get("/api/v1/cart").json()["data"]["shops"][0]["items"][0]
        assert (
            line["unit_price"] == "12.34"
            and line["line_total"] == "61.70"
            and line["unavailable_reason"] == "INSUFFICIENT_STOCK"
        )
        assert (
            client.patch(
                f"/api/v1/cart/items/{item}", json={"quantity": 3}, headers=csrf(client)
            ).status_code
            == 409
        )
        response = client.patch(
            f"/api/v1/cart/items/{item}", json={"quantity": 2}, headers=csrf(client)
        )
        assert (
            response.status_code == 200
            and response.json()["data"]["shops"][0]["items"][0]["is_available"]
        )


def test_int_overflow_and_invalid_requests(world):
    cfg, db, ids, r = world
    with db.sessions.begin() as session:
        session.get(Inventory, r["products"][0]).quantity = 2147483647
    with client_for(cfg, ids[0]) as client:
        assert add(client, r["products"][0], 2147483647).status_code == 200
        assert add(client, r["products"][0], 1).status_code == 409
        for qty in [0, -1, True, 1.5, "1", 2147483648]:
            assert add(client, r["products"][0], qty).status_code == 422
        assert add(client, 9223372036854775807).status_code == 404


def test_commit_failure_rolls_back_cart_and_item(world):
    cfg, db, ids, r = world

    def fail(_):
        raise SQLAlchemyError("private connection information")

    def override():
        with db.sessions() as session:
            event.listen(session, "before_commit", fail)
            yield session

    with client_for(cfg, ids[0]) as client:
        client.app.dependency_overrides[get_session] = override
        response = add(client, r["products"][0])
        assert response.status_code == 503 and "private" not in response.text
        client.app.dependency_overrides.clear()
        assert client.get("/api/v1/cart").json()["data"]["shops"] == []
    with db.sessions() as session:
        assert session.scalar(select(Cart.cart_id).where(Cart.user_id == ids[0])) is None
