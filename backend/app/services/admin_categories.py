from sqlalchemy.exc import IntegrityError

from app.core.errors import APIError
from app.db.locks import lock_category_tree_exclusive
from app.repositories.admin_categories import AdminCategoryRepository
from app.schemas.catalog import CategoryList, CategoryTree

# The existing public client accepts depths 0..99. Keep all trees renderable there.
MAX_CATEGORY_DEPTH = 100


def validate_tree(parents):
    depths = {}
    for start in parents:
        path, seen, node = [], set(), start
        while node is not None and node not in depths:
            if node not in parents:
                raise APIError(
                    409, "INVALID_CATEGORY_TREE", "Cây danh mục có liên kết không hợp lệ"
                )
            if node in seen:
                raise APIError(
                    409, "CATEGORY_CYCLE", "Danh mục cha không được là chính nó hoặc danh mục con"
                )
            seen.add(node)
            path.append(node)
            node = parents[node]
        depth = depths.get(node, 0)
        for current in reversed(path):
            depth += 1
            if depth > MAX_CATEGORY_DEPTH:
                raise APIError(422, "CATEGORY_TOO_DEEP", "Cây danh mục không được vượt quá 100 cấp")
            depths[current] = depth


def node(row):
    return CategoryTree(
        category_id=str(row.category_id),
        parent_category_id=str(row.parent_category_id)
        if row.parent_category_id is not None
        else None,
        category_name=row.category_name,
        category_slug=row.category_slug,
        is_active=row.is_active,
    )


class AdminCategoryService:
    def __init__(self, access):
        access.admin()
        if access.repository.write:
            # User -> exclusive tree advisory lock. Checkout and catalog writes use shared.
            lock_category_tree_exclusive(access.repository.session)
        self.repository = AdminCategoryRepository(access.repository.session)

    def list(self):
        rows = self.repository.rows()
        validate_tree({r.category_id: r.parent_category_id for r in rows})
        nodes = {r.category_id: node(r) for r in rows}
        roots = []
        for row in rows:
            if row.parent_category_id is None:
                roots.append(nodes[row.category_id])
            else:
                nodes[row.parent_category_id].children.append(nodes[row.category_id])
        return CategoryList(items=roots)

    def write(self, payload, category_id=None):
        # Read only after the exclusive lock, so concurrent reparents see the last commit.
        rows = self.repository.rows()
        by_id = {row.category_id: row for row in rows}
        if category_id is not None and category_id not in by_id:
            raise APIError(404, "NOT_FOUND", "Không tìm thấy danh mục")
        values = payload.model_dump(exclude_unset=category_id is not None)
        if "category_slug" in values and any(
            r.category_slug == values["category_slug"] and r.category_id != category_id
            for r in rows
        ):
            raise APIError(409, "SLUG_EXISTS", "Đường dẫn danh mục đã được sử dụng")
        parent = values.get(
            "parent_category_id",
            by_id[category_id].parent_category_id if category_id is not None else None,
        )
        if parent is not None and parent not in by_id:
            raise APIError(422, "INVALID_PARENT", "Không tìm thấy danh mục cha")
        parents = {r.category_id: r.parent_category_id for r in rows}
        parents[category_id if category_id is not None else 0] = parent
        validate_tree(parents)
        if category_id is None:
            row = self.repository.add(values)
        else:
            row = by_id[category_id]
            for field, value in values.items():
                setattr(row, field, value)
        try:
            self.repository.flush()
        except IntegrityError as exc:
            # The slug unique constraint is the final guard; other integrity failures stay503.
            if (
                getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
                == "categories_category_slug_key"
            ):
                raise APIError(409, "SLUG_EXISTS", "Đường dẫn danh mục đã được sử dụng") from exc
            raise
        return node(row)
