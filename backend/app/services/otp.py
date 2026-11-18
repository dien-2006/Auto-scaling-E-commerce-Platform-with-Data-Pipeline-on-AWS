"""Redis OTP, consumed before a transactional PostgreSQL account mutation."""

import hashlib
import hmac
import secrets
from uuid import uuid4

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from app.core.errors import APIError
from app.core.security import DUMMY_HASH, PASSWORD_HASHER, verify_password
from app.repositories.otp import OTPRepository
from app.repositories.users import UserRepository
from app.services.auth import AuthService
from app.services.otp_delivery import configured, deliver


class OTPService:
    def __init__(self, session, settings, store):
        self.session = session
        self.settings = settings
        self.store = store
        self.repository = OTPRepository(session)

    def enabled(self):
        if not self.settings.otp_enabled or not self.settings.otp_secret:
            raise APIError(503, "OTP_NOT_CONFIGURED", "Xác minh OTP chưa được cấu hình")

    def digest(self, *parts):
        return hmac.new(
            self.settings.otp_secret.get_secret_value().encode(),
            "\0".join(str(p) for p in parts).encode(),
            hashlib.sha256,
        ).hexdigest()

    def issue(self, data, ip):
        self.enabled()
        if not configured(self.settings, data.channel):
            raise APIError(503, "OTP_NOT_CONFIGURED", "Kênh gửi OTP chưa được cấu hình")
        challenge_id = uuid4()
        code = f"{secrets.randbelow(1000000):06d}"
        target_key = self.digest(data.purpose, data.channel, data.target)
        ip_key = self.digest("ip", ip)
        try:
            with self.session.begin():
                user = self.repository.user(
                    data.channel, data.target, registration=data.purpose == "REGISTER"
                )
                eligible = (
                    (user is None)
                    if data.purpose == "REGISTER"
                    else bool(user and user.user_status == "ACTIVE")
                )
            self.store.issue(
                challenge_id,
                {
                    "purpose": data.purpose,
                    "channel": data.channel,
                    "target": data.target,
                    "code_hash": self.digest(challenge_id, code),
                    "eligible": eligible,
                    "user_id": user.user_id if eligible and user else None,
                    "credential_stamp": self.digest("credential", user.password_hash)
                    if eligible and user
                    else None,
                    "attempts": 0,
                    "delivered": False,
                },
                target_key,
                ip_key,
            )
            return {"challenge_id": str(challenge_id), "expires_in": 60, "resend_after": 60}, (
                challenge_id,
                data.channel,
                data.target,
                code,
            ) if eligible else None
        except SQLAlchemyError as exc:
            raise APIError(503, "OTP_UNAVAILABLE", "Chức năng OTP chưa sẵn sàng") from exc

    def valid_reset_user(self, challenge):
        user = self.repository.by_id(challenge["user_id"]) if challenge["user_id"] else None
        if (
            not user
            or user.user_status != "ACTIVE"
            or not hmac.compare_digest(
                challenge["credential_stamp"], self.digest("credential", user.password_hash)
            )
            or user.email is None
            or user.email.lower() != challenge["target"]
        ):
            raise APIError(400, "OTP_INVALID", "Xác minh không còn hợp lệ. Vui lòng lấy mã mới")
        return user

    def verify(self, data):
        """Only proves email ownership; never receives or changes a password."""
        self.enabled()
        try:
            challenge = self.store.consume(
                data.challenge_id, self.digest(data.challenge_id, data.code.get_secret_value())
            )
            if not challenge.get("eligible"):
                raise APIError(400, "OTP_INVALID", "Mã không đúng hoặc đã hết hạn")
            with self.session.begin():
                if challenge["purpose"] == "RESET_PASSWORD":
                    self.valid_reset_user(challenge)
                elif self.repository.user("EMAIL", challenge["target"]):
                    raise APIError(400, "OTP_INVALID", "Xác minh không còn hợp lệ")
            token = secrets.token_hex(32)
            grant = {
                key: challenge[key] for key in ("purpose", "target", "user_id", "credential_stamp")
            }
            self.store.grant(self.digest("grant", token), grant)
            return {"purpose": challenge["purpose"], "verification_token": token, "expires_in": 300}
        except SQLAlchemyError as exc:
            raise APIError(
                503, "OTP_UNAVAILABLE", "Chưa xác minh được. Vui lòng yêu cầu mã mới"
            ) from exc

    def complete(self, data, purpose):
        """Requires a consumed OTP's short-lived proof, bound to its exact action."""
        self.enabled()
        try:
            grant = self.store.consume_grant(
                self.digest("grant", data.verification_token.get_secret_value()), purpose
            )
            with self.session.begin():
                self.repository.lock(self.digest("identity", "EMAIL", grant["target"]))
                if purpose == "REGISTER":
                    if self.repository.user("EMAIL", grant["target"], lock=True):
                        raise APIError(400, "OTP_INVALID", "Email đã đăng ký. Vui lòng đăng nhập")
                    user = UserRepository(self.session).add(
                        email=grant["target"],
                        phone=None,
                        full_name=data.full_name,
                        password_hash=PASSWORD_HASHER.hash(data.password.get_secret_value()),
                    )
                    return {
                        "purpose": purpose,
                        "user": AuthService(UserRepository(self.session))
                        .profile(user)
                        .model_dump(mode="json"),
                    }
                user = self.valid_reset_user(grant)
                user.password_hash = PASSWORD_HASHER.hash(data.new_password.get_secret_value())
                user.updated_at = func.now()
            return {"purpose": purpose}
        except SQLAlchemyError as exc:
            raise APIError(
                503,
                "OTP_UNAVAILABLE",
                "Chưa xác nhận được kết quả. Hãy thử đăng nhập trước khi lấy mã mới",
            ) from exc

    def login(self, data):
        self.enabled()
        try:
            with self.session.begin():
                user = self.repository.user("EMAIL", data.identifier, lock=True)
                valid = verify_password(
                    user.password_hash if user else DUMMY_HASH, data.password.get_secret_value()
                )
                if not user or not valid:
                    raise APIError(401, "INVALID_CREDENTIALS", "Email hoặc mật khẩu không đúng")
                AuthService.active(user)
                if PASSWORD_HASHER.check_needs_rehash(user.password_hash):
                    user.password_hash = PASSWORD_HASHER.hash(data.password.get_secret_value())
                profile = AuthService(UserRepository(self.session)).profile(user)
                return profile, user.password_hash
        except SQLAlchemyError as exc:
            raise APIError(503, "OTP_UNAVAILABLE", "Chức năng xác thực chưa sẵn sàng") from exc


def send_pending(store, settings, pending):
    """Best-effort delivery; expired/missing Redis proofs can never be revived."""
    challenge_id, channel, target, code = pending
    success = False
    try:
        deliver(settings, channel, target, code)
        success = True
    except APIError:
        pass
    try:
        store.delivered(challenge_id, success)
    except APIError:
        pass  # No code/token/target is logged; fail closed, user may request another code.
