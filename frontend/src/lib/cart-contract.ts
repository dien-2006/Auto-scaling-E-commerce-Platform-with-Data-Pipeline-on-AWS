export type CartItem = {
  cart_item_id: string;
  product_id: string;
  product_name: string;
  quantity: number;
  unit_price: string;
  line_total: string;
  available_quantity: number;
  is_available: boolean;
  unavailable_reason: string | null;
  primary_image_url: string | null;
};
export type CartShop = {
  shop_id: string;
  shop_name: string;
  shop_slug: string;
  items: CartItem[];
  subtotal: string;
};
export type CartData = { shops: CartShop[]; total_amount: string };
export const cartReasons: Record<string, string> = {
  HIDDEN_PRODUCT: "Sản phẩm đã bị ẩn.",
  SHOP_UNAVAILABLE: "Gian hàng hiện không nhận đơn.",
  CATEGORY_UNAVAILABLE: "Danh mục hiện không còn mở bán.",
  SELF_PURCHASE: "Bạn không thể mua sản phẩm của shop mình.",
  MISSING_INVENTORY: "Sản phẩm chưa có thông tin tồn kho.",
  OUT_OF_STOCK: "Sản phẩm đã hết hàng.",
  INSUFFICIENT_STOCK:
    "Tồn kho hiện tại thấp hơn số lượng trong giỏ. Hãy giảm số lượng.",
};
const record = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);
export const cartID = (value: unknown): value is string =>
  typeof value === "string" &&
  /^[1-9]\d{0,18}$/.test(value) &&
  BigInt(value) <= BigInt("9223372036854775807");
const integer = (value: unknown, min: number): value is number =>
  typeof value === "number" &&
  Number.isInteger(value) &&
  value >= min &&
  value <= 2147483647;
function cents(value: unknown): bigint | null {
  if (
    typeof value !== "string" ||
    !/^(0|[1-9]\d{0,49})(\.\d{1,2})?$/.test(value)
  )
    return null;
  const [whole, fraction = ""] = value.split(".");
  return BigInt(whole) * BigInt(100) + BigInt(fraction.padEnd(2, "0"));
}
function imageURL(value: unknown): value is string | null {
  if (value === null) return true;
  if (typeof value !== "string") return false;
  try {
    const url = new URL(value);
    return (
      ["https:", "http:"].includes(url.protocol) &&
      !url.username &&
      !url.password
    );
  } catch {
    return false;
  }
}
export function cartFrom(value: unknown): CartData | null {
  if (
    !record(value) ||
    !Array.isArray(value.shops) ||
    cents(value.total_amount) === null
  )
    return null;
  const shopIDs = new Set<string>(),
    itemIDs = new Set<string>(),
    productIDs = new Set<string>();
  const shops: CartShop[] = [];
  let total = BigInt(0);
  for (const shop of value.shops) {
    if (
      !record(shop) ||
      !cartID(shop.shop_id) ||
      shopIDs.has(shop.shop_id) ||
      typeof shop.shop_name !== "string" ||
      typeof shop.shop_slug !== "string" ||
      !Array.isArray(shop.items) ||
      !shop.items.length ||
      cents(shop.subtotal) === null
    )
      return null;
    shopIDs.add(shop.shop_id);
    const items: CartItem[] = [];
    let subtotal = BigInt(0);
    for (const item of shop.items) {
      if (
        !record(item) ||
        !cartID(item.cart_item_id) ||
        !cartID(item.product_id) ||
        itemIDs.has(item.cart_item_id) ||
        productIDs.has(item.product_id) ||
        typeof item.product_name !== "string" ||
        !integer(item.quantity, 1) ||
        !integer(item.available_quantity, 0) ||
        typeof item.is_available !== "boolean" ||
        !(
          item.unavailable_reason === null ||
          (typeof item.unavailable_reason === "string" &&
            Object.hasOwn(cartReasons, item.unavailable_reason))
        ) ||
        item.is_available !== (item.unavailable_reason === null) ||
        !imageURL(item.primary_image_url)
      )
        return null;
      const price = cents(item.unit_price),
        amount = cents(item.line_total);
      if (
        price === null ||
        price > BigInt("99999999999999") ||
        amount === null ||
        amount !== price * BigInt(item.quantity) ||
        (item.is_available && item.quantity > item.available_quantity)
      )
        return null;
      itemIDs.add(item.cart_item_id);
      productIDs.add(item.product_id);
      subtotal += amount;
      items.push({
        cart_item_id: item.cart_item_id,
        product_id: item.product_id,
        product_name: item.product_name,
        quantity: item.quantity,
        unit_price: item.unit_price as string,
        line_total: item.line_total as string,
        available_quantity: item.available_quantity,
        is_available: item.is_available,
        unavailable_reason: item.unavailable_reason as string | null,
        primary_image_url: item.primary_image_url,
      });
    }
    if (subtotal !== cents(shop.subtotal)) return null;
    total += subtotal;
    shops.push({
      shop_id: shop.shop_id,
      shop_name: shop.shop_name,
      shop_slug: shop.shop_slug,
      items,
      subtotal: shop.subtotal as string,
    });
  }
  return total === cents(value.total_amount)
    ? { shops, total_amount: value.total_amount as string }
    : null;
}
