export type ProductReview = {
  review_id: string;
  rating: number;
  comment: string | null;
  created_at: string;
};
export type ReviewPage = {
  items: ProductReview[];
  total: number;
  average_rating: string | null;
  page: number;
  page_size: number;
};
export type CouponQuote = {
  code: string;
  subtotal: string;
  discount_amount: string;
  total_amount: string;
};
const record = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);
const money = (v: unknown): v is string =>
  typeof v === "string" && /^(0|[1-9]\d{0,11})(\.\d{1,2})?$/.test(v);
const id = (v: string) =>
  /^[1-9]\d{0,18}$/.test(v) && BigInt(v) <= BigInt("9223372036854775807");
function review(v: unknown): v is ProductReview {
  return (
    record(v) &&
    typeof v.review_id === "string" &&
    id(v.review_id) &&
    typeof v.rating === "number" &&
    Number.isInteger(v.rating) &&
    v.rating >= 1 &&
    v.rating <= 5 &&
    (v.comment === null || typeof v.comment === "string") &&
    typeof v.created_at === "string" &&
    Number.isFinite(Date.parse(v.created_at))
  );
}
const messages: Record<string, string> = {
  COUPON_INVALID: "Mã không hợp lệ, hết hạn hoặc hết lượt.",
  COUPON_MINIMUM: "Phần hàng áp dụng mã chưa đạt giá trị tối thiểu.",
  COUPON_CUSTOMER_LIMIT: "Bạn đã dùng hết lượt của mã này.",
  CART_CHANGED: "Giỏ hàng đã thay đổi. Hãy tải lại.",
  REVIEW_EXISTS: "Bạn đã đánh giá. Hãy tải lại để xem đánh giá đã lưu.",
  REVIEW_NOT_ELIGIBLE: "Chỉ đánh giá sau khi đơn shop hoàn thành.",
  NOT_FOUND: "Không tìm thấy sản phẩm hoặc đơn mua.",
  COMMERCE_FORBIDDEN: "Tài khoản Admin không thực hiện mua hàng hoặc đánh giá.",
  UNAUTHENTICATED: "Vui lòng đăng nhập lại.",
  INVALID_TOKEN: "Phiên đăng nhập đã hết hạn.",
};
async function request(path: string, body?: unknown): Promise<unknown> {
  let token: string | undefined;
  if (body !== undefined) {
    const csrf = await fetch("/api/v1/auth/csrf", {
      credentials: "same-origin",
      cache: "no-store",
      signal: AbortSignal.timeout(15000),
    });
    const value: unknown = await csrf.json();
    if (
      !csrf.ok ||
      !record(value) ||
      !record(value.data) ||
      typeof value.data.csrf_token !== "string"
    )
      throw new Error("Chưa xác minh được phiên đăng nhập.");
    token = value.data.csrf_token;
  }
  const r = await fetch(path, {
    method: body === undefined ? "GET" : "POST",
    credentials: "same-origin",
    cache: "no-store",
    signal: AbortSignal.timeout(20000),
    ...(token
      ? {
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": token,
          },
          body: JSON.stringify(body),
        }
      : {}),
  });
  const v: unknown = await r.json();
  if (!r.ok) {
    const code =
      record(v) && record(v.error) && typeof v.error.code === "string"
        ? v.error.code
        : "";
    throw new Error(
      messages[code] ||
        "Chưa xác nhận được kết quả. Hãy tải lại để kiểm tra trước khi gửi tiếp.",
    );
  }
  return v;
}
export async function quoteCoupon(code: string, direct_item?: {product_id: string; quantity: number; expected_unit_price: string}, selected_product_ids?: string[]): Promise<CouponQuote> {
  const v = await request("/api/v1/coupons/quote", { code, ...(direct_item ? {direct_item} : {}), ...(selected_product_ids ? {selected_product_ids} : {}) });
  if (
    !record(v) ||
    typeof v.code !== "string" ||
    !money(v.subtotal) ||
    !money(v.discount_amount) ||
    !money(v.total_amount)
  )
    throw new Error("Kết quả mã giảm giá không hợp lệ.");
  return {
    code: v.code,
    subtotal: v.subtotal,
    discount_amount: v.discount_amount,
    total_amount: v.total_amount,
  };
}
export async function productReviews(
  productId: string,
  page: number,
): Promise<ReviewPage> {
  if (!id(productId) || !Number.isInteger(page) || page < 1)
    throw new Error("Sản phẩm không hợp lệ.");
  const v = await request(`/api/v1/products/${productId}/reviews?page=${page}`);
  if (
    !record(v) ||
    !Array.isArray(v.items) ||
    !v.items.every(review) ||
    typeof v.total !== "number" ||
    !Number.isInteger(v.total) ||
    v.total < 0 ||
    typeof v.page !== "number" ||
    typeof v.page_size !== "number" ||
    (v.average_rating !== null && typeof v.average_rating !== "string")
  )
    throw new Error("Chưa đọc được đánh giá.");
  return {
    items: v.items,
    total: v.total,
    page: v.page,
    page_size: v.page_size,
    average_rating: v.average_rating as string | null,
  };
}
export async function myReview(itemId: string): Promise<ProductReview | null> {
  if (!id(itemId)) throw new Error("Đơn mua không hợp lệ.");
  const v = await request(`/api/v1/order-items/${itemId}/review`);
  if (!record(v) || (v.data !== null && !review(v.data)))
    throw new Error("Chưa đọc được đánh giá.");
  return v.data as ProductReview | null;
}
export async function createReview(
  itemId: string,
  rating: number,
  comment: string,
): Promise<ProductReview> {
  if (
    !id(itemId) ||
    !Number.isInteger(rating) ||
    rating < 1 ||
    rating > 5 ||
    comment.length > 2000
  )
    throw new Error("Vui lòng chọn 1–5 sao, bình luận tối đa 2.000 ký tự.");
  const v = await request(`/api/v1/order-items/${itemId}/review`, {
    rating,
    comment: comment.trim() || null,
  });
  if (!record(v) || !review(v.data))
    throw new Error("Chưa xác nhận được đánh giá. Hãy tải lại để kiểm tra.");
  return v.data;
}
