import hashlib
import hmac
from types import SimpleNamespace

import pytest
from pydantic import SecretStr

from app.core.client_ip import otp_client_ip
from app.core.errors import APIError

PROXY_KEY = "test-only-proxy-key-with-at-least-32-characters"


def request(secret=None, headers=None):
    return SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(settings=SimpleNamespace(proxy_secret=secret))),
        client=SimpleNamespace(host="172.20.0.5"),
        headers=headers or {},
    )


def signed(address):
    signature = hmac.new(
        PROXY_KEY.encode(), f"otp-ip-v1:{address}".encode(), hashlib.sha256
    ).hexdigest()
    return {
        "x-marketplace-client-ip": address,
        "x-marketplace-client-signature": signature,
    }


def test_local_ignores_untrusted_forwarded_ip():
    assert otp_client_ip(request(headers=signed("198.51.100.1"))) == "172.20.0.5"


def test_distinct_clients_behind_one_proxy_keep_distinct_rate_limit_keys():
    first = otp_client_ip(request(SecretStr(PROXY_KEY), signed("198.51.100.1")))
    second = otp_client_ip(request(SecretStr(PROXY_KEY), signed("198.51.100.2")))
    assert (first, second) == ("198.51.100.1", "198.51.100.2")


def test_ipv6_is_normalized_before_rate_limiting():
    headers = signed("2001:0db8:0000::1")
    assert otp_client_ip(request(SecretStr(PROXY_KEY), headers)) == "2001:db8::1"


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"x-marketplace-client-ip": "198.51.100.1"},
        {**signed("198.51.100.1"), "x-marketplace-client-ip": "198.51.100.2"},
        signed("not-an-ip"),
        {**signed("198.51.100.1"), "x-marketplace-client-signature": "é" * 64},
    ],
)
def test_missing_or_forged_proxy_proofs_are_rejected(headers):
    with pytest.raises(APIError):
        otp_client_ip(request(SecretStr(PROXY_KEY), headers))
