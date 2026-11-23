"""FR-A01..04 acceptance on disposable marketplace_test, after pristine catalog suite."""

from uuid import uuid4

import pytest
from test_checkout_postgres import checkout, client_for, csrf, payload
from test_checkout_postgres import checkout_db as checkout_db  # noqa: F401
from test_checkout_postgres import world as world  # noqa: F401

from app.models import Category, Inventory, Product, Shop, User


def prepare(world):
    cfg, db, r = world
    with db.sessions.begin() as session:
        session.get(User, r["buyers"][1]).user_role = "ADMIN"
        owner = session.get(Shop, r["shops"][0]).owner_user_id
        category = session.get(Product, r["products"][0]).category_id
    return cfg, db, r, owner, category


@pytest.mark.parametrize("actor", ["guest", "buyer", "owner"])
def test_only_admin_can_read_management_or_mutate_moderation(world, actor):
    cfg, db, r, owner, category = prepare(world)
    uid = owner if actor == "owner" else r["buyers"][0]
    with client_for(cfg, uid) as client:
        if actor == "guest":
            client.cookies.clear()
        expected = 401 if actor == "guest" else 403
        for resource in ["users", "shops", "products", "categories"]:
            assert client.get(f"/api/v1/admin/{resource}").status_code == expected
        headers = csrf(client)
        for target, source in [("APPROVED", "PENDING"), ("LOCKED", "APPROVED")]:
            result = client.patch(
                f"/api/v1/admin/shops/{r['shops'][0]}/status",
                headers=headers,
                json={"expected_status": source, "shop_status": target},
            )
            assert result.status_code == expected
        assert (
            client.patch(
                f"/api/v1/admin/users/{r['buyers'][1]}/status",
                headers=headers,
                json={"user_status": "LOCKED"},
            ).status_code
            == expected
        )
        assert (
            client.post(
                f"/api/v1/admin/products/{r['products'][0]}/hide",
                headers=headers,
            ).status_code
            == expected
        )
        assert (
            client.patch(
                f"/api/v1/admin/categories/{category}",
                headers=headers,
                json={"is_active": False},
            ).status_code
            == expected
        )
        assert (
            client.post(
                "/api/v1/admin/categories",
                headers=headers,
                json={"category_name": "Forbidden", "category_slug": uuid4().hex},
            ).status_code
            == expected
        )
    with db.sessions() as session:
        assert session.get(Shop, r["shops"][0]).shop_status == "APPROVED"
        assert session.get(Product, r["products"][0]).is_active
        assert session.get(Category, category).is_active
        assert session.get(User, r["buyers"][1]).user_status == "ACTIVE"


def test_admin_acceptance_users_shops_hidden_search_and_category_links(world):
    cfg, db, r, owner, category = prepare(world)
    name = "Acceptance-" + uuid4().hex
    with db.sessions.begin() as session:
        session.get(User, r["buyers"][0]).full_name = name
        session.get(Product, r["products"][0]).product_name = name
        for sid in r["shops"]:
            session.get(Shop, sid).shop_status = "PENDING"
    with client_for(cfg, r["buyers"][1]) as admin:
        headers = csrf(admin)
        users = admin.get("/api/v1/admin/users", params={"q": name})
        assert users.status_code == 200
        assert [u["user_id"] for u in users.json()["items"]] == [str(r["buyers"][0])]
        for status in ["LOCKED", "ACTIVE"]:
            result = admin.patch(
                f"/api/v1/admin/users/{r['buyers'][0]}/status",
                headers=headers,
                json={"user_status": status},
            )
            assert result.status_code == 200 and result.json()["data"]["user_status"] == status
            with client_for(cfg, r["buyers"][0]) as buyer:
                assert buyer.get("/api/v1/auth/me").status_code == (
                    403 if status == "LOCKED" else 200
                )
        assert admin.get("/api/v1/admin/shops").status_code == 200
        for sid, target in zip(r["shops"], ["APPROVED", "REJECTED"], strict=True):
            assert (
                admin.patch(
                    f"/api/v1/admin/shops/{sid}/status",
                    headers=headers,
                    json={"expected_status": "PENDING", "shop_status": target},
                ).status_code
                == 200
            )
        assert admin.get("/api/v1/admin/products").status_code == 200

        def search():
            return admin.get("/api/v1/products", params={"q": name}).json()

        assert search()["total"] == 1
        assert (
            admin.post(
                f"/api/v1/admin/products/{r['products'][0]}/hide",
                headers=headers,
            ).status_code
            == 200
        )
        assert search()["total"] == 0
        assert admin.get(f"/api/v1/products/{r['products'][0]}").status_code == 404
        assert (
            admin.patch(
                f"/api/v1/admin/shops/{r['shops'][0]}/status",
                headers=headers,
                json={"expected_status": "APPROVED", "shop_status": "LOCKED"},
            ).status_code
            == 200
        )
        created = admin.post(
            "/api/v1/admin/categories",
            headers=headers,
            json={"category_name": "Acceptance category", "category_slug": uuid4().hex},
        )
        assert created.status_code == 201
        assert (
            admin.patch(
                f"/api/v1/admin/categories/{category}",
                headers=headers,
                json={"category_name": "Updated category", "is_active": False},
            ).status_code
            == 200
        )
        assert (
            admin.delete(f"/api/v1/admin/categories/{category}", headers=headers).status_code == 405
        )
    with client_for(cfg, owner) as seller:
        assert (
            seller.post(
                "/api/v1/seller/products",
                headers=csrf(seller),
                json={
                    "category_id": str(category),
                    "sku": uuid4().hex,
                    "product_name": "Blocked",
                    "price": "100",
                    "initial_quantity": 1,
                },
            ).status_code
            == 403
        )
    with client_for(cfg, r["buyers"][0]) as buyer:
        assert checkout(buyer, payload(r)).status_code == 409
    with db.sessions() as session:
        assert session.get(Category, category).category_name == "Updated category"
        assert not session.get(Category, category).is_active
        for pid in r["products"]:
            assert session.get(Product, pid).category_id == category
            assert session.get(Inventory, pid).quantity == 10
