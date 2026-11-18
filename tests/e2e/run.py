"""Run isolated browser journey after frontend production build.
Requires Docker postgres:16, backend uv environment, Node24 and Playwright.
No existing DB, root .env or production volume is used by child services.
"""

import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "backend"))
import jwt  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.db.session import Database  # noqa: E402

docker = os.environ.get("E2E_DOCKER", "docker")
node = os.environ.get("E2E_NODE", "node")


def cli(*args):
    return subprocess.check_output([docker, *args], text=True, timeout=45).strip()


def port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def ready(url):
    for _ in range(100):
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(0.3)
    raise RuntimeError("Test server not ready")


name = "marketplace-p802e2e-" + uuid.uuid4().hex[:10]
env = os.environ.copy()
env["POSTGRES_PASSWORD"] = secrets.token_urlsafe(32)
created = False
backend = None
frontend = None
replica = None
shutdown_dir = tempfile.TemporaryDirectory(prefix="marketplace-test-shutdown-")
suite = os.environ.get("E2E_SUITE", "journey")
if suite not in {"journey", "performance", "k6", "crud", "options"}:
    raise ValueError("Unknown isolated test suite")
# Child services never inherit production DB/auth/storage or AWS settings.
for key in list(env):
    if key.startswith(("MARKETPLACE_", "AWS_")):
        env.pop(key)
env["AWS_EC2_METADATA_DISABLED"] = "true"
try:
    cli_env = subprocess.run(
        [
            docker,
            "run",
            "-d",
            "--name",
            name,
            "--label",
            "marketplace.test=p802e2e",
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
        text=True,
        timeout=60,
    )
    assert cli_env.returncode == 0, "Test DB launch failed"
    created = True
    for _ in range(60):
        result = subprocess.run(
            [
                docker,
                "exec",
                name,
                "pg_isready",
                "-U",
                "marketplace_test",
                "-d",
                "marketplace_test",
            ],
            capture_output=True,
            timeout=5,
        )
        if result.returncode == 0:
            break
        time.sleep(0.3)
    info = json.loads(cli("inspect", name))[0]
    db_port = int(info["NetworkSettings"]["Ports"]["5432/tcp"][0]["HostPort"])
    front_port, api_port = port(), port()
    origin = f"http://127.0.0.1:{front_port}"
    secret = secrets.token_urlsafe(48)
    cfg = Settings(
        environment="test",
        public_origin=origin,
        jwt_secret=secret,
        db_host="127.0.0.1",
        db_port=db_port,
        db_name="marketplace_test",
        db_user="marketplace_test",
        db_password=env["POSTGRES_PASSWORD"],
    )
    db = Database(cfg)
    for _ in range(80):
        try:
            with db.engine.connect() as probe:
                assert probe.scalar(text("SELECT current_database()")) == "marketplace_test"
            break
        except Exception:
            time.sleep(0.3)
    else:
        raise RuntimeError("Test database TCP not ready")
    # Versioned, reviewed source SQL is executed only in the newly owned tmpfs DB.
    schema = (root / "backend/tests/fixtures/marketplace_25.sql").read_text(encoding="utf-8")
    schema += "\n" + (
        root / "backend/migrations/proposals/20261115_checkout_options.sql"
    ).read_text(encoding="utf-8")
    assert (
        json.loads(cli("inspect", name))[0]["Config"]["Labels"].get("marketplace.test") == "p802e2e"
    )
    initialized = subprocess.run(
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
        input=schema,
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert initialized.returncode == 0, "25-table isolated SQL initialization failed"
    with db.engine.connect() as connection:
        assert (
            connection.scalar(
                text(
                    "SELECT count(*) FROM information_schema.tables "
                    "WHERE table_schema='marketplace' AND table_type='BASE TABLE'"
                )
            )
            == 25
        )
    db.close()
    env.update(
        {
            "MARKETPLACE_ENVIRONMENT": "test",
            "MARKETPLACE_PUBLIC_ORIGIN": origin,
            "MARKETPLACE_JWT_SECRET": secret,
            "MARKETPLACE_DB_HOST": "127.0.0.1",
            "MARKETPLACE_DB_PORT": str(db_port),
            "MARKETPLACE_DB_NAME": "marketplace_test",
            "MARKETPLACE_DB_USER": "marketplace_test",
            "MARKETPLACE_DB_PASSWORD": env["POSTGRES_PASSWORD"],
            "INTERNAL_API_URL": f"http://127.0.0.1:{api_port}",
            "AUTH_E2E_URL": origin,
            "EXPIRED_TOKEN": jwt.encode(
                {"sub": "1", "iat": 1, "exp": 901, "iss": "marketplace", "aud": "marketplace-web"},
                secret,
                algorithm="HS256",
            ),
        }
    )
    env["CART_TEST_PYTHON"] = sys.executable
    if suite == "options":
        env.update(
            {
                "MARKETPLACE_CHECKOUT_OPTIONS_ENABLED": "true",
                "MARKETPLACE_BANK_NAME": "E2E TEST BANK",
                "MARKETPLACE_BANK_ACCOUNT_NUMBER": "TEST-ONLY-123",
                "MARKETPLACE_BANK_ACCOUNT_HOLDER": "E2E COCO ONLY",
            }
        )
    backend = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:create_app",
            "--factory",
            "--host",
            "127.0.0.1",
            "--port",
            str(api_port),
            "--no-access-log",
        ],
        cwd=root / "backend",
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    ready(f"http://127.0.0.1:{api_port}/health/ready")
    if suite == "performance":
        replica_port = port()
        stop_file = Path(shutdown_dir.name) / "stop"
        replica_env = env | {
            "PERF_REPLICA_PORT": str(replica_port),
            "PERF_STOP_FILE": str(stop_file),
        }
        replica = subprocess.Popen(
            [sys.executable, str(root / "tests/performance/serve.py")],
            cwd=root / "backend",
            env=replica_env | {"PYTHONPATH": str(root / "backend")},
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        ready(f"http://127.0.0.1:{replica_port}/health/ready")
        env["PERF_REPLICAS"] = json.dumps(
            [f"http://127.0.0.1:{api_port}", f"http://127.0.0.1:{replica_port}"]
        )
        result = subprocess.run(
            [sys.executable, str(root / "tests/performance/probe.py")],
            env=env,
            timeout=180,
        )
        assert result.returncode == 0, "Performance/replica checks failed"
        stop_file.touch()
        assert replica.wait(timeout=15) == 0, "Replica graceful shutdown failed"
        ready(f"http://127.0.0.1:{api_port}/health/ready")
        print("PASS replica graceful Uvicorn shutdown; other backend remains ready")
        # Fault injection only against the owned tmpfs test container.
        assert (
            json.loads(cli("inspect", name))[0]["Config"]["Labels"].get("marketplace.test")
            == "p802e2e"
        )
        cli("stop", "--time", "2", name)
        with urllib.request.urlopen(f"http://127.0.0.1:{api_port}/health/live", timeout=10) as live:
            assert live.status == 200
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{api_port}/health/ready", timeout=15)
        except urllib.error.HTTPError as error:
            assert error.code == 503
        else:
            raise AssertionError("Readiness must fail when test database is unavailable")
        print("PASS test DB outage: live200, readiness503")
    else:
        frontend = subprocess.Popen(
            [
                node,
                "node_modules/next/dist/bin/next",
                "start",
                "--hostname",
                "0.0.0.0" if suite == "k6" else "127.0.0.1",
                "--port",
                str(front_port),
            ],
            cwd=root / "frontend",
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        ready(origin + "/dang-nhap")
        if suite == "k6":
            image = os.environ.get(
                "K6_IMAGE",
                "grafana/k6@sha256:3d8e5c7f1d53ec59408c2ffbd9943602a0985ffcbd4a2430ec00f3ffca89796e",
            )
            target = f"http://host.docker.internal:{front_port}"
            result = subprocess.run(
                [
                    docker,
                    "run",
                    "--rm",
                    "--name",
                    name + "-k6",
                    "--label",
                    "marketplace.test=p802e2e",
                    "--mount",
                    f"type=bind,source={root / 'tests/k6'},target=/scripts,readonly",
                    image,
                    "run",
                    "-e",
                    f"BASE_URL={target}",
                    "-e",
                    f"PUBLIC_ORIGIN={origin}",
                    "-e",
                    "TEST_ENV=isolated",
                    "/scripts/web-smoke.js",
                ],
                env=env,
                timeout=120,
            )
        else:
            script = (
                "checkout-options.cjs"
                if suite == "options"
                else "seller-crud.cjs"
                if suite == "crud"
                else "journey.cjs"
            )
            result = subprocess.run([node, str(root / "tests/e2e" / script)], env=env, timeout=300)
        assert result.returncode == 0, "Browser test failed"
finally:
    for child in [frontend, replica, backend]:
        if child is not None and child.poll() is None:
            child.terminate()
            child.wait(timeout=15)
    if created:
        info = json.loads(cli("inspect", name))[0]
        assert info["Config"]["Labels"].get("marketplace.test") == "p802e2e"
        cli("rm", "-f", name)
    print("Cleaned only owned test processes/container; no production DB volume or .env used")
    shutdown_dir.cleanup()
