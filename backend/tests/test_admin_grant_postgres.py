import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import event, select
from sqlalchemy.exc import SQLAlchemyError
from test_checkout_postgres import checkout_db as checkout_db  # noqa: F401
from test_checkout_postgres import client_for
from test_checkout_postgres import world as world  # noqa: F401

from app.models import User
from app.services.admin_grant import AdminGrantError, AdminGrantService


def details(db, uid):
    with db.sessions() as s:
        row = s.get(User, uid)
        return row.email, row.password_hash, row.user_status, row.updated_at


def test_preview_readonly_grant_exact_account_and_repeat(world):
    cfg, db, r = world
    uid = r["buyers"][0]
    email, password, status, stamp = details(db, uid)
    statements = []

    def record(conn, cursor, statement, params, context, executemany):
        statements.append(statement)

    event.listen(db.engine, "before_cursor_execute", record)
    try:
        with db.sessions() as s:
            preview = AdminGrantService(s).run(" " + email.upper() + " ")
        assert preview["dry_run"] and not preview["changed"] and preview["user_role"] == "USER"
        assert preview["user_id"] == str(uid)
        assert any("SET TRANSACTION READ ONLY" in sql for sql in statements)
        assert not any("password_hash" in sql for sql in statements)
        assert not any(
            sql.lstrip().upper().startswith(("UPDATE", "INSERT", "DELETE")) for sql in statements
        )
    finally:
        event.remove(db.engine, "before_cursor_execute", record)
    with client_for(cfg, uid) as c:
        assert c.get("/api/v1/admin/users").status_code == 403
        with db.sessions() as s:
            result = AdminGrantService(s).run(email, apply=True, expected_user_id=uid)
        assert result["user_role"] == "ADMIN" and result["changed"] and not result["dry_run"]
        assert c.get("/api/v1/admin/users").status_code == 200
    after = details(db, uid)
    assert after[:3] == (email, password, status)
    with db.sessions() as s:
        result = AdminGrantService(s).run(email, apply=True, expected_user_id=uid)
    assert not result["changed"]
    assert details(db, uid) == after
    with db.sessions() as s:
        assert s.get(User, r["buyers"][1]).user_role == "USER"


@pytest.mark.parametrize("mode", ["missing", "locked", "mismatch", "no_expected"])
def test_fail_closed_without_creation_or_unblocking(world, mode):
    _, db, r = world
    uid = r["buyers"][0]
    email = details(db, uid)[0]
    if mode == "locked":
        with db.sessions.begin() as s:
            s.get(User, uid).user_status = "LOCKED"
    before = details(db, uid)
    with db.sessions() as s:
        with pytest.raises(AdminGrantError):
            AdminGrantService(s).run(
                "not-registered@example.com" if mode == "missing" else email,
                apply=True,
                expected_user_id=None
                if mode == "no_expected"
                else r["buyers"][1]
                if mode == "mismatch"
                else uid,
            )
    assert details(db, uid) == before
    with db.sessions() as s:
        assert s.get(User, uid).user_role == "USER"
        assert (
            s.scalar(select(User.user_id).where(User.email == "not-registered@example.com")) is None
        )


def test_grant_commit_failure_rolls_back(world):
    _, db, r = world
    uid = r["buyers"][0]
    email = details(db, uid)[0]

    def fail(session):
        raise SQLAlchemyError("private DSN")

    with db.sessions() as s:
        event.listen(s, "before_commit", fail)
        with pytest.raises(SQLAlchemyError):
            AdminGrantService(s).run(email, apply=True, expected_user_id=uid)
    with db.sessions() as s:
        assert s.get(User, uid).user_role == "USER"


def test_concurrent_grant_is_idempotent(world):
    _, db, r = world
    uid = r["buyers"][0]
    email = details(db, uid)[0]
    barrier = Barrier(2)

    def run(_):
        with db.sessions() as s:
            barrier.wait(timeout=10)
            return AdminGrantService(s).run(email, apply=True, expected_user_id=uid)["changed"]

    with ThreadPoolExecutor(2) as pool:
        assert sorted(pool.map(run, range(2))) == [False, True]


def test_real_cli_preview_and_apply_in_separate_process(world):
    cfg, db, r = world
    uid = r["buyers"][0]
    email = details(db, uid)[0]
    env = os.environ.copy()
    env.update(
        {
            "MARKETPLACE_ENVIRONMENT": "test",
            "MARKETPLACE_DB_HOST": cfg.db_host,
            "MARKETPLACE_DB_PORT": str(cfg.db_port),
            "MARKETPLACE_DB_NAME": "marketplace_test",
            "MARKETPLACE_DB_USER": cfg.db_user,
            "MARKETPLACE_DB_PASSWORD": cfg.db_password.get_secret_value(),
        }
    )
    for args, changed in [([], False), (["--apply", "--expected-user-id", str(uid)], True)]:
        result = subprocess.run(
            [sys.executable, "-m", "app.grant_admin", "--email", email, *args],
            env=env,
            capture_output=True,
            text=True,
            timeout=20,
        )
        assert result.returncode == 0
        value = json.loads(result.stdout)
        assert value["changed"] == changed and value["dry_run"] != changed
        assert "password_hash" not in result.stdout and result.stderr == ""
