"""Opt-in metadata audit against an existing database, strictly READ ONLY, no DDL or rows."""

import os
import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import CheckConstraint, UniqueConstraint, inspect, text

from app.core.config import Settings
from app.db.base import Base
from app.db.session import Database
from app.main import create_app


def canonical(expression):
    if expression is None:
        return None
    value = str(expression).lower()
    value = re.sub(r"::(?:character varying|text|numeric)(?:\[\])?", "", value)
    value = re.sub(r"= any\s*\(array\[(.*?)\]\)", r"in (\1)", value)
    value = re.sub(r"in\s*\(('(?:[^']|'')*')\)", r"= \1", value)
    return re.sub(r"[\s()]", "", value)


@pytest.fixture
def connection():
    if not os.environ.get("MARKETPLACE_AUDIT_DB_NAME"):
        pytest.skip("Set MARKETPLACE_AUDIT_DB_* to opt into read-only existing schema audit")
    settings = Settings(
        environment="test",
        db_host=os.environ.get("MARKETPLACE_AUDIT_DB_HOST", "127.0.0.1"),
        db_port=int(os.environ.get("MARKETPLACE_AUDIT_DB_PORT", "5432")),
        db_name=os.environ["MARKETPLACE_AUDIT_DB_NAME"],
        db_user=os.environ["MARKETPLACE_AUDIT_DB_USER"],
        db_password=os.environ["MARKETPLACE_AUDIT_DB_PASSWORD"],
    )
    database = Database(settings)
    try:
        with database.engine.connect() as connection:
            connection.execute(text("SET TRANSACTION READ ONLY"))
            assert connection.scalar(text("SHOW transaction_read_only")) == "on"
            yield connection
            connection.rollback()
        assert database.engine.pool.checkedout() == 0
    finally:
        database.close()


def test_existing_columns_defaults_identity_and_constraints(connection):
    inspector = inspect(connection)
    assert set(inspector.get_table_names(schema="marketplace")) == {
        table.name for table in Base.metadata.tables.values()
    }
    for table in Base.metadata.sorted_tables:
        columns = inspector.get_columns(table.name, schema="marketplace")
        assert [column["name"] for column in columns] == list(table.columns.keys())
        for actual, expected in zip(columns, table.columns, strict=True):
            assert actual["type"].compile(dialect=connection.dialect) == expected.type.compile(
                dialect=connection.dialect
            ), (table.name, expected.name, "type")
            assert actual["nullable"] == expected.nullable, (table.name, expected.name, "nullable")
            if expected.identity is not None:
                assert actual["identity"]["always"]
            else:
                assert not actual.get("identity")
            default = expected.server_default
            expected_default = (
                str(default.arg) if default is not None and hasattr(default, "arg") else None
            )
            assert canonical(actual["default"]) == canonical(expected_default), (
                table.name,
                expected.name,
                "default",
            )
        assert inspector.get_pk_constraint(table.name, schema="marketplace")[
            "constrained_columns"
        ] == list(table.primary_key.columns.keys())
        actual_unique = {
            row["name"]: row["column_names"]
            for row in inspector.get_unique_constraints(table.name, schema="marketplace")
        }
        expected_unique = {
            c.name: list(c.columns.keys())
            for c in table.constraints
            if isinstance(c, UniqueConstraint)
        }
        assert actual_unique == expected_unique, (table.name, "unique")
        actual_checks = {
            row["name"]: canonical(row["sqltext"])
            for row in inspector.get_check_constraints(table.name, schema="marketplace")
        }
        expected_checks = {
            c.name: canonical(c.sqltext)
            for c in table.constraints
            if isinstance(c, CheckConstraint)
        }
        assert actual_checks == expected_checks, (table.name, "checks")
        actual_fks = {
            row["name"]: row for row in inspector.get_foreign_keys(table.name, schema="marketplace")
        }
        assert set(actual_fks) == {fk.name for fk in table.foreign_key_constraints}
        for fk in table.foreign_key_constraints:
            actual = actual_fks[fk.name]
            assert actual["constrained_columns"] == list(fk.columns.keys())
            assert actual["referred_schema"] == "marketplace"
            assert actual["referred_table"] == fk.referred_table.name
            assert actual["referred_columns"] == [element.column.name for element in fk.elements]
            assert actual["options"].get("ondelete") == fk.ondelete


def test_existing_explicit_indexes(connection):
    inspector = inspect(connection)
    for table in Base.metadata.sorted_tables:
        actual = {
            row["name"]: row
            for row in inspector.get_indexes(table.name, schema="marketplace")
            if not row.get("duplicates_constraint")
        }
        assert set(actual) == {index.name for index in table.indexes}, table.name
        for index in table.indexes:
            row = actual[index.name]
            assert row["unique"] == index.unique
            expressions = row.get("expressions", row["column_names"])
            sorting = row.get("column_sorting", {})
            expressions = [
                expr + (" DESC" if "desc" in sorting.get(expr, ()) else "") for expr in expressions
            ]
            expected = [
                canonical(
                    str(expr.compile(dialect=connection.dialect)).replace(
                        "marketplace." + table.name + ".", ""
                    )
                )
                for expr in index.expressions
            ]
            assert [canonical(expr) for expr in expressions] == expected, (table.name, index.name)
            assert canonical(row["dialect_options"].get("postgresql_where")) == canonical(
                index.dialect_options["postgresql"].get("where")
            )


def test_real_database_readiness(connection):
    url = connection.engine.url
    app = create_app(
        Settings(
            environment="test",
            db_host=url.host,
            db_port=url.port,
            db_name=url.database,
            db_user=url.username,
            db_password=url.password,
        )
    )
    with TestClient(app) as client:
        assert client.get("/health/ready").json() == {"status": "ready"}
        assert client.get("/health/live").status_code == 200
