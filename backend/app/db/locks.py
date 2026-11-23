"""Stable database-wide lock namespace shared with future category mutations."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

# Checkout takes shared; category tree/status mutations must take exclusive
# pg_advisory_xact_lock with these same two keys, before locking shop/product.
CATEGORY_LOCK_NAMESPACE = 731921
CATEGORY_LOCK_ID = 1


def lock_category_tree(session: Session) -> None:
    session.execute(
        select(func.pg_advisory_xact_lock_shared(CATEGORY_LOCK_NAMESPACE, CATEGORY_LOCK_ID))
    )


def lock_category_tree_exclusive(session: Session) -> None:
    session.execute(select(func.pg_advisory_xact_lock(CATEGORY_LOCK_NAMESPACE, CATEGORY_LOCK_ID)))
