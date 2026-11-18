from uuid import uuid4

import pytest
from sqlalchemy import select
from test_checkout_postgres import checkout, client_for, csrf, payload
from test_checkout_postgres import checkout_db as checkout_db  # noqa: F401
from test_checkout_postgres import world as world  # noqa: F401

from app.models import CartItem, Inventory, Product, Shop, User
from app.models.extensions import product_price_history, shop_approval_history


def context(world):
    cfg, db, r = world
    with db.sessions() as session:
        owners = [session.get(Shop, sid).owner_user_id for sid in r["shops"]]
        category = session.get(Product, r["products"][0]).category_id
    return cfg, db, r, owners, category


def fresh(client, category):
    response = client.post(
        "/api/v1/seller/products",
        headers=csrf(client),
        json={
            "category_id": str(category),
            "sku": uuid4().hex,
            "product_name": "CRUD product",
            "price": "10",
            "initial_quantity": 3,
        },
    )
    assert response.status_code == 201
    return response.json()["data"]["product_id"]


def test_product_create_read_edit_delete_and_ownership(world):
    cfg, db, r, owners, category = context(world)
    with client_for(cfg, owners[0]) as seller:
        pid = fresh(seller, category)
        path = f"/api/v1/seller/products/{pid}"
        assert seller.get(path).status_code == 200
        assert (
            seller.patch(path, headers=csrf(seller), json={"product_name": "Updated"}).status_code
            == 200
        )
        with client_for(cfg, owners[1]) as other:
            assert other.delete(path, headers=csrf(other)).status_code == 404
        assert seller.delete(path).status_code == 403
        deleted = seller.delete(path, headers=csrf(seller))
        assert deleted.status_code == 204 and not deleted.content
        assert seller.get(path).status_code == 404
        assert seller.delete(path, headers=csrf(seller)).status_code == 404
    with db.sessions() as session:
        assert session.get(Product, int(pid)) is None
        assert session.get(Inventory, int(pid)) is None


@pytest.mark.parametrize("reference", ["cart", "order", "price_history"])
def test_product_used_cannot_be_deleted_and_inventory_rollback(world, reference):
    cfg, db, r, owners, category = context(world)
    if reference == "order":
        with client_for(cfg, r["buyers"][0]) as buyer:
            assert checkout(buyer, payload(r)).status_code == 201
        pid = str(r["products"][0])
        expected_quantity = 9
    elif reference == "cart":
        pid = str(r["products"][0])
        expected_quantity = 10
    else:
        with client_for(cfg, owners[0]) as seller:
            pid = fresh(seller, category)
        with db.sessions.begin() as session:
            session.execute(
                product_price_history.insert().values(
                    product_id=int(pid), old_price="1", new_price="10", changed_by=owners[0]
                )
            )
        expected_quantity = 3
    with client_for(cfg, owners[0]) as seller:
        result = seller.delete(f"/api/v1/seller/products/{pid}", headers=csrf(seller))
        assert result.status_code == 409
        assert result.json()["error"]["code"] == "PRODUCT_IN_USE"
    with db.sessions() as session:
        assert session.get(Product, int(pid)) is not None
        assert session.get(Inventory, int(pid)).quantity == expected_quantity


@pytest.mark.parametrize("status", ["PENDING", "APPROVED", "REJECTED", "LOCKED"])
def test_unused_shop_crud_and_stale_delete_cannot_delete_replacement(world, status):
    cfg, db, r, owners, category = context(world)
    with client_for(cfg, r["buyers"][0]) as owner:
        data = {"shop_name": "CRUD shop", "shop_slug": uuid4().hex}
        created = owner.post("/api/v1/seller/shop", headers=csrf(owner), json=data)
        assert created.status_code == 201
        sid = created.json()["data"]["shop_id"]
        with db.sessions.begin() as session:
            session.get(Shop, int(sid)).shop_status = status
        assert owner.get("/api/v1/seller/shop").status_code == 200
        assert (
            owner.patch(
                "/api/v1/seller/shop", headers=csrf(owner), json={"shop_name": "Edited"}
            ).status_code
            == 200
        )
        with client_for(cfg, owners[0]) as other:
            assert (
                other.delete(f"/api/v1/seller/shop/{sid}", headers=csrf(other)).status_code == 404
            )
        assert owner.delete(f"/api/v1/seller/shop/{sid}", headers=csrf(owner)).status_code == 204
        assert owner.get("/api/v1/seller/shop").status_code == 404
        replacement = owner.post("/api/v1/seller/shop", headers=csrf(owner), json=data)
        assert replacement.status_code == 201
        assert owner.delete(f"/api/v1/seller/shop/{sid}", headers=csrf(owner)).status_code == 404
        assert (
            owner.get("/api/v1/seller/shop").json()["data"]["shop_id"]
            == replacement.json()["data"]["shop_id"]
        )


def test_shop_with_products_or_approval_history_cannot_delete(world):
    cfg, db, r, owners, category = context(world)
    with client_for(cfg, owners[0]) as owner:
        result = owner.delete(f"/api/v1/seller/shop/{r['shops'][0]}", headers=csrf(owner))
        assert result.status_code == 409 and result.json()["error"]["code"] == "SHOP_IN_USE"
    with client_for(cfg, r["buyers"][0]) as owner:
        sid = owner.post(
            "/api/v1/seller/shop",
            headers=csrf(owner),
            json={"shop_name": "History", "shop_slug": uuid4().hex},
        ).json()["data"]["shop_id"]
        with db.sessions.begin() as session:
            session.get(User, r["buyers"][1]).user_role = "ADMIN"
            session.execute(
                shop_approval_history.insert().values(
                    shop_id=int(sid), admin_user_id=r["buyers"][1], new_status="PENDING"
                )
            )
        assert owner.delete(f"/api/v1/seller/shop/{sid}", headers=csrf(owner)).status_code == 409
    with db.sessions() as session:
        assert session.get(Shop, int(sid)) is not None
        assert session.scalar(select(CartItem).where(CartItem.cart_id == r["carts"][0])) is not None
