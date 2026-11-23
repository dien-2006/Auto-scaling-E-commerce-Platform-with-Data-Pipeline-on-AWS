from sqlalchemy import func

from app.core.errors import APIError
from app.models import ProductImage
from app.repositories.product_images import ProductImageRepository
from app.schemas.product_images import ImageCreate, ImagePatch, ImageUpload, SellerImage
from app.services.access import AccessPolicy
from app.services.seller_products import SellerProductService
from app.services.storage import ObjectStorage


class ProductImageService:
    def __init__(self, access: AccessPolicy, storage: ObjectStorage, product_id: int):
        seller = SellerProductService(access)
        self.product = seller.repository.owned(product_id, write=True)
        if self.product is None:
            raise APIError(404, "NOT_FOUND", "Không tìm thấy sản phẩm")
        self.storage = storage
        self.repository = ProductImageRepository(seller.session, product_id)
        self.session = seller.session

    def project(self, row: ProductImage):
        return SellerImage(
            product_image_id=str(row.product_image_id),
            product_id=str(row.product_id),
            image_key=row.image_key,
            url=self.storage.url(row.image_key),
            is_primary=row.is_primary,
            sort_order=row.sort_order,
        )

    def upload(self, payload: ImageUpload):
        return self.storage.issue(
            self.product.shop_id, self.product.product_id, payload.content_type, payload.size_bytes
        )

    def create(self, payload: ImageCreate):
        final = self.storage.final_key(
            payload.image_key, self.product.shop_id, self.product.product_id
        )
        if self.repository.by_key(final) is not None:
            raise APIError(409, "IMAGE_EXISTS", "Ảnh đã được liên kết, hãy tải lại danh sách ảnh")
        key = self.storage.finalize(
            payload.image_key, self.product.shop_id, self.product.product_id
        )
        if payload.is_primary:
            self.repository.unset_primary()
        row = ProductImage(
            product_id=self.product.product_id,
            image_key=key,
            is_primary=payload.is_primary,
            sort_order=payload.sort_order,
        )
        self.session.add(row)
        self.product.updated_at = func.now()
        self.session.flush()
        return self.project(row)

    def patch(self, image_id: int, payload: ImagePatch):
        row = self.repository.image(image_id)
        if row is None:
            raise APIError(404, "NOT_FOUND", "Không tìm thấy ảnh")
        if payload.is_primary:
            self.repository.unset_primary()
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, key, value)
        self.product.updated_at = func.now()
        self.session.flush()
        return self.project(row)

    def delete(self, image_id: int):
        row = self.repository.image(image_id)
        if row is None:
            raise APIError(404, "NOT_FOUND", "Không tìm thấy ảnh")
        self.session.delete(row)
        self.product.updated_at = func.now()
        self.session.flush()
