from datetime import UTC

from app.schemas.products import PublicProductImage
from app.schemas.seller_products import SellerProduct
from app.services.products import summary


def management_products(rows, image_rows, storage):
    images = {}
    for image in image_rows:
        images.setdefault(image["product_id"], []).append(
            PublicProductImage(
                product_image_id=str(image["product_image_id"]),
                is_primary=image["is_primary"],
                sort_order=image["sort_order"],
                url=storage.url(image["image_key"]) if storage else None,
            )
        )
    return [
        SellerProduct(
            **summary(row, storage).model_dump(),
            description=row["description"],
            sku=row["sku"],
            images=images.get(row["product_id"], []),
            available_quantity=row["available_quantity"],
            is_active=row["is_active"],
            created_at=row["created_at"].astimezone(UTC),
            updated_at=row["updated_at"].astimezone(UTC),
        )
        for row in rows
    ]
