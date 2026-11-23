from app.core.errors import APIError
from app.repositories.catalog import CatalogRepository
from app.schemas.catalog import CategoryList, CategoryTree, ShopPublic, ShopResponse
from app.services.storage import ObjectStorage


class CatalogService:
    def __init__(self, repository: CatalogRepository, storage: ObjectStorage | None = None) -> None:
        self.repository = repository
        self.storage = storage

    def categories(self) -> CategoryList:
        rows = self.repository.active_categories()
        nodes = {
            row["category_id"]: CategoryTree(
                category_id=str(row["category_id"]),
                parent_category_id=(
                    str(row["parent_category_id"])
                    if row["parent_category_id"] is not None
                    else None
                ),
                category_name=row["category_name"],
                category_slug=row["category_slug"],
                is_active=True,
            )
            for row in rows
        }
        roots = []
        # Iterative linking preserves query order and does not recurse through malformed cycles.
        # Children of an inactive/missing ancestor remain unreachable from the public roots.
        for row in rows:
            node = nodes[row["category_id"]]
            if row["parent_category_id"] is None:
                roots.append(node)
            elif row["parent_category_id"] in nodes:
                nodes[row["parent_category_id"]].children.append(node)
        return CategoryList(items=roots)

    def shop(self, slug: str) -> ShopResponse:
        row = self.repository.public_shop(slug)
        if row is None:
            raise APIError(404, "NOT_FOUND", "Không tìm thấy tài nguyên")
        return ShopResponse(
            data=ShopPublic(
                shop_id=str(row["shop_id"]),
                shop_name=row["shop_name"],
                shop_slug=row["shop_slug"],
                description=row["description"],
                logo_url=self.storage.logo_url(row.get("logo_key")) if self.storage else None,
            )
        )
