"""HTTP probe routes exist only in test apps; never expose these routes in production."""

import os
import secrets
from typing import Annotated
from uuid import uuid4

import pytest
from fastapi import Depends, Path
from fastapi.testclient import TestClient
from sqlalchemy import event, select, text
from sqlalchemy.exc import SQLAlchemyError

from app.api.dependencies import ReadAccess, WriteAccess, require_admin, require_buyer
from app.core.config import Settings
from app.core.errors import APIError
from app.core.security import Security
from app.db.base import Base
from app.db.session import Database, get_session
from app.main import create_app
from app.models import Address, Cart, Category, Order, Product, Shop, ShopOrder, User
from app.services.access import Principal


@pytest.fixture(scope="module")
def policy_db():
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
        Base.metadata.create_all(conn)  # Disposable test DB only; no production DDL.
    yield cfg, db
    db.close()


@pytest.fixture
def world(policy_db):
    cfg, db = policy_db
    with db.sessions.begin() as session:
        users = [
            User(
                email=f"{uuid4().hex}@example.com",
                password_hash="not-used-in-probe",
                full_name="Test",
                user_role=role,
                user_status="ACTIVE",
            )
            for role in ["USER", "USER", "ADMIN"]
        ]
        session.add_all(users)
        session.flush()
        ids = [user.user_id for user in users]
        shops = [
            Shop(owner_user_id=uid, shop_name="Test", shop_slug=uuid4().hex, shop_status="APPROVED")
            for uid in ids[:2]
        ]
        session.add_all(shops)
        category = Category(category_name="Test", category_slug=uuid4().hex)
        session.add(category)
        session.flush()
        addresses = [
            Address(
                user_id=uid,
                recipient_name="Test",
                phone="0900000000",
                address_line="Test",
                city="Test",
            )
            for uid in ids[:2]
        ]
        carts = [Cart(user_id=uid) for uid in ids[:2]]
        products = [
            Product(
                shop_id=shop.shop_id,
                category_id=category.category_id,
                sku=uuid4().hex,
                product_name="Test",
                price="1.00",
            )
            for shop in shops
        ]
        orders = [
            Order(
                buyer_user_id=uid,
                idempotency_key=uuid4(),
                payment_method="COD",
                total_amount="1.00",
                recipient_name="Test",
                phone="0900000000",
                shipping_address="Test snapshot address",
            )
            for uid in ids[:2]
        ]
        session.add_all(addresses + carts + products + orders)
        session.flush()
        shop_orders = [
            ShopOrder(order_id=order.order_id, shop_id=shop.shop_id, subtotal="1.00")
            for order, shop in zip(orders, shops, strict=True)
        ]
        session.add_all(shop_orders)
        session.flush()
        resources = {
            "address": [row.address_id for row in addresses],
            "cart": [row.cart_id for row in carts],
            "order": [row.order_id for row in orders],
            "buyer_shop_order": [row.shop_order_id for row in shop_orders],
            "seller_product": [row.product_id for row in products],
            "seller_shop_order": [row.shop_order_id for row in shop_orders],
            "shop": [row.shop_id for row in shops],
        }
    app = create_app(cfg)

    @app.get("/probe/admin")
    def admin(principal: Annotated[Principal, Depends(require_admin)]):
        return {"user_id": str(principal.user_id)}

    @app.get("/probe/buyer")
    def buyer(principal: Annotated[Principal, Depends(require_buyer)]):
        return {"user_id": str(principal.user_id)}

    @app.get("/probe/selling")
    def selling(access: ReadAccess):
        return access.selling_shop()

    @app.get("/probe/{kind}/{resource_id}")
    def resource(
        kind: str,
        resource_id: Annotated[int, Path(ge=1, le=9223372036854775807)],
        access: ReadAccess,
    ):
        result = getattr(access, kind)(resource_id)
        return {"authorized": str(result)}

    @app.post("/probe/write/{fail}")
    def write(fail: bool, access: WriteAccess):
        access.admin()
        session = access.repository.session
        user = session.get(User, access.principal.user_id)
        user.full_name = "Updated by authorized action"
        session.flush()
        if fail:
            raise APIError(409, "TEST_ROLLBACK", "Rollback test")
        return {"ok": True}

    with TestClient(app) as client:
        yield client, db, Security(cfg), ids, resources


def use_user(client, security, user_id):
    client.cookies.clear()
    client.cookies.set(security.access_cookie, security.issue_access(user_id))


def test_http_role_matrix_and_cross_user_shop_ids(world):
    client, db, sec, ids, resources = world
    assert client.get("/probe/admin").status_code == 401
    client.cookies.set(sec.access_cookie, "forged")
    assert client.get("/probe/buyer").status_code == 401
    for index, user_id in enumerate(ids):
        use_user(client, sec, user_id)
        assert client.get("/probe/admin").status_code == (200 if index == 2 else 403)
        assert client.get("/probe/buyer").status_code == (403 if index == 2 else 200)
        for kind, pair in resources.items():
            for owner_index, resource_id in enumerate(pair):
                status = client.get(f"/probe/{kind}/{resource_id}").status_code
                expected = (
                    200
                    if index == owner_index
                    else (
                        403
                        if index == 2 and kind in {"seller_product", "seller_shop_order", "shop"}
                        else 404
                    )
                )
                assert status == expected, (kind, index, status, expected)
    with db.sessions() as session:
        assert session.scalar(select(User.user_status).where(User.user_id == ids[0])) == "ACTIVE"


@pytest.mark.parametrize("status", ["PENDING", "REJECTED", "LOCKED", "APPROVED"])
def test_live_shop_state_and_old_orders(world, status):
    client, db, sec, ids, resources = world
    use_user(client, sec, ids[0])
    with db.sessions.begin() as session:
        session.get(Shop, resources["shop"][0]).shop_status = status
    assert client.get("/probe/selling").status_code == (200 if status == "APPROVED" else 403)
    assert client.get(f"/probe/shop/{resources['shop'][0]}").status_code == 200
    assert client.get(f"/probe/seller_product/{resources['seller_product'][0]}").status_code == (
        200 if status == "APPROVED" else 403
    )
    assert client.get(
        f"/probe/seller_shop_order/{resources['seller_shop_order'][0]}"
    ).status_code == (200 if status in {"APPROVED", "LOCKED"} else 403)
    assert (
        client.get(f"/probe/seller_shop_order/{resources['seller_shop_order'][1]}").status_code
        == 404
    )


def test_status_role_change_without_reissuing_jwt(world):
    client, db, sec, ids, _ = world
    use_user(client, sec, ids[2])
    assert client.get("/probe/admin").status_code == 200
    with db.sessions.begin() as session:
        session.get(User, ids[2]).user_role = "USER"
    assert client.get("/probe/admin").status_code == 403
    with db.sessions.begin() as session:
        session.get(User, ids[2]).user_status = "LOCKED"
    assert client.get("/probe/buyer").json()["error"]["code"] == "USER_LOCKED"
    assert client.get("/api/v1/auth/me").json()["error"]["code"] == "USER_LOCKED"
    use_user(client, sec, 9223372036854775807)
    assert client.get("/probe/buyer").status_code == 401


def test_write_csrf_commit_rollback_and_user_lock(world):
    client, db, sec, ids, _ = world
    use_user(client, sec, ids[2])
    assert client.post("/probe/write/false").status_code == 403
    token = client.get("/api/v1/auth/csrf").json()["data"]["csrf_token"]
    headers = {"Origin": "http://testserver", "X-CSRF-Token": token}
    assert client.post("/probe/write/true", headers=headers).status_code == 409
    with db.sessions() as session:
        assert session.get(User, ids[2]).full_name == "Test"
    assert client.post("/probe/write/false", headers=headers).status_code == 200
    with db.sessions() as session:
        assert session.get(User, ids[2]).full_name == "Updated by authorized action"
    with db.sessions.begin() as session:
        session.get(User, ids[2]).user_status = "LOCKED"
    assert client.post("/probe/write/false", headers=headers).status_code == 403


def test_multishop_order_cannot_be_used_to_cross_seller_scope(world):
    client, db, sec, ids, resources = world
    with db.sessions.begin() as session:
        extra = ShopOrder(
            order_id=resources["order"][0], shop_id=resources["shop"][1], subtotal="1.00"
        )
        session.add(extra)
        session.flush()
        extra_id = extra.shop_order_id
    use_user(client, sec, ids[0])
    assert client.get(f"/probe/buyer_shop_order/{extra_id}").status_code == 200
    assert client.get(f"/probe/seller_shop_order/{extra_id}").status_code == 404
    use_user(client, sec, ids[1])
    assert client.get(f"/probe/buyer_shop_order/{extra_id}").status_code == 404
    assert client.get(f"/probe/seller_shop_order/{extra_id}").status_code == 200
    with db.sessions.begin() as session:
        session.get(User, ids[1]).user_status = "LOCKED"
    result = client.get(f"/probe/seller_shop_order/{extra_id}")
    assert result.status_code == 403 and result.json()["error"]["code"] == "USER_LOCKED"


def test_commit_failure_is_503_before_response_and_rolls_back(world):
    client, db, sec, ids, _ = world
    use_user(client, sec, ids[2])
    token = client.get("/api/v1/auth/csrf").json()["data"]["csrf_token"]

    def fail_commit(_session):
        raise SQLAlchemyError("private database connection information")

    def session_override():
        with db.sessions() as session:
            event.listen(session, "before_commit", fail_commit)
            yield session

    client.app.dependency_overrides[get_session] = session_override
    result = client.post(
        "/probe/write/false", headers={"Origin": "http://testserver", "X-CSRF-Token": token}
    )
    assert result.status_code == 503
    assert result.json()["error"]["code"] == "DEPENDENCY_UNAVAILABLE"
    assert "private database" not in result.text
    with db.sessions() as session:
        assert session.get(User, ids[2]).full_name == "Test"
