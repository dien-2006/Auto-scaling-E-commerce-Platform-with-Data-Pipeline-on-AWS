from decimal import ROUND_HALF_UP, Decimal

from app.core.errors import APIError
from app.models import Product, Shop
from app.repositories.products import ProductRepository
from app.repositories.shopping import CouponRepository, ReviewRepository
from app.schemas.products import ProductQuery
from app.schemas.shopping import CouponQuote, ReviewCreate, ReviewData, ReviewPage


class CouponService:
    def __init__(self, repository: CouponRepository):
        self.repository = repository

    def calculate(
        self,
        code: str,
        subtotals: dict[int, Decimal],
        buyer_id: int,
        *,
        lock: bool = False,
        minimum_base: Decimal | None = None,
    ):
        row = self.repository.find(code, lock=lock)
        now = self.repository.now()
        if (
            not row
            or not row["is_active"]
            or not row["starts_at"] <= now < row["expires_at"]
            or row["used_count"] >= row["usage_limit"]
        ):
            raise APIError(409, "COUPON_INVALID", "Mã giảm giá không hợp lệ hoặc đã hết lượt")
        if self.repository.active_uses(row["coupon_id"], buyer_id) >= 1:
            raise APIError(409, "COUPON_CUSTOMER_LIMIT", "Bạn đã dùng hết lượt của mã giảm giá này")
        eligible = (
            sum(subtotals.values(), Decimal("0.00"))
            if row["shop_id"] is None
            else subtotals.get(row["shop_id"], Decimal("0.00"))
        )
        if (
            eligible <= 0
            or (eligible if minimum_base is None else minimum_base) < row["min_order_amount"]
        ):
            raise APIError(409, "COUPON_MINIMUM", "Đơn hàng chưa đáp ứng điều kiện của mã giảm giá")
        discount = min(
            eligible,
            (eligible * row["discount_percent"] / 100).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            ),
        )
        return row["coupon_id"], discount

    def cart_subtotals(self, buyer_id: int, selected_product_ids=None):
        rows = self.repository.cart(buyer_id)
        if selected_product_ids is not None:
            selected = set(selected_product_ids)
            rows = [row for row in rows if str(row["product_id"]) in selected]
            if len(rows) != len(selected) or len(selected) != len(selected_product_ids):
                raise APIError(409, "CART_CHANGED", "Sản phẩm đã chọn không còn trong giỏ")
        subtotals: dict[int, Decimal] = {}
        if not rows:
            raise APIError(409, "CART_CHANGED", "Giỏ hàng đang trống")
        for row in rows:
            if (
                not row["is_active"]
                or not row["visible"]
                or row["shop_status"] != "APPROVED"
                or row["owner_user_id"] == buyer_id
            ):
                raise APIError(409, "CART_CHANGED", "Có sản phẩm hiện không thể mua")
            subtotals[row["shop_id"]] = subtotals.get(row["shop_id"], Decimal("0.00")) + (
                row["price"] * row["quantity"]
            )
        return subtotals

    def purchase_subtotals(self, buyer_id: int, direct_item=None, selected_product_ids=None):
        if direct_item is None:
            subtotals = self.cart_subtotals(buyer_id, selected_product_ids)
        else:
            statement = ProductRepository(self.repository.session).public_statement(ProductQuery())
            row = (
                self.repository.session.execute(
                    statement.where(
                        Product.product_id == direct_item.product_id,
                        Shop.owner_user_id != buyer_id,
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None or row["available_quantity"] < direct_item.quantity:
                raise APIError(409, "CART_CHANGED", "Sản phẩm hiện không thể mua")
            if row["price"] != direct_item.expected_unit_price:
                raise APIError(409, "PRICE_CHANGED", "Giá đã thay đổi. Hãy tải lại sản phẩm")
            subtotals = {row["shop_id"]: row["price"] * direct_item.quantity}
        return subtotals

    def quote(self, code: str, buyer_id: int, direct_item=None, selected_product_ids=None):
        subtotals = self.purchase_subtotals(buyer_id, direct_item, selected_product_ids)
        row = self.repository.find(code)
        if row and row.get("coupon_type", "GOODS") != "GOODS":
            raise APIError(409, "COUPON_SCOPE", "Use the shipping coupon field")
        _, discount = self.calculate(code, subtotals, buyer_id)
        subtotal = sum(subtotals.values(), Decimal("0.00"))
        return CouponQuote(
            code=code, subtotal=subtotal, discount_amount=discount, total_amount=subtotal - discount
        )

    def stack(self, selection, subtotals, buyer_id, shipping_total, *, lock=False):
        codes = [c.code for c in selection.shop_coupons]
        codes += [c for c in [selection.coco_coupon_code, selection.shipping_coupon_code] if c]
        rows = self.repository.selected(codes, lock=lock) if codes else []
        by_code = {r["code"]: r for r in rows}
        if len(rows) != len(codes):
            raise APIError(409, "COUPON_INVALID", "Coupon not found")
        remaining = dict(subtotals)
        applied = []
        for choice in sorted(selection.shop_coupons, key=lambda c: c.shop_id):
            row = by_code[choice.code]
            if (
                row["shop_id"] != choice.shop_id
                or choice.shop_id not in subtotals
                or row.get("coupon_type", "GOODS") != "GOODS"
            ):
                raise APIError(409, "COUPON_SCOPE", "Coupon does not belong to this shop")
            cid, amount = self.calculate(choice.code, subtotals, buyer_id)
            remaining[choice.shop_id] -= amount
            applied.append((cid, choice.shop_id, choice.code, amount, "GOODS"))
        if selection.coco_coupon_code:
            row = by_code[selection.coco_coupon_code]
            if row["shop_id"] is not None or row.get("coupon_type", "GOODS") != "GOODS":
                raise APIError(409, "COUPON_SCOPE", "COCO goods coupon required")
            cid, amount = self.calculate(selection.coco_coupon_code, remaining, buyer_id)
            applied.append((cid, None, selection.coco_coupon_code, amount, "GOODS"))
        goods_discount = sum((a[3] for a in applied), Decimal("0.00"))
        shipping_discount = Decimal("0.00")
        if selection.shipping_coupon_code:
            row = by_code[selection.shipping_coupon_code]
            if row["shop_id"] is not None or row.get("coupon_type", "GOODS") != "SHIPPING":
                raise APIError(409, "COUPON_SCOPE", "COCO shipping coupon required")
            # Minimum spend is merchandise after goods discounts, never freight.
            goods_net = sum(subtotals.values(), Decimal("0.00")) - goods_discount
            if goods_net < row["min_order_amount"]:
                raise APIError(409, "COUPON_MINIMUM", "Minimum merchandise spend not met")
            cid, shipping_discount = self.calculate(
                selection.shipping_coupon_code,
                {0: shipping_total},
                buyer_id,
                minimum_base=goods_net,
            )
            applied.append(
                (cid, None, selection.shipping_coupon_code, shipping_discount, "SHIPPING")
            )
        return applied, goods_discount, shipping_discount


def review_data(row):
    return ReviewData(
        review_id=str(row["review_id"]),
        rating=row["rating"],
        comment=row["comment"],
        created_at=row["created_at"],
    )


class ReviewService:
    def __init__(self, repository: ReviewRepository):
        self.repository = repository

    def owned(self, item_id: int, buyer_id: int, *, lock: bool = False):
        row = self.repository.owned_line(item_id, buyer_id, lock=lock)
        if row is None:
            raise APIError(404, "NOT_FOUND", "Không tìm thấy sản phẩm trong đơn mua")
        if row["order_status"] != "COMPLETED":
            raise APIError(409, "REVIEW_NOT_ELIGIBLE", "Chỉ đánh giá khi đơn shop đã hoàn thành")
        return row

    def mine(self, item_id: int, buyer_id: int):
        self.owned(item_id, buyer_id)
        row = self.repository.existing(item_id)
        return review_data(row) if row else None

    def create(self, item_id: int, buyer_id: int, payload: ReviewCreate):
        line = self.owned(item_id, buyer_id, lock=True)
        if self.repository.existing(item_id):
            raise APIError(409, "REVIEW_EXISTS", "Bạn đã đánh giá sản phẩm trong đơn này")
        return review_data(
            self.repository.create(
                item_id, line["product_id"], buyer_id, payload.rating, payload.comment or None
            )
        )

    def public(self, product_id: int, page: int, page_size: int):
        if ProductRepository(self.repository.session).detail(product_id) is None:
            raise APIError(404, "NOT_FOUND", "Không tìm thấy sản phẩm")
        rows, total, average = self.repository.public(product_id, page, page_size)
        return ReviewPage(
            items=[review_data(row) for row in rows],
            total=total,
            average_rating=average,
            page=page,
            page_size=page_size,
        )
