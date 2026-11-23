"""Verify the IP signed by the private Next.js proxy before applying OTP limits."""

import hashlib
import hmac
import re
from ipaddress import ip_address

from fastapi import Request

from app.core.errors import APIError


def otp_client_ip(request: Request) -> str:
    secret = request.app.state.settings.proxy_secret
    if secret is None:
        # Local development does not trust browser-supplied forwarding headers.
        return request.client.host if request.client else "unknown"

    value = request.headers.get("x-marketplace-client-ip", "")
    signature = request.headers.get("x-marketplace-client-signature", "")
    if not re.fullmatch(r"[a-f0-9]{64}", signature):
        raise APIError(403, "INVALID_PROXY_SIGNATURE", "Không xác minh được nguồn yêu cầu")
    try:
        address = str(ip_address(value))
    except ValueError as exc:
        raise APIError(403, "INVALID_PROXY_SIGNATURE", "Không xác minh được nguồn yêu cầu") from exc
    expected = hmac.new(
        secret.get_secret_value().encode(),
        f"otp-ip-v1:{value}".encode(),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise APIError(403, "INVALID_PROXY_SIGNATURE", "Không xác minh được nguồn yêu cầu")
    return address
