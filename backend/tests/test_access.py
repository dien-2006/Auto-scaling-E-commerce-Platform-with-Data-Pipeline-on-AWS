from types import SimpleNamespace

import pytest

from app.core.errors import APIError
from app.services.access import AccessPolicy


def policy(role="USER", status="ACTIVE", shop_status="APPROVED", has_shop=True):
    row = dict(
        user_id=17,
        user_role=role,
        user_status=status,
        email="u@example.com",
        full_name="User",
        phone=None,
    )
    repository = SimpleNamespace(
        principal=lambda _: row,
        shop=lambda _: {"shop_id": 23, "shop_status": shop_status} if has_shop else None,
        address=lambda resource, user: 31 if resource == 31 and user == 17 else None,
        cart=lambda resource, user: 32 if resource == 32 and user == 17 else None,
        order=lambda resource, user: 33 if resource == 33 and user == 17 else None,
        buyer_shop_order=lambda resource, user: 34 if resource == 34 and user == 17 else None,
        product=lambda resource, shop: 35 if resource == 35 and shop == 23 else None,
        seller_shop_order=lambda resource, shop: 34 if resource == 34 and shop == 23 else None,
    )
    return AccessPolicy(repository, 17)


@pytest.mark.parametrize("role", ["USER", "ADMIN"])
def test_buyers_and_owners_never_gain_cross_resource_access(role):
    access = policy(role)
    if role == "ADMIN":
        with pytest.raises(APIError) as error:
            access.buyer()
        assert error.value.code == "COMMERCE_FORBIDDEN"
    else:
        assert access.buyer().user_id == 17
    assert access.shop(23).shop_id == "23"
    for method, own in [
        (access.address, 31),
        (access.cart, 32),
        (access.order, 33),
        (access.buyer_shop_order, 34),
        (access.seller_product, 35),
        (access.seller_shop_order, 34),
        (access.shop, 23),
    ]:
        method(own)
        for other in [999, 0]:
            with pytest.raises(APIError) as exc:
                method(other)
            assert exc.value.status_code == 404


@pytest.mark.parametrize("status", ["PENDING", "REJECTED", "LOCKED"])
def test_nonapproved_shop_cannot_sell(status):
    access = policy(shop_status=status)
    assert access.owned_shop().shop_status == status
    for operation in [access.selling_shop, lambda: access.seller_product(35)]:
        with pytest.raises(APIError) as exc:
            operation()
        assert exc.value.code == "SHOP_NOT_APPROVED"
    # Wrong owner is still a generic404 even when the current shop is locked.
    with pytest.raises(APIError) as exc:
        access.seller_product(999)
    assert exc.value.status_code == 404
    if status == "LOCKED":
        assert access.seller_shop_order(34) == 34
    else:
        with pytest.raises(APIError) as exc:
            access.seller_shop_order(34)
        assert exc.value.status_code == 403


def test_admin_active_and_no_shop_policy():
    assert policy("ADMIN").admin().user_role == "ADMIN"
    with pytest.raises(APIError) as exc:
        policy().admin()
    assert exc.value.status_code == 403
    for role in ["USER", "ADMIN"]:
        with pytest.raises(APIError) as exc:
            policy(role, status="LOCKED")
        assert exc.value.code == "USER_LOCKED"
        with pytest.raises(APIError) as exc:
            policy(role, has_shop=False).selling_shop()
        assert exc.value.code == "FORBIDDEN"
    with pytest.raises(APIError) as exc:
        AccessPolicy(SimpleNamespace(principal=lambda _: None), 17)
    assert exc.value.status_code == 401


def test_profile_exposes_only_contract_fields():
    profile = policy().profile().model_dump()
    assert set(profile) == {
        "user_id",
        "email",
        "full_name",
        "phone",
        "user_role",
        "user_status",
        "owned_shop",
    }
    assert profile["user_id"] == "17"
    assert profile["owned_shop"] == {"shop_id": "23", "shop_status": "APPROVED"}
