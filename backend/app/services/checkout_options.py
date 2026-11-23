from decimal import Decimal

from app.core.config import Settings
from app.core.errors import APIError
from app.schemas.checkout_options import AppliedCoupon, OptionsQuote, ShippingCost
from app.services.shopping import CouponService

SHIPPING = {"STANDARD": "Tiêu chuẩn", "EXPRESS": "Nhanh", "COCOEXPRESS": "COCO Express"}
PAYMENTS = {
    "COD": "Thanh toán khi nhận hàng",
    "BANK_TRANSFER": "Chuyển khoản ngân hàng",
    "MOMO": "Ví MoMo",
    "VNPAY": "VNPay",
}


class CheckoutOptionsService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def enabled(self):
        if not self.settings.checkout_options_enabled:
            raise APIError(
                503, "CHECKOUT_OPTIONS_NOT_CONFIGURED", "Lựa chọn mới chưa được kích hoạt"
            )

    def bank(self):
        values = [
            self.settings.bank_name,
            self.settings.bank_account_number,
            self.settings.bank_account_holder,
        ]
        return all(v and v.strip() for v in values)

    def fee(self, method):
        return {
            "STANDARD": self.settings.shipping_standard_fee,
            "EXPRESS": self.settings.shipping_express_fee,
            "COCOEXPRESS": self.settings.shipping_cocoexpress_fee,
        }[method]

    def options(self):
        return {
            "enabled": self.settings.checkout_options_enabled,
            "bank": {
                "name": self.settings.bank_name,
                "account_number": self.settings.bank_account_number,
                "account_holder": self.settings.bank_account_holder,
            }
            if self.bank()
            else None,
            "shipping_methods": [
                {
                    "code": k,
                    "label": label,
                    "fee_per_shop": self.fee(k),
                    "enabled": self.fee(k) is not None,
                    "reason": None if self.fee(k) is not None else "Chưa cấu hình mức cước",
                }
                for k, label in SHIPPING.items()
            ],
            "payment_methods": [
                {
                    "code": k,
                    "label": label,
                    "enabled": k == "COD" or (k == "BANK_TRANSFER" and self.bank()),
                    "reason": None
                    if k == "COD" or (k == "BANK_TRANSFER" and self.bank())
                    else "Chưa cấu hình chuyển khoản"
                    if k == "BANK_TRANSFER"
                    else "Chưa tích hợp cổng thanh toán",
                }
                for k, label in PAYMENTS.items()
            ],
        }

    def payment(self, method):
        if method == "COD":
            return
        self.enabled()
        if method != "BANK_TRANSFER" or not self.bank():
            raise APIError(503, "PAYMENT_NOT_CONFIGURED", "Phương thức thanh toán chưa sẵn sàng")

    def shipping(self, method, shop_ids, discount=Decimal("0.00")):
        self.enabled()
        fee = self.fee(method)
        if fee is None:
            raise APIError(503, "SHIPPING_NOT_CONFIGURED", "Chưa cấu hình cước vận chuyển")
        fee = fee.quantize(Decimal("0.01"))
        gross = fee * len(shop_ids)
        if gross > Decimal("999999999999.99") or not 0 <= discount <= gross:
            raise APIError(409, "CART_CHANGED", "Cước vận chuyển vượt giới hạn")
        share, extra = divmod(int(discount * 100), len(shop_ids))
        costs = [
            ShippingCost(
                shop_id=str(sid), method=method, fee=fee - Decimal(share + (i < extra)) / 100
            )
            for i, sid in enumerate(sorted(shop_ids))
        ]
        return costs, gross - discount

    def quote(self, payload, coupon_repository, buyer_id):
        self.enabled()
        self.payment(payload.payment_method)
        coupons = CouponService(coupon_repository)
        subtotals = coupons.purchase_subtotals(
            buyer_id, payload.direct_item, payload.selected_product_ids
        )
        _, gross_shipping = self.shipping(payload.shipping_method, subtotals)
        applied, discount, shipping_discount = coupons.stack(
            payload, subtotals, buyer_id, gross_shipping
        )
        shipping, shipping_fee = self.shipping(
            payload.shipping_method, subtotals, shipping_discount
        )
        subtotal = sum(subtotals.values(), Decimal("0.00"))
        total = subtotal - discount + shipping_fee
        if total > Decimal("999999999999.99"):
            raise APIError(409, "CART_CHANGED", "Tổng tiền vượt giới hạn")
        return OptionsQuote(
            subtotal=subtotal,
            discount_amount=discount,
            shipping_fee=shipping_fee,
            shipping_discount_amount=shipping_discount,
            total_amount=total,
            shipping=shipping,
            applied_coupons=[
                AppliedCoupon(
                    code=a[2],
                    shop_id=str(a[1]) if a[1] else None,
                    discount_amount=a[3],
                    coupon_type=a[4],
                )
                for a in applied
            ],
        )
