from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import delete, event, func, select, update
from sqlalchemy.exc import SQLAlchemyError
from test_checkout_postgres import checkout, client_for, csrf, payload
from test_checkout_postgres import checkout_db as checkout_db  # noqa: F401
from test_checkout_postgres import world as world  # noqa: F401
from test_seller_orders_postgres import cancel, change
from test_shopping_postgres import count_used, coupon

from app.db.session import get_session
from app.models import CartItem, Inventory, Shop
from app.models.extensions import coupon_usages, coupons, payments, shipments


def setup(world):
    cfg, db, r = world
    cfg = cfg.model_copy(update={"checkout_options_enabled": True})
    shop1 = coupon(db, shop_id=r["shops"][0], discount_percent="10")
    shop2 = coupon(db, shop_id=r["shops"][1], discount_percent="20")
    coco = coupon(db, discount_percent="10")
    freight = coupon(db, coupon_type="SHIPPING", discount_percent="50", min_order_amount="10")
    selection = {
        "shipping_method": "STANDARD",
        "payment_method": "COD",
        "shop_coupons": [
            {"shop_id": str(r["shops"][0]), "code": shop1["code"]},
            {"shop_id": str(r["shops"][1]), "code": shop2["code"]},
        ],
        "coco_coupon_code": coco["code"],
        "shipping_coupon_code": freight["code"],
    }
    return cfg, db, r, [shop1, shop2, coco, freight], selection


def quote(c, selection):
    return c.post("/api/v1/checkout/quote", json=selection, headers=csrf(c))


def quoted_payload(r, selection, q):
    return (
        payload(r)
        | selection
        | {
            "expected_coupon_discount": q["discount_amount"],
            "expected_shipping_fee": q["shipping_fee"],
            "expected_shipping_discount": q["shipping_discount_amount"],
        }
    )


def test_four_coupons_shipping_snapshot_idempotency_and_cancel_all(world):
    cfg, db, r, codes, selection = setup(world)
    with client_for(cfg, r["buyers"][0]) as c:
        options = c.get("/api/v1/checkout/options").json()
        assert options["enabled"]
        assert [Decimal(m["fee_per_shop"]) for m in options["shipping_methods"]] == [
            25000,
            40000,
            60000,
        ]
        assert [m["enabled"] for m in options["payment_methods"]] == [True, False, False, False]
        result = quote(c, selection)
        assert result.status_code == 200, result.text
        q = result.json()
        assert q["discount_amount"] == "3.93"
        assert q["shipping_discount_amount"] == "25000.00"
        assert q["shipping_fee"] == "25000.00"
        assert q["total_amount"] == "25014.08"
        assert len(q["applied_coupons"]) == 4
        assert all(count_used(db, code["coupon_id"]) == 0 for code in codes)
        data = quoted_payload(r, selection, q)
        key = uuid4()
        placed = checkout(c, data, key)
        assert placed.status_code == 201, placed.text
        order = placed.json()["data"]
        assert order["total_amount"] == q["total_amount"]
        assert order["shipping_discount_amount"] == q["shipping_discount_amount"]
        assert order["payment_status"] == "PENDING"
        assert len(order["applied_coupons"]) == 4
        assert checkout(c, data, key).json()["data"] == order
        with db.sessions() as s:
            assert (
                s.scalar(
                    select(func.count())
                    .select_from(coupon_usages)
                    .where(coupon_usages.c.order_id == int(order["order_id"]))
                )
                == 4
            )
            assert s.scalar(
                select(func.sum(shipments.c.shipping_fee)).where(
                    shipments.c.shop_order_id.in_(
                        [int(x["shop_order_id"]) for x in order["shop_orders"]]
                    )
                )
            ) == Decimal("25000")
        for i, child in enumerate(order["shop_orders"]):
            assert cancel(c, order["order_id"], child["shop_order_id"]).status_code == 200
            assert all(count_used(db, code["coupon_id"]) == (1 if i == 0 else 0) for code in codes)
        assert (
            cancel(c, order["order_id"], order["shop_orders"][-1]["shop_order_id"]).status_code
            == 200
        )
        assert all(count_used(db, code["coupon_id"]) == 0 for code in codes)
        assert (
            c.get(f"/api/v1/orders/{order['order_id']}").json()["data"]["payment_status"]
            == "FAILED"
        )


@pytest.mark.parametrize("field,which", [("coco_coupon_code", 0), ("shipping_coupon_code", 2)])
def test_coupon_slots_reject_wrong_scope_and_type(world, field, which):
    cfg, db, r, codes, selection = setup(world)
    selection[field] = codes[which]["code"]
    # Avoid duplicate-code validation so the scope/type policy is exercised.
    if field == "coco_coupon_code":
        selection["shop_coupons"] = selection["shop_coupons"][1:]
    else:
        selection.pop("coco_coupon_code")
    with client_for(cfg, r["buyers"][0]) as c:
        response = quote(c, selection)
        assert response.status_code == 409 and response.json()["error"]["code"] == "COUPON_SCOPE"


def test_quote_required_rate_tampering_and_unconfigured_payments(world):
    cfg, db, r, codes, selection = setup(world)
    with client_for(cfg, r["buyers"][0]) as c:
        assert checkout(c, payload(r)).json()["error"]["code"] == "QUOTE_REQUIRED"
        q = quote(c, selection).json()
        data = quoted_payload(r, selection, q)
        assert (
            checkout(c, data | {"expected_shipping_fee": "0"}).json()["error"]["code"]
            == "SHIPPING_CHANGED"
        )
        for method in ["BANK_TRANSFER", "MOMO", "VNPAY"]:
            assert quote(c, selection | {"payment_method": method}).status_code == 503
            assert checkout(c, data | {"payment_method": method}).status_code == 503
        assert all(count_used(db, code["coupon_id"]) == 0 for code in codes)
    with db.sessions() as s:
        assert s.get(Inventory, r["products"][0]).quantity == 10


def test_bank_transfer_is_pending_and_prevents_unpaid_fulfillment(world):
    cfg, db, r, codes, selection = setup(world)
    cfg = cfg.model_copy(
        update={
            "bank_name": "TEST BANK",
            "bank_account_number": "TEST-ONLY",
            "bank_account_holder": "TEST ONLY",
        }
    )
    selection["payment_method"] = "BANK_TRANSFER"
    selection["shipping_method"] = "COCOEXPRESS"
    with client_for(cfg, r["buyers"][0]) as c:
        q = quote(c, selection).json()
        placed = checkout(c, quoted_payload(r, selection, q))
        assert placed.status_code == 201, placed.text
        order = placed.json()["data"]
        assert order["payment_method"] == "BANK_TRANSFER" and order["payment_status"] == "PENDING"
        assert all(x["shipping_method"] == "COCOEXPRESS" for x in order["shop_orders"])
    first = order["shop_orders"][0]
    with db.sessions() as s:
        owner = s.get(Shop, int(first["shop_id"])).owner_user_id
    with client_for(cfg, owner) as seller:
        response = change(seller, first["shop_order_id"], "CONFIRMED")
        assert response.status_code == 409 and response.json()["error"]["code"] == "PAYMENT_PENDING"
    with db.sessions() as s:
        record = (
            s.execute(select(payments).where(payments.c.order_id == int(order["order_id"])))
            .mappings()
            .one()
        )
        assert record["payment_status"] == "PENDING" and record["paid_at"] is None


def test_shipping_discount_rounding_never_negative_and_fee_cannot_be_discounted_as_goods(world):
    cfg, db, r, codes, selection = setup(world)
    cfg = cfg.model_copy(update={"shipping_standard_fee": Decimal("0.01")})
    freight = coupon(db, coupon_type="SHIPPING", discount_percent="75")
    selection["shipping_coupon_code"] = freight["code"]
    with client_for(cfg, r["buyers"][0]) as c:
        result = quote(c, selection)
        assert result.status_code == 200, result.text
        q = result.json()
        assert q["shipping_discount_amount"] == "0.02" and q["shipping_fee"] == "0.00"
        assert all(Decimal(x["fee"]) >= 0 for x in q["shipping"])


def test_stacked_coupon_last_global_use_across_different_shops(world):
    cfg, db, r, codes, selection = setup(world)
    with db.sessions.begin() as s:
        s.execute(
            update(coupons)
            .where(coupons.c.coupon_id == codes[2]["coupon_id"])
            .values(usage_limit=1)
        )
        for i in [0, 1]:
            s.execute(
                delete(CartItem).where(
                    CartItem.cart_id == r["carts"][i], CartItem.product_id == r["products"][1 - i]
                )
            )
    barrier = Barrier(2)

    def buy(i):
        choice = {k: v for k, v in selection.items() if k != "shipping_coupon_code"}
        choice["shop_coupons"] = [selection["shop_coupons"][i]]
        with client_for(cfg, r["buyers"][i]) as c:
            q = quote(c, choice)
            assert q.status_code == 200, q.text
            data = quoted_payload(r, choice, q.json())
            data["address_id"] = str(r["addresses"][i])
            data["items"] = [data["items"][i]]
            barrier.wait(timeout=10)
            return checkout(c, data).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(buy, [0, 1])) == [201, 409]
    assert count_used(db, codes[2]["coupon_id"]) == 1


def test_stacked_coupon_commit_failure_rolls_back_every_usage(world):
    cfg, db, r, codes, selection = setup(world)

    def fail(_):
        raise SQLAlchemyError("test commit failure")

    def override():
        with db.sessions() as s:
            event.listen(s, "before_commit", fail)
            yield s

    with client_for(cfg, r["buyers"][0]) as c:
        q = quote(c, selection).json()
        data = quoted_payload(r, selection, q)
        key = uuid4()
        c.app.dependency_overrides[get_session] = override
        assert checkout(c, data, key).status_code == 503
        assert all(count_used(db, code["coupon_id"]) == 0 for code in codes)
        with db.sessions() as s:
            assert all(s.get(Inventory, pid).quantity == 10 for pid in r["products"])
            assert (
                s.scalar(
                    select(func.count())
                    .select_from(coupon_usages)
                    .where(coupon_usages.c.coupon_id.in_([code["coupon_id"] for code in codes]))
                )
                == 0
            )
        c.app.dependency_overrides.clear()
        assert checkout(c, data, key).status_code == 201
