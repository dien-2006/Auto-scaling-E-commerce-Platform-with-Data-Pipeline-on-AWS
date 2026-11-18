import type { CartData } from "@/lib/cart-contract";

export type PaymentMethod = "COD" | "BANK_TRANSFER" | "MOMO" | "VNPAY";
export type ShippingMethod = "STANDARD" | "EXPRESS" | "COCOEXPRESS";
export const paymentLabels = {
  COD: "COD",
  BANK_TRANSFER: "Chuyển khoản",
  MOMO: "MoMo",
  VNPAY: "VNPay",
};
export const shippingLabels = {
  STANDARD: "Tiêu chuẩn",
  EXPRESS: "Nhanh",
  COCOEXPRESS: "COCO Express",
};
export type CheckoutPayload = {
  purchase_mode?: "CART" | "BUY_NOW" | "SELECTED_CART";
  address_id: string;
  payment_method: PaymentMethod;
  shipping_method?: ShippingMethod;
  expected_shipping_fee?: string;
  expected_shipping_discount?: string;
  coco_coupon_code?: string;
  shipping_coupon_code?: string;
  shop_coupons?: { shop_id: string; code: string }[];
  coupon_code?: string;
  expected_coupon_discount?: string;
  items: {
    product_id: string;
    quantity: number;
    expected_unit_price: string;
  }[];
};
export type CheckoutIntent = {
  version: 1;
  user_id: string;
  key: string;
  payload: CheckoutPayload;
};
export type OrderLine = {
  order_item_id: string;
  product_id: string;
  product_name: string;
  unit_price: string;
  quantity: number;
  line_total: string;
};
export type ShopOrder = {
  shop_order_id: string;
  shop_id: string;
  shop_name: string;
  order_status: string;
  subtotal: string;
  items: OrderLine[];
};
export type CheckoutOrder = {
  order_id: string;
  total_amount: string;
  discount_amount?: string;
  shipping_fee?: string;
  shipping_discount_amount?: string;
  payment_status?: string | null;
  payment_method: PaymentMethod;
  created_at: string;
  recipient_name: string;
  phone: string;
  shipping_address: string;
  shop_orders: ShopOrder[];
};
export const orderStatuses: Record<string, string> = {
  PENDING: "Chờ xác nhận",
  CONFIRMED: "Đã xác nhận",
  SHIPPING: "Đang giao",
  COMPLETED: "Hoàn thành",
  CANCELLED: "Đã hủy",
};
const record = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);
const id = (v: unknown): v is string =>
  typeof v === "string" &&
  /^[1-9]\d{0,18}$/.test(v) &&
  BigInt(v) <= BigInt("9223372036854775807");
const quantity = (v: unknown): v is number =>
  typeof v === "number" && Number.isInteger(v) && v >= 1 && v <= 2147483647;
const uuid = (v: unknown): v is string =>
  typeof v === "string" &&
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(v);
const only = (v: Record<string, unknown>, keys: string[]) =>
  Object.keys(v).every((key) => keys.includes(key));
function cents(v: unknown): bigint | null {
  if (typeof v !== "string" || !/^(0|[1-9]\d{0,11})(\.\d{1,2})?$/.test(v))
    return null;
  const [whole, fraction = ""] = v.split(".");
  return BigInt(whole) * BigInt(100) + BigInt(fraction.padEnd(2, "0"));
}
export function checkoutPayloadFrom(value: unknown): CheckoutPayload | null {
  if (
    !record(value) ||
    !only(value, [
      "purchase_mode",
      "address_id",
      "payment_method",
      "items",
      "coupon_code",
      "expected_coupon_discount",
      "shipping_method",
      "expected_shipping_fee",
      "expected_shipping_discount",
      "coco_coupon_code",
      "shipping_coupon_code",
      "shop_coupons",
    ]) ||
    (value.purchase_mode !== undefined && !["CART", "BUY_NOW", "SELECTED_CART"].includes(String(value.purchase_mode))) ||
    (value.expected_coupon_discount !== undefined &&
      cents(value.expected_coupon_discount) === null) ||
    (value.coupon_code !== undefined &&
      (typeof value.coupon_code !== "string" ||
        !value.coupon_code.trim() ||
        value.coupon_code.length > 50)) ||
    !id(value.address_id) ||
    typeof value.payment_method !== "string" ||
    !Object.hasOwn(paymentLabels, value.payment_method) ||
    !Array.isArray(value.items) ||
    !value.items.length ||
    value.items.length > 1000
  )
    return null;
  if (
    value.shipping_method !== undefined &&
    (typeof value.shipping_method !== "string" ||
      !Object.hasOwn(shippingLabels, value.shipping_method))
  )
    return null;
  for (const field of ["expected_shipping_fee", "expected_shipping_discount"])
    if (value[field] !== undefined && cents(value[field]) === null) return null;
  const selectedCodes: string[] = [];
  for (const field of ["coco_coupon_code", "shipping_coupon_code"])
    if (value[field] !== undefined) {
      if (
        typeof value[field] !== "string" ||
        !value[field].trim() ||
        value[field].length > 50
      )
        return null;
      selectedCodes.push((value[field] as string).trim());
    }
  const shopCoupons: { shop_id: string; code: string }[] = [];
  if (value.shop_coupons !== undefined) {
    if (!Array.isArray(value.shop_coupons) || value.shop_coupons.length > 1000)
      return null;
    for (const c of value.shop_coupons) {
      if (
        !record(c) ||
        !only(c, ["shop_id", "code"]) ||
        !id(c.shop_id) ||
        typeof c.code !== "string" ||
        !c.code.trim() ||
        c.code.length > 50 ||
        shopCoupons.some((v) => v.shop_id === c.shop_id)
      )
        return null;
      shopCoupons.push({ shop_id: c.shop_id, code: c.code.trim() });
      selectedCodes.push(c.code.trim());
    }
  }
  if (
    new Set(selectedCodes).size !== selectedCodes.length ||
    (selectedCodes.length && (!value.shipping_method || value.coupon_code))
  )
    return null;
  const items: CheckoutPayload["items"] = [],
    seen = new Set<string>();
  let total = BigInt(0);
  for (const item of value.items) {
    if (
      !record(item) ||
      !only(item, ["product_id", "quantity", "expected_unit_price"]) ||
      !id(item.product_id) ||
      seen.has(item.product_id) ||
      !quantity(item.quantity)
    )
      return null;
    const price = cents(item.expected_unit_price);
    if (price === null) return null;
    total += price * BigInt(item.quantity);
    seen.add(item.product_id);
    items.push({
      product_id: item.product_id,
      quantity: item.quantity,
      expected_unit_price: item.expected_unit_price as string,
    });
  }
  if (total > BigInt("99999999999999") || (value.purchase_mode === "BUY_NOW" && items.length !== 1)) return null;
  return {
    ...(value.purchase_mode ? {purchase_mode: value.purchase_mode as "CART" | "BUY_NOW" | "SELECTED_CART"} : {}),
    address_id: value.address_id,
    payment_method: value.payment_method as PaymentMethod,
    ...(value.shipping_method
      ? { shipping_method: value.shipping_method as ShippingMethod }
      : {}),
    ...(value.expected_shipping_fee !== undefined
      ? { expected_shipping_fee: value.expected_shipping_fee as string }
      : {}),
    ...(value.expected_shipping_discount !== undefined
      ? {
          expected_shipping_discount:
            value.expected_shipping_discount as string,
        }
      : {}),
    ...(value.coco_coupon_code
      ? { coco_coupon_code: (value.coco_coupon_code as string).trim() }
      : {}),
    ...(value.shipping_coupon_code
      ? { shipping_coupon_code: (value.shipping_coupon_code as string).trim() }
      : {}),
    ...(value.shop_coupons !== undefined ? { shop_coupons: shopCoupons } : {}),
    items,
    ...(typeof value.expected_coupon_discount === "string"
      ? { expected_coupon_discount: value.expected_coupon_discount }
      : {}),
    ...(typeof value.coupon_code === "string"
      ? { coupon_code: value.coupon_code.trim() }
      : {}),
  };
}
export function checkoutBlock(cart: CartData): string | null {
  const items = cart.shops.flatMap((shop) => shop.items);
  if (!items.length) return "Giỏ hàng đang trống.";
  if (items.length > 1000)
    return "Một lần đặt hàng hỗ trợ tối đa 1.000 sản phẩm khác nhau.";
  if (items.some((item) => !item.is_available))
    return "Có sản phẩm chưa thể mua. Vui lòng sửa giỏ hàng trước khi đặt.";
  if (cents(cart.total_amount) === null)
    return "Tổng tiền vượt giới hạn đơn hàng. Vui lòng giảm số lượng.";
  return null;
}
export function orderFrom(value: unknown): CheckoutOrder | null {
  if (
    !record(value) ||
    !id(value.order_id) ||
    typeof value.payment_method !== "string" ||
    !Object.hasOwn(paymentLabels, value.payment_method) ||
    cents(value.total_amount) === null ||
    typeof value.created_at !== "string" ||
    !Number.isFinite(Date.parse(value.created_at)) ||
    ["recipient_name", "phone", "shipping_address"].some(
      (key) => typeof value[key] !== "string",
    ) ||
    !Array.isArray(value.shop_orders) ||
    !value.shop_orders.length
  )
    return null;
  const shops: ShopOrder[] = [],
    shopIDs = new Set<string>(),
    orderIDs = new Set<string>(),
    lineIDs = new Set<string>(),
    productIDs = new Set<string>();
  let total = BigInt(0);
  for (const shop of value.shop_orders) {
    if (
      !record(shop) ||
      !id(shop.shop_order_id) ||
      orderIDs.has(shop.shop_order_id) ||
      !id(shop.shop_id) ||
      shopIDs.has(shop.shop_id) ||
      typeof shop.shop_name !== "string" ||
      typeof shop.order_status !== "string" ||
      !Object.hasOwn(orderStatuses, shop.order_status) ||
      cents(shop.subtotal) === null ||
      !Array.isArray(shop.items) ||
      !shop.items.length
    )
      return null;
    shopIDs.add(shop.shop_id);
    orderIDs.add(shop.shop_order_id);
    const items: OrderLine[] = [];
    let subtotal = BigInt(0);
    for (const item of shop.items) {
      if (
        !record(item) ||
        !id(item.order_item_id) ||
        lineIDs.has(item.order_item_id) ||
        !id(item.product_id) ||
        productIDs.has(item.product_id) ||
        typeof item.product_name !== "string" ||
        !quantity(item.quantity)
      )
        return null;
      const price = cents(item.unit_price),
        amount = cents(item.line_total);
      if (
        price === null ||
        amount === null ||
        amount !== price * BigInt(item.quantity)
      )
        return null;
      lineIDs.add(item.order_item_id);
      productIDs.add(item.product_id);
      subtotal += amount;
      items.push({
        order_item_id: item.order_item_id,
        product_id: item.product_id,
        product_name: item.product_name,
        unit_price: item.unit_price as string,
        quantity: item.quantity,
        line_total: item.line_total as string,
      });
    }
    if (subtotal !== cents(shop.subtotal)) return null;
    total += subtotal;
    shops.push({
      shop_order_id: shop.shop_order_id,
      shop_id: shop.shop_id,
      shop_name: shop.shop_name,
      order_status: shop.order_status,
      subtotal: shop.subtotal as string,
      items,
    });
  }
  const discount = cents(value.discount_amount ?? "0"),
    shipping = cents(value.shipping_fee ?? "0");
  return discount !== null &&
    shipping !== null &&
    discount <= total &&
    total - discount + shipping === cents(value.total_amount)
    ? {
        order_id: value.order_id,
        total_amount: value.total_amount as string,
        ...(value.discount_amount !== undefined
          ? { discount_amount: value.discount_amount as string }
          : {}),
        ...(value.shipping_fee !== undefined
          ? { shipping_fee: value.shipping_fee as string }
          : {}),
        payment_method: value.payment_method as PaymentMethod,
        ...(typeof value.shipping_discount_amount === "string" &&
        cents(value.shipping_discount_amount) !== null
          ? { shipping_discount_amount: value.shipping_discount_amount }
          : {}),
        ...(value.payment_status === null ||
        (typeof value.payment_status === "string" &&
          ["PENDING", "SUCCESS", "FAILED", "REFUNDED"].includes(
            value.payment_status,
          ))
          ? { payment_status: value.payment_status }
          : {}),
        created_at: value.created_at,
        recipient_name: value.recipient_name as string,
        phone: value.phone as string,
        shipping_address: value.shipping_address as string,
        shop_orders: shops,
      }
    : null;
}
export function intentFrom(
  value: unknown,
  userId: string,
): CheckoutIntent | null {
  if (
    !record(value) ||
    !only(value, ["version", "user_id", "key", "payload"]) ||
    value.version !== 1 ||
    !id(userId) ||
    value.user_id !== userId ||
    !uuid(value.key)
  )
    return null;
  const payload = checkoutPayloadFrom(value.payload);
  return payload
    ? { version: 1, user_id: userId, key: value.key, payload }
    : null;
}
type IntentStorage = Pick<Storage, "getItem" | "setItem" | "removeItem">;
const storageKey = (userId: string) => `coco.checkout.intent.v1:${userId}`;
export function readIntent(
  storage: IntentStorage,
  userId: string,
): CheckoutIntent | null {
  const raw = storage.getItem(storageKey(userId));
  if (raw === null) return null;
  if (raw.length > 131072)
    throw new Error(
      "Yêu cầu lưu trong phiên không hợp lệ. Chưa thể xác minh đơn trước đó.",
    );
  const value = intentFrom(JSON.parse(raw), userId);
  if (!value)
    throw new Error(
      "Yêu cầu lưu trong phiên không hợp lệ. Chưa thể xác minh đơn trước đó.",
    );
  return value;
}
export function saveIntent(
  storage: IntentStorage,
  value: CheckoutIntent,
): void {
  const safe = intentFrom(value, value.user_id);
  if (!safe) throw new Error("Yêu cầu đặt hàng không hợp lệ.");
  const serialized = JSON.stringify(safe);
  storage.setItem(storageKey(safe.user_id), serialized);
  if (storage.getItem(storageKey(safe.user_id)) !== serialized)
    throw new Error("Không lưu được yêu cầu đặt hàng trong phiên này.");
}
export function clearIntent(storage: IntentStorage, userId: string): void {
  storage.removeItem(storageKey(userId));
  if (storage.getItem(storageKey(userId)) !== null)
    throw new Error(
      "Chưa xóa được yêu cầu đã xác nhận. Vui lòng tải lại trước khi tạo lượt mới.",
    );
}


export function checkoutKey(source: Pick<Crypto, "getRandomValues"> = globalThis.crypto): string {
  if (!source?.getRandomValues) throw new Error("Secure random source unavailable");
  const bytes = source.getRandomValues(new Uint8Array(16));
  bytes[6] = (bytes[6] & 15) | 64;
  bytes[8] = (bytes[8] & 63) | 128;
  const hex = Array.from(bytes, b => b.toString(16).padStart(2, "0")).join("");
  return `${hex.slice(0,8)}-${hex.slice(8,12)}-${hex.slice(12,16)}-${hex.slice(16,20)}-${hex.slice(20)}`;
}
