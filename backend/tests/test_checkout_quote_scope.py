from decimal import Decimal
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.errors import APIError
from app.schemas.checkout_options import OptionsQuoteRequest
from app.services import shopping
from app.services.checkout_options import CheckoutOptionsService


class QuoteRepository:
    def __init__(self, rows=(), direct=None):
        self.rows = rows
        self.cart_reads = 0
        self.session = SimpleNamespace(
            execute=lambda statement: SimpleNamespace(
                mappings=lambda: SimpleNamespace(one_or_none=lambda: direct)
            )
        )

    def cart(self, buyer_id):
        self.cart_reads += 1
        return self.rows


def cart_row(product_id, shop_id, price):
    return {
        "product_id": product_id,
        "shop_id": shop_id,
        "price": Decimal(price),
        "quantity": 1,
        "is_active": True,
        "visible": True,
        "shop_status": "APPROVED",
        "owner_user_id": 99,
    }


def service():
    return CheckoutOptionsService(
        Settings(
            environment="test",
            checkout_options_enabled=True,
            shipping_standard_fee=Decimal("10.00"),
        )
    )


def test_selected_cart_quote_excludes_other_products_and_their_shipping():
    repository = QuoteRepository([cart_row(1, 10, "100"), cart_row(2, 20, "400")])
    payload = OptionsQuoteRequest(shipping_method="STANDARD", selected_product_ids=["1"])
    quote = service().quote(payload, repository, buyer_id=7)
    assert quote.subtotal == Decimal("100.00")
    assert quote.total_amount == Decimal("110.00")
    assert [(row.shop_id, row.fee) for row in quote.shipping] == [("10", Decimal("10.00"))]


def test_full_cart_quote_remains_backward_compatible():
    repository = QuoteRepository([cart_row(1, 10, "100"), cart_row(2, 20, "400")])
    quote = service().quote(OptionsQuoteRequest(shipping_method="STANDARD"), repository, 7)
    assert quote.subtotal == Decimal("500.00")
    assert quote.total_amount == Decimal("520.00")


def test_buy_now_quote_does_not_require_a_cart(monkeypatch):
    monkeypatch.setattr(
        shopping,
        "ProductRepository",
        lambda session: SimpleNamespace(
            public_statement=lambda query: SimpleNamespace(where=lambda *conditions: None)
        ),
    )
    repository = QuoteRepository(
        direct={"shop_id": 30, "price": Decimal("75.00"), "available_quantity": 3}
    )
    payload = OptionsQuoteRequest(
        shipping_method="STANDARD",
        direct_item={"product_id": "3", "quantity": 2, "expected_unit_price": "75.00"},
    )
    quote = service().quote(payload, repository, 7)
    assert repository.cart_reads == 0
    assert quote.subtotal == Decimal("150.00")
    assert quote.total_amount == Decimal("160.00")
    assert [row.shop_id for row in quote.shipping] == ["30"]


def test_selected_product_must_still_belong_to_the_cart():
    payload = OptionsQuoteRequest(shipping_method="STANDARD", selected_product_ids=["999"])
    with pytest.raises(APIError):
        service().quote(payload, QuoteRepository([cart_row(1, 10, "100")]), 7)


@pytest.mark.parametrize(
    "scope",
    [
        {"selected_product_ids": []},
        {"selected_product_ids": ["1", "1"]},
        {"selected_product_ids": ["9223372036854775808"]},
        {
            "selected_product_ids": ["1"],
            "direct_item": {
                "product_id": "1",
                "quantity": 1,
                "expected_unit_price": "100.00",
            },
        },
    ],
)
def test_quote_rejects_invalid_or_ambiguous_purchase_scope(scope):
    with pytest.raises(ValidationError):
        OptionsQuoteRequest(shipping_method="STANDARD", **scope)
