from datetime import UTC

from app.core.errors import APIError
from app.repositories.inventory import InventoryRepository
from app.schemas.inventory import InventoryData
from app.services.access import AccessPolicy
from app.services.seller_products import SellerProductService


class InventoryService:
    def __init__(self, access: AccessPolicy, product_id: int):
        seller = SellerProductService(access)
        # WriteAccess user -> shared category -> shop -> product -> inventory.
        product = seller.repository.owned(product_id, write=access.repository.write)
        if product is None:
            raise APIError(404, "NOT_FOUND", "Không tìm thấy sản phẩm")
        self.product_id = product_id
        self.repository = InventoryRepository(seller.session)
        self.inventory = self.repository.get(product_id, write=access.repository.write)
        if self.inventory is None:
            raise APIError(409, "INVENTORY_UNAVAILABLE", "Sản phẩm chưa có bản ghi tồn kho")

    def get(self) -> InventoryData:
        return InventoryData(
            product_id=str(self.product_id),
            quantity=self.inventory.quantity,
            updated_at=self.inventory.updated_at.astimezone(UTC),
        )

    def adjust(self, expected: int, delta: int) -> InventoryData:
        if self.inventory.quantity != expected:
            raise APIError(
                409,
                "STALE_INVENTORY",
                "Tồn kho đã thay đổi, hãy tải lại và xác nhận điều chỉnh mới",
            )
        quantity = expected + delta
        if not 0 <= quantity <= 2147483647:
            raise APIError(409, "INVALID_STOCK", "Số lượng sau điều chỉnh phải từ 0 đến 2147483647")
        row = self.repository.adjust(self.product_id, expected, delta)
        if row is None:
            raise APIError(
                409,
                "STALE_INVENTORY",
                "Tồn kho đã thay đổi, hãy tải lại và xác nhận điều chỉnh mới",
            )
        return InventoryData(
            product_id=str(self.product_id),
            quantity=row["quantity"],
            updated_at=row["updated_at"].astimezone(UTC),
        )
