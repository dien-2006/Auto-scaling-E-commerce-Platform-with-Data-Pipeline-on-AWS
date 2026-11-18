import { authMessages } from "@/lib/auth-contract";
import { cartFrom, cartID, type CartData } from "@/lib/cart-contract";

export class CartFailure extends Error {
  constructor(public code: string) {
    super(
      (
        {
          OUT_OF_STOCK:
            "Sản phẩm không đủ tồn kho. Hãy tải lại giỏ và kiểm tra số lượng.",
          CART_CHANGED:
            "Giỏ hàng đã thay đổi hoặc số lượng vượt giới hạn. Vui lòng tải lại.",
          FORBIDDEN:
            "Bạn không thể mua sản phẩm của shop mình hoặc không có quyền thao tác.",
        } as Record<string, string>
      )[code] ??
        authMessages[code] ??
        "Chưa thể kết nối dịch vụ giỏ hàng. Vui lòng thử lại.",
    );
  }
}
async function call(path: string, init?: RequestInit): Promise<unknown> {
  try {
    const response = await fetch(`/api/v1/${path}`, {
      ...init,
      credentials: "same-origin",
      cache: "no-store",
      signal: AbortSignal.timeout(20000),
    });
    if (response.status === 204) return null;
    const payload = await response.json();
    if (!response.ok)
      throw new CartFailure(
        typeof payload?.error?.code === "string"
          ? payload.error.code
          : "UNAVAILABLE",
      );
    return payload;
  } catch (e) {
    if (e instanceof CartFailure) throw e;
    throw new CartFailure("UNAVAILABLE");
  }
}
function parse(payload: unknown): CartData {
  const result = cartFrom((payload as { data?: unknown })?.data);
  if (!result) throw new CartFailure("UNAVAILABLE");
  return result;
}
export async function fetchCart(): Promise<CartData> {
  return parse(await call("cart"));
}
export async function changeCart(
  method: "POST" | "PATCH" | "DELETE",
  id: string,
  quantity?: number,
): Promise<CartData | null> {
  if (
    !cartID(id) ||
    (method !== "DELETE" &&
      (!Number.isInteger(quantity) || quantity! < 1 || quantity! > 2147483647))
  )
    throw new CartFailure("VALIDATION_ERROR");
  const csrf = (await call("auth/csrf")) as { data?: { csrf_token?: unknown } };
  if (typeof csrf?.data?.csrf_token !== "string")
    throw new CartFailure("UNAVAILABLE");
  const result = await call(
    method === "POST" ? "cart/items" : `cart/items/${id}`,
    {
      method,
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrf.data.csrf_token,
      },
      ...(method !== "DELETE"
        ? {
            body: JSON.stringify({
              ...(method === "POST" ? { product_id: id } : {}),
              quantity,
            }),
          }
        : {}),
    },
  );
  const cart = method === "DELETE" ? null : parse(result);
  window.dispatchEvent(new Event("coco:cart-changed"));
  return cart;
}
