import type { PaymentMethod, ShippingMethod } from "@/lib/checkout-contract";
export type OptionsSelection = {
  shipping_method: ShippingMethod;
  payment_method: PaymentMethod;
  coco_coupon_code?: string;
  shipping_coupon_code?: string;
  shop_coupons: { shop_id: string; code: string }[];
};
export type CheckoutOptions = {
  enabled: boolean;
  bank: { name: string; account_number: string; account_holder: string } | null;
  shipping_methods: {
    code: ShippingMethod;
    label: string;
    fee_per_shop: string | null;
    enabled: boolean;
    reason: string | null;
  }[];
  payment_methods: {
    code: PaymentMethod;
    label: string;
    enabled: boolean;
    reason: string | null;
  }[];
};
export type OptionsQuote = {
  subtotal: string;
  discount_amount: string;
  shipping_fee: string;
  shipping_discount_amount: string;
  total_amount: string;
  applied_coupons: {
    code: string;
    shop_id: string | null;
    coupon_type: "GOODS" | "SHIPPING";
    discount_amount: string;
  }[];
  shipping: { shop_id: string; method: ShippingMethod; fee: string }[];
};
export type QuotedChoices = {
  selection: OptionsSelection;
  quote: OptionsQuote;
};
const record = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);
function cents(v: unknown): bigint | null {
  if (typeof v !== "string" || !/^(0|[1-9]\d{0,11})(\.\d{1,2})?$/.test(v))
    return null;
  const [w, f = ""] = v.split(".");
  return BigInt(w) * BigInt(100) + BigInt(f.padEnd(2, "0"));
}
const shipping = ["STANDARD", "EXPRESS", "COCOEXPRESS"],
  payments = ["COD", "BANK_TRANSFER", "MOMO", "VNPAY"];
const messages: Record<string, string> = {
  COUPON_SCOPE: "Mã không đúng loại hoặc không thuộc shop này.",
  COUPON_MINIMUM: "Chưa đạt giá trị tối thiểu của mã.",
  COUPON_INVALID: "Mã không hợp lệ, hết hạn hoặc hết lượt.",
  COUPON_CUSTOMER_LIMIT: "Bạn đã dùng hết lượt của mã.",
  PAYMENT_NOT_CONFIGURED: "Phương thức thanh toán chưa được cấu hình.",
  SHIPPING_NOT_CONFIGURED: "Chưa cấu hình cước vận chuyển.",
  CHECKOUT_OPTIONS_NOT_CONFIGURED: "Lựa chọn mới chưa được kích hoạt.",
  CART_CHANGED: "Giỏ hàng đã thay đổi. Hãy tải lại.",
  VALIDATION_ERROR: "Thông tin lựa chọn chưa hợp lệ.",
};
async function request(
  path: string,
  body?: OptionsSelection,
): Promise<unknown> {
  let token: string | undefined;
  if (body) {
    const r = await fetch("/api/v1/auth/csrf", {
      credentials: "same-origin",
      cache: "no-store",
      signal: AbortSignal.timeout(15000),
    });
    const p: unknown = await r.json();
    if (
      !r.ok ||
      !record(p) ||
      !record(p.data) ||
      typeof p.data.csrf_token !== "string"
    )
      throw new Error("Vui lòng kiểm tra phiên đăng nhập.");
    token = p.data.csrf_token;
  }
  const r = await fetch(path, {
    credentials: "same-origin",
    cache: "no-store",
    signal: AbortSignal.timeout(20000),
    ...(body
      ? {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": token!,
          },
          body: JSON.stringify(body),
        }
      : {}),
  });
  const p: unknown = await r.json();
  if (!r.ok) {
    const code =
      record(p) && record(p.error) && typeof p.error.code === "string"
        ? p.error.code
        : "";
    throw new Error(
      messages[code] || "Chưa tải được lựa chọn thanh toán. Vui lòng thử lại.",
    );
  }
  return p;
}
export async function fetchCheckoutOptions(): Promise<CheckoutOptions> {
  const p = await request("/api/v1/checkout/options");
  if (
    !record(p) ||
    typeof p.enabled !== "boolean" ||
    !Array.isArray(p.shipping_methods) ||
    !Array.isArray(p.payment_methods) ||
    p.shipping_methods.length !== 3 ||
    p.payment_methods.length !== 4 ||
    !p.shipping_methods.every(
      (v) =>
        record(v) &&
        shipping.includes(String(v.code)) &&
        typeof v.label === "string" &&
        typeof v.enabled === "boolean" &&
        (v.fee_per_shop === null || cents(v.fee_per_shop) !== null),
    ) ||
    !p.payment_methods.every(
      (v) =>
        record(v) &&
        payments.includes(String(v.code)) &&
        typeof v.label === "string" &&
        typeof v.enabled === "boolean",
    ) ||
    !(
      p.bank === null ||
      (record(p.bank) &&
        typeof p.bank.name === "string" &&
        typeof p.bank.account_number === "string" &&
        typeof p.bank.account_holder === "string")
    )
  )
    throw new Error("Cấu hình thanh toán không hợp lệ.");
  return p as unknown as CheckoutOptions;
}
export async function quoteChoices(
  selection: OptionsSelection,
): Promise<OptionsQuote> {
  const p = await request("/api/v1/checkout/quote", selection);
  if (
    !record(p) ||
    ![
      "subtotal",
      "discount_amount",
      "shipping_fee",
      "shipping_discount_amount",
      "total_amount",
    ].every((k) => cents(p[k]) !== null) ||
    !Array.isArray(p.applied_coupons) ||
    !Array.isArray(p.shipping)
  )
    throw new Error("Tổng tiền không hợp lệ.");
  if (
    cents(p.discount_amount)! > cents(p.subtotal)! ||
    cents(p.subtotal)! - cents(p.discount_amount)! + cents(p.shipping_fee)! !==
      cents(p.total_amount)
  )
    throw new Error("Tổng tiền không khớp.");
  const ids = new Set<string>();
  let shippingFee = BigInt(0);
  for (const v of p.shipping) {
    if (
      !record(v) ||
      typeof v.shop_id !== "string" ||
      !/^[1-9]\d{0,18}$/.test(v.shop_id) ||
      ids.has(v.shop_id) ||
      v.method !== selection.shipping_method ||
      cents(v.fee) === null
    )
      throw new Error("Cước không hợp lệ.");
    ids.add(v.shop_id);
    shippingFee += cents(v.fee)!;
  }
  if (shippingFee !== cents(p.shipping_fee))
    throw new Error("Cước không khớp.");
  for (const v of p.applied_coupons)
    if (
      !record(v) ||
      typeof v.code !== "string" ||
      !["GOODS", "SHIPPING"].includes(String(v.coupon_type)) ||
      cents(v.discount_amount) === null
    )
      throw new Error("Mã giảm giá không hợp lệ.");
  return p as unknown as OptionsQuote;
}
