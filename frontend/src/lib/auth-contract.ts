export type Account = {
  user_id: string;
  email: string | null;
  full_name: string;
  phone: string | null;
  user_role: "USER" | "ADMIN";
  user_status: "ACTIVE";
  owned_shop: {
    shop_id: string;
    shop_status: "PENDING" | "APPROVED" | "REJECTED" | "LOCKED";
  } | null;
};
const record = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);
const id = (value: unknown): value is string =>
  typeof value === "string" &&
  /^[1-9]\d{0,18}$/.test(value) &&
  BigInt(value) <= BigInt("9223372036854775807");
export function accountFrom(value: unknown): Account | null {
  if (
    !record(value) ||
    !id(value.user_id) ||
    (value.email !== null && typeof value.email !== "string") ||
    typeof value.full_name !== "string" ||
    !(value.phone === null || typeof value.phone === "string") ||
    !["USER", "ADMIN"].includes(String(value.user_role)) ||
    value.user_status !== "ACTIVE"
  )
    return null;
  const shop = value.owned_shop;
  if (
    shop !== null &&
    (!record(shop) ||
      !id(shop.shop_id) ||
      !["PENDING", "APPROVED", "REJECTED", "LOCKED"].includes(
        String(shop.shop_status),
      ))
  )
    return null;
  return {
    user_id: value.user_id,
    email: value.email,
    full_name: value.full_name,
    phone: value.phone,
    user_role: value.user_role as Account["user_role"],
    user_status: "ACTIVE",
    owned_shop:
      shop === null
        ? null
        : {
            shop_id: (shop as Record<string, unknown>).shop_id as string,
            shop_status: (shop as Record<string, unknown>)
              .shop_status as NonNullable<Account["owned_shop"]>["shop_status"],
          },
  };
}
export function safeReturnPath(value: unknown): string {
  if (
    typeof value !== "string" ||
    value.length > 2048 ||
    !value.startsWith("/") ||
    value.startsWith("//")
  )
    return "/";
  try {
    const decoded = decodeURIComponent(value);
    if (/[\\\u0000-\u0020\u007f]/.test(decoded) || decoded.startsWith("//"))
      return "/";
    const url = new URL(value, "https://coco.invalid");
    if (
      url.origin !== "https://coco.invalid" ||
      !/^\/(?:$|admin\/(?:users|shops|products|categories)$|san-pham(?:\/|$)|gian-hang(?:\/|$)|tai-khoan(?:\/|$)|kenh-nguoi-ban(?:\/|$)|gio-hang$|thanh-toan$)/.test(
        url.pathname,
      )
    )
      return "/";
    return url.pathname + url.search + url.hash;
  } catch {
    return "/";
  }
}
export const authMessages: Record<string, string> = {
  OTP_INVALID: "Mã không đúng, đã hết hạn hoặc đã được sử dụng. Mỗi mã chỉ được thử tối đa 5 lần.",
  OTP_NOT_CONFIGURED: "Dịch vụ gửi mã xác nhận chưa được cấu hình.",
  OTP_UNAVAILABLE: "Chức năng xác minh chưa sẵn sàng. Vui lòng thử lại sau.",
  OTP_REQUIRED: "Vui lòng xác minh OTP trước khi tạo tài khoản.",
  OTP_DELIVERY_FAILED: "Chưa gửi được mã xác nhận. Vui lòng thử lại sau.",
  NOT_FOUND: "Không tìm thấy tài nguyên. Vui lòng tải lại danh sách.",
  INVALID_CREDENTIALS: "Email hoặc mật khẩu không đúng.",
  EMAIL_EXISTS: "Email này đã được sử dụng. Hãy đăng nhập hoặc dùng email khác.",
  USER_LOCKED: "Tài khoản đã bị khóa. Vui lòng liên hệ quản trị viên.",
  AUTH_REQUIRED: "Vui lòng đăng nhập để tiếp tục.",
  INVALID_TOKEN: "Phiên đăng nhập không hợp lệ. Vui lòng đăng nhập lại.",
  TOKEN_EXPIRED: "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.",
  CSRF_FAILED: "Phiên xác thực không hợp lệ. Hãy tải lại trang rồi gửi lại. Nếu lỗi tiếp tục, vui lòng liên hệ quản trị viên.",
  VALIDATION_ERROR: "Thông tin chưa hợp lệ. Vui lòng kiểm tra lại.",
  NETWORK_ERROR: "Không kết nối được máy chủ. Hãy kiểm tra kết nối mạng rồi thử lại.",
  REQUEST_TIMEOUT: "Máy chủ phản hồi quá lâu. Vui lòng thử lại sau.",
  RATE_LIMITED: "Bạn đã gửi quá nhiều yêu cầu. Vui lòng đợi một lúc rồi thử lại.",
  SERVER_ERROR: "Hệ thống đang gặp sự cố. Vui lòng thử lại sau.",
  DEPENDENCY_UNAVAILABLE: "Dịch vụ tạm thời không sẵn sàng. Vui lòng thử lại sau.",
  AUTH_NOT_CONFIGURED: "Đăng nhập chưa sẵn sàng. Vui lòng thử lại sau.",
};

export const registrationPasswordHint =
  "Mật khẩu từ 9–128 ký tự, có chữ hoa (A–Z), số (0–9) và ký tự đặc biệt (ví dụ !, @, #).";
export function validRegistrationPassword(value: string): boolean {
  const length = Array.from(value).length;
  return (
    length >= 9 &&
    length <= 128 &&
    /[A-Z]/.test(value) &&
    /[0-9]/.test(value) &&
    /[\p{P}\p{S}]/u.test(value)
  );
}
