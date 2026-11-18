import type { Account } from "@/lib/auth-contract";

export const shopStatuses = {
  PENDING: {
    label: "Chờ phê duyệt",
    message:
      "Hồ sơ đã được gửi. Bạn có thể cập nhật thông tin trong lúc chờ Admin phê duyệt.",
  },
  APPROVED: {
    label: "Đã phê duyệt",
    message:
      "Gian hàng đã được duyệt và được phép bán. Bạn có thể xem trang shop công khai.",
  },
  REJECTED: {
    label: "Đã từ chối",
    message:
      "Hồ sơ chưa được phê duyệt. Hiện chưa hỗ trợ gửi duyệt lại; việc sửa thông tin không thay đổi trạng thái này.",
  },
  LOCKED: {
    label: "Đã khóa",
    message:
      "Gian hàng đang bị khóa và không nhận đơn mới. Cập nhật hồ sơ không mở khóa gian hàng.",
  },
} as const;
export type SellerShop = {
  shop_id: string;
  owner_user_id: string;
  shop_name: string;
  shop_slug: string;
  description: string | null;
  contact_email: string | null;
  logo_url: null;
  shop_status: keyof typeof shopStatuses;
  created_at: string;
  updated_at: string;
};
export type ShopInput = {
  shop_name: string;
  shop_slug?: string;
  description: string | null;
  contact_email: string | null;
};
const record = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);
const id = (v: unknown): v is string =>
  typeof v === "string" &&
  /^[1-9]\d{0,18}$/.test(v) &&
  BigInt(v) <= BigInt("9223372036854775807");
export function sellerShopFrom(
  value: unknown,
  ownerId: string,
): SellerShop | null {
  if (
    !record(value) ||
    !id(value.shop_id) ||
    !id(value.owner_user_id) ||
    value.owner_user_id !== ownerId ||
    typeof value.shop_name !== "string" ||
    typeof value.shop_slug !== "string" ||
    !(value.description === null || typeof value.description === "string") ||
    !(
      value.contact_email === null || typeof value.contact_email === "string"
    ) ||
    value.logo_url !== null ||
    typeof value.shop_status !== "string" ||
    !Object.hasOwn(shopStatuses, value.shop_status) ||
    typeof value.created_at !== "string" ||
    !Number.isFinite(Date.parse(value.created_at)) ||
    typeof value.updated_at !== "string" ||
    !Number.isFinite(Date.parse(value.updated_at))
  )
    return null;
  return {
    shop_id: value.shop_id,
    owner_user_id: value.owner_user_id,
    shop_name: value.shop_name,
    shop_slug: value.shop_slug,
    description: value.description,
    contact_email: value.contact_email,
    logo_url: null,
    shop_status: value.shop_status as SellerShop["shop_status"],
    created_at: value.created_at,
    updated_at: value.updated_at,
  };
}
export function shopInputError(
  input: ShopInput,
  create: boolean,
): string | null {
  const length = Array.from(input.shop_name.trim()).length;
  if (!length || length > 150) return "Tên gian hàng cần từ 1 đến 150 ký tự.";
  if (
    create &&
    (!input.shop_slug ||
      input.shop_slug.length > 160 ||
      !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(input.shop_slug))
  )
    return "Đường dẫn dùng chữ thường không dấu, số và dấu gạch nối; tối đa 160 ký tự.";
  if (input.description !== null && Array.from(input.description).length > 5000)
    return "Mô tả tối đa 5.000 ký tự.";
  if (
    input.contact_email !== null &&
    (Array.from(input.contact_email).length > 255 ||
      !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input.contact_email))
  )
    return "Email liên hệ chưa hợp lệ.";
  return null;
}
const messages: Record<string, string> = {
  SHOP_EXISTS: "Tài khoản đã có gian hàng. Hãy tải lại hồ sơ để kiểm tra.",
  SHOP_IN_USE: "Gian hàng có sản phẩm hoặc lịch sử liên quan, không thể xóa.",
  SLUG_EXISTS: "Đường dẫn này đã được sử dụng. Vui lòng chọn đường dẫn khác.",
  VALIDATION_ERROR: "Thông tin chưa hợp lệ. Vui lòng kiểm tra các trường nhập.",
  CSRF_FAILED:
    "Phiên xác thực đã thay đổi. Vui lòng kiểm tra phiên rồi thử lại.",
  USER_LOCKED: "Tài khoản đã bị khóa. Vui lòng liên hệ quản trị viên.",
};
export class ShopFailure extends Error {
  constructor(public code: string) {
    super(
      messages[code] ??
        (["AUTH_REQUIRED", "INVALID_TOKEN", "TOKEN_EXPIRED"].includes(code)
          ? "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại."
          : "Chưa kết nối được gian hàng. Vui lòng tải lại hồ sơ để kiểm tra."),
    );
  }
}
async function request(
  path: string,
  init?: RequestInit,
): Promise<{ response: Response; payload: unknown }> {
  try {
    const response = await fetch(path, {
      ...init,
      credentials: "same-origin",
      cache: "no-store",
      signal: init?.signal
        ? AbortSignal.any([init.signal, AbortSignal.timeout(20000)])
        : AbortSignal.timeout(20000),
    });
    const payload: unknown =
      response.status === 204 ? null : await response.json();
    if (!response.ok)
      throw new ShopFailure(
        record(payload) &&
          record(payload.error) &&
          typeof payload.error.code === "string"
          ? payload.error.code
          : "UNAVAILABLE",
      );
    return { response, payload };
  } catch (error) {
    if (error instanceof ShopFailure) throw error;
    throw new ShopFailure("UNAVAILABLE");
  }
}
export async function deleteSellerShop(
  shopId: string,
  signal: AbortSignal,
): Promise<void> {
  if (
    !/^[1-9]\d{0,18}$/.test(shopId) ||
    BigInt(shopId) > BigInt("9223372036854775807")
  )
    throw new ShopFailure("NOT_FOUND");
  const { payload: csrf } = await request("/api/v1/auth/csrf", { signal });
  if (
    !record(csrf) ||
    !record(csrf.data) ||
    typeof csrf.data.csrf_token !== "string"
  )
    throw new ShopFailure("UNAVAILABLE");
  const { response } = await request(`/api/v1/seller/shop/${shopId}`, {
    method: "DELETE",
    signal,
    headers: { "X-CSRF-Token": csrf.data.csrf_token },
  });
  if (response.status !== 204) throw new ShopFailure("UNAVAILABLE");
}

export async function fetchSellerShop(
  ownerId: string,
  signal?: AbortSignal,
): Promise<SellerShop | null> {
  let payload: unknown;
  try {
    ({ payload } = await request("/api/v1/seller/shop", { signal }));
  } catch (error) {
    if (error instanceof ShopFailure && error.code === "NOT_FOUND") return null;
    throw error;
  }
  const shop = sellerShopFrom(record(payload) ? payload.data : null, ownerId);
  if (!shop) throw new ShopFailure("UNAVAILABLE");
  return shop;
}
export async function saveSellerShop(
  method: "POST" | "PATCH",
  input: ShopInput,
  ownerId: Account["user_id"],
  signal?: AbortSignal,
): Promise<SellerShop> {
  const issue = shopInputError(input, method === "POST");
  if (issue) throw new Error(issue);
  const { payload: csrf } = await request("/api/v1/auth/csrf", { signal });
  if (
    !record(csrf) ||
    !record(csrf.data) ||
    typeof csrf.data.csrf_token !== "string"
  )
    throw new ShopFailure("UNAVAILABLE");
  // Construct the allowlisted body; never forward status/owner/logo/IDs.
  const body = {
    shop_name: input.shop_name.trim(),
    description: input.description?.trim() || null,
    contact_email: input.contact_email?.trim() || null,
    ...(method === "POST" ? { shop_slug: input.shop_slug } : {}),
  };
  const { response, payload } = await request("/api/v1/seller/shop", {
    method,
    signal,
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": csrf.data.csrf_token,
    },
    body: JSON.stringify(body),
  });
  const shop = sellerShopFrom(record(payload) ? payload.data : null, ownerId);
  if (!shop || response.status !== (method === "POST" ? 201 : 200))
    throw new ShopFailure("UNAVAILABLE");
  return shop;
}
