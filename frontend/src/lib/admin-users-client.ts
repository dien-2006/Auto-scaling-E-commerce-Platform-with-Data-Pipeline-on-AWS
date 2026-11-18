export type AdminUser = {
  user_id: string;
  email: string | null;
  full_name: string;
  phone: string | null;
  user_role: "USER" | "ADMIN";
  user_status: "ACTIVE" | "LOCKED";
  created_at: string;
};
export type AdminUserPage = {
  items: AdminUser[];
  page: number;
  page_size: number;
  total: number;
};
const record = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);
const validId = (v: unknown): v is string =>
  typeof v === "string" &&
  /^[1-9]\d{0,18}$/.test(v) &&
  BigInt(v) <= BigInt("9223372036854775807");
export function adminUserFrom(value: unknown): AdminUser | null {
  if (
    !record(value) ||
    !validId(value.user_id) ||
    (value.email !== null && typeof value.email !== "string") ||
    typeof value.full_name !== "string" ||
    !(value.phone === null || typeof value.phone === "string") ||
    !["USER", "ADMIN"].includes(String(value.user_role)) ||
    !["ACTIVE", "LOCKED"].includes(String(value.user_status)) ||
    typeof value.created_at !== "string" ||
    !Number.isFinite(Date.parse(value.created_at))
  )
    return null;
  return {
    user_id: value.user_id,
    email: value.email,
    full_name: value.full_name,
    phone: value.phone,
    user_role: value.user_role as AdminUser["user_role"],
    user_status: value.user_status as AdminUser["user_status"],
    created_at: value.created_at,
  };
}
export class AdminUserFailure extends Error {
  constructor(public code: string) {
    super(
      (
        {
          AUTH_REQUIRED: "Vui lòng đăng nhập lại.",
          TOKEN_EXPIRED: "Phiên đăng nhập đã hết hạn.",
          INVALID_TOKEN: "Phiên đăng nhập không hợp lệ.",
          USER_LOCKED: "Tài khoản đã bị khóa.",
          FORBIDDEN: "Chỉ quản trị viên được quản lý người dùng.",
          ADMIN_PROTECTED: "Tài khoản quản trị viên chỉ được xem.",
          NOT_FOUND: "Không tìm thấy người dùng.",
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
      throw new AdminUserFailure(
        record(value) &&
          record(value.error) &&
          typeof value.error.code === "string"
          ? value.error.code
          : "UNAVAILABLE",
      );
    return value;
  } catch (e) {
    if (e instanceof AdminUserFailure) throw e;
    throw new AdminUserFailure("UNAVAILABLE");
  }
}
export async function fetchAdminUsers(
  page: number,
  q: string,
  status: string,
  signal: AbortSignal,
): Promise<AdminUserPage> {
  if (
    !Number.isInteger(page) ||
    page < 1 ||
    page > 2147483647 ||
    q.length > 200 ||
    (status && !["ACTIVE", "LOCKED"].includes(status))
  )
    throw new AdminUserFailure("NOT_FOUND");
  const query = new URLSearchParams({ page: String(page), page_size: "24" });
  if (q) query.set("q", q);
  if (status) query.set("status", status);
  const value = await request(`/api/v1/admin/users?${query}`, signal);
  if (
    !record(value) ||
    value.page !== page ||
    value.page_size !== 24 ||
    !Number.isSafeInteger(value.total) ||
    Number(value.total) < 0 ||
    !Array.isArray(value.items) ||
    value.items.length > Math.min(24, Number(value.total))
  )
    throw new AdminUserFailure("UNAVAILABLE");
  const items = value.items.map(adminUserFrom);
  if (
    items.some((v) => !v || (status && v.user_status !== status)) ||
    new Set(items.map((v) => v?.user_id)).size !== items.length
  )
    throw new AdminUserFailure("UNAVAILABLE");
  return {
    items: items as AdminUser[],
    page,
    page_size: 24,
    total: Number(value.total),
  };
}
export async function changeUserStatus(
  userId: string,
  status: AdminUser["user_status"],
  signal: AbortSignal,
): Promise<AdminUser> {
  if (!validId(userId) || !["ACTIVE", "LOCKED"].includes(status))
    throw new AdminUserFailure("NOT_FOUND");
  const csrf = await request("/api/v1/auth/csrf", signal);
  if (
    !record(csrf) ||
    !record(csrf.data) ||
    typeof csrf.data.csrf_token !== "string"
  )
    throw new AdminUserFailure("UNAVAILABLE");
  const value = await request(`/api/v1/admin/users/${userId}/status`, signal, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": csrf.data.csrf_token,
    },
    body: JSON.stringify({ user_status: status }),
  });
  const result = adminUserFrom(record(value) ? value.data : null);
  if (!result || result.user_id !== userId || result.user_status !== status)
    throw new AdminUserFailure("UNAVAILABLE");
  return result;
}
