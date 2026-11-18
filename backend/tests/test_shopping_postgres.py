"""Coupons/reviews against the isolated schema25 PostgreSQL fixture only."""

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import delete, event, func, insert, select
from sqlalchemy.exc import SQLAlchemyError
from test_checkout_postgres import checkout, client_for, csrf, payload
from test_checkout_postgres import checkout_db as checkout_db  # noqa: F401
from test_checkout_postgres import world as world  # noqa: F401
from test_seller_orders_postgres import cancel, change

from app.db.session import get_session
from app.models import CartItem, Inventory, Order, Shop, ShopOrder, User
from app.models.extensions import coupon_usages, coupons, product_reviews


def coupon(db, **changes):
    values = dict(
        code=uuid4().hex,
        discount_percent=Decimal("10"),
        usage_limit=10,
        starts_at=datetime.now(UTC) - timedelta(days=1),
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )
    values.update(changes)
    with db.sessions.begin() as s:
        return dict(s.execute(insert(coupons).values(**values).returning(coupons)).mappings().one())


def refill(db, r, buyer=0):
    with db.sessions.begin() as s:
        s.add_all(
            [
                CartItem(cart_id=r["carts"][buyer], product_id=pid, quantity=1)
                for pid in r["products"]
            ]
        )


def count_used(db, cid):
    with db.sessions() as s:
        return s.scalar(select(coupons.c.used_count).where(coupons.c.coupon_id == cid))


def test_coupon_server_quote_scope_rounding_and_idempotent_commit(world):
    cfg, db, r = world
    row = coupon(db, shop_id=r["shops"][0], min_order_amount=Decimal("12.00"))
    data = payload(r) | {"coupon_code": row["code"], "expected_coupon_discount": "1.23"}
    key = uuid4()
    with client_for(cfg, r["buyers"][0]) as c:
        quote = c.post("/api/v1/coupons/quote", json={"code": row["code"]}, headers=csrf(c))
        assert quote.status_code == 200
        assert quote.json()["discount_amount"] == "1.23"
        assert count_used(db, row["coupon_id"]) == 0
        result = checkout(c, data, key)
        assert result.status_code == 201, result.text
        order = result.json()["data"]
        assert order["total_amount"] == "16.78"
        assert order["discount_amount"] == "1.23"
        assert sum(Decimal(x["subtotal"]) for x in order["shop_orders"]) == Decimal("18.01")
        assert checkout(c, data, key).json()["data"] == order
        assert c.get(f"/api/v1/orders/{order['order_id']}").json()["data"] == order
    assert count_used(db, row["coupon_id"]) == 1
    with db.sessions() as s:
        assert (
            s.scalar(
                select(func.count())
                .select_from(coupon_usages)
                .where(coupon_usages.c.coupon_id == row["coupon_id"])
            )
            == 1
        )


@pytest.mark.parametrize(
    "changes,code",
    [
        ({"is_active": False}, "COUPON_INVALID"),
        ({"expires_at": datetime.now(UTC) - timedelta(hours=1)}, "COUPON_INVALID"),
        ({"starts_at": datetime.now(UTC) + timedelta(hours=1)}, "COUPON_INVALID"),
        ({"used_count": 10}, "COUPON_INVALID"),
        ({"min_order_amount": Decimal("19")}, "COUPON_MINIMUM"),
    ],
)
def test_invalid_coupon_rolls_back_order_stock_cart_usage(world, changes, code):
    cfg, db, r = world
    row = coupon(db, **changes)
    with client_for(cfg, r["buyers"][0]) as c:
        result = checkout(c, payload(r) | {"coupon_code": row["code"]})
        assert result.status_code == 409 and result.json()["error"]["code"] == code
    with db.sessions() as s:
        assert (
            s.scalar(
                select(func.count()).select_from(Order).where(Order.buyer_user_id == r["buyers"][0])
            )
            == 0
        )
        assert s.get(Inventory, r["products"][0]).quantity == 10
        assert (
            s.scalar(
                select(func.count()).select_from(CartItem).where(CartItem.cart_id == r["carts"][0])
            )
            == 2
        )


def test_shop_minimum_uses_only_eligible_goods_and_discount_must_be_confirmed(world):
    cfg, db, r = world
    row = coupon(db, shop_id=r["shops"][1], min_order_amount=Decimal("10"))
    with client_for(cfg, r["buyers"][0]) as c:
        assert (
            checkout(c, payload(r) | {"coupon_code": row["code"]}).json()["error"]["code"]
            == "COUPON_MINIMUM"
        )
        other = coupon(db)
        assert (
            checkout(
                c, payload(r) | {"coupon_code": other["code"], "expected_coupon_discount": "1.00"}
            ).json()["error"]["code"]
            == "COUPON_CHANGED"
        )
        assert checkout(c, payload(r) | {"coupon_code": "unknown"}).status_code == 409


def test_customer_limit_full_cancel_restores_once_and_can_use_again(world):
    cfg, db, r = world
    row = coupon(db)
    data = payload(r) | {"coupon_code": row["code"]}
    with client_for(cfg, r["buyers"][0]) as c:
        order = checkout(c, data).json()["data"]
        refill(db, r)
        assert checkout(c, data).json()["error"]["code"] == "COUPON_CUSTOMER_LIMIT"
        sid1, sid2 = [x["shop_order_id"] for x in order["shop_orders"]]
        assert cancel(c, order["order_id"], sid1).status_code == 200
        assert count_used(db, row["coupon_id"]) == 1
        assert checkout(c, data).status_code == 409
        assert cancel(c, order["order_id"], sid2).status_code == 200
        assert count_used(db, row["coupon_id"]) == 0
        assert cancel(c, order["order_id"], sid2).status_code == 200
        assert count_used(db, row["coupon_id"]) == 0
        assert checkout(c, data).status_code == 201
        assert count_used(db, row["coupon_id"]) == 1


def test_last_coupon_use_concurrent_buyers_only_one_order_commits(world):
    cfg, db, r = world
    row = coupon(db, usage_limit=1)
    # Different shops/products prevent catalog locks from serializing the coupon race.
    with db.sessions.begin() as s:
        for i in [0, 1]:
            s.execute(
                delete(CartItem).where(
                    CartItem.cart_id == r["carts"][i],
                    CartItem.product_id == r["products"][1 - i],
                )
            )
    barrier = Barrier(2)

    def buy(i):
        with client_for(cfg, r["buyers"][i]) as c:
            barrier.wait(timeout=10)
            data = payload(r, i)
            data["items"] = [data["items"][i]]
            return checkout(c, data | {"coupon_code": row["code"]}).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(buy, [0, 1])) == [201, 409]
    assert count_used(db, row["coupon_id"]) == 1


def test_pending_order_does_not_block_another_purchase(world):
    cfg, db, r = world
    with client_for(cfg, r["buyers"][0]) as c:
        with db.sessions.begin() as s:
            s.execute(
                delete(CartItem).where(
                    CartItem.cart_id == r["carts"][0], CartItem.product_id == r["products"][1]
                )
            )
        first_payload = payload(r)
        first_payload["items"] = first_payload["items"][:1]
        first = checkout(c, first_payload).json()["data"]
        refill(db, r)
        with db.sessions.begin() as s:
            s.execute(
                delete(CartItem).where(
                    CartItem.cart_id == r["carts"][0], CartItem.product_id == r["products"][0]
                )
            )
        second_payload = payload(r)
        second_payload["items"] = second_payload["items"][1:]
        second = checkout(c, second_payload)
        assert second.status_code == 201
        assert second.json()["data"]["order_id"] != first["order_id"]
        assert all(x["order_status"] == "PENDING" for x in first["shop_orders"])


def test_coupon_commit_failure_rolls_back_usage_and_retry_succeeds(world):
    cfg, db, r = world
    row = coupon(db)

    def fail(_):
        raise SQLAlchemyError("test commit failure")

    def override():
        with db.sessions() as s:
            event.listen(s, "before_commit", fail)
            yield s

    with client_for(cfg, r["buyers"][0]) as c:
        c.app.dependency_overrides[get_session] = override
        assert checkout(c, payload(r) | {"coupon_code": row["code"]}).status_code == 503
        assert count_used(db, row["coupon_id"]) == 0
        c.app.dependency_overrides.clear()
        assert checkout(c, payload(r) | {"coupon_code": row["code"]}).status_code == 201


def test_concurrent_shop_cancellations_restore_coupon_once(world):
    cfg, db, r = world
    row = coupon(db)
    with client_for(cfg, r["buyers"][0]) as c:
        order = checkout(c, payload(r) | {"coupon_code": row["code"]}).json()["data"]
    with db.sessions() as s:
        owners = {sid: s.get(Shop, sid).owner_user_id for sid in r["shops"]}
    barrier = Barrier(2)

    def cancel_shop(shop):
        with client_for(cfg, owners[int(shop["shop_id"])]) as c:
            barrier.wait(timeout=10)
            return change(c, shop["shop_order_id"], "CANCELLED").status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(cancel_shop, order["shop_orders"])) == [200, 200]
    assert count_used(db, row["coupon_id"]) == 0


def test_reviews_require_completed_owned_purchase_and_public_projection(world):
    cfg, db, r = world
    with client_for(cfg, r["buyers"][0]) as c:
        order = checkout(c, payload(r)).json()["data"]
        shop = order["shop_orders"][0]
        line = shop["items"][0]
        path = f"/api/v1/order-items/{line['order_item_id']}/review"
        assert c.post(path, json={"rating": 5}, headers=csrf(c)).status_code == 409
        with db.sessions.begin() as s:
            s.get(ShopOrder, int(shop["shop_order_id"])).order_status = "COMPLETED"
        assert c.get(path).json() == {"data": None}
        assert c.post(path, json={"rating": 6}, headers=csrf(c)).status_code == 422
        assert c.post(path, json={"rating": True}, headers=csrf(c)).status_code == 422
        assert (
            c.post(path, json={"rating": 5, "comment": "a" * 2001}, headers=csrf(c)).status_code
            == 422
        )
        assert c.post(path, json={"rating": 5}).status_code == 403
        created = c.post(path, json={"rating": 4, "comment": "  Tốt <script>  "}, headers=csrf(c))
        assert created.status_code == 201, created.text
        assert c.get(path).json() == created.json()
        assert c.post(path, json={"rating": 1}, headers=csrf(c)).status_code == 409
        public = c.get(f"/api/v1/products/{line['product_id']}/reviews")
        assert public.status_code == 200
        assert public.json()["total"] == 1
        assert Decimal(public.json()["average_rating"]) == 4
        assert set(public.json()["items"][0]) == {"review_id", "rating", "comment", "created_at"}
        assert public.json()["items"][0]["comment"] == "Tốt <script>"
    with client_for(cfg, r["buyers"][1]) as other:
        assert other.get(path).status_code == 404
        assert other.post(path, json={"rating": 1}, headers=csrf(other)).status_code == 404
    with db.sessions.begin() as s:
        from app.models import Product

        s.get(Product, int(line["product_id"])).is_active = False
        s.get(User, r["buyers"][1]).user_role = "ADMIN"
    with client_for(cfg, r["buyers"][1]) as admin:
        assert admin.post(path, json={"rating": 5}, headers=csrf(admin)).status_code == 403
        assert (
            admin.post(
                "/api/v1/coupons/quote", json={"code": "any"}, headers=csrf(admin)
            ).status_code
            == 403
        )
        assert admin.get(f"/api/v1/products/{line['product_id']}/reviews").status_code == 404


def test_concurrent_review_has_single_record(world):
    cfg, db, r = world
    with client_for(cfg, r["buyers"][0]) as c:
        order = checkout(c, payload(r)).json()["data"]
    shop = order["shop_orders"][0]
    item = shop["items"][0]["order_item_id"]
    with db.sessions.begin() as s:
        s.get(ShopOrder, int(shop["shop_order_id"])).order_status = "COMPLETED"
    barrier = Barrier(2)

    def post(_):
        with client_for(cfg, r["buyers"][0]) as c:
            barrier.wait(timeout=10)
            return c.post(
                f"/api/v1/order-items/{item}/review", json={"rating": 5}, headers=csrf(c)
            ).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(post, [0, 1])) == [201, 409]
    with db.sessions() as s:
        assert (
            s.scalar(
                select(func.count())
                .select_from(product_reviews)
                .where(product_reviews.c.order_item_id == int(item))
            )
            == 1
        )


def test_direct_buy_coupon_quote_does_not_include_existing_cart(world):
    cfg, db, r = world
    offer = coupon(db)
    selected = payload(r)["items"][0] | {"quantity": 2}
    with client_for(cfg, r["buyers"][0]) as c:
        quote = c.post(
            "/api/v1/coupons/quote",
            json={"code": offer["code"], "direct_item": selected},
            headers=csrf(c),
        )
        assert quote.status_code == 200
        assert quote.json()["subtotal"] == "24.68"
        data = payload(r) | {
            "purchase_mode": "BUY_NOW",
            "items": [selected],
            "coupon_code": offer["code"],
            "expected_coupon_discount": quote.json()["discount_amount"],
        }
        result = checkout(c, data)
        assert result.status_code == 201
        assert result.json()["data"]["total_amount"] == quote.json()["total_amount"]
    with db.sessions() as s:
        assert (
            s.scalar(
                select(func.count()).select_from(CartItem).where(CartItem.cart_id == r["carts"][0])
            )
            == 2
        )


def test_selected_coupon_quote_uses_only_selected_cart_lines(world):
    cfg, db, r = world
    offer = coupon(db)
    with client_for(cfg, r["buyers"][0]) as c:
        q = c.post(
            "/api/v1/coupons/quote",
            json={"code": offer["code"], "selected_product_ids": [str(r["products"][0])]},
            headers=csrf(c),
        )
        assert q.status_code == 200
        assert q.json()["subtotal"] == "12.34"
