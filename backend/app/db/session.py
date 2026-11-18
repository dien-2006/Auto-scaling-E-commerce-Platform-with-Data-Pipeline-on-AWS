from collections.abc import Generator

from fastapi import Request
from sqlalchemy import URL, create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.core.errors import APIError
from app.db.base import Base
from app.models import marketplace as _models  # noqa: F401 -- register mappings, never create tables
from app.services.otp_store import OTPStore


class Database:
    def __init__(self, settings: Settings) -> None:
        self.otp_enabled = settings.otp_enabled
        self.otp_store = OTPStore(settings)
        self.engine: Engine | None = None
        self.sessions: sessionmaker[Session] | None = None
        if settings.db_name is None:
            return
        url = URL.create(
            "postgresql+psycopg",
            username=settings.db_user,
            password=settings.db_password.get_secret_value(),
            host=settings.db_host,
            port=settings.db_port,
            database=settings.db_name,
        )
        self.engine = create_engine(
            url,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_timeout=settings.db_pool_timeout,
            pool_pre_ping=True,
            pool_recycle=1800,
            echo=False,
            hide_parameters=True,
            connect_args={
                "connect_timeout": settings.db_connect_timeout,
                "options": f"-c statement_timeout={settings.db_statement_timeout_ms}",
                "application_name": "marketplace_backend",
            },
        )
        self.sessions = sessionmaker(self.engine, expire_on_commit=False, autoflush=False)

    def ready(self) -> bool:
        if self.engine is None:
            return False
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SET TRANSACTION READ ONLY"))
                if connection.scalar(text("SELECT 1")) != 1:
                    return False
                names = [table.fullname for table in Base.metadata.sorted_tables]
                found = connection.scalar(
                    text(
                        "SELECT count(*) FROM unnest(CAST(:names AS text[])) AS name "
                        "WHERE to_regclass(name) IS NOT NULL"
                    ),
                    {"names": names},
                )
                if found != len(names):
                    return False
                if self.otp_enabled and not self.otp_store.ready():
                    return False
                # Context exit rolls back the read transaction and returns the connection.
                return True
        except SQLAlchemyError:
            return False

    def close(self) -> None:
        self.otp_store.close()
        if self.engine is not None:
            self.engine.dispose()


def get_session(request: Request) -> Generator[Session]:
    database: Database = request.app.state.database
    if database.sessions is None:
        raise APIError(503, "DEPENDENCY_UNAVAILABLE", "Dịch vụ chưa sẵn sàng")
    with database.sessions() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        # No implicit commit: service code must use an explicit transaction boundary.
