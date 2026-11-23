from uuid import uuid4

import pytest
from test_checkout_postgres import checkout, client_for, payload
from test_checkout_postgres import checkout_db as checkout_db  # noqa: F401
from test_checkout_postgres import world as world  # noqa: F401

from app.models import Shop


@pytest.mark.parametrize("status", ["PENDING", "APPROVED", "LOCKED"])
def test_shop_owner_keeps_access_to_personal_purchases_only(world, status):
    cfg, db, r = world
    with db.sessions.begin() as s:
        s.add(
            Shop(
                owner_user_id=r["buyers"][0],
                shop_name="Buyer own shop",
                shop_slug=uuid4().hex,
                shop_status=status,
            )
        )
    with client_for(cfg, r["buyers"][0]) as owner:
        response = checkout(owner, payload(r))
        assert response.status_code == 201
        order = response.json()["data"]
        listed = owner.get("/api/v1/orders")
        assert listed.status_code == 200
        assert listed.json()["total"] == 1
        assert listed.json()["items"][0]["order_id"] == order["order_id"]
        assert owner.get(f"/api/v1/orders/{order['order_id']}").json()["data"] == order
    with client_for(cfg, r["buyers"][1]) as other:
        assert other.get("/api/v1/orders").json()["total"] == 0
        assert other.get(f"/api/v1/orders/{order['order_id']}").status_code == 404
