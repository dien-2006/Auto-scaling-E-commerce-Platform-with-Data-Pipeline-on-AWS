import pytest
from pydantic import ValidationError

from app.schemas.addresses import AddressCreate, AddressPatch

VALID = {
    "recipient_name": " Mai ",
    "phone": "0901234567",
    "address_line": " 12 Nguyễn Huệ ",
    "city": " Hà Nội ",
}


def test_trim_and_partial_update():
    row = AddressCreate(**VALID)
    assert row.recipient_name == "Mai" and row.city == "Hà Nội"
    assert AddressPatch(ward=None).model_dump(exclude_unset=True) == {"ward": None}
    assert AddressPatch(is_default=False).model_dump(exclude_unset=True) == {"is_default": False}


@pytest.mark.parametrize(
    "values",
    [
        {"recipient_name": "  "},
        {"city": " "},
        {"phone": "abc"},
        {"address_line": " "},
        {"is_default": "true"},
        {"user_id": "12"},
        {"address_line": "a" * 2001},
        {"ward": " "},
    ],
)
def test_invalid_create(values):
    with pytest.raises(ValidationError):
        AddressCreate(**(VALID | values))


@pytest.mark.parametrize(
    "values",
    [
        {},
        {"city": None},
        {"phone": None},
        {"is_default": None},
        {"recipient_name": None},
        {"address_line": None},
        {"user_id": 2},
    ],
)
def test_invalid_patch(values):
    with pytest.raises(ValidationError):
        AddressPatch(**values)
