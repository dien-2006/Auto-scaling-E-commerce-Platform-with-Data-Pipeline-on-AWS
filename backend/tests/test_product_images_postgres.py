from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import event, func, select
from sqlalchemy.exc import SQLAlchemyError
from test_checkout_postgres import checkout_db as checkout_db  # noqa: F401
from test_checkout_postgres import client_for, csrf  # noqa: F401
from test_checkout_postgres import world as world
from test_seller_products_postgres import seller_world as seller_world  # noqa: F401
from test_storage_images import MemoryS3, configured, stage

from app.db.session import get_session
from app.models import ProductImage, Shop
from app.services.storage import ObjectStorage, get_storage


@pytest.fixture
def image_world(seller_world):
    cfg, db, r, owners, category = seller_world
    memory = MemoryS3()
    storage = ObjectStorage(configured(), memory)
    return cfg, db, r, owners, storage, memory


def attached(c, storage, memory, shop, product, primary=False):
    key = stage(storage, memory, shop, product)
    return c.post(
        f"/api/v1/seller/products/{product}/images",
        json={"image_key": key, "is_primary": primary},
        headers=csrf(c),
    )


def test_link_delivery_primary_order_delete_reference_only(image_world):
    cfg, db, r, owners, storage, memory = image_world
    pid, shop = r["products"][0], r["shops"][0]
    with client_for(cfg, owners[0]) as c:
        c.app.dependency_overrides[get_storage] = lambda: storage
        one = attached(c, storage, memory, shop, pid, True)
        assert one.status_code == 201, one.text
        first = one.json()["data"]
        assert first["image_key"].startswith(f"product-images/{shop}/{pid}/")
        two = attached(c, storage, memory, shop, pid, True).json()["data"]
        images = c.get(f"/api/v1/seller/products/{pid}").json()["data"]["images"]
        assert sum(x["is_primary"] for x in images) == 1
        assert images[0]["product_image_id"] == two["product_image_id"]
        public = c.get(f"/api/v1/products/{pid}")
        assert (
            public.status_code == 200 and public.json()["data"]["primary_image_url"] == two["url"]
        )
        assert "image_key" not in public.text and "x-amz-meta" not in public.text
        assert c.get("/api/v1/products").json()["items"]
        changed = c.patch(
            f"/api/v1/seller/products/{pid}/images/{first['product_image_id']}",
            json={"is_primary": True, "sort_order": 7},
            headers=csrf(c),
        )
        assert changed.status_code == 200 and changed.json()["data"]["is_primary"]
        assert (
            c.delete(
                f"/api/v1/seller/products/{pid}/images/{first['product_image_id']}", headers=csrf(c)
            ).status_code
            == 204
        )
        assert first["image_key"] in memory.objects
        assert (
            c.get(f"/api/v1/products/{pid}").json()["data"]["images"][0]["product_image_id"]
            == two["product_image_id"]
        )


def test_cross_shop_product_keys_ids_and_csrf(image_world):
    cfg, db, r, owners, storage, memory = image_world
    pid, shop = r["products"][0], r["shops"][0]
    with client_for(cfg, owners[0]) as c:
        c.app.dependency_overrides[get_storage] = lambda: storage
        first = attached(c, storage, memory, shop, pid).json()["data"]
        key = stage(storage, memory, r["shops"][1], r["products"][1])
        assert (
            c.post(
                f"/api/v1/seller/products/{pid}/images", json={"image_key": key}, headers=csrf(c)
            ).status_code
            == 422
        )
        assert (
            c.post(
                f"/api/v1/seller/products/{pid}/images/upload-url",
                json={"content_type": "image/png", "size_bytes": 10},
            ).status_code
            == 403
        )
    with client_for(cfg, owners[1]) as other:
        other.app.dependency_overrides[get_storage] = lambda: storage
        assert (
            other.post(
                f"/api/v1/seller/products/{pid}/images/upload-url",
                json={"content_type": "image/png", "size_bytes": 10},
                headers=csrf(other),
            ).status_code
            == 404
        )
        own_pid = r["products"][1]
        for method in ["PATCH", "DELETE"]:
            result = other.request(
                method,
                f"/api/v1/seller/products/{own_pid}/images/{first['product_image_id']}",
                json={"is_primary": True} if method == "PATCH" else None,
                headers=csrf(other),
            )
            assert result.status_code == 404
        other.cookies.clear()
        assert (
            other.post(
                f"/api/v1/seller/products/{pid}/images/upload-url",
                json={"content_type": "image/png", "size_bytes": 10},
            ).status_code
            == 401
        )


@pytest.mark.parametrize("status", ["PENDING", "REJECTED", "LOCKED"])
def test_unapproved_shop_image_write_denied(image_world, status):
    cfg, db, r, owners, storage, memory = image_world
    with db.sessions.begin() as s:
        s.get(Shop, r["shops"][0]).shop_status = status
    with client_for(cfg, owners[0]) as c:
        c.app.dependency_overrides[get_storage] = lambda: storage
        assert attached(c, storage, memory, r["shops"][0], r["products"][0]).status_code == 403


def test_missing_storage_and_sdk_failure_are_sanitized(image_world):
    cfg, db, r, owners, storage, memory = image_world
    with client_for(cfg, owners[0]) as c:
        url = f"/api/v1/seller/products/{r['products'][0]}/images/upload-url"
        result = c.post(url, json={"content_type": "image/png", "size_bytes": 10}, headers=csrf(c))
        assert (
            result.status_code == 503 and result.json()["error"]["code"] == "STORAGE_NOT_CONFIGURED"
        )
        assert not c.get("/api/v1/seller/products").json()["image_upload_enabled"]
        from botocore.exceptions import ClientError

        def broken(**kwargs):
            raise ClientError(
                {"Error": {"Code": "AccessDenied", "Message": "private credential"}}, "Post"
            )

        memory.generate_presigned_post = broken
        c.app.dependency_overrides[get_storage] = lambda: storage
        result = c.post(url, json={"content_type": "image/png", "size_bytes": 10}, headers=csrf(c))
        assert result.status_code == 503 and "private credential" not in result.text


def test_two_primary_requests_atomic_and_rollback(image_world):
    cfg, db, r, owners, storage, memory = image_world
    pid, shop = r["products"][0], r["shops"][0]
    with client_for(cfg, owners[0]) as c:
        c.app.dependency_overrides[get_storage] = lambda: storage
        images = [attached(c, storage, memory, shop, pid, True).json()["data"] for _ in range(2)]
    barrier = Barrier(2)

    def worker(image):
        with client_for(cfg, owners[0]) as c:
            c.app.dependency_overrides[get_storage] = lambda: storage
            headers = csrf(c)
            barrier.wait(timeout=10)
            return c.patch(
                f"/api/v1/seller/products/{pid}/images/{image['product_image_id']}",
                json={"is_primary": True},
                headers=headers,
            )

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert all(x.status_code == 200 for x in pool.map(worker, images))
    with db.sessions() as s:
        before = s.scalar(
            select(ProductImage.product_image_id).where(
                ProductImage.product_id == pid, ProductImage.is_primary.is_(True)
            )
        )
    with client_for(cfg, owners[0]) as c:
        c.app.dependency_overrides[get_storage] = lambda: storage

        def fail(session):
            raise SQLAlchemyError("private DSN")

        def broken():
            with db.sessions() as session:
                event.listen(session, "before_commit", fail)
                yield session

        c.app.dependency_overrides[get_session] = broken
        result = attached(c, storage, memory, shop, pid, True)
        assert result.status_code == 503 and "private DSN" not in result.text
    with db.sessions() as s:
        assert (
            s.scalar(
                select(func.count()).select_from(ProductImage).where(ProductImage.product_id == pid)
            )
            == 2
        )
        assert (
            s.scalar(
                select(ProductImage.product_image_id).where(
                    ProductImage.product_id == pid, ProductImage.is_primary.is_(True)
                )
            )
            == before
        )
