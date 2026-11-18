from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import event, func, select
from sqlalchemy.exc import SQLAlchemyError
from test_checkout_postgres import checkout, client_for, csrf, payload
from test_checkout_postgres import checkout_db as checkout_db  # noqa: F401
from test_checkout_postgres import world as world  # noqa: F401

from app.core.errors import APIError
from app.db.session import get_session
from app.models import Category, Inventory, Order, Product, Shop, User
from app.services.admin_categories import validate_tree


@pytest.fixture
def category_world(world):
    cfg, db, r = world
    with db.sessions.begin() as s:
        for uid in r["buyers"]:
            s.get(User, uid).user_role = "ADMIN"
        owners = [s.get(Shop, sid).owner_user_id for sid in r["shops"]]
        child = s.get(Product, r["products"][0]).category_id
    return cfg, db, r, owners, child


def create(c, name="Category", parent=None, slug=None, active=True):
    return c.post(
        "/api/v1/admin/categories",
        headers=csrf(c),
        json={
            "category_name": name,
            "category_slug": slug or uuid4().hex,
            "parent_category_id": str(parent) if parent else None,
            "is_active": active,
        },
    )


def patch(c, cid, **values):
    return c.patch(f"/api/v1/admin/categories/{cid}", headers=csrf(c), json=values)


def flat(tree):
    rows = []
    pending = list(tree)
    while pending:
        row = pending.pop()
        rows.append(row)
        pending.extend(row["children"])
    return {r["category_id"]: r for r in rows}


def test_create_edit_reparent_inactive_tree_readonly_and_unique_slug(category_world):
    cfg, db, r, _, _ = category_world
    with client_for(cfg, r["buyers"][0]) as c:
        parent = create(c, " Root ", active=False)
        assert parent.status_code == 201
        root = parent.json()["data"]
        assert root["category_name"] == "Root"
        cid = create(c, "Child", root["category_id"]).json()["data"]["category_id"]
        response = c.get("/api/v1/admin/categories")
        assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
        tree = flat(response.json()["items"])
        assert tree[cid]["parent_category_id"] == root["category_id"] and tree[cid]["is_active"]
        assert cid not in flat(c.get("/api/v1/categories").json()["items"])
        assert patch(c, cid, parent_category_id=None, category_name="Renamed").status_code == 200
        assert cid in flat(c.get("/api/v1/categories").json()["items"])
        assert create(c, slug=root["category_slug"]).status_code == 409
        assert patch(c, cid, category_slug=root["category_slug"]).status_code == 409
        assert patch(c, 9223372036854775807, is_active=False).status_code == 404
        assert patch(c, cid, parent_category_id="9223372036854775807").status_code == 422
        assert patch(c, cid, is_active=True).status_code == 200
        statements = []

        def record(conn, cursor, statement, params, context, executemany):
            statements.append(statement)

        def observed():
            with db.sessions() as s:
                yield s

        c.app.dependency_overrides[get_session] = observed
        event.listen(db.engine, "before_cursor_execute", record)
        try:
            assert c.get("/api/v1/admin/categories").status_code == 200
            assert any("SET TRANSACTION READ ONLY" in sql for sql in statements)
            assert sum("FROM marketplace.categories" in sql for sql in statements) == 1
        finally:
            event.remove(db.engine, "before_cursor_execute", record)


def test_self_and_multinode_cycle_with_parent_inactive(category_world):
    cfg, _, r, _, _ = category_world
    with client_for(cfg, r["buyers"][0]) as c:
        a = create(c).json()["data"]["category_id"]
        b = create(c, parent=a, active=False).json()["data"]["category_id"]
        child = create(c, parent=b).json()["data"]["category_id"]
        for parent in [a, b, child]:
            result = patch(c, a, parent_category_id=parent)
            assert result.status_code == 409 and result.json()["error"]["code"] == "CATEGORY_CYCLE"
        assert patch(c, child, parent_category_id=a).status_code == 200
        assert patch(c, b, parent_category_id=None).status_code == 200


def test_concurrent_reparent_different_admins_cannot_form_cycle(category_world):
    cfg, db, r, _, _ = category_world
    with client_for(cfg, r["buyers"][0]) as c:
        ids = [create(c).json()["data"]["category_id"] for _ in range(2)]
    barrier = Barrier(2)

    def run(index):
        with client_for(cfg, r["buyers"][index]) as c:
            headers = csrf(c)
            barrier.wait(timeout=10)
            return c.patch(
                f"/api/v1/admin/categories/{ids[index]}",
                headers=headers,
                json={"parent_category_id": ids[1 - index]},
            ).status_code

    with ThreadPoolExecutor(2) as pool:
        assert sorted(pool.map(run, range(2))) == [200, 409]
    with db.sessions() as s:
        parents = {i: s.get(Category, int(i)).parent_category_id for i in ids}
        assert sum(value is None for value in parents.values()) == 1


def test_concurrent_duplicate_slug_one_creation(category_world):
    cfg, db, r, _, _ = category_world
    slug = uuid4().hex
    barrier = Barrier(2)

    def run(index):
        with client_for(cfg, r["buyers"][index]) as c:
            barrier.wait(timeout=10)
            return create(c, slug=slug).status_code

    with ThreadPoolExecutor(2) as pool:
        assert sorted(pool.map(run, range(2))) == [201, 409]
    with db.sessions() as s:
        assert (
            s.scalar(
                select(func.count()).select_from(Category).where(Category.category_slug == slug)
            )
            == 1
        )


def test_disable_parent_preserves_children_product_stock_and_old_order(category_world):
    cfg, db, r, owners, child = category_world
    with db.sessions.begin() as session:
        session.get(User, r["buyers"][0]).user_role = "USER"
    with client_for(cfg, r["buyers"][0]) as buyer:
        order = checkout(buyer, payload(r)).json()["data"]
    with client_for(cfg, r["buyers"][1]) as admin:
        assert patch(admin, r["parent"], is_active=False).status_code == 200
        public = flat(admin.get("/api/v1/categories").json()["items"])
        assert str(child) not in public and str(r["parent"]) not in public
        assert str(child) in flat(admin.get("/api/v1/admin/categories").json()["items"])
        assert admin.get(f"/api/v1/products/{r['products'][0]}").status_code == 404
        assert checkout(admin, payload(r, 1)).status_code == 403
        assert patch(admin, r["parent"], is_active=True).status_code == 200
        assert admin.get(f"/api/v1/products/{r['products'][0]}").status_code == 200
    with client_for(cfg, r["buyers"][0]) as buyer:
        assert buyer.get(f"/api/v1/orders/{order['order_id']}").json()["data"] == order
    with db.sessions() as s:
        assert s.get(Category, child).is_active
        assert s.get(Product, r["products"][0]).category_id == child
        assert s.get(Inventory, r["products"][0]).quantity == 9


def test_disable_races_checkout_without_partial_order(category_world):
    cfg, db, r, _, _ = category_world
    with db.sessions.begin() as session:
        session.get(User, r["buyers"][0]).user_role = "USER"
    barrier = Barrier(2)

    def run(index):
        with client_for(cfg, r["buyers"][index]) as c:
            barrier.wait(timeout=10)
            return (
                checkout(c, payload(r)) if index == 0 else patch(c, r["parent"], is_active=False)
            ).status_code

    with ThreadPoolExecutor(2) as pool:
        ordered, disabled = list(pool.map(run, range(2)))
    assert ordered in [201, 409] and disabled == 200
    with db.sessions() as s:
        assert not s.get(Category, r["parent"]).is_active
        assert s.scalar(
            select(func.count()).select_from(Order).where(Order.buyer_user_id == r["buyers"][0])
        ) == (1 if ordered == 201 else 0)
        for pid in r["products"]:
            assert s.get(Inventory, pid).quantity == (9 if ordered == 201 else 10)


def test_authorization_csrf_role_revocation_and_no_delete(category_world):
    cfg, db, r, owners, _ = category_world
    with client_for(cfg, owners[0]) as seller:
        assert seller.get("/api/v1/admin/categories").status_code == 403
        assert create(seller).status_code == 403
        assert patch(seller, r["parent"], is_active=False).status_code == 403
    with client_for(cfg, r["buyers"][0]) as admin:
        assert admin.post("/api/v1/admin/categories", json={}).status_code == 403
        assert (
            admin.delete(f"/api/v1/admin/categories/{r['parent']}", headers=csrf(admin)).status_code
            == 405
        )
        with db.sessions.begin() as s:
            s.get(User, r["buyers"][0]).user_role = "USER"
        assert admin.get("/api/v1/admin/categories").status_code == 403
        assert create(admin).status_code == 403
        with db.sessions.begin() as s:
            u = s.get(User, r["buyers"][0])
            u.user_role = "ADMIN"
            u.user_status = "LOCKED"
        assert patch(admin, r["parent"], is_active=False).status_code == 403
        admin.cookies.clear()
        assert admin.get("/api/v1/admin/categories").status_code == 401


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"category_name": None},
        {"category_slug": None},
        {"is_active": None},
        {"is_active": "false"},
        {"parent_category_id": True},
        {"parent_category_id": 1.5},
        {"category_slug": "UPPER"},
        {"category_name": " "},
        {"category_name": "a" * 121},
        {"category_slug": "a" * 141},
        {"owner_user_id": "1"},
    ],
)
def test_patch_validation(category_world, body):
    cfg, _, r, _, _ = category_world
    with client_for(cfg, r["buyers"][0]) as c:
        assert (
            c.patch(
                f"/api/v1/admin/categories/{r['parent']}", headers=csrf(c), json=body
            ).status_code
            == 422
        )


def test_commit_failure_rolls_back_create_and_edit(category_world):
    cfg, db, r, _, _ = category_world
    slug = uuid4().hex

    def fail(session):
        raise SQLAlchemyError("private DSN")

    def broken():
        with db.sessions() as s:
            event.listen(s, "before_commit", fail)
            yield s

    with client_for(cfg, r["buyers"][0]) as c:
        c.app.dependency_overrides[get_session] = broken
        assert create(c, slug=slug).status_code == 503
        result = patch(c, r["parent"], is_active=False)
        assert result.status_code == 503 and "private DSN" not in result.text
    with db.sessions() as s:
        assert s.scalar(select(Category).where(Category.category_slug == slug)) is None
        assert s.get(Category, r["parent"]).is_active


def test_depth_bound_matches_existing_public_client():
    validate_tree({i: i - 1 if i > 1 else None for i in range(1, 101)})
    with pytest.raises(APIError) as error:
        validate_tree({i: i - 1 if i > 1 else None for i in range(1, 102)})
    assert error.value.code == "CATEGORY_TOO_DEEP"
