from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.exc import OperationalError

from app.core.config import Settings
from app.db.base import Base
from app.db.session import Database, get_session
from app.main import create_app


def test_mapping_is_schema_qualified_and_complete():
    tables = Base.metadata.sorted_tables
    assert len(tables) == 25
    assert sum(len(table.columns) for table in tables) == 184
    assert all(table.schema == "marketplace" for table in tables)
    assert sum(len(table.indexes) for table in tables) == 28
    assert len(Base.registry.mappers) == 12


@pytest.mark.parametrize(
    "values",
    [
        {"db_name": "db"},
        {"db_pool_size": 0},
        {"db_max_overflow": -1},
        {"db_connect_timeout": 0},
        {"db_port": 0},
        {"db_name": "db", "db_user": "user", "db_password": ""},
    ],
)
def test_invalid_database_settings(values):
    with pytest.raises(ValidationError):
        Settings(**values)


def test_engine_is_lazy_bounded_and_password_is_hidden():
    settings = Settings(db_name="db", db_user="user", db_password="secret-with-@:/symbols")
    database = Database(settings)
    try:
        assert database.engine.url.host == "postgres"
        assert database.engine.pool.size() == 5
        assert database.engine.pool.checkedout() == 0
        assert "secret-with" not in repr(database.engine)
        assert "secret-with" not in repr(settings)
    finally:
        database.close()


def test_invalid_configuration_does_not_expose_password():
    with pytest.raises(ValidationError) as error:
        Settings(db_password="private-config-secret")
    assert "private-config-secret" not in str(error.value)


def test_readiness_success_failure_and_liveness_independence():
    app = create_app(Settings(environment="test"))
    with TestClient(app) as client:
        app.state.database.ready = MagicMock(return_value=True)
        assert client.get("/health/ready").json() == {"status": "ready"}
        app.state.database.ready = MagicMock(return_value=False)
        assert client.get("/health/ready").status_code == 503
        assert client.get("/health/live").status_code == 200


def test_readiness_checks_required_tables_and_sanitizes_connection_errors():
    database = Database(Settings())
    connection = MagicMock()
    connection.scalar.side_effect = [1, 25]
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value = connection
    database.engine = engine
    assert database.ready()
    connection.scalar.side_effect = [1, 0]
    assert not database.ready()
    engine.connect.side_effect = OperationalError("private-query", {}, Exception("private-secret"))
    assert not database.ready()


def test_session_cleanup_never_commits_implicitly_and_rolls_back_failure():
    session = MagicMock()
    factory = MagicMock()
    factory.return_value.__enter__.return_value = session
    request = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(database=SimpleNamespace(sessions=factory)))
    )
    dependency = get_session(request)
    assert next(dependency) is session
    with pytest.raises(RuntimeError):
        dependency.throw(RuntimeError("service failed"))
    session.rollback.assert_called_once()
    session.commit.assert_not_called()
    factory.return_value.__exit__.assert_called_once()
