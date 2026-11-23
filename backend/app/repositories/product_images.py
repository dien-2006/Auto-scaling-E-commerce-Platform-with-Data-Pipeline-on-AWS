from sqlalchemy import select, update

from app.models import ProductImage


class ProductImageRepository:
    def __init__(self, session, product_id: int):
        self.session = session
        self.product_id = product_id

    def image(self, image_id: int):
        return self.session.scalar(
            select(ProductImage).where(
                ProductImage.product_id == self.product_id,
                ProductImage.product_image_id == image_id,
            )
        )

    def by_key(self, key: str):
        return self.session.scalar(
            select(ProductImage).where(
                ProductImage.product_id == self.product_id, ProductImage.image_key == key
            )
        )

    def unset_primary(self):
        self.session.execute(
            update(ProductImage)
            .where(ProductImage.product_id == self.product_id, ProductImage.is_primary.is_(True))
            .values(is_primary=False)
        )
        self.session.flush()
