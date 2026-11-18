from pydantic import EmailStr, TypeAdapter
from sqlalchemy import text

from app.repositories.admin_grant import AdminGrantRepository


class AdminGrantError(ValueError):
    pass


class AdminGrantService:
    def __init__(self, session):
        self.session = session
        self.repository = AdminGrantRepository(session)

    def run(self, email, *, apply=False, expected_user_id=None):
        if not isinstance(email, str) or len(email.strip()) > 255:
            raise AdminGrantError("INVALID_EMAIL")
        email = str(TypeAdapter(EmailStr).validate_python(email.strip().lower()))
        if apply and (
            type(expected_user_id) is not int or not 0 < expected_user_id <= 9223372036854775807
        ):
            raise AdminGrantError("EXPECTED_USER_REQUIRED")
        with self.session.begin():
            if not apply:
                self.session.execute(text("SET TRANSACTION READ ONLY"))
            row = self.repository.find(email, write=apply)
            if row is None:
                raise AdminGrantError("NOT_FOUND")
            if apply and row["user_id"] != expected_user_id:
                raise AdminGrantError("IDENTITY_CHANGED")
            if row["user_status"] != "ACTIVE":
                raise AdminGrantError("USER_LOCKED")
            changed = False
            if apply and row["user_role"] != "ADMIN":
                if not self.repository.grant(row["user_id"]):
                    raise AdminGrantError("STATE_CHANGED")
                changed = True
            result = {
                "user_id": str(row["user_id"]),
                "email": row["email"],
                "full_name": row["full_name"],
                "user_status": row["user_status"],
                "user_role": "ADMIN" if apply else row["user_role"],
                "changed": changed,
                "dry_run": not apply,
            }
        # The caller receives success only after COMMIT, including repeated no-ops.
        return result
