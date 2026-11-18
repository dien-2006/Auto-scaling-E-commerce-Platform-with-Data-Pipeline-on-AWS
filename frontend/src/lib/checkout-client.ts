import { authMessages } from "@/lib/auth-contract";
import {
  orderFrom,
  type CheckoutIntent,
  type CheckoutOrder,
} from "@/lib/checkout-contract";

export class CheckoutFailure extends Error {
  constructor(
    public code: string,
    public repairAllowed = false,
  ) {
    super(
      (
        {
          COUPON_INVALID: "Mã giảm giá không hợp lệ, đã hết hạn hoặc hết lượt.",
          COUPON_SCOPE: "Mã không đúng loại hoặc không thuộc shop đã chọn.",
          QUOTE_REQUIRED:
            "Hãy chọn vận chuyển rồi áp dụng và tính lại tổng tiền.",
          SHIPPING_CHANGED: "Cước đã thay đổi. Hãy tính lại tổng tiền.",
          PAYMENT_NOT_CONFIGURED: "Phương thức thanh toán chưa được cấu hình.",
          COUPON_CHANGED:
            "Mức giảm đã thay đổi. Hãy tải lại và áp dụng mã lần nữa.",
          COUPON_MINIMUM: "Phần hàng áp dụng mã chưa đạt giá trị tối thiểu.",
          COUPON_CUSTOMER_LIMIT: "Bạn đã dùng hết lượt của mã giảm giá này.",
          PRICE_CHANGED:
            "Giá đã thay đổi. Hãy tải lại giỏ và xác nhận giá mới.",
          OUT_OF_STOCK:
            "Sản phẩm không đủ tồn kho. Hãy kiểm tra và sửa giỏ hàng.",
          CART_CHANGED:
            "Giỏ hàng hoặc trạng thái sản phẩm đã thay đổi. Vui lòng kiểm tra lại.",
          NOT_FOUND:
            "Địa chỉ hoặc sản phẩm không còn hợp lệ. Vui lòng kiểm tra lại.",
          FORBIDDEN:
            "Yêu cầu đặt hàng không được phép, chẳng hạn mua từ shop của chính bạn.",
        } as Record<string, string>
      )[code] ??
        authMessages[code] ??
        "Chưa kiểm tra được kết quả đặt hàng. Vui lòng kiểm tra kết nối và thử lại.",
    );
  }
}
export async function lookupCheckout(
  key: string,
): Promise<CheckoutOrder | null> {
  try {
    const response = await fetch("/api/v1/orders/checkout-status", {
      credentials: "same-origin",
      cache: "no-store",
      signal: AbortSignal.timeout(20000),
      headers: { "Idempotency-Key": key },
    });
    const payload = await response.json();
    if (!response.ok)
      throw new CheckoutFailure(
        typeof payload?.error?.code === "string"
          ? payload.error.code
          : "UNAVAILABLE",
      );
    if (response.status !== 200 || !payload || !Object.hasOwn(payload, "data"))
      throw new CheckoutFailure("UNAVAILABLE");
    if (payload.data === null) return null;
    const order = orderFrom(payload.data);
    if (!order) throw new CheckoutFailure("UNAVAILABLE");
    return order;
  } catch (error) {
    if (error instanceof CheckoutFailure) throw error;
    throw new CheckoutFailure("UNAVAILABLE");
  }
}
export async function submitCheckout(
  intent: CheckoutIntent,
): Promise<{ order: CheckoutOrder; replayed: boolean }> {
  try {
    const csrfResponse = await fetch("/api/v1/auth/csrf", {
      credentials: "same-origin",
      cache: "no-store",
      signal: AbortSignal.timeout(20000),
    });
    const csrf = await csrfResponse.json();
    if (!csrfResponse.ok)
      throw new CheckoutFailure(
        typeof csrf?.error?.code === "string" ? csrf.error.code : "UNAVAILABLE",
      );
    if (typeof csrf?.data?.csrf_token !== "string")
      throw new CheckoutFailure("UNAVAILABLE");
    const response = await fetch("/api/v1/orders/checkout", {
      method: "POST",
      credentials: "same-origin",
      cache: "no-store",
      signal: AbortSignal.timeout(25000),
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrf.data.csrf_token,
        "Idempotency-Key": intent.key,
      },
      body: JSON.stringify(intent.payload),
    });
    const payload = await response.json();
    if (!response.ok) {
      const code =
        typeof payload?.error?.code === "string"
          ? payload.error.code
          : "UNAVAILABLE";
      const repair =
        [400, 403, 404, 409, 422].includes(response.status) &&
        [
          "PRICE_CHANGED",
          "COUPON_INVALID",
          "COUPON_SCOPE",
          "QUOTE_REQUIRED",
          "SHIPPING_CHANGED",
          "COUPON_CHANGED",
          "COUPON_MINIMUM",
          "COUPON_CUSTOMER_LIMIT",
          "OUT_OF_STOCK",
          "CART_CHANGED",
          "NOT_FOUND",
          "FORBIDDEN",
          "VALIDATION_ERROR",
          "INVALID_REQUEST",
        ].includes(code);
      throw new CheckoutFailure(code, repair);
    }
    if (![200, 201].includes(response.status))
      throw new CheckoutFailure("UNAVAILABLE");
    const order = orderFrom(payload?.data);
    if (!order) throw new CheckoutFailure("UNAVAILABLE");
    return { order, replayed: response.status === 200 };
  } catch (error) {
    if (error instanceof CheckoutFailure) throw error;
    throw new CheckoutFailure("UNAVAILABLE");
  }
}
