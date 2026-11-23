"""Bounded measurements and concurrent HTTP writes on two real worker processes."""

import json
import math
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from uuid import uuid4

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "backend"))
from sqlalchemy import func, select, text  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.core.security import Security  # noqa: E402
from app.db.session import Database  # noqa: E402
from app.models import Address, Cart, CartItem, Category, Inventory, Order, Product, Shop, User  # noqa: E402
from app.repositories.products import ProductRepository  # noqa: E402
from app.schemas.products import ProductQuery  # noqa: E402

cfg = Settings()
assert (cfg.environment, cfg.db_name, cfg.db_host) == ("test", "marketplace_test", "127.0.0.1")
urls = json.loads(os.environ["PERF_REPLICAS"])
assert len(set(urls)) == 2 and all(url.startswith("http://127.0.0.1:") for url in urls)
db = Database(cfg)


def request(url, path, data=None, headers=None):
    req = urllib.request.Request(
        url + path,
        data=json.dumps(data).encode() if data is not None else None,
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    try:
        response = urllib.request.urlopen(req, timeout=20)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        body = json.loads(response.read())
        return response.status, body, response.headers


try:
    with db.sessions.begin() as session:
        assert session.scalar(text("SELECT current_database()")) == "marketplace_test"
        users = [
            User(
                email=f"perf-{uuid4().hex}@example.com", password_hash="test-only", full_name="Perf"
            )
            for _ in range(3)
        ]
        session.add_all(users)
        session.flush()
        category = Category(category_name="Perf", category_slug="perf")
        shop = Shop(
            owner_user_id=users[0].user_id,
            shop_name="Perf",
            shop_slug="perf",
            shop_status="APPROVED",
        )
        session.add_all([category, shop])
        session.flush()
        products = [
            Product(
                shop_id=shop.shop_id,
                category_id=category.category_id,
                sku=f"PERF-{i}",
                product_name=f"Perf product {i:05}",
                price="100",
            )
            for i in range(2000)
        ]
        session.add_all(products)
        session.flush()
        session.add_all(
            [
                Inventory(product_id=p.product_id, quantity=1 if i == 1 else 10)
                for i, p in enumerate(products)
            ]
        )
        buyer_ids = [u.user_id for u in users[1:]]
        addresses = [
            Address(
                user_id=uid,
                recipient_name="Perf",
                phone="0901234567",
                address_line="Test only",
                city="Test",
            )
            for uid in buyer_ids
        ]
        carts = [Cart(user_id=uid) for uid in buyer_ids]
        session.add_all([*addresses, *carts])
        session.flush()
        session.add(
            CartItem(cart_id=carts[0].cart_id, product_id=products[0].product_id, quantity=1)
        )
        cart_ids = [c.cart_id for c in carts]
        pids = [p.product_id for p in products[:2]]
        aids = [a.address_id for a in addresses]

    # Warm both pools, then bounded read load. No performance assertion based on hardware.
    for url in urls:
        assert request(url, "/api/v1/products?page_size=24")[0] == 200

    def read(index):
        started = time.perf_counter()
        status, body, _ = request(
            urls[index % 2], f"/api/v1/products?page_size=24&page={index % 4 + 1}"
        )
        assert status == 200 and len(body["items"]) == 24 and body["total"] == 2000
        return (time.perf_counter() - started) * 1000

    start = time.perf_counter()
    with ThreadPoolExecutor(8) as pool:
        latencies = sorted(pool.map(read, range(120)))
    elapsed = time.perf_counter() - start
    measurements = {
        "dataset_products": 2000,
        "workers": 2,
        "concurrency": 8,
        "requests": 120,
        "errors": 0,
        "elapsed_seconds": round(elapsed, 3),
        "requests_per_second": round(120 / elapsed, 2),
        "p50_ms": round(latencies[math.ceil(0.50 * len(latencies)) - 1], 2),
        "p95_ms": round(latencies[math.ceil(0.95 * len(latencies)) - 1], 2),
        "max_ms": round(max(latencies), 2),
    }
    # Real repository SQL, bounded EXPLAIN ANALYZE on isolated test data only.
    with db.sessions() as session:
        session.execute(text("ANALYZE marketplace.products"))
        statement = ProductRepository(session).public_statement(ProductQuery())
        plans = {}
        for page in [1, 80]:
            query = (
                statement.order_by(Product.created_at.desc(), Product.product_id.desc())
                .offset((page - 1) * 24)
                .limit(24)
            )
            sql = str(query.compile(db.engine, compile_kwargs={"literal_binds": True}))
            result = session.scalar(text("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + sql))
            plans[str(page)] = result[0]
        measurements["query_plans"] = plans

    security = Security(cfg)

    def auth(index, url):
        access = f"{security.access_cookie}={security.issue_access(buyer_ids[index])}"
        status, body, headers = request(url, "/api/v1/auth/csrf", headers={"Cookie": access})
        assert status == 200
        cookie = headers.get("Set-Cookie").split(";", 1)[0]
        return {
            "Cookie": access + "; " + cookie,
            "Origin": str(cfg.public_origin).rstrip("/"),
            "X-CSRF-Token": body["data"]["csrf_token"],
        }

    key = str(uuid4())
    barrier = Barrier(4)

    def buy(index, product_index=0, buyer_index=0, shared_key=key, sync=barrier):
        url = urls[index % 2]
        headers = auth(buyer_index, url) | {"Idempotency-Key": shared_key}
        sync.wait(timeout=15)
        status, body, _ = request(
            url,
            "/api/v1/orders/checkout",
            {
                "address_id": str(aids[buyer_index]),
                "payment_method": "COD",
                "items": [
                    {
                        "product_id": str(pids[product_index]),
                        "quantity": 1,
                        "expected_unit_price": "100",
                    }
                ],
            },
            headers,
        )
        return status, body

    with ThreadPoolExecutor(4) as pool:
        results = list(pool.map(buy, range(4)))
    assert sorted(status for status, _ in results) == [200, 200, 200, 201], results
    assert len({body["data"]["order_id"] for _, body in results}) == 1
    with db.sessions.begin() as session:
        session.add_all([CartItem(cart_id=cid, product_id=pids[1], quantity=1) for cid in cart_ids])
    last_unit = Barrier(2)

    def compete(index):
        return buy(index, 1, index, str(uuid4()), last_unit)

    with ThreadPoolExecutor(2) as pool:
        competed = list(pool.map(compete, range(2)))
    assert sorted(status for status, _ in competed) == [201, 409]
    with db.sessions() as session:
        assert session.get(Inventory, pids[0]).quantity == 9
        assert session.get(Inventory, pids[1]).quantity == 0
        assert session.scalar(select(func.count()).select_from(Order)) == 2
    measurements["same_key_http_statuses"] = sorted(s for s, _ in results)
    measurements["last_unit_http_statuses"] = sorted(s for s, _ in competed)
    destination = os.environ.get("PERF_REPORT")
    if destination:
        Path(destination).write_text(json.dumps(measurements, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in measurements.items() if k != "query_plans"}))
    print("PASS two real backend processes: shared-key single order, no overselling, exact stock")
finally:
    db.close()
