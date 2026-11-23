from decimal import Decimal

from app.core.errors import APIError
from app.models import CartItem
from app.repositories.cart import CartRepository
from app.schemas.cart import CartData, CartLine, CartShop, UnavailableReason
from app.services.access import AccessPolicy
from app.services.storage import ObjectStorage


def unavailable(row, buyer_id: int, quantity: int) -> UnavailableReason | None:
    if not row["is_active"]:
        return "HIDDEN_PRODUCT"
    if row["shop_status"] != "APPROVED":
        return "SHOP_UNAVAILABLE"
    if row["visible_category_id"] is None:
        return "CATEGORY_UNAVAILABLE"
    if row["owner_user_id"] == buyer_id:
        return "SELF_PURCHASE"
    stock = row["available_quantity"]
    if stock is None:
        return "MISSING_INVENTORY"
    if stock == 0:
        return "OUT_OF_STOCK"
    if stock < quantity:
        return "INSUFFICIENT_STOCK"
    return None


class CartService:
    def __init__(self, access: AccessPolicy, storage: ObjectStorage | None = None):
        self.storage = storage
        self.repository = CartRepository(access.repository.session, access.buyer().user_id)

    def snapshot(self) -> CartData:
        shops: dict[int, CartShop] = {}
        total = Decimal("0.00")
        for row in self.repository.lines():
            reason = unavailable(row, self.repository.user_id, row["quantity"])
            line_total = row["price"] * row["quantity"]
            shop_id = row["shop_id"]
            if shop_id not in shops:
                shops[shop_id] = CartShop(
                    shop_id=str(shop_id),
                    shop_name=row["shop_name"],
                    shop_slug=row["shop_slug"],
                    items=[],
                    subtotal=Decimal("0.00"),
                )
            shops[shop_id].items.append(
                CartLine(
                    cart_item_id=str(row["cart_item_id"]),
                    product_id=str(row["product_id"]),
                    product_name=row["product_name"],
                    primary_image_url=self.storage.url(row["primary_image_key"])
                    if self.storage
                    else None,
                    quantity=row["quantity"],
                    unit_price=row["price"],
                    line_total=line_total,
                    available_quantity=row["available_quantity"] or 0,
                    is_available=reason is None,
                    unavailable_reason=reason,
                )
            )
            shops[shop_id].subtotal += line_total
            total += line_total
        return CartData(shops=list(shops.values()), total_amount=total)

    def _validate(self, product_id: int, quantity: int) -> None:
        row = self.repository.product(product_id)
        if row is None:
            raise APIError(404, "NOT_FOUND", "Không tìm thấy sản phẩm")
        reason = unavailable(row, self.repository.user_id, quantity)
        if reason == "SELF_PURCHASE":
            raise APIError(403, "FORBIDDEN", "Không thể mua sản phẩm từ gian hàng của chính bạn")
        if reason in {"HIDDEN_PRODUCT", "SHOP_UNAVAILABLE", "CATEGORY_UNAVAILABLE"}:
            raise APIError(404, "NOT_FOUND", "Không tìm thấy sản phẩm đang bán")
        if reason is not None:
            raise APIError(409, "OUT_OF_STOCK", "Sản phẩm không đủ tồn kho")

    def add(self, product_id: int, quantity: int) -> CartData:
        cart = self.repository.lock_cart(create=True)
        assert cart is not None
        item = self.repository.item(cart.cart_id, product_id=product_id)
        target = (item.quantity if item else 0) + quantity
        if target > 2147483647:
            raise APIError(409, "CART_CHANGED", "Số lượng vượt giới hạn cho phép")
        self._validate(product_id, target)
        if item is None:
            self.repository.session.add(
                CartItem(cart_id=cart.cart_id, product_id=product_id, quantity=target)
            )
        else:
            item.quantity = target
        self.repository.session.flush()
        return self.snapshot()

    def update(self, item_id: int, quantity: int) -> CartData:
        item = self._owned_item(item_id)
        self._validate(item.product_id, quantity)
        item.quantity = quantity
        self.repository.session.flush()
        return self.snapshot()

    def delete(self, item_id: int) -> None:
        self.repository.session.delete(self._owned_item(item_id))
        self.repository.session.flush()

    def _owned_item(self, item_id: int) -> CartItem:
        cart = self.repository.lock_cart()
        item = self.repository.item(cart.cart_id, item_id=item_id) if cart else None
        if item is None:
            raise APIError(404, "NOT_FOUND", "Không tìm thấy sản phẩm trong giỏ")
        return item
