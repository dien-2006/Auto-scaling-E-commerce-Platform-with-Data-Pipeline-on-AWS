from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.core.config import Settings
from app.db.session import get_session
from app.main import create_app
from app.services.catalog import CatalogService


def category(category_id, parent=None, name="Category"):
    return {
        "category_id": category_id,
        "parent_category_id": parent,
        "category_name": name,
        "category_slug": f"category-{category_id}",
        "is_active": True,
    }


def test_tree_excludes_orphans_and_cycles_without_promoting_children():
    repository = MagicMock()
    repository.active_categories.return_value = [
        category(1),
        category(2, 1),
        category(3, 99),
        category(4, 3),
        category(5, 6),
        category(6, 5),
        category(7, 7),
    ]
    response = CatalogService(repository).categories().model_dump()
    assert [row["category_id"] for row in response["items"]] == ["1"]
    assert [row["category_id"] for row in response["items"][0]["children"]] == ["2"]
    repository.active_categories.assert_called_once()


def test_empty_tree_and_bigint_ids_are_exact():
    repository = MagicMock()
    repository.active_categories.return_value = []
    assert CatalogService(repository).categories().model_dump() == {"items": []}
    large = 9007199254740993
    repository.active_categories.return_value = [category(large), category(large + 1, large)]
    root = CatalogService(repository).categories().items[0]
    assert root.category_id == str(large)
    assert root.children[0].parent_category_id == str(large)
    repository.public_shop.return_value = {
        "shop_id": large,
        "shop_name": "Shop",
        "shop_slug": "shop",
        "description": None,
    }
    assert CatalogService(repository).shop("shop").data.shop_id == str(large)


def test_public_catalog_without_database_returns_503_and_openapi_has_routes():
    with TestClient(create_app(Settings(environment="test"))) as client:
        for path in ("/api/v1/categories", "/api/v1/shops/example"):
            response = client.get(path)
            assert response.status_code == 503
            assert response.json()["error"]["code"] == "DEPENDENCY_UNAVAILABLE"
            assert response.headers["Cache-Control"] == "no-store"
        paths = client.get("/openapi.json").json()["paths"]
        assert "/api/v1/categories" in paths
        assert "/api/v1/shops/{shop_slug}" in paths


def test_public_shop_resolves_logo_without_exposing_the_storage_key():
    repository = MagicMock()
    repository.public_shop.return_value = {
        "shop_id": 1, "shop_name": "Shop", "shop_slug": "shop",
        "description": None, "logo_key": "logo/1.png",
    }
    storage = MagicMock()
    storage.logo_url.return_value = "https://images.example/logo/1.png?signed=test"
    response = CatalogService(repository, storage).shop("shop").model_dump()
    storage.logo_url.assert_called_once_with("logo/1.png")
    assert response["data"]["logo_url"] == storage.logo_url.return_value
    assert "logo_key" not in response["data"]


def test_unreachable_database_is_503_and_does_not_expose_driver_error():
    app = create_app(Settings(environment="test"))
    session = MagicMock()
    session.execute.side_effect = OperationalError(
        "private-query", {}, Exception("private-db-secret")
    )

    def failed_session():
        yield session

    app.dependency_overrides[get_session] = failed_session
    with TestClient(app) as client:
        response = client.get("/api/v1/categories")
        assert response.status_code == 503
        assert "private-db-secret" not in response.text
        assert "private-query" not in response.text
