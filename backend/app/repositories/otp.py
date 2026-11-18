"""Existing email accounts only; OTP proofs live in Redis, no extra SQL tables."""

from sqlalchemy import func, select, text

from app.models import User


class OTPRepository:
    def __init__(self, session):
        self.session = session

    def lock(self, key):
        self.session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key,0))"), {"key": key}
        )

    def user(self, channel, target, lock=False, registration=False):
        if channel != "EMAIL":
            raise ValueError("Only email OTP is supported")
        statement = select(User).where(func.lower(User.email) == target)
        if lock:
            statement = statement.with_for_update()
        return self.session.scalar(statement)

    def by_id(self, user_id):
        return self.session.scalar(select(User).where(User.user_id == user_id).with_for_update())
