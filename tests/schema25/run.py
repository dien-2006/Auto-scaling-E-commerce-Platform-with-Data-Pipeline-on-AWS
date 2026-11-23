"""Full backend suite against the reviewed 25-table SQL in disposable PostgreSQL16."""

import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4

root = Path(__file__).resolve().parents[2]
docker = os.environ.get("E2E_DOCKER", "docker")
name = "marketplace-schema25-" + uuid4().hex[:10]
label = "schema25-reference"
env = {k: v for k, v in os.environ.items() if not k.startswith(("MARKETPLACE_", "AWS_"))}
if os.environ.get("MARKETPLACE_LEGACY_SCHEMA") == "true":
    env["MARKETPLACE_LEGACY_SCHEMA"] = "true"
env["POSTGRES_PASSWORD"] = secrets.token_urlsafe(32)
created = False


def cli(*args):
    return subprocess.check_output([docker, *args], text=True, timeout=45).strip()


try:
    launched = subprocess.run(
        [
            docker,
            "run",
            "-d",
            "--name",
            name,
            "--label",
            "marketplace.test=" + label,
            "--network",
            "bridge",
            "--tmpfs",
            "/var/lib/postgresql/data:rw,size=512m",
            "-p",
            "127.0.0.1::5432",
            "-e",
            "POSTGRES_PASSWORD",
            "-e",
            "POSTGRES_USER=marketplace_test",
            "-e",
            "POSTGRES_DB=marketplace_test",
            "postgres:16",
        ],
        env=env,
        capture_output=True,
        timeout=60,
    )
    assert launched.returncode == 0, "Isolated test DB launch failed"
    created = True
    for _ in range(100):
        if (
            subprocess.run(
                [
                    docker,
                    "exec",
                    name,
                    "pg_isready",
                    "-h",
                    "127.0.0.1",
                    "-U",
                    "marketplace_test",
                ],
                capture_output=True,
            ).returncode
            == 0
        ):
            break
        time.sleep(0.2)
    sql = (root / "backend/tests/fixtures/marketplace_25.sql").read_text(encoding="utf-8")
    if os.environ.get("MARKETPLACE_LEGACY_SCHEMA") != "true":
        sql += "\n" + (
            root / "backend/migrations/proposals/20261115_checkout_options.sql"
        ).read_text(encoding="utf-8")
    result = subprocess.run(
        [
            docker,
            "exec",
            "-i",
            name,
            "psql",
            "-U",
            "marketplace_test",
            "-d",
            "marketplace_test",
            "-v",
            "ON_ERROR_STOP=1",
        ],
        input=sql,
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == 0, "Reviewed 25-table SQL failed in isolated DB"
    port = json.loads(cli("inspect", name))[0]["NetworkSettings"]["Ports"]["5432/tcp"][0][
        "HostPort"
    ]
    for prefix in ["MARKETPLACE_TEST_DB_", "MARKETPLACE_AUDIT_DB_"]:
        env.update(
            {
                prefix + "HOST": "127.0.0.1",
                prefix + "PORT": port,
                prefix + "NAME": "marketplace_test",
                prefix + "USER": "marketplace_test",
                prefix + "PASSWORD": env["POSTGRES_PASSWORD"],
            }
        )
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--tb=short"],
        cwd=root / "backend",
        env=env,
    )
    assert result.returncode == 0, "Backend/reference schema tests failed"
finally:
    if created:
        assert (
            json.loads(cli("inspect", name))[0]["Config"]["Labels"].get("marketplace.test") == label
        )
        cli("rm", "-f", name)
    print("Removed only owned schema25 test DB; production database never used")
