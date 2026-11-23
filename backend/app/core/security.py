"""Stateless JWT cookies and session-bound signed double-submit CSRF."""

import hashlib
import hmac
import re
import secrets
import time
from urllib.parse import urlsplit

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Request, Response

from app.core.config import Settings
from app.core.errors import APIError

PASSWORD_HASHER = PasswordHasher()  # Argon2id, RFC 9106 low-memory defaults.
DUMMY_HASH = PASSWORD_HASHER.hash(secrets.token_urlsafe(32))
ACCESS_SECONDS = 900
CSRF_SECONDS = 3600
POSITIVE_ID = re.compile(r"[1-9][0-9]{0,18}\Z")
CSRF_PATTERN = re.compile(r"[0-9]{1,12}\.[a-f0-9]{48}\.[a-f0-9]{64}\Z")


def verify_password(encoded: str, password: str) -> bool:
    try:
        return PASSWORD_HASHER.verify(encoded, password)
    except (VerificationError, InvalidHashError):
        return False


class Security:
    def __init__(self, settings: Settings) -> None:
        if settings.jwt_secret is None or settings.public_origin is None:
            raise APIError(503, "AUTH_NOT_CONFIGURED", "Xác thực chưa được cấu hình")
        self.key = settings.jwt_secret.get_secret_value()
        self.settings = settings
        self.secure = settings.environment == "production"
        self.access_cookie = "__Host-marketplace_access" if self.secure else "marketplace_access"
        self.csrf_cookie = "__Host-marketplace_csrf" if self.secure else "marketplace_csrf"
        self.origin = str(settings.public_origin).rstrip("/")
        self.allowed_origins = {
            self.origin,
            *(str(value).rstrip("/") for value in settings.additional_origins),
        }

    def issue_access(self, user_id: int, credential: str | None = None) -> str:
        now = int(time.time())
        return jwt.encode(
            {
                **({"credential": credential} if credential is not None else {}),
                "sub": str(user_id),
                "iat": now,
                "exp": now + ACCESS_SECONDS,
                "iss": self.settings.jwt_issuer,
                "aud": self.settings.jwt_audience,
            },
            self.key,
            algorithm="HS256",
        )

    def subject(self, request: Request) -> int:
        token = request.cookies.get(self.access_cookie)
        if not token:
            raise APIError(401, "AUTH_REQUIRED", "Vui lòng đăng nhập")
        try:
            if len(token) > 4096:
                raise ValueError
            claims = jwt.decode(
                token,
                self.key,
                algorithms=["HS256"],
                issuer=self.settings.jwt_issuer,
                audience=self.settings.jwt_audience,
                options={"require": ["exp", "iat", "sub", "iss", "aud"], "strict_aud": True},
            )
            subject = claims["sub"]
            if (
                not isinstance(subject, str)
                or not POSITIVE_ID.fullmatch(subject)
                or int(subject) > 9223372036854775807
            ):
                raise ValueError
            issued, expires = claims["iat"], claims["exp"]
            if (
                type(issued) is not int
                or type(expires) is not int
                or not 0 < expires - issued <= ACCESS_SECONDS
            ):
                raise ValueError
            request.state.auth_credential = claims.get("credential")
            return int(subject)
        except jwt.ExpiredSignatureError as exc:
            raise APIError(401, "TOKEN_EXPIRED", "Phiên đăng nhập đã hết hạn") from exc
        except (jwt.InvalidTokenError, ValueError, TypeError) as exc:
            raise APIError(401, "INVALID_TOKEN", "Phiên đăng nhập không hợp lệ") from exc

    def _signature(self, payload: str, access: str) -> str:
        binding = hashlib.sha256(access.encode()).hexdigest()
        return hmac.new(
            self.key.encode(), f"csrf-v1:{binding}:{payload}".encode(), hashlib.sha256
        ).hexdigest()

    def issue_csrf(self, access: str = "") -> str:
        payload = f"{int(time.time())}.{secrets.token_hex(24)}"
        return f"{payload}.{self._signature(payload, access)}"

    def check_csrf(self, request: Request) -> None:
        rejected = APIError(403, "CSRF_FAILED", "Yêu cầu xác thực nguồn không hợp lệ")
        origins = request.headers.getlist("origin")
        if origins:
            if len(origins) != 1 or origins[0] not in self.allowed_origins:
                raise rejected
        else:
            referers = request.headers.getlist("referer")
            if len(referers) != 1:
                raise rejected
            try:
                ref = urlsplit(referers[0])
                if (
                    ref.scheme not in {"http", "https"}
                    or ref.username
                    or ref.password
                    or f"{ref.scheme}://{ref.netloc}" not in self.allowed_origins
                ):
                    raise rejected
            except ValueError as exc:
                raise rejected from exc
        tokens = request.headers.getlist("x-csrf-token")
        cookie = request.cookies.get(self.csrf_cookie, "")
        if (
            len(tokens) != 1
            or not CSRF_PATTERN.fullmatch(tokens[0])
            or not CSRF_PATTERN.fullmatch(cookie)
        ):
            raise rejected
        token = tokens[0]
        if not hmac.compare_digest(token, cookie):
            raise rejected
        payload, signature = token.rsplit(".", 1)
        age = time.time() - int(payload.split(".")[0])
        if not 0 <= age <= CSRF_SECONDS or not hmac.compare_digest(
            signature, self._signature(payload, request.cookies.get(self.access_cookie, ""))
        ):
            raise rejected

    def set_csrf(self, response: Response, access: str = "") -> str:
        token = self.issue_csrf(access)
        response.set_cookie(
            self.csrf_cookie,
            token,
            max_age=CSRF_SECONDS,
            path="/",
            secure=self.secure,
            httponly=False,
            samesite="lax",
        )
        return token

    def credential_stamp(self, password_hash: str) -> str:
        return hmac.new(
            self.key.encode(), ("credential:" + password_hash).encode(), hashlib.sha256
        ).hexdigest()

    def login_cookies(
        self, response: Response, user_id: int, credential: str | None = None
    ) -> None:
        access = self.issue_access(user_id, credential)
        response.set_cookie(
            self.access_cookie,
            access,
            max_age=ACCESS_SECONDS,
            path="/",
            secure=self.secure,
            httponly=True,
            samesite="lax",
        )
        self.set_csrf(response, access)

    def clear_cookies(self, response: Response) -> None:
        for name, http_only in [(self.access_cookie, True), (self.csrf_cookie, False)]:
            response.delete_cookie(
                name, path="/", secure=self.secure, httponly=http_only, samesite="lax"
            )


def get_security(request: Request) -> Security:
    return Security(request.app.state.settings)
