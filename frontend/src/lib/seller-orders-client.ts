import {
  orderFrom,
  orderStatuses,
  type ShopOrder,
  type PaymentMethod,
} from "@/lib/checkout-contract";

export type OrderStatus =
  "PENDING" | "CONFIRMED" | "SHIPPING" | "COMPLETED" | "CANCELLED";
export type SellerOrderSummary = {
  shop_order_id: string;
  order_id: string;
  shop_id: string;
  order_status: OrderStatus;
  subtotal: string;
  created_at: string;
  updated_at: string;
};
export type SellerOrderDetail = SellerOrderSummary & {
  buyer_name?: string | null;
  recipient_name: string;
  phone: string;
  shipping_address: string;
  payment_method: PaymentMethod;
  items: ShopOrder["items"];
};
export type SellerOrderPage = {
  items: SellerOrderSummary[];
  page: number;
  page_size: number;
  total: number;
};
const record = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);
const validId = (v: unknown): v is string =>
  typeof v === "string" &&
  /^[1-9]\d{0,18}$/.test(v) &&
  BigInt(v) <= BigInt("9223372036854775807");
export function sellerOrderFrom(
  v: unknown,
  shopId?: string,
  detail = false,
): SellerOrderSummary | SellerOrderDetail | null {
  if (
    !record(v) ||
    !validId(v.shop_order_id) ||
    !validId(v.order_id) ||
    !validId(v.shop_id) ||
    (shopId !== undefined && v.shop_id !== shopId) ||
    typeof v.order_status !== "string" ||
    !Object.hasOwn(orderStatuses, v.order_status) ||
    typeof v.subtotal !== "string" ||
    !/^(0|[1-9]\d{0,11})(\.\d{1,2})?$/.test(v.subtotal) ||
    typeof v.created_at !== "string" ||
    !Number.isFinite(Date.parse(v.created_at)) ||
    typeof v.updated_at !== "string" ||
    !Number.isFinite(Date.parse(v.updated_at))
  )
    return null;
  const summary: SellerOrderSummary = {
    shop_order_id: v.shop_order_id,
    order_id: v.order_id,
    shop_id: v.shop_id,
    order_status: v.order_status as OrderStatus,
    subtotal: v.subtotal,
    created_at: v.created_at,
    updated_at: v.updated_at,
  };
  if (!detail) return summary;
  if (v.buyer_name !== undefined && v.buyer_name !== null && typeof v.buyer_name !== "string") return null;
  // Reuse exact-money and snapshot validation for only this shop's lines.
  const order = orderFrom({
    order_id: v.order_id,
    total_amount: v.subtotal,
    payment_method: v.payment_method,
    created_at: v.created_at,
    recipient_name: v.recipient_name,
    phone: v.phone,
    shipping_address: v.shipping_address,
    shop_orders: [
      {
        shop_order_id: v.shop_order_id,
        shop_id: v.shop_id,
        shop_name: "Shop",
        order_status: v.order_status,
        subtotal: v.subtotal,
        items: v.items,
      },
    ],
  });
  if (!order) return null;
  return {
    ...summary,
    ...(v.buyer_name !== undefined ? {buyer_name: v.buyer_name as string | null} : {}),
    recipient_name: order.recipient_name,
    phone: order.phone,
    shipping_address: order.shipping_address,
    payment_method: order.payment_method,
    items: order.shop_orders[0].items,
  };
}
export class SellerOrderFailure extends Error {
  constructor(public code: string) {
    super(
      (
        {
          INVALID_TRANSITION:
            "Trạng thái đơn đã thay đổi hoặc không hợp lệ. Hãy tải lại đơn.",
          RESTOCK_CONFLICT:
            "Chưa thể hoàn tồn. Vui lòng liên hệ quản trị viên.",
          NOT_FOUND: "Không tìm thấy đơn shop.",
          AUTH_REQUIRED: "Vui lòng đăng nhập lại.",
          TOKEN_EXPIRED: "Phiên đăng nhập đã hết hạn.",
          INVALID_TOKEN: "Phiên đăng nhập không hợp lệ.",
          USER_LOCKED: "Tài khoản đã bị khóa.",
          FORBIDDEN: "Bạn không có quyền xử lý đơn shop.",
          SHOP_NOT_APPROVED: "Gian hàng chưa được phép xử lý đơn.",
          CSRF_FAILED: "Phiên xác thực đã thay đổi. Hãy tải lại trang.",
        } as Record<string, string>
      )[code] ??
        "Chưa xác minh được kết quả. Hãy tải lại đơn trước khi tiếp tục.",
    );
  }
}
async function request(
  path: string,
  signal: AbortSignal,
  init?: RequestInit,
): Promise<unknown> {
  try {
    const response = await fetch(path, {
      ...init,
      credentials: "same-origin",
      cache: "no-store",
      signal: AbortSignal.any([signal, AbortSignal.timeout(20000)]),
    });
    const value: unknown = await response.json();
    if (!response.ok)
      throw new SellerOrderFailure(
        record(value) &&
          record(value.error) &&
          typeof value.error.code === "string"
          ? value.error.code
          : "UNAVAILABLE",
      );
    return value;
  } catch (e) {
    if (e instanceof SellerOrderFailure) throw e;
    throw new SellerOrderFailure("UNAVAILABLE");
  }
}
export async function fetchSellerOrders(
  shopId: string,
  page: number,
  status: string,
  signal: AbortSignal,
): Promise<SellerOrderPage> {
  if (
    !validId(shopId) ||
    !Number.isInteger(page) ||
    page < 1 ||
    page > 2147483647 ||
    (status && !Object.hasOwn(orderStatuses, status))
  )
    throw new SellerOrderFailure("NOT_FOUND");
  const value = await request(
    `/api/v1/seller/orders?page=${page}&page_size=24${status ? `&status=${status}` : ""}`,
    signal,
  );
  if (
    !record(value) ||
    value.page !== page ||
    value.page_size !== 24 ||
    !Number.isSafeInteger(value.total) ||
    Number(value.total) < 0 ||
    !Array.isArray(value.items) ||
    value.items.length > Math.min(24, Number(value.total))
  )
    throw new SellerOrderFailure("UNAVAILABLE");
  const items = value.items.map((v) => sellerOrderFrom(v, shopId));
  if (
    items.some((v) => !v || (status && v.order_status !== status)) ||
    new Set(items.map((v) => v?.shop_order_id)).size !== items.length
  )
    throw new SellerOrderFailure("UNAVAILABLE");
  return {
    items: items as SellerOrderSummary[],
    page,
    page_size: 24,
    total: Number(value.total),
  };
}
export async function fetchSellerOrder(
  id: string,
  shopId: string,
  signal: AbortSignal,
): Promise<SellerOrderDetail> {
  if (!validId(id) || !validId(shopId))
    throw new SellerOrderFailure("NOT_FOUND");
  const value = await request(`/api/v1/seller/orders/${id}`, signal);
  const detail = sellerOrderFrom(
    record(value) ? value.data : null,
    shopId,
    true,
  );
  if (!detail || detail.shop_order_id !== id)
    throw new SellerOrderFailure("UNAVAILABLE");
  return detail as SellerOrderDetail;
}
export async function changeShopOrder(
  order: { order_id: string; shop_order_id: string; order_status: string },
  target: OrderStatus,
  signal: AbortSignal,
  buyer = false,
): Promise<void> {
  if (
    !validId(order.order_id) ||
    !validId(order.shop_order_id) ||
    !Object.hasOwn(orderStatuses, order.order_status) ||
    !Object.hasOwn(orderStatuses, target) ||
    (buyer && target !== "CANCELLED")
  )
    throw new SellerOrderFailure("NOT_FOUND");
  const csrf = await request("/api/v1/auth/csrf", signal);
  if (
    !record(csrf) ||
    !record(csrf.data) ||
    typeof csrf.data.csrf_token !== "string"
  )
    throw new SellerOrderFailure("UNAVAILABLE");
  const value = await request(
    buyer
      ? `/api/v1/orders/${order.order_id}/shop-orders/${order.shop_order_id}/cancel`
      : `/api/v1/seller/orders/${order.shop_order_id}/status`,
    signal,
    {
      method: buyer ? "POST" : "PATCH",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrf.data.csrf_token,
      },
      ...(buyer
        ? {}
        : {
            body: JSON.stringify({
              expected_status: order.order_status,
              status: target,
            }),
          }),
    },
  );
  const result = sellerOrderFrom(
    record(value) ? value.data : null,
    undefined,
    true,
  );
  if (
    !result ||
    result.shop_order_id !== order.shop_order_id ||
    result.order_id !== order.order_id ||
    result.order_status !== target
  )
    throw new SellerOrderFailure("UNAVAILABLE");
}
