"""Delivery adapters; never log or return OTP codes. No provider fallback."""

import smtplib
import ssl
from email.message import EmailMessage

import boto3
from botocore.config import Config

from app.core.errors import APIError


def configured(settings, channel):
    if channel == "EMAIL":
        return bool(
            settings.otp_from_email
            and (
                settings.otp_email_provider == "ses"
                or (
                    settings.otp_email_provider == "smtp"
                    and settings.smtp_host
                    and settings.smtp_username
                    and settings.smtp_password
                )
            )
        )
    return False


def deliver(settings, channel, target, code):
    if not configured(settings, channel):
        raise APIError(503, "OTP_NOT_CONFIGURED", "Dịch vụ gửi mã chưa được cấu hình")
    body = (
        f"Ma xac nhan COCO cua ban: {code}. Het han sau 1 phut. Khong chia se ma nay voi bat ky ai."
    )
    try:
        if channel == "EMAIL" and settings.otp_email_provider == "smtp":
            message = EmailMessage()
            message["Subject"] = "COCO - Ma xac nhan"
            message["From"] = settings.otp_from_email
            message["To"] = target
            message.set_content(body)
            smtp = smtplib.SMTP_SSL if settings.smtp_security == "TLS" else smtplib.SMTP
            with smtp(
                settings.smtp_host,
                settings.smtp_port,
                timeout=10,
                **(
                    {"context": ssl.create_default_context()}
                    if settings.smtp_security == "TLS"
                    else {}
                ),
            ) as client:
                if settings.smtp_security == "STARTTLS":
                    client.starttls(context=ssl.create_default_context())
                client.login(settings.smtp_username, settings.smtp_password.get_secret_value())
                client.send_message(message)
        else:
            client = boto3.client(
                "ses",
                region_name=settings.otp_aws_region,
                config=Config(connect_timeout=5, read_timeout=10, retries={"max_attempts": 0}),
            )
            client.send_email(
                Source=settings.otp_from_email,
                Destination={"ToAddresses": [target]},
                Message={
                    "Subject": {"Data": "COCO - Ma xac nhan"},
                    "Body": {"Text": {"Data": body}},
                },
            )
    except Exception as exc:
        raise APIError(
            503, "OTP_DELIVERY_FAILED", "Chưa gửi được mã. Vui lòng thử lại sau."
        ) from exc
