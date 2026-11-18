import pytest
from pydantic import ValidationError

from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.checkout import CheckoutRequest


@pytest.mark.parametrize(
    "password", ["Abcd1!xy", "abcdef1!x", "Abcdefg!x", "Abcdef12x", "Abcdef12 ", "A1!" + "x" * 126]
)
def test_registration_rejects_weak_passwords(password):
    with pytest.raises(ValidationError):
        RegisterRequest(email="a@example.com", full_name="A", password=password)


@pytest.mark.parametrize("password", ["Abcde1!xy", "ABCDEF1!G", "  Abcd1!xy  ", "Abcde12🙂x"])
def test_registration_policy_and_password_preservation(password):
    assert (
        RegisterRequest(
            email="a@example.com", full_name="A", password=password
        ).password.get_secret_value()
        == password
    )


def test_login_does_not_reapply_new_registration_policy():
    assert (
        LoginRequest(email="a@example.com", password="legacy-password").password.get_secret_value()
        == "legacy-password"
    )


def valid():
    return {
        "address_id": "1",
        "payment_method": "COD",
        "items": [{"product_id": "2", "quantity": 1, "expected_unit_price": "12.34"}],
    }


@pytest.mark.parametrize(
    "change",
    [{"payment_method": "CARD"}, {"address_id": True}, {"items": []}, {"buyer_user_id": "1"}],
)
def test_checkout_validation(change):
    with pytest.raises(ValidationError):
        CheckoutRequest(**(valid() | change))


@pytest.mark.parametrize("price", [12.34, 12, "NaN", "1e2", "-1", "1.001", "1000000000000.00"])
def test_exact_decimal_string_price(price):
    data = valid()
    data["items"][0]["expected_unit_price"] = price
    with pytest.raises(ValidationError):
        CheckoutRequest(**data)


def test_duplicate_products_rejected_and_exact_bigints():
    data = valid()
    data["items"].append(dict(data["items"][0]))
    with pytest.raises(ValidationError):
        CheckoutRequest(**data)
    data = valid()
    data["address_id"] = "9007199254740993"
    assert CheckoutRequest(**data).address_id == 9007199254740993
