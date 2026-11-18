"""Admin role cannot participate in Buyer flows or create a shop."""

from uuid import uuid4

import pytest
from sqlalchemy import func, select
from test_checkout_postgres import checkout, client_for, csrf, payload
from test_checkout_postgres import checkout_db as checkout_db  # noqa: F401
from test_checkout_postgres import world as world  # noqa: F401

from app.models import Inventory, Order, Shop, User


@pytest.mark.parametrize("has_shop", [False, True])
def test_promotion_blocks_commerce_even_with_old_token_order_and_shop(world, has_shop):
    cfg, db, r = world
    uid = r["buyers"][0]
    key = uuid4()
    with client_for(cfg, uid) as client:
        order = checkout(client, payload(r), key)
        assert order.status_code == 201
        oid = order.json()["data"]["order_id"]
        sid = order.json()["data"]["shop_orders"][0]["shop_order_id"]
        with db.sessions.begin() as session:
            session.get(User, uid).user_role = "ADMIN"
            if has_shop:
                session.add(Shop(owner_user_id=uid, shop_name="Existing", shop_slug=uuid4().hex))
        paths = ["cart", "addresses", "orders", f"orders/{oid}", "seller/shop"]
        for path in paths:
            result = client.get("/api/v1/" + path)
            assert result.status_code == 403
            assert result.json()["error"]["code"] == "COMMERCE_FORBIDDEN"
        assert checkout(client, payload(r), key).status_code == 403
        assert checkout(client, payload(r)).status_code == 403
        for method, path, data in [
            ("POST", "cart/items", {"product_id": str(r["products"][0]), "quantity": 1}),
            ("POST", "seller/shop", {"shop_name": "Forbidden", "shop_slug": uuid4().hex}),
            ("POST", f"orders/{oid}/shop-orders/{sid}/cancel", None),
            (
                "POST",
                "addresses",
                {
                    "recipient_name": "Admin",
                    "phone": "0901234567",
                    "address_line": "Test",
                    "city": "Test",
                },
            ),
        ]:
            result = client.request(method, "/api/v1/" + path, headers=csrf(client), json=data)
            assert result.status_code == 403
            assert result.json()["error"]["code"] == "COMMERCE_FORBIDDEN"
        assert client.get("/api/v1/auth/me").json()["data"]["user_role"] == "ADMIN"
        assert client.get("/api/v1/admin/users").status_code == 200
        assert client.get("/api/v1/admin/shops").status_code == 200
        assert client.get("/api/v1/products").status_code == 200
        with db.sessions() as session:
            assert (
                session.scalar(
                    select(func.count()).select_from(Order).where(Order.buyer_user_id == uid)
                )
                == 1
            )
            assert session.scalar(
                select(func.count()).select_from(Shop).where(Shop.owner_user_id == uid)
            ) == int(has_shop)
            assert all(session.get(Inventory, pid).quantity == 9 for pid in r["products"])
        with db.sessions.begin() as session:
            session.get(User, uid).user_role = "USER"
        assert client.get("/api/v1/cart").status_code == 200
