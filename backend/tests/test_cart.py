import pytest
from pydantic import ValidationError

from app.schemas.cart import CartAdd, CartQuantity


@pytest.mark.parametrize("quantity", [0, -1, True, 1.5, 1.0, "1", 2147483648, None])
def test_quantity_requires_positive_int32(quantity):
    with pytest.raises(ValidationError):
        CartQuantity(quantity=quantity)


@pytest.mark.parametrize("product_id", [True, 1.0, 0, -1, "1.5", 9223372036854775808])
def test_product_id_exact_bigint(product_id):
    with pytest.raises(ValidationError):
        CartAdd(product_id=product_id, quantity=1)


def test_bigint_string_and_extra_fields():
    assert CartAdd(product_id="9007199254740993", quantity=1).product_id == 9007199254740993
    with pytest.raises(ValidationError):
        CartAdd(product_id="1", quantity=1, user_id=2)
    with pytest.raises(ValidationError):
        CartQuantity(quantity=1, unit_price="1.00")
