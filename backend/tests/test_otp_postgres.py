"""OTP fixtures use only explicitly isolated marketplace_test; never sends mail/SMS."""

import json
import secrets
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import text
from test_checkout_postgres import checkout_db as checkout_db  # noqa:F401

from app.core.errors import APIError
from app.core.security import Security, verify_password
from app.main import create_app
from app.models import User
from app.repositories.otp import OTPRepository
from app.schemas.otp import OTPRegister, OTPRequest, OTPReset, OTPVerify
from app.services.otp import OTPService, send_pending
from app.services.otp_store import PREFIX, OTPStore


@pytest.fixture(scope="module")
def redis_url(checkout_db):
    # Only an owned disposable Redis; never use a configured application cache.
    name = "marketplace-otp-test-" + uuid4().hex[:10]
    created = False
    try:
        subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                name,
                "--label",
                "marketplace.test=otp-redis",
                "-p",
                "127.0.0.1::6379",
                "redis:7.4-alpine",
                "redis-server",
                "--save",
                "",
                "--appendonly",
                "no",
            ],
            check=True,
            capture_output=True,
            timeout=60,
        )
        created = True
        info = json.loads(subprocess.check_output(["docker", "inspect", name], text=True))[0]
        port = info["NetworkSettings"]["Ports"]["6379/tcp"][0]["HostPort"]
        url = f"redis://127.0.0.1:{port}/0"
        from redis import Redis
        from redis.exceptions import RedisError

        client = Redis.from_url(url)
        try:
            for _ in range(100):
                try:
                    if client.ping():
                        break
                except RedisError:
                    time.sleep(0.1)
            else:
                pytest.fail("Owned Redis did not become ready")
        finally:
            client.close()
        yield url
    finally:
        if created:
            info = json.loads(subprocess.check_output(["docker", "inspect", name], text=True))[0]
            assert info["Config"]["Labels"]["marketplace.test"] == "otp-redis"
            subprocess.run(["docker", "rm", "-f", name], check=True, capture_output=True)


@pytest.fixture
def otp(checkout_db, redis_url):
    base, db = checkout_db
    cfg = base.model_copy(
        update={
            "otp_enabled": True,
            "otp_redis_url": SecretStr(redis_url),
            "otp_secret": SecretStr(secrets.token_urlsafe(48)),
            "otp_email_provider": "smtp",
            "otp_from_email": "sender@example.test",
            "smtp_host": "smtp-relay.brevo.com",
            "smtp_username": "test",
            "smtp_password": SecretStr("test-only"),
        }
    )
    previous = db.otp_store
    db.otp_store = OTPStore(cfg)
    try:
        yield cfg, db
    finally:
        db.otp_store.close()
        db.otp_store = previous


def expire_cooldown(cfg, db, target):
    with db.sessions() as session:
        digest = OTPService(session, cfg, db.otp_store).digest("REGISTER", "EMAIL", target)
    db.otp_store.client.delete(PREFIX + "cooldown:" + digest)


def challenge(db, challenge_id):
    raw = db.otp_store.client.get(db.otp_store.key(challenge_id))
    return json.loads(raw) if raw else None


def issue(cfg, db, *, purpose="REGISTER", channel="EMAIL", target=None):
    target = target or f"{uuid4().hex}@example.com"
    data = OTPRequest(
        purpose=purpose,
        channel=channel,
        target=target,
    )
    with db.sessions() as s:
        response, pending = OTPService(s, cfg, db.otp_store).issue(data, "fixture")
    if pending:
        db.otp_store.delivered(pending[0], True)
    return response, pending


def proof(cfg, db, pending):
    with db.sessions() as s:
        return OTPService(s, cfg, db.otp_store).verify(
            OTPVerify(challenge_id=pending[0], code=pending[3])
        )


def complete(cfg, db, verified, **changes):
    data = (
        OTPRegister(
            verification_token=verified["verification_token"],
            full_name="OTP Test",
            password="OldPassword9!",
        )
        if verified["purpose"] == "REGISTER"
        else OTPReset(
            verification_token=verified["verification_token"], new_password=changes["new_password"]
        )
    )
    with db.sessions() as s:
        return OTPService(s, cfg, db.otp_store).complete(data, verified["purpose"])


def verify(cfg, db, pending, **changes):
    return complete(cfg, db, proof(cfg, db, pending), **changes)


def test_register_otp_single_use_60_seconds_and_no_plaintext_code(otp):
    cfg, db = otp
    response, pending = issue(cfg, db)
    assert response["expires_in"] == 60 and response["resend_after"] == 60
    row = challenge(db, pending[0])
    assert row["code_hash"] != pending[3] and len(row["code_hash"]) == 64
    assert row["expires_at"] - row["created_at"] == 60000
    assert 0 < db.otp_store.client.pttl(db.otp_store.key(pending[0])) <= 60000
    assert "pending" not in row and "password_hash" not in row
    assert pending[3] not in str(response)
    with db.sessions() as s:
        assert OTPRepository(s).user("EMAIL", pending[2]) is None
    result = verify(cfg, db, pending)
    assert result["purpose"] == "REGISTER" and result["user"]["user_role"] == "USER"
    with pytest.raises(APIError) as error:
        verify(cfg, db, pending)
    assert error.value.code == "OTP_INVALID"


def test_wrong_attempts_commit_and_expiry_fails_closed(otp):
    cfg, db = otp
    _, pending = issue(cfg, db)
    wrong = "000000" if pending[3] != "000000" else "111111"
    for _ in range(5):
        with db.sessions() as s, pytest.raises(APIError):
            OTPService(s, cfg, db.otp_store).verify(OTPVerify(challenge_id=pending[0], code=wrong))
    assert challenge(db, pending[0]) is None
    with pytest.raises(APIError):
        verify(cfg, db, pending)
    _, expired = issue(cfg, db)
    db.otp_store.client.pexpire(db.otp_store.key(expired[0]), 1)
    time.sleep(0.02)
    with pytest.raises(APIError):
        verify(cfg, db, expired)


def test_email_only_keeps_25_tables_and_email_required(otp):
    cfg, db = otp
    with db.sessions() as s:
        assert (
            s.scalar(
                text(
                    "SELECT count(*) FROM information_schema.tables "
                    "WHERE table_schema='marketplace' AND table_type='BASE TABLE'"
                )
            )
            == 25
        )
        assert (
            s.scalar(
                text(
                    "SELECT count(*) FROM information_schema.tables "
                    "WHERE table_schema='auth_security'"
                )
            )
            == 0
        )
        assert (
            s.scalar(
                text(
                    "SELECT is_nullable FROM information_schema.columns "
                    "WHERE table_schema='marketplace' AND table_name='users' "
                    "AND column_name='email'"
                )
            )
            == "NO"
        )
    with pytest.raises(ValueError):
        OTPRequest(
            purpose="REGISTER",
            channel="SMS",
            target="+84901234567",
            full_name="Test",
            password="Password9!",
        )


def test_reset_password_revokes_previous_session_without_unlocking_accounts(otp):
    cfg, db = otp
    _, registration = issue(cfg, db)
    user = verify(cfg, db, registration)["user"]
    security = Security(cfg)
    with db.sessions() as s:
        old_hash = s.get(User, int(user["user_id"])).password_hash
    token = security.issue_access(int(user["user_id"]), security.credential_stamp(old_hash))
    with TestClient(create_app(cfg)) as c:
        c.cookies.set(security.access_cookie, token)
        assert c.get("/api/v1/auth/me").status_code == 200
        _, reset = issue(cfg, db, purpose="RESET_PASSWORD", target=registration[2])
        assert verify(cfg, db, reset, new_password="NewPassword9!")["purpose"] == "RESET_PASSWORD"
        assert c.get("/api/v1/auth/me").status_code == 401
    with db.sessions() as s:
        row = s.get(User, int(user["user_id"]))
        assert verify_password(row.password_hash, "NewPassword9!")
        assert not verify_password(row.password_hash, "OldPassword9!")


def test_unknown_reset_and_duplicate_registration_are_generic_and_no_delivery(otp):
    cfg, db = otp
    unknown, pending = issue(cfg, db, purpose="RESET_PASSWORD")
    assert pending is None and set(unknown) == {"challenge_id", "expires_in", "resend_after"}
    _, registration = issue(cfg, db)
    verify(cfg, db, registration)
    expire_cooldown(cfg, db, registration[2])
    duplicate, pending = issue(cfg, db, target=registration[2])
    assert pending is None and set(duplicate) == set(unknown)


def test_cooldown_and_failed_delivery_do_not_create_verified_account(otp, monkeypatch):
    cfg, db = otp
    _, pending = issue(cfg, db)
    with pytest.raises(APIError) as error:
        issue(cfg, db, target=pending[2])
    assert error.value.status_code == 429

    def fail(*args):
        raise APIError(503, "OTP_DELIVERY_FAILED", "Unavailable")

    monkeypatch.setattr("app.services.otp.deliver", fail)
    # The real delivery adapter is never called by this suite.
    row = challenge(db, pending[0])
    row["delivered"] = False
    db.otp_store.client.set(db.otp_store.key(pending[0]), json.dumps(row), keepttl=True)
    send_pending(db.otp_store, cfg, pending)
    with pytest.raises(APIError):
        verify(cfg, db, pending)


def test_simultaneous_verify_consumes_once(otp):
    cfg, db = otp
    _, pending = issue(cfg, db)

    def attempt():
        try:
            verify(cfg, db, pending)
            return "OK"
        except APIError as e:
            return e.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: attempt(), range(2)))
    assert sorted(results) == ["OK", "OTP_INVALID"]


def test_legacy_registration_is_blocked_and_options_no_secrets(otp):
    cfg, db = otp
    with TestClient(create_app(cfg)) as c:
        options = c.get("/api/v1/auth/otp-options")
        assert options.json() == {"enabled": True, "email": True, "sms": False}
        token = c.get("/api/v1/auth/csrf").json()["data"]["csrf_token"]
        response = c.post(
            "/api/v1/auth/register",
            json={
                "email": f"{uuid4().hex}@example.com",
                "full_name": "Test",
                "password": "Password9!",
            },
            headers={"Origin": "http://testserver", "X-CSRF-Token": token},
        )
        assert response.status_code == 403 and response.json()["error"]["code"] == "OTP_REQUIRED"


def test_resend_invalidates_previous_code_and_email_login_works(otp):
    cfg, db = otp
    target = f"{uuid4().hex}@example.com"
    _, old = issue(cfg, db, target=target)
    expire_cooldown(cfg, db, target)
    _, new = issue(cfg, db, target=target)
    with pytest.raises(APIError):
        verify(cfg, db, old)
    user = verify(cfg, db, new)["user"]
    with TestClient(create_app(cfg)) as c:
        csrf = c.get("/api/v1/auth/csrf").json()["data"]["csrf_token"]
        response = c.post(
            "/api/v1/auth/login",
            json={"email": target, "password": "OldPassword9!"},
            headers={"Origin": "http://testserver", "X-CSRF-Token": csrf},
        )
        assert response.status_code == 200 and response.json()["data"]["email"] == target
        assert response.json()["data"]["user_id"] == user["user_id"]
        assert c.get("/api/v1/auth/me").status_code == 200


def test_reset_challenge_cannot_unlock_locked_account(otp):
    cfg, db = otp
    _, registration = issue(cfg, db)
    user = verify(cfg, db, registration)["user"]
    _, reset = issue(cfg, db, purpose="RESET_PASSWORD", target=registration[2])
    with db.sessions.begin() as s:
        s.get(User, int(user["user_id"])).user_status = "LOCKED"
    with pytest.raises(APIError):
        verify(cfg, db, reset, new_password="NewPassword9!")
    with db.sessions() as s:
        row = s.get(User, int(user["user_id"]))
        assert row.user_status == "LOCKED" and verify_password(row.password_hash, "OldPassword9!")


def test_missing_csrf_blocks_otp_request_before_delivery(otp, monkeypatch):
    cfg, db = otp
    calls = []
    monkeypatch.setattr("app.services.otp.deliver", lambda *args: calls.append(args))
    with TestClient(create_app(cfg)) as c:
        result = c.post(
            "/api/v1/auth/otp-request",
            json={"purpose": "RESET_PASSWORD", "channel": "EMAIL", "target": "test@example.com"},
            headers={"Origin": "http://evil.invalid"},
        )
        assert result.status_code == 403
    assert calls == []


def test_otp_readiness_requires_redis_without_schema_change(otp, monkeypatch):
    from app.db.session import Database

    cfg, db = otp
    probe = Database(cfg)
    try:
        assert probe.ready()
        monkeypatch.setattr(probe.otp_store, "ready", lambda: False)
        assert not probe.ready()
    finally:
        probe.close()


def test_sql_failure_burns_proof_instead_of_allowing_replay(otp, monkeypatch):
    from sqlalchemy.exc import SQLAlchemyError

    cfg, db = otp
    _, pending = issue(cfg, db)

    def fail(*args, **kwargs):
        raise SQLAlchemyError("private error")

    monkeypatch.setattr("app.services.otp.UserRepository.add", fail)
    with pytest.raises(APIError) as error:
        verify(cfg, db, pending)
    assert error.value.code == "OTP_UNAVAILABLE"
    assert challenge(db, pending[0]) is None
    with pytest.raises(APIError) as error:
        verify(cfg, db, pending)
    assert error.value.code == "OTP_INVALID"
    with db.sessions() as s:
        assert OTPRepository(s).user("EMAIL", pending[2]) is None


def test_redis_failure_prevents_issue_and_account_creation(otp, monkeypatch):
    from redis.exceptions import ConnectionError

    cfg, db = otp

    def fail(*args, **kwargs):
        raise ConnectionError("private redis URL")

    monkeypatch.setattr(db.otp_store.client, "eval", fail)
    with pytest.raises(APIError) as error:
        issue(cfg, db)
    assert error.value.code == "OTP_UNAVAILABLE"
    assert "private" not in error.value.message


def test_late_delivery_cannot_revive_expired_proof(otp):
    cfg, db = otp
    _, pending = issue(cfg, db)
    key = db.otp_store.key(pending[0])
    db.otp_store.client.delete(key)
    db.otp_store.delivered(pending[0], True)
    assert not db.otp_store.client.exists(key)
    with pytest.raises(APIError):
        verify(cfg, db, pending)


def test_redis_hourly_limits_cannot_be_bypassed_by_resending(otp):
    cfg, db = otp
    store = db.otp_store
    target, ip = uuid4().hex, uuid4().hex
    row = {"purpose": "REGISTER", "attempts": 0, "delivered": False}
    for _ in range(5):
        store.issue(uuid4(), row, target, ip)
        store.client.delete(PREFIX + "cooldown:" + target)
    with pytest.raises(APIError) as error:
        store.issue(uuid4(), row, target, ip)
    assert error.value.code == "RATE_LIMITED"
    ip = uuid4().hex
    for _ in range(100):
        store.issue(uuid4(), row, uuid4().hex, ip)
    with pytest.raises(APIError) as error:
        store.issue(uuid4(), row, uuid4().hex, ip)
    assert error.value.code == "RATE_LIMITED"


def test_reset_requires_otp_verification_before_accepting_new_password(otp):
    cfg, db = otp
    _, registration = issue(cfg, db)
    user = verify(cfg, db, registration)["user"]
    _, pending = issue(cfg, db, purpose="RESET_PASSWORD", target=registration[2])
    verified = proof(cfg, db, pending)
    assert verified["purpose"] == "RESET_PASSWORD" and verified["expires_in"] == 300
    assert len(verified["verification_token"]) == 64
    with db.sessions() as s:
        assert verify_password(s.get(User, int(user["user_id"])).password_hash, "OldPassword9!")
    with pytest.raises(ValueError):
        OTPVerify(challenge_id=pending[0], code=pending[3], new_password="NewPassword9!")
    with TestClient(create_app(cfg)) as client:
        csrf = client.get("/api/v1/auth/csrf").json()["data"]["csrf_token"]
        headers = {"Origin": "http://testserver", "X-CSRF-Token": csrf}
        assert (
            client.post(
                "/api/v1/auth/password-reset",
                json={"new_password": "NewPassword9!"},
                headers=headers,
            ).status_code
            == 422
        )
        assert (
            client.post(
                "/api/v1/auth/password-reset",
                json={"verification_token": "0" * 64, "new_password": "NewPassword9!"},
                headers=headers,
            ).status_code
            == 400
        )
        response = client.post(
            "/api/v1/auth/password-reset",
            json={
                "verification_token": verified["verification_token"],
                "new_password": "NewPassword9!",
            },
            headers=headers,
        )
        assert response.status_code == 200
    with pytest.raises(APIError):
        complete(cfg, db, verified, new_password="OtherPassword9!")


def test_grant_is_action_bound_and_expires(otp):
    cfg, db = otp
    _, pending = issue(cfg, db)
    verified = proof(cfg, db, pending)
    with db.sessions() as s, pytest.raises(APIError):
        OTPService(s, cfg, db.otp_store).complete(
            OTPReset(
                verification_token=verified["verification_token"], new_password="NewPassword9!"
            ),
            "RESET_PASSWORD",
        )
    with db.sessions() as s:
        digest = OTPService(s, cfg, db.otp_store).digest("grant", verified["verification_token"])
    key = PREFIX + "grant:" + digest
    assert 0 < db.otp_store.client.ttl(key) <= 300
    assert verified["verification_token"] not in str(db.otp_store.client.get(key))
    db.otp_store.client.pexpire(key, 1)
    time.sleep(0.02)
    with pytest.raises(APIError):
        complete(cfg, db, verified)
    with db.sessions() as s:
        assert OTPRepository(s).user("EMAIL", pending[2]) is None


def test_concurrent_grant_completion_creates_one_account(otp):
    cfg, db = otp
    _, pending = issue(cfg, db)
    verified = proof(cfg, db, pending)

    def attempt():
        try:
            return complete(cfg, db, verified)["purpose"]
        except APIError as error:
            return error.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(lambda _: attempt(), range(2))) == ["OTP_INVALID", "REGISTER"]


def test_reset_grant_rechecks_locked_account_and_password_stamp(otp):
    cfg, db = otp
    _, registration = issue(cfg, db)
    user = verify(cfg, db, registration)["user"]
    _, pending = issue(cfg, db, purpose="RESET_PASSWORD", target=registration[2])
    verified = proof(cfg, db, pending)
    with db.sessions.begin() as s:
        s.get(User, int(user["user_id"])).user_status = "LOCKED"
    with pytest.raises(APIError):
        complete(cfg, db, verified, new_password="NewPassword9!")
    with db.sessions() as s:
        assert verify_password(s.get(User, int(user["user_id"])).password_hash, "OldPassword9!")
