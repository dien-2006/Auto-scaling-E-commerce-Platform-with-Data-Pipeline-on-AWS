"""Write fixtures ONLY to the explicitly named isolated marketplace_test database."""

import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, text
from sqlalchemy.orm import Session

from app.api.v1.routers.catalog import read_session
from app.core.config import Settings
from app.db.base import Base
from app.db.session import Database
from app.main import create_app
from app.models import Category, Inventory, Product, ProductImage, Shop, User


@pytest.fixture(scope="module")
def isolated_database():
    if os.environ.get("MARKETPLACE_TEST_DB_NAME") != "marketplace_test":
        pytest.skip("Requires a separate marketplace_test PostgreSQL, never the existing DB")
    settings = Settings(
        environment="test",
        db_host=os.environ["MARKETPLACE_TEST_DB_HOST"],
        db_port=int(os.environ["MARKETPLACE_TEST_DB_PORT"]),
        db_name="marketplace_test",
        db_user=os.environ["MARKETPLACE_TEST_DB_USER"],
        db_password=os.environ["MARKETPLACE_TEST_DB_PASSWORD"],
    )
    database = Database(settings)
    try:
        with database.engine.begin() as connection:
            assert connection.scalar(text("SELECT current_database()")) == "marketplace_test"
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS marketplace"))
            Base.metadata.create_all(connection)  # Isolated test DB ONLY, never app startup.
        yield database
    finally:
        database.close()


@pytest.fixture
def catalog(isolated_database):
    connection = isolated_database.engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    app = create_app(Settings(environment="test"))

    def test_read_session():
        # Test fixtures share this rollback transaction. Production uses READ ONLY instead.
        yield session

    app.dependency_overrides[read_session] = test_read_session
    try:
        with TestClient(app) as client:
            yield client, session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


def add_category(session, name, parent=None, active=True):
    row = Category(
        category_name=name,
        category_slug=uuid4().hex,
        parent_category_id=parent.category_id if parent else None,
        is_active=active,
    )
    session.add(row)
    session.flush()
    return row


def test_category_tree_hides_inactive_ancestors_and_orders_deterministically(catalog):
    client, session = catalog
    root = add_category(session, "Root")
    child_b = add_category(session, "B", root)
    child_a = add_category(session, "A", root)
    grandchild = add_category(session, "Leaf", child_a)
    add_category(session, "Inactive", root, active=False)
    hidden_root = add_category(session, "Hidden", active=False)
    hidden_child = add_category(session, "Still active", hidden_root)
    add_category(session, "Also active", hidden_child)
    response = client.get("/api/v1/categories")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["category_id"] == str(root.category_id)
    children = data["items"][0]["children"]
    assert [row["category_id"] for row in children] == [
        str(child_a.category_id),
        str(child_b.category_id),
    ]
    assert children[0]["children"][0]["category_id"] == str(grandchild.category_id)
    assert "Still active" not in response.text


def test_category_empty_tree_and_one_query_for_deep_tree(catalog):
    client, session = catalog
    assert client.get("/api/v1/categories").json() == {"items": []}
    parent = None
    for index in range(15):
        parent = add_category(session, f"Level {index}", parent)
    statements = []

    def record_query(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            statements.append(statement)

    event.listen(session.connection(), "before_cursor_execute", record_query)
    try:
        assert client.get("/api/v1/categories").status_code == 200
    finally:
        event.remove(session.connection(), "before_cursor_execute", record_query)
    assert len(statements) == 1


@pytest.mark.parametrize("status", ["APPROVED", "PENDING", "REJECTED", "LOCKED"])
def test_only_approved_shop_is_public_and_never_exposes_private_fields(catalog, status):
    client, session = catalog
    owner = User(email=f"{uuid4().hex}@example.test", password_hash="test-only", full_name="Owner")
    session.add(owner)
    session.flush()
    shop = Shop(
        owner_user_id=owner.user_id,
        shop_name="Gian hàng thử",
        shop_slug=uuid4().hex,
        description="Mô tả",
        contact_email="private@example.test",
        logo_key="private/storage-key",
        shop_status=status,
    )
    session.add(shop)
    session.flush()
    response = client.get(f"/api/v1/shops/{shop.shop_slug}")
    if status == "APPROVED":
        assert response.status_code == 200
        data = response.json()["data"]
        assert set(data) == {"shop_id", "shop_name", "shop_slug", "description", "logo_url"}
        assert data["shop_id"] == str(shop.shop_id)
        assert data["description"] == "Mô tả"
        assert data["logo_url"] is None
        assert "private@" not in response.text and "storage-key" not in response.text
    else:
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "NOT_FOUND"
    assert client.get("/api/v1/shops/not-found").status_code == 404
    assert client.get("/api/v1/shops/approved' OR 1=1 --").status_code == 404
    assert client.get("/api/v1/shops/" + "x" * 161).status_code == 422


def add_shop(session, status="APPROVED"):
    owner = User(email=f"{uuid4().hex}@example.test", password_hash="test-only", full_name="Owner")
    session.add(owner)
    session.flush()
    shop = Shop(
        owner_user_id=owner.user_id,
        shop_name="Shop",
        shop_slug=uuid4().hex,
        shop_status=status,
        contact_email="private@example.test",
        logo_key="private/key",
    )
    session.add(shop)
    session.flush()
    return shop


def add_product(session, category, shop, name="Serum", price="100.00", active=True, quantity=5):
    from decimal import Decimal

    product = Product(
        shop_id=shop.shop_id,
        category_id=category.category_id,
        sku=uuid4().hex,
        product_name=name,
        price=Decimal(price),
        is_active=active,
        description="Description",
    )
    session.add(product)
    session.flush()
    if quantity is not None:
        session.add(Inventory(product_id=product.product_id, quantity=quantity))
        session.flush()
    return product


def test_product_visibility_and_category_descendants(catalog):
    client, session = catalog
    root = add_category(session, "Root")
    leaf = add_category(session, "Leaf", root)
    deep = add_category(session, "Deep", leaf)
    hidden_root = add_category(session, "Hidden", active=False)
    hidden_leaf = add_category(session, "Hidden leaf", hidden_root)
    shop = add_shop(session)
    public = [add_product(session, category, shop) for category in (root, leaf, deep)]
    hidden = [
        add_product(session, hidden_leaf, shop),
        add_product(session, root, shop, active=False),
        *[
            add_product(session, root, add_shop(session, status))
            for status in ("PENDING", "REJECTED", "LOCKED")
        ],
    ]
    # A disconnected category cycle is not public and must not cause recursive query loops.
    cycle_a = add_category(session, "Cycle A")
    cycle_b = add_category(session, "Cycle B", cycle_a)
    cycle_a.parent_category_id = cycle_b.category_id
    session.flush()
    hidden.append(add_product(session, cycle_a, shop))
    response = client.get("/api/v1/products", params={"category_id": root.category_id})
    assert response.status_code == 200
    assert response.json()["total"] == 3
    assert {item["product_id"] for item in response.json()["items"]} == {
        str(p.product_id) for p in public
    }
    assert (
        client.get("/api/v1/products", params={"category_id": leaf.category_id}).json()["total"]
        == 2
    )
    for category in (hidden_root, hidden_leaf, cycle_a):
        assert (
            client.get("/api/v1/products", params={"category_id": category.category_id}).json()[
                "items"
            ]
            == []
        )
    for product in hidden:
        assert client.get(f"/api/v1/products/{product.product_id}").status_code == 404
    assert client.get("/api/v1/products/9223372036854775807").status_code == 404


def test_search_literals_sorting_pagination_and_shop_filter(catalog):
    client, session = catalog
    category = add_category(session, "Root")
    shop = add_shop(session)
    first = add_product(session, category, shop, name="SERUM 100%_A/", price="20.01")
    second = add_product(session, category, shop, name="Serum normal", price="20.01")
    cheapest = add_product(session, category, shop, name="Other", price="10.00")
    add_product(session, category, add_shop(session), name="Other shop", price="5.00")
    for term in ("%_", "/", "serum 100"):
        response = client.get("/api/v1/products", params={"q": term}).json()
        assert [item["product_id"] for item in response["items"]] == [str(first.product_id)]
    assert client.get("/api/v1/products", params={"q": "' OR 1=1 --"}).json()["items"] == []
    assert client.get("/api/v1/products", params={"q": "serum"}).json()["total"] == 2
    params = {"shop_id": shop.shop_id, "sort": "price_asc", "page_size": 2}
    response = client.get("/api/v1/products", params=params).json()
    assert response["total"] == 3
    assert [item["product_id"] for item in response["items"]] == [
        str(cheapest.product_id),
        str(second.product_id),
    ]
    assert response["items"][1]["price"] == "20.01"
    response = client.get("/api/v1/products", params={**params, "page": 2}).json()
    assert [item["product_id"] for item in response["items"]] == [str(first.product_id)]
    assert client.get("/api/v1/products", params={**params, "page": 3}).json()["items"] == []
    response = client.get("/api/v1/products", params={**params, "sort": "price_desc"}).json()
    assert [item["product_id"] for item in response["items"]] == [
        str(second.product_id),
        str(first.product_id),
    ]
    response = client.get("/api/v1/products", params={**params, "sort": "newest"}).json()
    assert [item["product_id"] for item in response["items"]] == [
        str(cheapest.product_id),
        str(second.product_id),
    ]


def test_product_detail_stock_image_projection_and_constant_query_count(catalog):
    client, session = catalog
    category = add_category(session, "Root")
    shop = add_shop(session)
    products = [add_product(session, category, shop, quantity=value) for value in (0, None, 7)]
    product = products[-1]
    first = ProductImage(
        product_id=product.product_id, image_key="private/first", sort_order=9, is_primary=True
    )
    second = ProductImage(product_id=product.product_id, image_key="private/second", sort_order=0)
    session.add_all([first, second])
    session.flush()
    statements = []

    def record(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(session.connection(), "before_cursor_execute", record)
    try:
        response = client.get("/api/v1/products?page_size=100")
        assert response.status_code == 200
        assert len(statements) == 2  # Total + one projected page, regardless of page size.
        statements.clear()
        response = client.get(f"/api/v1/products/{product.product_id}")
        assert response.status_code == 200
        assert len(statements) == 2  # Detail + all image metadata, no per-image queries.
    finally:
        event.remove(session.connection(), "before_cursor_execute", record)
    data = response.json()["data"]
    assert data["available_quantity"] == 7 and data["in_stock"]
    assert data["images"] == [
        {
            "product_image_id": str(first.product_image_id),
            "url": None,
            "is_primary": True,
            "sort_order": 9,
        },
        {
            "product_image_id": str(second.product_image_id),
            "url": None,
            "is_primary": False,
            "sort_order": 0,
        },
    ]
    assert "private/" not in response.text and "private@example" not in response.text
    assert "owner_user_id" not in response.text and "password_hash" not in response.text
    for row in products[:2]:
        data = client.get(f"/api/v1/products/{row.product_id}").json()["data"]
        assert data["available_quantity"] == 0 and not data["in_stock"]


def test_bestseller_completed_sales_visibility_and_fallback(catalog):
    from decimal import Decimal

    from app.models import Order, OrderItem, ShopOrder

    client, session = catalog
    category = add_category(session, "Bestseller")
    shop = add_shop(session)
    first = add_product(session, category, shop, name="First")
    second = add_product(session, category, shop, name="Second")
    hidden = add_product(session, category, shop, active=False)
    initial = client.get("/api/v1/products/bestsellers").json()
    assert initial["ranked"] is False
    assert str(hidden.product_id) not in {p["product_id"] for p in initial["items"]}

    def sale(product, quantity, status):
        order = Order(
            buyer_user_id=shop.owner_user_id,
            idempotency_key=uuid4(),
            recipient_name="Test",
            phone="0900000000",
            shipping_address="Test",
            total_amount=Decimal("0"),
            payment_method="COD",
        )
        session.add(order)
        session.flush()
        child = ShopOrder(
            order_id=order.order_id,
            shop_id=shop.shop_id,
            order_status=status,
            subtotal=Decimal("0"),
        )
        session.add(child)
        session.flush()
        session.add(
            OrderItem(
                shop_order_id=child.shop_order_id,
                shop_id=shop.shop_id,
                product_id=product.product_id,
                product_name=product.product_name,
                unit_price=product.price,
                quantity=quantity,
            )
        )
        session.flush()

    sale(first, 3, "COMPLETED")
    sale(second, 5, "COMPLETED")
    sale(first, 100, "PENDING")
    sale(first, 100, "CANCELLED")
    sale(hidden, 200, "COMPLETED")
    response = client.get("/api/v1/products/bestsellers")
    assert response.status_code == 200
    result = response.json()
    assert result["ranked"] is True
    assert [p["product_id"] for p in result["items"]] == [
        str(second.product_id),
        str(first.product_id),
    ]
    assert "buyer_user_id" not in response.text
