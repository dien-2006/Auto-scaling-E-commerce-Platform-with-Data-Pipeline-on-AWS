import {
  sellerProductFrom,
  type SellerProduct,
} from "@/lib/seller-products-client";
import { imagesFrom, type SellerImage } from "@/lib/product-images-client";

export type AdminProduct = SellerProduct & {
  shop: { shop_id: string; shop_name: string; shop_slug: string };
  images: SellerImage[];
};
export type AdminProductPage = {
  items: AdminProduct[];
  page: number;
  page_size: number;
  total: number;
};
const record = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);
const id = (v: string) =>
  /^[1-9]\d{0,18}$/.test(v) && BigInt(v) <= BigInt("9223372036854775807");
export function adminProductFrom(value: unknown): AdminProduct | null {
  if (
    !record(value) ||
    !record(value.shop) ||
    typeof value.shop.shop_id !== "string" ||
    !id(value.shop.shop_id) ||
    typeof value.shop.shop_name !== "string" ||
    typeof value.shop.shop_slug !== "string"
  )
    return null;
  const product = sellerProductFrom(value, value.shop.shop_id),
    images = imagesFrom(value.images);
  if (!product || !images) return null;
  return {
    ...product,
    shop: {
      shop_id: value.shop.shop_id,
      shop_name: value.shop.shop_name,
      shop_slug: value.shop.shop_slug,
    },
    images,
  };
}
export class AdminProductFailure extends Error {
  constructor(public code: string) {
    super(
      (
        {
          AUTH_REQUIRED: "Vui lòng đăng nhập lại.",
          TOKEN_EXPIRED: "Phiên đăng nhập đã hết hạn.",
          INVALID_TOKEN: "Phiên đăng nhập không hợp lệ.",
          USER_LOCKED: "Tài khoản đã bị khóa.",
          FORBIDDEN: "Chỉ quản trị viên được kiểm duyệt sản phẩm.",
          NOT_FOUND: "Không tìm thấy sản phẩm.",
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
      throw new AdminProductFailure(
        record(value) &&
          record(value.error) &&
          typeof value.error.code === "string"
          ? value.error.code
          : "UNAVAILABLE",
      );
    return value;
  } catch (e) {
    if (e instanceof AdminProductFailure) throw e;
    throw new AdminProductFailure("UNAVAILABLE");
  }
}
export async function fetchAdminProducts(
  page: number,
  q: string,
  shopId: string,
  active: string,
  signal: AbortSignal,
): Promise<AdminProductPage> {
  if (
    !Number.isInteger(page) ||
    page < 1 ||
    page > 2147483647 ||
    q.length > 200 ||
    (shopId && !id(shopId)) ||
    !["", "true", "false"].includes(active)
  )
    throw new AdminProductFailure("VALIDATION_ERROR");
  const query = new URLSearchParams({ page: String(page), page_size: "24" });
  if (q) query.set("q", q);
  if (shopId) query.set("shop_id", shopId);
  if (active) query.set("is_active", active);
  const value = await request(`/api/v1/admin/products?${query}`, signal);
  if (
    !record(value) ||
    value.page !== page ||
    value.page_size !== 24 ||
    !Number.isSafeInteger(value.total) ||
    Number(value.total) < 0 ||
    !Array.isArray(value.items) ||
    value.items.length > Math.min(24, Number(value.total))
  )
    throw new AdminProductFailure("UNAVAILABLE");
  const items = value.items.map(adminProductFrom);
  if (
    items.some(
      (v) =>
        !v ||
        (shopId && v.shop.shop_id !== shopId) ||
        (active && v.is_active !== (active === "true")),
    ) ||
    new Set(items.map((v) => v?.product_id)).size !== items.length
  )
    throw new AdminProductFailure("UNAVAILABLE");
  return {
    items: items as AdminProduct[],
    page,
    page_size: 24,
    total: Number(value.total),
  };
}
export async function hideAdminProduct(
  productId: string,
  signal: AbortSignal,
): Promise<AdminProduct> {
  if (!id(productId)) throw new AdminProductFailure("NOT_FOUND");
  const csrf = await request("/api/v1/auth/csrf", signal);
  if (
    !record(csrf) ||
    !record(csrf.data) ||
    typeof csrf.data.csrf_token !== "string"
  )
    throw new AdminProductFailure("UNAVAILABLE");
  const value = await request(
    `/api/v1/admin/products/${productId}/hide`,
    signal,
    { method: "POST", headers: { "X-CSRF-Token": csrf.data.csrf_token } },
  );
  const result = adminProductFrom(record(value) ? value.data : null);
  if (!result || result.product_id !== productId || result.is_active)
    throw new AdminProductFailure("UNAVAILABLE");
  return result;
}
