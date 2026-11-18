from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError

from app.core.errors import APIError
from app.db.locks import lock_category_tree
from app.models import Inventory, Product
from app.repositories.seller_products import SellerProductRepository
from app.schemas.seller_products import (
    ProductCreate,
    ProductPatch,
    SellerProduct,
    SellerProductList,
    SellerQuery,
)
from app.services.access import AccessPolicy
from app.services.product_projection import management_products
from app.services.storage import ObjectStorage


class SellerProductService:
    def __init__(self, access: AccessPolicy, storage: ObjectStorage | None = None):
        self.storage = storage
        self.access = access
        self.session = access.repository.session
        # User was locked by WriteAccess. Category must precede shop/product.
        if access.repository.write:
            lock_category_tree(self.session)
        shop = access.selling_shop()
        self.repository = SellerProductRepository(self.session, int(shop.shop_id))

    def project(self, rows):
        return management_products(
            rows, self.repository.images([row["product_id"] for row in rows]), self.storage
        )

    def detail(self, product_id: int) -> SellerProduct:
        row = self.repository.detail(product_id)
        if row is None:
            raise APIError(404, "NOT_FOUND", "Không tìm thấy sản phẩm")
        return self.project([row])[0]

    def list(self, query: SellerQuery) -> SellerProductList:
        rows, total = self.repository.list(query)
        return SellerProductList(
            items=self.project(rows),
            total=total,
            page=query.page,
            page_size=query.page_size,
            image_upload_enabled=bool(self.storage and self.storage.settings.s3_bucket),
        )

    def category(self, category_id: int):
        if not self.repository.valid_category(category_id):
            raise APIError(422, "INVALID_CATEGORY", "Danh mục không hợp lệ hoặc đã bị ẩn")

    def flush(self):
        try:
            self.session.flush()
        except IntegrityError as exc:
            if (
                getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
                == "uq_products_shop_sku"
            ):
                raise APIError(409, "SKU_EXISTS", "SKU đã tồn tại trong gian hàng") from exc
            raise

    def create(self, payload: ProductCreate) -> SellerProduct:
        self.category(payload.category_id)
        product = Product(
            shop_id=self.repository.shop_id, **payload.model_dump(exclude={"initial_quantity"})
        )
        self.session.add(product)
        self.flush()
        self.session.add(
            Inventory(product_id=product.product_id, quantity=payload.initial_quantity)
        )
        self.flush()
        return self.detail(product.product_id)

    def patch(self, product_id: int, payload: ProductPatch) -> SellerProduct:
        product = self.repository.owned(product_id, write=True)
        if product is None:
            raise APIError(404, "NOT_FOUND", "Không tìm thấy sản phẩm")
        if payload.category_id is not None:
            self.category(payload.category_id)
        for name, value in payload.model_dump(exclude_unset=True).items():
            setattr(product, name, value)
        product.updated_at = func.now()
        self.flush()
        return self.detail(product_id)

    def hide(self, product_id: int) -> SellerProduct:
        product = self.repository.owned(product_id, write=True)
        if product is None:
            raise APIError(404, "NOT_FOUND", "Không tìm thấy sản phẩm")
        if product.is_active:
            product.is_active = False
            product.updated_at = func.now()
            self.flush()
        return self.detail(product_id)

    def delete(self, product_id: int) -> None:
        product = self.repository.owned(product_id, write=True)
        if product is None:
            raise APIError(404, "NOT_FOUND", "Không tìm thấy sản phẩm")
        self.session.scalar(
            select(Inventory).where(Inventory.product_id == product_id).with_for_update()
        )
        try:
            self.session.execute(delete(Inventory).where(Inventory.product_id == product_id))
            self.session.delete(product)
            self.session.flush()
        except IntegrityError as exc:
            if getattr(exc.orig, "sqlstate", None) == "23503":
                raise APIError(
                    409,
                    "PRODUCT_IN_USE",
                    "Sản phẩm có giỏ hàng, đơn hoặc lịch sử liên quan; hãy dùng Ẩn sản phẩm",
                ) from exc
            raise
