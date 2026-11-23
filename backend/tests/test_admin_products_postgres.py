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
from app.models import Inventory, Order, Product, ProductImage, Shop, User


@pytest.fixture
def admin_products(world):
    cfg, db, r = world
    prefix = uuid4().hex
    with db.sessions.begin() as s:
        s.get(User, r["buyers"][1]).user_role = "ADMIN"
        owners = [s.get(Shop, sid).owner_user_id for sid in r["shops"]]
        for i, pid in enumerate(r["products"]):
            p = s.get(Product, pid)
            p.product_name = f"{prefix} Product {i}"
            p.sku = f"{prefix}-SKU-{i}"
        s.add(ProductImage(product_id=r["products"][0], image_key="private-key", is_primary=True))
    return cfg, db, r, owners, prefix


def hide(c, pid):
    return c.post(f"/api/v1/admin/products/{pid}/hide", headers=csrf(c))


def test_list_readonly_search_shop_filter_and_projection(admin_products):
    cfg, db, r, _, prefix = admin_products
    statements = []

    def record(conn, cursor, statement, params, context, executemany):
        statements.append(statement)

    def observed():
        with db.sessions() as s:
            yield s

    with client_for(cfg, r["buyers"][1]) as c:
        c.app.dependency_overrides[get_session] = observed
        event.listen(db.engine, "before_cursor_execute", record)
        try:
            response = c.get("/api/v1/admin/products", params={"q": prefix, "page_size": 1})
            assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
            data = response.json()
            assert data["total"] == 2
            assert data["items"][0]["product_id"] == str(max(r["products"]))
            assert data["items"][0]["price"] == "5.67"
            assert any("SET TRANSACTION READ ONLY" in sql for sql in statements)
            assert not any(
                sql.lstrip().upper().startswith(("UPDATE", "INSERT", "DELETE"))
                for sql in statements
            )
            assert sum("FROM marketplace.product_images" in sql for sql in statements) <= 3
        finally:
            event.remove(db.engine, "before_cursor_execute", record)
        own = c.get("/api/v1/admin/products", params={"shop_id": r["shops"][0], "q": prefix}).json()
        assert own["total"] == 1 and own["items"][0]["images"][0]["url"] is None
        assert own["items"][0]["available_quantity"] == 10
        assert not any(
            key in str(own)
            for key in [
                "image_key",
                "private-key",
                "password_hash",
                "owner_user_id",
                "contact_email",
            ]
        )
        assert c.get("/api/v1/admin/products", params={"q": prefix + "-SKU-0"}).json()["total"] == 1
        assert c.get("/api/v1/admin/products?q=%25_").json()["total"] == 0
        assert (
            c.get("/api/v1/admin/products", params={"q": prefix, "page": 2147483647}).json()[
                "items"
            ]
            == []
        )


def test_hide_public_cart_checkout_and_seller_cannot_reactivate(admin_products):
    cfg, db, r, owners, prefix = admin_products
    pid = r["products"][0]
    with client_for(cfg, r["buyers"][1]) as c:
        first = hide(c, pid)
        assert first.status_code == 200
        assert not first.json()["data"]["is_active"]
        assert hide(c, pid).json() == first.json()
        assert c.get(f"/api/v1/products/{pid}").status_code == 404
        assert c.get("/api/v1/products", params={"q": prefix + " Product 0"}).json()["total"] == 0
        assert (
            c.get("/api/v1/admin/products", params={"q": prefix, "is_active": "false"}).json()[
                "total"
            ]
            == 1
        )
    with client_for(cfg, r["buyers"][0]) as buyer:
        cart = buyer.get("/api/v1/cart").json()["data"]
        line = next(
            item
            for shop in cart["shops"]
            for item in shop["items"]
            if item["product_id"] == str(pid)
        )
        assert not line["is_available"] and line["unavailable_reason"] == "HIDDEN_PRODUCT"
        assert checkout(buyer, payload(r)).status_code == 409
    with client_for(cfg, owners[0]) as seller:
        assert (
            seller.patch(
                f"/api/v1/seller/products/{pid}", headers=csrf(seller), json={"is_active": True}
            ).status_code
            == 422
        )
        result = seller.patch(
            f"/api/v1/seller/products/{pid}", headers=csrf(seller), json={"price": "2.50"}
        )
        assert result.status_code == 200 and not result.json()["data"]["is_active"]
        assert seller.get(f"/api/v1/products/{pid}").status_code == 404
    with db.sessions() as s:
        assert s.get(Inventory, pid).quantity == 10
        assert (
            s.scalar(
                select(func.count()).select_from(Order).where(Order.buyer_user_id == r["buyers"][0])
            )
            == 0
        )


@pytest.mark.parametrize("status", ["PENDING", "REJECTED", "APPROVED", "LOCKED"])
def test_admin_can_hide_in_any_shop_status_and_keep_old_order(admin_products, status):
    cfg, db, r, _, _ = admin_products
    with client_for(cfg, r["buyers"][0]) as buyer:
        order = checkout(buyer, payload(r)).json()["data"]
    with db.sessions.begin() as s:
        s.get(Shop, r["shops"][0]).shop_status = status
    with client_for(cfg, r["buyers"][1]) as admin:
        assert hide(admin, r["products"][0]).status_code == 200
    with client_for(cfg, r["buyers"][0]) as buyer:
        assert buyer.get(f"/api/v1/orders/{order['order_id']}").json()["data"] == order
    with db.sessions() as s:
        assert s.get(Inventory, r["products"][0]).quantity == 9


def test_hide_vs_checkout_atomic(admin_products):
    cfg, db, r, _, _ = admin_products
    barrier = Barrier(2)

    def run(index):
        with client_for(cfg, r["buyers"][index]) as c:
            barrier.wait(timeout=10)
            return (
                checkout(c, payload(r)) if index == 0 else hide(c, r["products"][0])
            ).status_code

    with ThreadPoolExecutor(2) as pool:
        ordered, hidden = list(pool.map(run, range(2)))
    assert ordered in [201, 409] and hidden == 200
    with db.sessions() as s:
        assert not s.get(Product, r["products"][0]).is_active
        for pid in r["products"]:
            assert s.get(Inventory, pid).quantity == (9 if ordered == 201 else 10)


def test_duplicate_hide_and_seller_edit_no_reactivation(admin_products):
    cfg, db, r, owners, _ = admin_products
    barrier = Barrier(2)

    def run(index):
        with client_for(cfg, r["buyers"][1] if index == 0 else owners[0]) as c:
            barrier.wait(timeout=10)
            return (
                hide(c, r["products"][0])
                if index == 0
                else c.patch(
                    f"/api/v1/seller/products/{r['products'][0]}",
                    headers=csrf(c),
                    json={"description": "Updated"},
                )
            ).status_code

    with ThreadPoolExecutor(2) as pool:
        assert list(pool.map(run, range(2))) == [200, 200]
    with db.sessions() as s:
        p = s.get(Product, r["products"][0])
        assert not p.is_active and p.description == "Updated"


def test_permissions_status_csrf_and_missing(admin_products):
    cfg, db, r, owners, _ = admin_products
    with client_for(cfg, owners[0]) as c:
        assert c.get("/api/v1/admin/products").status_code == 403
        assert hide(c, r["products"][0]).status_code == 403
    with client_for(cfg, r["buyers"][1]) as c:
        assert c.post(f"/api/v1/admin/products/{r['products'][0]}/hide").status_code == 403
        assert hide(c, 9223372036854775807).status_code == 404
        with db.sessions.begin() as s:
            s.get(User, r["buyers"][1]).user_role = "USER"
        assert c.get("/api/v1/admin/products").status_code == 403
        assert hide(c, r["products"][0]).status_code == 403
        with db.sessions.begin() as s:
            u = s.get(User, r["buyers"][1])
            u.user_role = "ADMIN"
            u.user_status = "LOCKED"
        assert hide(c, r["products"][0]).status_code == 403
        c.cookies.clear()
        assert c.get("/api/v1/admin/products").status_code == 401


@pytest.mark.parametrize(
    "query",
    ["other=1", "page=0", "page_size=101", "shop_id=0", "is_active=not-bool", "q=" + "a" * 201],
)
def test_query_validation(admin_products, query):
    cfg, _, r, _, _ = admin_products
    with client_for(cfg, r["buyers"][1]) as c:
        assert c.get("/api/v1/admin/products?" + query).status_code == 422


def test_commit_failure_rolls_back(admin_products):
    cfg, db, r, _, _ = admin_products

    def fail(session):
        raise SQLAlchemyError("private DSN")

    def broken():
        with db.sessions() as s:
            event.listen(s, "before_commit", fail)
            yield s

    with client_for(cfg, r["buyers"][1]) as c:
        headers = csrf(c)
        c.app.dependency_overrides[get_session] = broken
        result = c.post(f"/api/v1/admin/products/{r['products'][0]}/hide", headers=headers)
        assert result.status_code == 503 and "private DSN" not in result.text
    with db.sessions() as s:
        assert s.get(Product, r["products"][0]).is_active
