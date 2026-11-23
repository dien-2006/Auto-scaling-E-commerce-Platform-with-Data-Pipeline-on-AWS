from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import OperationalError

from app.api.v1.routers.products import get_product_service
from app.core.config import Settings
from app.db.session import get_session
from app.main import create_app
from app.repositories.products import ProductRepository
from app.schemas.products import ProductQuery
from app.services.products import ProductService


@pytest.mark.parametrize(
    "query",
    [
        "page=0",
        "page_size=101",
        "page=-1",
        "page_size=0",
        "category_id=0",
        "shop_id=-1",
        "sort=price;DROP TABLE",
        "q=" + "a" * 201,
        "page=2147483648",
        "shop_id=9223372036854775808",
        "unknown=1",
    ],
)
def test_invalid_product_query_is_422(query):
    app = create_app(Settings(environment="test"))
    service = MagicMock()
    app.dependency_overrides[get_product_service] = lambda: service
    with TestClient(app) as client:
        response = client.get(f"/api/v1/products?{query}")
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"
        service.list.assert_not_called()


@pytest.mark.parametrize("product_id", ["0", "-1", "abc", "9223372036854775808"])
def test_invalid_product_id_is_422(product_id):
    app = create_app(Settings(environment="test"))
    service = MagicMock()
    app.dependency_overrides[get_product_service] = lambda: service
    with TestClient(app) as client:
        assert client.get(f"/api/v1/products/{product_id}").status_code == 422
        service.detail.assert_not_called()


def test_product_db_failures_are_sanitized_503():
    app = create_app(Settings(environment="test"))
    session = MagicMock()
    session.execute.side_effect = OperationalError("private-query", {}, Exception("db-secret"))

    def failed_session():
        yield session

    app.dependency_overrides[get_session] = failed_session
    with TestClient(app) as client:
        for path in ("/api/v1/products", "/api/v1/products/1"):
            response = client.get(path)
            assert response.status_code == 503
            assert response.headers["Cache-Control"] == "no-store"
            assert "db-secret" not in response.text and "private-query" not in response.text
        paths = client.get("/openapi.json").json()["paths"]
        assert "/api/v1/products/{product_id}" in paths


def test_search_is_bound_and_literal_wildcards_are_escaped():
    query = ProductQuery(q="%_/' OR 1=1 --")
    statement = ProductRepository(MagicMock()).public_statement(query)
    compiled = statement.compile(dialect=postgresql.dialect())
    assert query.q not in str(compiled)
    assert any("/%/_//" in str(value) for value in compiled.params.values())
    assert "password_hash" not in str(compiled)
    assert "contact_email" not in str(compiled)


def test_money_and_bigint_serialization_do_not_lose_precision():
    repository = MagicMock()
    row = {
        "product_id": 9007199254740993,
        "product_name": "Product",
        "price": Decimal("999999999999.99"),
        "category_id": 9007199254740994,
        "shop_id": 9007199254740995,
        "shop_name": "Shop",
        "shop_slug": "shop",
        "available_quantity": 0,
        "description": None,
        "sku": "sku",
    }
    repository.detail.return_value = row
    repository.images.return_value = []
    data = ProductService(repository).detail(row["product_id"]).model_dump(mode="json")["data"]
    assert data["product_id"] == "9007199254740993"
    assert data["shop"]["shop_id"] == "9007199254740995"
    assert data["price"] == "999999999999.99"
    assert data["available_quantity"] == 0 and not data["in_stock"]
    assert data["primary_image_url"] is None
