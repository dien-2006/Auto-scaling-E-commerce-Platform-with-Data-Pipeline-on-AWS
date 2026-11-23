"""Promote an E2E account only inside the runner's disposable test database."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from sqlalchemy import select, text  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.db.session import Database  # noqa: E402
from app.models import User  # noqa: E402

cfg = Settings()
if (cfg.environment, cfg.db_name, cfg.db_host) != ("test", "marketplace_test", "127.0.0.1"):
    raise RuntimeError("Requires isolated loopback marketplace_test")
if len(sys.argv) != 2 or not sys.argv[1].startswith("e2e-admin-"):
    raise RuntimeError("Requires runner-created admin email")
db = Database(cfg)
try:
    with db.sessions.begin() as session:
        assert session.scalar(text("SELECT current_database()")) == "marketplace_test"
        user = session.scalar(select(User).where(User.email == sys.argv[1]))
        assert user is not None
        user.user_role = "ADMIN"
finally:
    db.close()
