import pytest
from pydantic import ValidationError

from app.schemas.seller_products import ProductCreate, ProductPatch, SellerQuery


def body(**changes):
    return {
        "sku": " SKU ",
        "category_id": "9007199254740993",
        "product_name": " Serum ",
        "price": "999999999999.99",
        "initial_quantity": 0,
        **changes,
    }


def test_exact_decimal_bigint_and_trim():
    item = ProductCreate(**body())
    assert str(item.price) == "999999999999.99"
    assert item.category_id == 9007199254740993 and item.sku == "SKU"
    assert item.product_name == "Serum"
    assert ProductPatch(description=None).model_dump(exclude_unset=True) == {"description": None}


def test_catalog_name_matches_sql_500_character_limit():
    name = "Đ" * 500
    assert ProductCreate(**body(product_name=name)).product_name == name
    assert ProductPatch(product_name=name).product_name == name
    with pytest.raises(ValidationError):
        ProductCreate(**body(product_name=name + "x"))
    with pytest.raises(ValidationError):
        ProductPatch(product_name=name + "x")


@pytest.mark.parametrize(
    "changes",
    [
        {"sku": " "},
        {"product_name": " "},
        {"sku": "x" * 65},
        {"price": "-1"},
        {"price": "NaN"},
        {"price": "Infinity"},
        {"price": "1000000000000"},
        {"price": "0.001"},
        {"price": 1.25},
        {"initial_quantity": True},
        {"initial_quantity": 1.5},
        {"initial_quantity": -1},
        {"initial_quantity": 2147483648},
        {"shop_id": "1"},
        {"is_active": False},
        {"category_id": "9223372036854775808"},
        {"description": "x" * 5001},
    ],
)
def test_invalid_create(changes):
    with pytest.raises(ValidationError):
        ProductCreate(**body(**changes))


@pytest.mark.parametrize(
    "changes",
    [
        {},
        {"sku": None},
        {"category_id": None},
        {"product_name": None},
        {"price": None},
        {"is_active": True},
        {"shop_id": "1"},
        {"initial_quantity": 5},
        {"quantity": 5},
    ],
)
def test_patch_does_not_overwrite_stock_or_reactivate(changes):
    with pytest.raises(ValidationError):
        ProductPatch(**changes)


def test_query_bounds_and_allowlist():
    assert SellerQuery(is_active=False).is_active is False
    for values in [{"page": 0}, {"page_size": 101}, {"q": "x" * 201}, {"shop_id": 1}]:
        with pytest.raises(ValidationError):
            SellerQuery(**values)
