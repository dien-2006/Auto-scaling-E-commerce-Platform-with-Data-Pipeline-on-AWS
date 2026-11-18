"""Operator-only local CLI. No HTTP endpoint, account creation or schema changes."""

import argparse
import json
import sys

from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings
from app.db.session import Database
from app.services.admin_grant import AdminGrantError, AdminGrantService


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Preview or grant ADMIN to an existing ACTIVE user"
    )
    parser.add_argument("--email", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--expected-user-id", type=int)
    args = parser.parse_args(argv)
    if args.apply and (
        args.expected_user_id is None or not 0 < args.expected_user_id <= 9223372036854775807
    ):
        parser.error("--apply requires --expected-user-id from the preview")
    database = None
    try:
        settings = Settings()
        if settings.environment not in {"local", "test"}:
            raise AdminGrantError("LOCAL_ONLY")
        database = Database(settings)
        if database.sessions is None:
            raise AdminGrantError("DATABASE_NOT_CONFIGURED")
        with database.sessions() as session:
            result = AdminGrantService(session).run(
                args.email, apply=args.apply, expected_user_id=args.expected_user_id
            )
        print(json.dumps(result, ensure_ascii=True))
        return 0
    except AdminGrantError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1
    except ValidationError:
        print('{"error":"INVALID_INPUT_OR_CONFIGURATION"}', file=sys.stderr)
        return 1
    except SQLAlchemyError:
        print('{"error":"DATABASE_UNAVAILABLE"}', file=sys.stderr)
        return 1
    finally:
        if database is not None:
            database.close()


if __name__ == "__main__":
    sys.exit(main())
