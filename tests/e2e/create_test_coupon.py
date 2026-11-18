"""Create a coupon only in the runner-owned loopback test database."""

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from sqlalchemy import insert, text  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.db.session import Database  # noqa: E402
from app.models.extensions import coupons  # noqa: E402

cfg = Settings()
if (cfg.environment, cfg.db_name, cfg.db_host) != (
    "test",
    "marketplace_test",
    "127.0.0.1",
):
    raise RuntimeError("Requires isolated loopback marketplace_test")
db = Database(cfg)
try:
    with db.sessions.begin() as session:
        assert session.scalar(text("SELECT current_database()")) == "marketplace_test"
        session.execute(
            insert(coupons).values(
                code="E2E10",
                discount_percent="10",
                usage_limit=10,
                starts_at=datetime.now(UTC) - timedelta(days=1),
                expires_at=datetime.now(UTC) + timedelta(days=1),
            )
        )
finally:
    db.close()
