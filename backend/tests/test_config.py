import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_read_environment(monkeypatch):
    monkeypatch.setenv("MARKETPLACE_ENVIRONMENT", "test")
    monkeypatch.setenv("MARKETPLACE_LOG_LEVEL", "WARNING")
    settings = Settings()
    assert settings.environment == "test"
    assert settings.log_level == "WARNING"


@pytest.mark.parametrize(
    "values",
    [
        {"environment": "unknown"},
        {"log_level": "verbose"},
        {"public_origin": "*"},
        {"public_origin": "https://user:password@example.com"},
        {"public_origin": "https://example.com/path"},
        {"public_origin": "https://example.com?token=secret"},
        {"public_origin": "https://example.com#fragment"},
        {"environment": "production", "public_origin": "http://example.com"},
    ],
)
def test_invalid_settings_fail_early(values):
    with pytest.raises(ValidationError):
        Settings(**values)


def test_production_accepts_exact_https_origin():
    settings = Settings(environment="production", public_origin="https://example.com")
    assert settings.public_origin.host == "example.com"
