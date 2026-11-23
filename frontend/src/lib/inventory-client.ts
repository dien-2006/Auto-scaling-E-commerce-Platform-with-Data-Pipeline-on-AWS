export type Inventory = {
  product_id: string;
  quantity: number;
  updated_at: string;
};
const record = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);
const id = (v: string) =>
  /^[1-9]\d{0,18}$/.test(v) && BigInt(v) <= BigInt("9223372036854775807");
const stock = (v: unknown): v is number =>
  typeof v === "number" && Number.isInteger(v) && v >= 0 && v <= 2147483647;
export function inventoryFrom(v: unknown, productId: string): Inventory | null {
  if (
    !record(v) ||
    !id(productId) ||
    v.product_id !== productId ||
    !stock(v.quantity) ||
    typeof v.updated_at !== "string" ||
    !Number.isFinite(Date.parse(v.updated_at))
  )
    return null;
  return {
    product_id: productId,
    quantity: v.quantity,
    updated_at: v.updated_at,
  };
}
export class InventoryFailure extends Error {
  constructor(public code: string) {
    super(
      (
        {
          STALE_INVENTORY:
            "Tồn kho đã thay đổi. Tải lại và kiểm tra số lượng trước khi xác nhận điều chỉnh mới.",
          INVALID_STOCK: "Số lượng sau điều chỉnh phải từ 0 đến 2147483647.",
          INVENTORY_UNAVAILABLE:
            "Sản phẩm chưa có bản ghi tồn kho. Vui lòng liên hệ quản trị viên.",
          NOT_FOUND: "Không tìm thấy sản phẩm thuộc gian hàng của bạn.",
          VALIDATION_ERROR: "Số lượng điều chỉnh chưa hợp lệ.",
          AUTH_REQUIRED: "Vui lòng đăng nhập lại.",
          TOKEN_EXPIRED: "Phiên đăng nhập đã hết hạn.",
          INVALID_TOKEN: "Phiên đăng nhập không hợp lệ.",
          USER_LOCKED: "Tài khoản đã bị khóa.",
          SHOP_NOT_APPROVED: "Gian hàng không được phép điều chỉnh tồn kho.",
          FORBIDDEN: "Bạn không có quyền điều chỉnh tồn kho.",
          CSRF_FAILED: "Phiên xác thực đã thay đổi. Hãy tải lại trang.",
        } as Record<string, string>
      )[code] ??
        "Chưa xác minh được kết quả. Tải lại tồn kho và kiểm tra trước khi tiếp tục.",
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
      throw new InventoryFailure(
        record(value) &&
        record(value.error) &&
        typeof value.error.code === "string"
          ? value.error.code
          : "UNAVAILABLE",
      );
    return value;
  } catch (e) {
    if (e instanceof InventoryFailure) throw e;
    throw new InventoryFailure("UNAVAILABLE");
  }
}
export async function readInventory(
  productId: string,
  signal: AbortSignal,
): Promise<Inventory> {
  if (!id(productId)) throw new InventoryFailure("NOT_FOUND");
  const value = await request(
    `/api/v1/seller/products/${productId}/inventory`,
    signal,
  );
  const inventory = inventoryFrom(record(value) ? value.data : null, productId);
  if (!inventory) throw new InventoryFailure("UNAVAILABLE");
  return inventory;
}
export async function adjustInventory(
  productId: string,
  expected: number,
  delta: number,
  signal: AbortSignal,
): Promise<Inventory> {
  if (
    !id(productId) ||
    !stock(expected) ||
    !Number.isInteger(delta) ||
    !delta ||
    Math.abs(delta) > 2147483647 ||
    !stock(expected + delta)
  )
    throw new InventoryFailure("VALIDATION_ERROR");
  const csrf = await request("/api/v1/auth/csrf", signal);
  if (
    !record(csrf) ||
    !record(csrf.data) ||
    typeof csrf.data.csrf_token !== "string"
  )
    throw new InventoryFailure("UNAVAILABLE");
  const value = await request(
    `/api/v1/seller/products/${productId}/inventory/adjustments`,
    signal,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrf.data.csrf_token,
        "X-Expected-Quantity": String(expected),
      },
      body: JSON.stringify({ delta }),
    },
  );
  const inventory = inventoryFrom(record(value) ? value.data : null, productId);
  if (!inventory || inventory.quantity !== expected + delta)
    throw new InventoryFailure("UNAVAILABLE");
  return inventory;
}
