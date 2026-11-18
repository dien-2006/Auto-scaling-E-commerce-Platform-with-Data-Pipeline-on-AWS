from uuid import uuid4

from sqlalchemy import func, select
from test_checkout_postgres import checkout, client_for, payload
from test_checkout_postgres import checkout_db as checkout_db  # noqa: F401
from test_checkout_postgres import world as world  # noqa: F401

from app.models import Inventory, Order, User


def test_checkout_status_reads_only_owned_order_without_creating_or_replaying(world):
    cfg, db, r = world
    key = uuid4()
    path = "/api/v1/orders/checkout-status"
    headers = {"Idempotency-Key": str(key)}
    with client_for(cfg, r["buyers"][0]) as c:
        assert c.get(path, headers=headers).json() == {"data": None}
        with db.sessions() as s:
            assert (
                s.scalar(
                    select(func.count())
                    .select_from(Order)
                    .where(Order.buyer_user_id == r["buyers"][0])
                )
                == 0
            )
            assert s.get(Inventory, r["products"][0]).quantity == 10
        placed = checkout(c, payload(r), key).json()
        for _ in range(2):
            status = c.get(path, headers=headers)
            assert status.status_code == 200
            assert status.headers["cache-control"] == "no-store"
            assert status.json() == placed
        assert c.get(path).status_code == 422
        assert c.get(path, headers={"Idempotency-Key": "bad"}).status_code == 422
    with client_for(cfg, r["buyers"][1]) as other:
        assert other.get(path, headers=headers).json() == {"data": None}
    with db.sessions.begin() as s:
        s.get(User, r["buyers"][1]).user_role = "ADMIN"
    with client_for(cfg, r["buyers"][1]) as admin:
        assert admin.get(path, headers=headers).status_code == 403
    with db.sessions() as s:
        assert s.get(Inventory, r["products"][0]).quantity == 9
