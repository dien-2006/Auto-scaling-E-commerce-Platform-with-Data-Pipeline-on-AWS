from app.core.errors import APIError
from app.db.locks import lock_category_tree
from app.repositories.admin_products import AdminProductRepository
from app.schemas.admin_products import AdminProductList
from app.services.product_projection import management_products


class AdminProductService:
    def __init__(self, access, storage):
        access.admin()
        self.storage = storage
        self.session = access.repository.session
        if access.repository.write:
            lock_category_tree(self.session)
        self.repository = AdminProductRepository(self.session)

    def project(self, rows):
        return management_products(
            rows, self.repository.images([r["product_id"] for r in rows]), self.storage
        )

    def list(self, query):
        rows, total = self.repository.list(query)
        return AdminProductList(
            items=self.project(rows), total=total, page=query.page, page_size=query.page_size
        )

    def hide(self, product_id):
        row = self.repository.lock(product_id)
        if row is None:
            raise APIError(404, "NOT_FOUND", "Không tìm thấy sản phẩm")
        if row["is_active"]:
            self.repository.hide(product_id)
        return self.project([self.repository.detail(product_id)])[0]
