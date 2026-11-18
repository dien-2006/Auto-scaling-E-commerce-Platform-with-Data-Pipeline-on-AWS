import {
  paymentLabels,
  type PaymentMethod,
  orderFrom,
  orderStatuses,
  type CheckoutOrder,
  type ShopOrder,
} from "@/lib/checkout-contract";

export type OrderSummary = Pick<
  CheckoutOrder,
  | "order_id"
  | "total_amount"
  | "payment_method"
  | "created_at"
  | "discount_amount"
  | "shipping_fee"
> & {
  shop_orders: Omit<ShopOrder, "items">[];
};
export type OrderPage = {
  items: OrderSummary[];
  page: number;
  page_size: number;
  total: number;
};
const record = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);
export const validOrderId = (v: string) =>
  /^[1-9]\d{0,18}$/.test(v) && BigInt(v) <= BigInt("9223372036854775807");
function cents(v: unknown): bigint | null {
  if (typeof v !== "string" || !/^(0|[1-9]\d{0,11})(\.\d{1,2})?$/.test(v))
    return null;
  const [whole, fraction = ""] = v.split(".");
  return BigInt(whole) * BigInt(100) + BigInt(fraction.padEnd(2, "0"));
}
export function orderPageFrom(value: unknown): OrderPage | null {
  if (
    !record(value) ||
    !Array.isArray(value.items) ||
    !Number.isInteger(value.page) ||
    Number(value.page) < 1 ||
    Number(value.page) > 2147483647 ||
    !Number.isInteger(value.page_size) ||
    Number(value.page_size) < 1 ||
    Number(value.page_size) > 100 ||
    !Number.isSafeInteger(value.total) ||
    Number(value.total) < 0 ||
    value.items.length > Number(value.page_size) ||
    value.items.length > Number(value.total)
  )
    return null;
  const items: OrderSummary[] = [],
    seen = new Set<string>();
  for (const row of value.items) {
    if (
      !record(row) ||
      typeof row.order_id !== "string" ||
      !validOrderId(row.order_id) ||
      seen.has(row.order_id) ||
      typeof row.payment_method !== "string" ||
      !Object.hasOwn(paymentLabels, row.payment_method) ||
      typeof row.created_at !== "string" ||
      !Number.isFinite(Date.parse(row.created_at)) ||
      cents(row.total_amount) === null ||
      !Array.isArray(row.shop_orders) ||
      !row.shop_orders.length
    )
      return null;
    seen.add(row.order_id);
    const shops: OrderSummary["shop_orders"] = [],
      ids = new Set<string>(),
      shopIds = new Set<string>();
    let total = BigInt(0);
    for (const shop of row.shop_orders) {
      if (
        !record(shop) ||
        typeof shop.shop_order_id !== "string" ||
        !validOrderId(shop.shop_order_id) ||
        ids.has(shop.shop_order_id) ||
        typeof shop.shop_id !== "string" ||
        !validOrderId(shop.shop_id) ||
        shopIds.has(shop.shop_id) ||
        typeof shop.shop_name !== "string" ||
        typeof shop.order_status !== "string" ||
        !Object.hasOwn(orderStatuses, shop.order_status) ||
        cents(shop.subtotal) === null
      )
        return null;
      ids.add(shop.shop_order_id);
      shopIds.add(shop.shop_id);
      total += cents(shop.subtotal)!;
      shops.push({
        shop_order_id: shop.shop_order_id,
        shop_id: shop.shop_id,
        shop_name: shop.shop_name,
        order_status: shop.order_status,
        subtotal: shop.subtotal as string,
      });
    }
    const discount = cents(row.discount_amount ?? "0"),
      shipping = cents(row.shipping_fee ?? "0");
    if (
      discount === null ||
      shipping === null ||
      discount > total ||
      total - discount + shipping !== cents(row.total_amount)
    )
      return null;
    items.push({
      order_id: row.order_id,
      total_amount: row.total_amount as string,
      ...(row.discount_amount !== undefined
        ? { discount_amount: row.discount_amount as string }
        : {}),
      ...(row.shipping_fee !== undefined
        ? { shipping_fee: row.shipping_fee as string }
        : {}),
      payment_method: row.payment_method as PaymentMethod,
      created_at: row.created_at,
      shop_orders: shops,
    });
  }
  return {
    items,
    page: Number(value.page),
    page_size: Number(value.page_size),
    total: Number(value.total),
  };
}
export class OrdersFailure extends Error {
  constructor(public code: string) {
    super(
      code === "NOT_FOUND"
        ? "Không tìm thấy đơn hàng của bạn."
        : [
              "AUTH_REQUIRED",
              "TOKEN_EXPIRED",
              "INVALID_TOKEN",
              "UNAUTHORIZED",
              "USER_LOCKED",
            ].includes(code)
          ? "Phiên đăng nhập đã hết hạn hoặc tài khoản không còn quyền truy cập. Vui lòng kiểm tra lại phiên."
          : "Chưa tải được đơn hàng. Vui lòng thử lại.",
    );
  }
}
async function request(path: string, signal?: AbortSignal): Promise<unknown> {
  try {
    const response = await fetch(`/api/v1/orders${path}`, {
      cache: "no-store",
      credentials: "same-origin",
      signal: signal
        ? AbortSignal.any([signal, AbortSignal.timeout(20000)])
        : AbortSignal.timeout(20000),
    });
    const payload = await response.json();
    if (!response.ok)
      throw new OrdersFailure(payload?.error?.code ?? "UNAVAILABLE");
    return payload;
  } catch (error) {
    if (error instanceof OrdersFailure) throw error;
    throw new OrdersFailure("UNAVAILABLE");
  }
}
export async function fetchOrders(
  page: number,
  signal?: AbortSignal,
): Promise<OrderPage> {
  if (!Number.isInteger(page) || page < 1 || page > 2147483647)
    throw new OrdersFailure("INVALID_REQUEST");
  const data = orderPageFrom(
    await request(`?page=${page}&page_size=12`, signal),
  );
  if (!data || data.page !== page || data.page_size !== 12)
    throw new OrdersFailure("UNAVAILABLE");
  return data;
}
export async function fetchOrder(
  id: string,
  signal?: AbortSignal,
): Promise<CheckoutOrder> {
  if (!validOrderId(id)) throw new OrdersFailure("NOT_FOUND");
  const payload = await request(`/${id}`, signal);
  const data = orderFrom(record(payload) ? payload.data : null);
  if (!data || data.order_id !== id) throw new OrdersFailure("UNAVAILABLE");
  return data;
}
