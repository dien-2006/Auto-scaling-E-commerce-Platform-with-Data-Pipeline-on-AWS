"""Cross-feature regression; fixtures write only to disposable marketplace_test.

Run after test_public_catalog: that suite intentionally expects a pristine schema.
"""

from uuid import uuid4

import pytest
from test_checkout_postgres import checkout, client_for, csrf, payload
from test_checkout_postgres import checkout_db as checkout_db  # noqa: F401
from test_checkout_postgres import world as world  # noqa: F401
from test_seller_orders_postgres import change

from app.models import Inventory, Shop, User


@pytest.mark.parametrize("moderation", ["product", "shop", "category"])
def test_moderation_preserves_checkout_replay_and_seller_cancellation(world, moderation):
    cfg, db, r = world
    with db.sessions.begin() as session:
        admin_id = r["buyers"][1]
        session.get(User, admin_id).user_role = "ADMIN"
        owner_id = session.get(Shop, r["shops"][0]).owner_user_id

    key = uuid4()
    request = payload(r)
    with client_for(cfg, r["buyers"][0]) as buyer:
        placed = checkout(buyer, request, key)
        assert placed.status_code == 201
        original = placed.json()["data"]
        target = next(
            row for row in original["shop_orders"] if row["shop_id"] == str(r["shops"][0])
        )
        with client_for(cfg, admin_id) as admin:
            if moderation == "product":
                result = admin.post(
                    f"/api/v1/admin/products/{r['products'][0]}/hide", headers=csrf(admin)
                )
            elif moderation == "shop":
                result = admin.patch(
                    f"/api/v1/admin/shops/{r['shops'][0]}/status",
                    headers=csrf(admin),
                    json={"expected_status": "APPROVED", "shop_status": "LOCKED"},
                )
            else:
                result = admin.patch(
                    f"/api/v1/admin/categories/{r['parent']}",
                    headers=csrf(admin),
                    json={"is_active": False},
                )
            assert result.status_code == 200, result.text

        assert buyer.get(f"/api/v1/products/{r['products'][0]}").status_code == 404
        replay = checkout(buyer, request, key)
        assert replay.status_code == 200
        assert replay.json()["data"] == original
        assert buyer.get(f"/api/v1/orders/{original['order_id']}").json()["data"] == original

        with client_for(cfg, admin_id) as other_buyer:
            assert other_buyer.get(f"/api/v1/orders/{original['order_id']}").status_code == 403
        with client_for(cfg, owner_id) as seller:
            sid = target["shop_order_id"]
            assert change(seller, sid, "CANCELLED").status_code == 200
            assert change(seller, sid, "CANCELLED").status_code == 200

    with db.sessions() as session:
        assert session.get(Inventory, r["products"][0]).quantity == 10
        assert session.get(Inventory, r["products"][1]).quantity == 9
