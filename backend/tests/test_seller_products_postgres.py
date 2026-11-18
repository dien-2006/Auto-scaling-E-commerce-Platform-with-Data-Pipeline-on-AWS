from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import event, func, select
from sqlalchemy.exc import SQLAlchemyError
from test_checkout_postgres import checkout_db as checkout_db  # noqa: F401
from test_checkout_postgres import client_for, csrf  # noqa: F401
from test_checkout_postgres import world as world

from app.db.session import get_session
from app.models import Category, Inventory, Product, Shop, User


@pytest.fixture
def seller_world(world):
    cfg, db, r = world
    with db.sessions() as s:
        owners = [s.get(Shop, sid).owner_user_id for sid in r["shops"]]
        category = s.get(Product, r["products"][0]).category_id
    return cfg, db, r, owners, category


def body(category, **changes):
    return {
        "sku": uuid4().hex,
        "category_id": str(category),
        "product_name": "Seller Serum",
        "description": "Description",
        "price": "12.34",
        "initial_quantity": 7,
        **changes,
    }


def create(c, payload):
    return c.post("/api/v1/seller/products", json=payload, headers=csrf(c))


def test_crud_visibility_stock_and_projection(seller_world):
    cfg, db, r, owners, category = seller_world
    with client_for(cfg, owners[0]) as c:
        response = create(c, body(category))
        assert response.status_code == 201, response.text
        item = response.json()["data"]
        pid = item["product_id"]
        assert item["price"] == "12.34" and item["available_quantity"] == 7
        assert item["is_active"] and item["images"] == []
        assert item["primary_image_url"] is None and item["created_at"].endswith("Z")
        assert response.headers["cache-control"] == "no-store"
        assert not any(
            key in response.text
            for key in ["owner_user_id", "image_key", "password_hash", "contact_email"]
        )
        assert c.get(f"/api/v1/products/{pid}").status_code == 200
        changed = c.patch(
            f"/api/v1/seller/products/{pid}",
            json={"price": "2.50", "description": None},
            headers=csrf(c),
        )
        assert changed.status_code == 200 and changed.json()["data"]["description"] is None
        assert changed.json()["data"]["price"] == "2.50"
        assert changed.json()["data"]["available_quantity"] == 7
        before = c.get(f"/api/v1/seller/products/{pid}").json()["data"]
        hidden = c.post(f"/api/v1/seller/products/{pid}/hide", headers=csrf(c))
        assert hidden.status_code == 200 and not hidden.json()["data"]["is_active"]
        again = c.post(f"/api/v1/seller/products/{pid}/hide", headers=csrf(c))
        assert again.json() == hidden.json()
        assert c.get(f"/api/v1/products/{pid}").status_code == 404
        assert c.get(f"/api/v1/seller/products/{pid}").status_code == 200
        assert (
            c.patch(
                f"/api/v1/seller/products/{pid}", json={"is_active": True}, headers=csrf(c)
            ).status_code
            == 422
        )
        assert (
            c.patch(
                f"/api/v1/seller/products/{pid}", json={"initial_quantity": 10}, headers=csrf(c)
            ).status_code
            == 422
        )
        page = c.get(
            "/api/v1/seller/products",
            params={"q": "Seller Serum", "is_active": "false", "page_size": 1},
        ).json()
        assert page["total"] == 1 and page["items"][0]["product_id"] == pid
        assert c.get("/api/v1/seller/products?q=%25_").json()["total"] == 0
        assert c.get("/api/v1/seller/products?page=2147483647").json()["items"] == []
        assert before["available_quantity"] == 7
    with db.sessions() as s:
        assert s.get(Inventory, int(pid)).quantity == 7


@pytest.mark.parametrize("status", ["PENDING", "REJECTED", "LOCKED"])
def test_unapproved_shop_cannot_read_or_mutate(seller_world, status):
    cfg, db, r, owners, category = seller_world
    with db.sessions.begin() as s:
        s.get(Shop, r["shops"][0]).shop_status = status
    with client_for(cfg, owners[0]) as c:
        pid = r["products"][0]
        assert c.get("/api/v1/seller/products").status_code == 403
        assert c.get(f"/api/v1/seller/products/{pid}").status_code == 403
        assert create(c, body(category)).status_code == 403
        assert (
            c.patch(
                f"/api/v1/seller/products/{pid}", json={"price": "1"}, headers=csrf(c)
            ).status_code
            == 403
        )
        assert c.post(f"/api/v1/seller/products/{pid}/hide", headers=csrf(c)).status_code == 403


def test_ownership_admin_guest_csrf_and_locked_user(seller_world):
    cfg, db, r, owners, category = seller_world
    with db.sessions.begin() as s:
        s.get(User, owners[1]).user_role = "ADMIN"
    with client_for(cfg, owners[1]) as c:
        pid = r["products"][0]
        assert c.get(f"/api/v1/seller/products/{pid}").status_code == 404
        assert (
            c.patch(
                f"/api/v1/seller/products/{pid}", json={"price": "1"}, headers=csrf(c)
            ).status_code
            == 404
        )
        assert c.post(f"/api/v1/seller/products/{pid}/hide", headers=csrf(c)).status_code == 404
        assert str(pid) not in [
            i["product_id"] for i in c.get("/api/v1/seller/products").json()["items"]
        ]
        assert c.post("/api/v1/seller/products", json=body(category)).status_code == 403
        headers = {**csrf(c), "Origin": "https://evil.example"}
        assert (
            c.post("/api/v1/seller/products", json=body(category), headers=headers).status_code
            == 403
        )
        c.cookies.clear()
        assert c.get("/api/v1/seller/products").status_code == 401
    with db.sessions.begin() as s:
        s.get(User, owners[0]).user_status = "LOCKED"
    with client_for(cfg, owners[0]) as c:
        assert c.get("/api/v1/seller/products").status_code == 403
        assert create(c, body(category)).status_code == 403


def test_category_parent_hidden_and_invalid_ids(seller_world):
    cfg, db, r, owners, category = seller_world
    with db.sessions.begin() as s:
        s.get(Category, r["parent"]).is_active = False
    with client_for(cfg, owners[0]) as c:
        assert create(c, body(category)).status_code == 422
        pid = r["products"][0]
        assert (
            c.patch(
                f"/api/v1/seller/products/{pid}",
                json={"category_id": str(category)},
                headers=csrf(c),
            ).status_code
            == 422
        )
        # Existing private products remain readable when their category is hidden.
        assert c.get(f"/api/v1/seller/products/{pid}").status_code == 200
        assert c.get("/api/v1/seller/products/9223372036854775808").status_code == 422
        assert c.get("/api/v1/seller/products?shop_id=1").status_code == 422


def test_sku_unique_per_shop_and_race(seller_world):
    cfg, db, r, owners, category = seller_world
    sku = uuid4().hex
    barrier = Barrier(2)

    def worker(_):
        with client_for(cfg, owners[0]) as c:
            headers = csrf(c)
            barrier.wait(timeout=10)
            return c.post("/api/v1/seller/products", json=body(category, sku=sku), headers=headers)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(worker, range(2)))
    assert sorted(x.status_code for x in results) == [201, 409]
    conflict = next(x for x in results if x.status_code == 409)
    assert conflict.json()["error"]["code"] == "SKU_EXISTS"
    with client_for(cfg, owners[1]) as c:
        assert create(c, body(category, sku=sku)).status_code == 201
    with db.sessions() as s:
        assert (
            s.scalar(
                select(func.count())
                .select_from(Product)
                .where(Product.shop_id == r["shops"][0], Product.sku == sku)
            )
            == 1
        )
    with client_for(cfg, owners[0]) as c:
        result = c.patch(
            f"/api/v1/seller/products/{r['products'][0]}", json={"sku": sku}, headers=csrf(c)
        )
        assert result.status_code == 409


def test_rollback_inventory_failure_and_commit_failure(seller_world, monkeypatch):
    cfg, db, r, owners, category = seller_world
    sku = uuid4().hex
    with client_for(cfg, owners[0]) as c:

        def fail_inventory(session, context, instances):
            if any(isinstance(x, Inventory) for x in session.new):
                raise SQLAlchemyError("private DSN")

        def session_with_listener():
            with db.sessions() as s:
                event.listen(s, "before_flush", fail_inventory)
                yield s

        c.app.dependency_overrides[get_session] = session_with_listener
        response = create(c, body(category, sku=sku))
        assert response.status_code == 503 and "private DSN" not in response.text
        with db.sessions() as s:
            assert s.scalar(select(Product).where(Product.sku == sku)) is None

        def fail_commit(session):
            raise SQLAlchemyError("private DSN")

        def broken():
            with db.sessions() as s:
                event.listen(s, "before_commit", fail_commit)
                yield s

        c.app.dependency_overrides[get_session] = broken
        for method, path, data in [
            ("POST", "/api/v1/seller/products", body(category, sku=sku)),
            ("PATCH", f"/api/v1/seller/products/{r['products'][0]}", {"price": "999"}),
            ("POST", f"/api/v1/seller/products/{r['products'][0]}/hide", None),
        ]:
            result = c.request(method, path, json=data, headers=csrf(c))
            assert result.status_code == 503 and "private DSN" not in result.text
        with db.sessions() as s:
            assert s.scalar(select(Product).where(Product.sku == sku)) is None
            item = s.get(Product, r["products"][0])
            assert str(item.price) == "12.34" and item.is_active


def test_reads_are_readonly_and_listing_has_no_n_plus_one(seller_world):
    cfg, db, r, owners, category = seller_world
    with client_for(cfg, owners[0]) as c:
        for _ in range(3):
            assert create(c, body(category)).status_code == 201
        statements = []

        def capture(conn, cursor, sql, parameters, context, executemany):
            statements.append(sql)

        event.listen(c.app.state.database.engine, "before_cursor_execute", capture)
        try:
            assert c.get("/api/v1/seller/products").status_code == 200
        finally:
            event.remove(c.app.state.database.engine, "before_cursor_execute", capture)
        assert any("SET TRANSACTION READ ONLY" in q for q in statements)
        assert len([q for q in statements if q.startswith("SELECT")]) == 5
