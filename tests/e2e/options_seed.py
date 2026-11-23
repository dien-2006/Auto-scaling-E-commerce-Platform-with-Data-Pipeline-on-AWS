"""Seed only the runner-owned loopback test DB, never the business database."""

import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from sqlalchemy import insert, text  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.core.security import PASSWORD_HASHER  # noqa: E402
from app.db.session import Database  # noqa: E402
from app.models import Address, Cart, CartItem, Category, Inventory, Product, Shop, User  # noqa: E402
from app.models.extensions import coupons  # noqa: E402

cfg = Settings()
assert (cfg.environment, cfg.db_name, cfg.db_host) == ("test", "marketplace_test", "127.0.0.1")
db = Database(cfg)
try:
    with db.sessions.begin() as s:
        assert s.scalar(text("SELECT current_database()")) == "marketplace_test"
        users = [
            User(
                email=f"{uuid4().hex}@example.com",
                full_name=f"Options {i}",
                password_hash=PASSWORD_HASHER.hash("Options1!"),
            )
            for i in range(3)
        ]
        s.add_all(users)
        s.flush()
        shops = [
            Shop(
                owner_user_id=u.user_id,
                shop_name=f"Options shop {i}",
                shop_slug=uuid4().hex,
                shop_status="APPROVED",
            )
            for i, u in enumerate(users[1:])
        ]
        cat = Category(category_name="Options test", category_slug=uuid4().hex)
        s.add_all([*shops, cat])
        s.flush()
        products = [
            Product(
                shop_id=shop.shop_id,
                category_id=cat.category_id,
                sku=uuid4().hex,
                product_name=f"Options product {i}",
                price=price,
            )
            for i, (shop, price) in enumerate(zip(shops, ["100000", "200000"], strict=True))
        ]
        s.add_all(products)
        s.flush()
        address = Address(
            user_id=users[0].user_id,
            recipient_name="Options Buyer",
            phone="0901234567",
            address_line="Test street",
            city="Test city",
        )
        cart = Cart(user_id=users[0].user_id)
        s.add_all([address, cart])
        s.flush()
        s.add_all([Inventory(product_id=p.product_id, quantity=10) for p in products])
        s.add_all(
            [CartItem(cart_id=cart.cart_id, product_id=p.product_id, quantity=1) for p in products]
        )
        for code, scope, kind, percent in [
            ("SHOP10", shops[0].shop_id, "GOODS", 10),
            ("SHOP20", shops[1].shop_id, "GOODS", 20),
            ("COCO10", None, "GOODS", 10),
            ("SHIP50", None, "SHIPPING", 50),
        ]:
            s.execute(
                insert(coupons).values(
                    code=code,
                    shop_id=scope,
                    coupon_type=kind,
                    discount_percent=percent,
                    usage_limit=10,
                    starts_at=datetime.now(UTC) - timedelta(days=1),
                    expires_at=datetime.now(UTC) + timedelta(days=1),
                )
            )
        result = {"email": users[0].email, "shops": [str(x.shop_id) for x in shops]}
    print(json.dumps(result))
finally:
    db.close()
