from unittest.mock import MagicMock

import pytest

from app.core.config import Settings
from app.core.errors import APIError
from app.schemas.otp import OTPRegister, OTPVerify, normalize_target
from app.services.otp_delivery import deliver


def test_email_normalization_and_secret_validation():
    assert normalize_target("EMAIL", " Test@Example.com ") == "test@example.com"
    with pytest.raises(ValueError):
        normalize_target("SMS", "not-a-phone")
    with pytest.raises(ValueError):
        OTPVerify(challenge_id="11111111-1111-4111-8111-111111111111", code="abc123")
    with pytest.raises(ValueError):
        OTPRegister(
            verification_token="0" * 64,
            full_name="Test",
            password="weak",
        )


def test_unconfigured_delivery_never_calls_network(monkeypatch):
    client = MagicMock()
    monkeypatch.setattr("app.services.otp_delivery.boto3.client", client)
    with pytest.raises(APIError) as error:
        deliver(Settings(), "EMAIL", "test@example.com", "123456")
    assert error.value.code == "OTP_NOT_CONFIGURED"
    client.assert_not_called()


def test_smtp_enforces_starttls_and_one_send(monkeypatch):
    factory = MagicMock()
    client = factory.return_value.__enter__.return_value
    monkeypatch.setattr("app.services.otp_delivery.smtplib.SMTP", factory)
    cfg = Settings(
        otp_email_provider="smtp",
        otp_from_email="sender@example.com",
        smtp_host="smtp-relay.brevo.com",
        smtp_username="user",
        smtp_password="test-only",
    )
    deliver(cfg, "EMAIL", "recipient@example.com", "123456")
    assert factory.call_args.args == ("smtp-relay.brevo.com", 587)
    client.starttls.assert_called_once()
    client.login.assert_called_once_with("user", "test-only")
    client.send_message.assert_called_once()
    message = client.send_message.call_args.args[0]
    assert "1 phut" in message.get_content()


def test_aws_ses_uses_email_delivery_without_retry(monkeypatch):
    factory = MagicMock()
    monkeypatch.setattr("app.services.otp_delivery.boto3.client", factory)
    cfg = Settings(
        otp_email_provider="ses", otp_sms_provider="sns", otp_from_email="sender@example.com"
    )
    deliver(cfg, "EMAIL", "recipient@example.com", "123456")
    factory.return_value.send_email.assert_called_once()
    with pytest.raises(APIError):
        deliver(cfg, "SMS", "+84900000000", "123456")
    factory.return_value.publish.assert_not_called()


def test_enabled_otp_requires_shared_redis_configuration():
    import secrets

    with pytest.raises(ValueError):
        Settings(
            otp_enabled=True,
            otp_secret=secrets.token_urlsafe(48),
            jwt_secret=secrets.token_urlsafe(48),
            public_origin="http://testserver",
        )
