import {
  sellerShopFrom,
  shopStatuses,
  type SellerShop,
} from "@/lib/seller-shop-client";

export type AdminShop = SellerShop;
export type ShopStatus = AdminShop["shop_status"];
export type AdminShopPage = {
  items: AdminShop[];
  page: number;
  page_size: number;
  total: number;
};
const record = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);
const id = (v: string) =>
  /^[1-9]\d{0,18}$/.test(v) && BigInt(v) <= BigInt("9223372036854775807");
export function adminShopFrom(value: unknown): AdminShop | null {
  // Admin may inspect any shop; validate the shared private shape with that row's owner.
  return record(value) && typeof value.owner_user_id === "string"
    ? sellerShopFrom(value, value.owner_user_id)
    : null;
}
export class AdminShopFailure extends Error {
  constructor(public code: string) {
    super(
      (
        {
          INVALID_TRANSITION:
            "Trạng thái gian hàng đã thay đổi hoặc không hợp lệ. Hãy tải lại danh sách.",
          AUTH_REQUIRED: "Vui lòng đăng nhập lại.",
          TOKEN_EXPIRED: "Phiên đăng nhập đã hết hạn.",
          INVALID_TOKEN: "Phiên đăng nhập không hợp lệ.",
          USER_LOCKED: "Tài khoản đã bị khóa.",
          FORBIDDEN: "Chỉ quản trị viên được phê duyệt gian hàng.",
          NOT_FOUND: "Không tìm thấy gian hàng.",
          CSRF_FAILED: "Phiên xác thực đã thay đổi. Hãy tải lại trang.",
        } as Record<string, string>
      )[code] ??
        "Chưa xác minh được kết quả. Hãy tải lại danh sách để kiểm tra.",
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
      throw new AdminShopFailure(
        record(value) &&
          record(value.error) &&
          typeof value.error.code === "string"
          ? value.error.code
          : "UNAVAILABLE",
      );
    return value;
  } catch (e) {
    if (e instanceof AdminShopFailure) throw e;
    throw new AdminShopFailure("UNAVAILABLE");
  }
}
export async function fetchAdminShops(
  page: number,
  q: string,
  status: string,
  signal: AbortSignal,
): Promise<AdminShopPage> {
  if (
    !Number.isInteger(page) ||
    page < 1 ||
    page > 2147483647 ||
    q.length > 200 ||
    (status && !Object.hasOwn(shopStatuses, status))
  )
    throw new AdminShopFailure("NOT_FOUND");
  const query = new URLSearchParams({ page: String(page), page_size: "24" });
  if (q) query.set("q", q);
  if (status) query.set("status", status);
  const value = await request(`/api/v1/admin/shops?${query}`, signal);
  if (
    !record(value) ||
    value.page !== page ||
    value.page_size !== 24 ||
    !Number.isSafeInteger(value.total) ||
    Number(value.total) < 0 ||
    !Array.isArray(value.items) ||
    value.items.length > Math.min(24, Number(value.total))
  )
    throw new AdminShopFailure("UNAVAILABLE");
  const items = value.items.map(adminShopFrom);
  if (
    items.some((v) => !v || (status && v.shop_status !== status)) ||
    new Set(items.map((v) => v?.shop_id)).size !== items.length
  )
    throw new AdminShopFailure("UNAVAILABLE");
  return {
    items: items as AdminShop[],
    page,
    page_size: 24,
    total: Number(value.total),
  };
}
export async function changeShopStatus(
  shop: AdminShop,
  target: ShopStatus,
  signal: AbortSignal,
): Promise<AdminShop> {
  if (
    !id(shop.shop_id) ||
    !Object.hasOwn(shopStatuses, shop.shop_status) ||
    !Object.hasOwn(shopStatuses, target)
  )
    throw new AdminShopFailure("NOT_FOUND");
  const csrf = await request("/api/v1/auth/csrf", signal);
  if (
    !record(csrf) ||
    !record(csrf.data) ||
    typeof csrf.data.csrf_token !== "string"
  )
    throw new AdminShopFailure("UNAVAILABLE");
  const value = await request(
    `/api/v1/admin/shops/${shop.shop_id}/status`,
    signal,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrf.data.csrf_token,
      },
      body: JSON.stringify({
        expected_status: shop.shop_status,
        shop_status: target,
      }),
    },
  );
  const result = adminShopFrom(record(value) ? value.data : null);
  if (
    !result ||
    result.shop_id !== shop.shop_id ||
    result.owner_user_id !== shop.owner_user_id ||
    result.shop_status !== target
  )
    throw new AdminShopFailure("UNAVAILABLE");
  return result;
}
