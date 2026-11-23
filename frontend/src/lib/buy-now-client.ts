import { cartFrom, type CartData } from "@/lib/cart-contract";
export type BuyNow = {product: string; quantity: number};
export async function buyNowReview(selection: BuyNow): Promise<CartData> {
  const response = await fetch(`/api/v1/products/${selection.product}`, {cache:"no-store", credentials:"same-origin", signal:AbortSignal.timeout(10000)});
  if (!response.ok) throw new Error("Sản phẩm hiện không thể mua. Vui lòng chọn lại.");
  const {data:p} = await response.json();
  if (p?.product_id !== selection.product || typeof p.price !== "string" || !/^(0|[1-9]\d{0,11})(\.\d{1,2})?$/.test(p.price)) throw new Error("Dữ liệu sản phẩm không hợp lệ.");
  const [whole, fraction=""] = p.price.split(".");
  const amount = (BigInt(whole)*BigInt(100)+BigInt(fraction.padEnd(2,"0")))*BigInt(selection.quantity);
  const total = `${amount/BigInt(100)}.${String(amount%BigInt(100)).padStart(2,"0")}`;
  const enough = p.available_quantity >= selection.quantity;
  const cart = cartFrom({shops:[{...p.shop,items:[{cart_item_id:p.product_id,product_id:p.product_id,product_name:p.product_name,unit_price:p.price,quantity:selection.quantity,line_total:total,available_quantity:p.available_quantity,is_available:enough,unavailable_reason:enough?null:"INSUFFICIENT_STOCK",primary_image_url:p.primary_image_url}],subtotal:total}],total_amount:total});
  if (!cart) throw new Error("Không thể kiểm tra sản phẩm mua ngay.");
  return cart;
}
