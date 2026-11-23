from sqlalchemy.engine import RowMapping

from app.core.errors import APIError
from app.repositories.products import ProductRepository
from app.schemas.products import (
    ProductDetail,
    ProductList,
    ProductQuery,
    ProductResponse,
    ProductShop,
    ProductSummary,
    PublicProductImage,
)
from app.services.storage import ObjectStorage


def summary(row: RowMapping, storage: ObjectStorage | None = None) -> ProductSummary:
    return ProductSummary(
        product_id=str(row["product_id"]),
        product_name=row["product_name"],
        price=row["price"],
        category_id=str(row["category_id"]),
        in_stock=row["available_quantity"] > 0,
        primary_image_url=storage.url(row.get("primary_image_key")) if storage else None,
        shop=ProductShop(
            shop_id=str(row["shop_id"]),
            shop_name=row["shop_name"],
            shop_slug=row["shop_slug"],
        ),
    )


class ProductService:
    def __init__(self, repository: ProductRepository, storage: ObjectStorage | None = None) -> None:
        self.repository = repository
        self.storage = storage

    def list(self, query: ProductQuery) -> ProductList:
        rows, total = self.repository.list(query)
        return ProductList(
            items=[summary(row, self.storage) for row in rows],
            page=query.page,
            page_size=query.page_size,
            total=total,
        )

    def detail(self, product_id: int) -> ProductResponse:
        row = self.repository.detail(product_id)
        if row is None:
            raise APIError(404, "NOT_FOUND", "Không tìm thấy tài nguyên")
        images = self.repository.images(product_id)
        return ProductResponse(
            data=ProductDetail(
                **summary(row, self.storage).model_dump(),
                description=row["description"],
                sku=row["sku"],
                available_quantity=row["available_quantity"],
                images=[
                    PublicProductImage(
                        product_image_id=str(image["product_image_id"]),
                        is_primary=image["is_primary"],
                        sort_order=image["sort_order"],
                        url=self.storage.url(image.get("image_key")) if self.storage else None,
                    )
                    for image in images
                ],
            )
        )
