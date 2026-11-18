from unittest.mock import Mock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.grant_admin import main


def test_apply_requires_expected_id_before_connecting(monkeypatch):
    database = Mock()
    monkeypatch.setattr("app.grant_admin.Database", database)
    with pytest.raises(SystemExit) as exc:
        main(["--email", "example@example.com", "--apply"])
    assert exc.value.code == 2
    database.assert_not_called()


def test_production_environment_is_rejected(monkeypatch, capsys):
    monkeypatch.setattr("app.grant_admin.Settings", lambda: Mock(environment="production"))
    database = Mock()
    monkeypatch.setattr("app.grant_admin.Database", database)
    assert main(["--email", "example@example.com"]) == 1
    assert "LOCAL_ONLY" in capsys.readouterr().err
    database.assert_not_called()


def test_database_error_does_not_expose_connection_details(monkeypatch, capsys):
    monkeypatch.setattr("app.grant_admin.Settings", lambda: Mock(environment="local"))
    monkeypatch.setattr(
        "app.grant_admin.Database", Mock(side_effect=SQLAlchemyError("private DSN"))
    )
    assert main(["--email", "example@example.com"]) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err.strip() == '{"error":"DATABASE_UNAVAILABLE"}'
