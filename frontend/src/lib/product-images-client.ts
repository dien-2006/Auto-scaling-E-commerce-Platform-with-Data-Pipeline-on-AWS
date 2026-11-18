export type SellerImage = {
  product_image_id: string;
  url: string | null;
  is_primary: boolean;
  sort_order: number;
};
const record = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);
const id = (v: unknown): v is string =>
  typeof v === "string" &&
  /^[1-9]\d{0,18}$/.test(v) &&
  BigInt(v) <= BigInt("9223372036854775807");
export function httpsUrl(v: unknown): v is string {
  if (typeof v !== "string") return false;
  try {
    const u = new URL(v);
    return u.protocol === "https:" && !u.username && !u.password;
  } catch {
    return false;
  }
}
export class ImageFailure extends Error {
  constructor(public code: string) {
    super(
      (
        {
          STORAGE_NOT_CONFIGURED: "Chưa cấu hình kho ảnh S3.",
          INVALID_IMAGE:
            "Ảnh không hợp lệ hoặc đã hết hạn. Chọn JPEG, PNG hoặc WebP tối đa 5 MiB và 4096 px mỗi chiều.",
          IMAGE_EXISTS:
            "Ảnh đã được liên kết. Tải lại danh sách ảnh để kiểm tra.",
          IMAGE_CONFLICT: "Ảnh đã thay đổi. Hãy tải một ảnh mới.",
          NOT_FOUND: "Không tìm thấy sản phẩm hoặc ảnh.",
          VALIDATION_ERROR: "Thông tin ảnh chưa hợp lệ.",
          AUTH_REQUIRED: "Phiên đăng nhập đã hết hạn.",
          TOKEN_EXPIRED: "Phiên đăng nhập đã hết hạn.",
          INVALID_TOKEN: "Phiên đăng nhập đã hết hạn.",
          USER_LOCKED: "Tài khoản đã bị khóa.",
          SHOP_NOT_APPROVED: "Gian hàng không được phép quản lý ảnh.",
          FORBIDDEN: "Bạn không có quyền quản lý ảnh.",
          CSRF_FAILED: "Phiên xác thực đã thay đổi. Hãy tải lại trang.",
        } as Record<string, string>
      )[code] ??
        "Chưa xác minh được kết quả. Tải lại danh sách ảnh trước khi thao tác tiếp.",
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
    if (response.status === 204) return null;
    const value: unknown = await response.json();
    if (!response.ok)
      throw new ImageFailure(
        record(value) &&
        record(value.error) &&
        typeof value.error.code === "string"
          ? value.error.code
          : "UNAVAILABLE",
      );
    return value;
  } catch (e) {
    if (e instanceof ImageFailure) throw e;
    throw new ImageFailure("UNAVAILABLE");
  }
}
export function imagesFrom(value: unknown): SellerImage[] | null {
  if (!Array.isArray(value)) return null;
  const items: SellerImage[] = [];
  for (const v of value) {
    if (
      !record(v) ||
      !id(v.product_image_id) ||
      !(v.url === null || httpsUrl(v.url)) ||
      typeof v.is_primary !== "boolean" ||
      !Number.isInteger(v.sort_order) ||
      Number(v.sort_order) < 0 ||
      Number(v.sort_order) > 2147483647
    )
      return null;
    items.push({
      product_image_id: v.product_image_id,
      url: v.url,
      is_primary: v.is_primary,
      sort_order: Number(v.sort_order),
    });
  }
  return new Set(items.map((v) => v.product_image_id)).size === items.length &&
    items.filter((v) => v.is_primary).length <= 1
    ? items
    : null;
}
export async function readImages(
  productId: string,
  shopId: string,
  signal: AbortSignal,
) {
  if (!id(productId) || !id(shopId)) throw new ImageFailure("NOT_FOUND");
  const value = await request(`/api/v1/seller/products/${productId}`, signal);
  if (
    !record(value) ||
    !record(value.data) ||
    value.data.product_id !== productId ||
    !record(value.data.shop) ||
    value.data.shop.shop_id !== shopId
  )
    throw new ImageFailure("UNAVAILABLE");
  const images = imagesFrom(value.data.images);
  if (!images) throw new ImageFailure("UNAVAILABLE");
  return images;
}
async function mutate(
  productId: string,
  signal: AbortSignal,
  resource: string,
  method: "POST" | "PATCH" | "DELETE",
  data?: Record<string, unknown>,
) {
  if (!id(productId)) throw new ImageFailure("NOT_FOUND");
  const csrf = await request("/api/v1/auth/csrf", signal);
  if (
    !record(csrf) ||
    !record(csrf.data) ||
    typeof csrf.data.csrf_token !== "string"
  )
    throw new ImageFailure("UNAVAILABLE");
  return request(
    `/api/v1/seller/products/${productId}/images${resource ? `/${resource}` : ""}`,
    signal,
    {
      method,
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrf.data.csrf_token,
      },
      ...(data ? { body: JSON.stringify(data) } : {}),
    },
  );
}
export async function uploadImage(
  productId: string,
  file: File,
  primary: boolean,
  signal: AbortSignal,
) {
  if (
    !["image/jpeg", "image/png", "image/webp"].includes(file.type) ||
    file.size < 1 ||
    file.size > 5 * 1024 * 1024
  )
    throw new ImageFailure("INVALID_IMAGE");
  const grant = await mutate(productId, signal, "upload-url", "POST", {
    content_type: file.type,
    size_bytes: file.size,
  });
  if (
    !record(grant) ||
    !httpsUrl(grant.upload_url) ||
    !record(grant.fields) ||
    typeof grant.image_key !== "string" ||
    grant.fields.key !== grant.image_key ||
    typeof grant.expires_at !== "string" ||
    !Number.isFinite(Date.parse(grant.expires_at)) ||
    Date.parse(grant.expires_at) <= Date.now()
  )
    throw new ImageFailure("UNAVAILABLE");
  const body = new FormData();
  for (const [key, value] of Object.entries(grant.fields)) {
    if (typeof value !== "string") throw new ImageFailure("UNAVAILABLE");
    body.append(key, value);
  }
  body.append("file", file);
  try {
    const response = await fetch(grant.upload_url, {
      method: "POST",
      body,
      credentials: "omit",
      referrerPolicy: "no-referrer",
      signal: AbortSignal.any([signal, AbortSignal.timeout(60000)]),
    });
    if (!response.ok) throw new ImageFailure("UNAVAILABLE");
  } catch (e) {
    if (e instanceof ImageFailure) throw e;
    throw new ImageFailure("UNAVAILABLE");
  }
  const value = await mutate(productId, signal, "", "POST", {
    image_key: grant.image_key,
    is_primary: primary,
    sort_order: 0,
  });
  if (
    !record(value) ||
    !record(value.data) ||
    value.data.product_id !== productId ||
    !imagesFrom([value.data])
  )
    throw new ImageFailure("UNAVAILABLE");
}
export async function updateImage(
  productId: string,
  imageId: string,
  signal: AbortSignal,
  patch: { is_primary?: boolean; sort_order?: number } | null,
) {
  if (!id(imageId)) throw new ImageFailure("NOT_FOUND");
  const data = patch
    ? {
        ...(patch.is_primary !== undefined
          ? { is_primary: patch.is_primary }
          : {}),
        ...(patch.sort_order !== undefined
          ? { sort_order: patch.sort_order }
          : {}),
      }
    : undefined;
  const value = await mutate(
    productId,
    signal,
    imageId,
    patch ? "PATCH" : "DELETE",
    data,
  );
  if (
    patch &&
    (!record(value) ||
      !record(value.data) ||
      value.data.product_id !== productId ||
      value.data.product_image_id !== imageId ||
      !imagesFrom([value.data]))
  )
    throw new ImageFailure("UNAVAILABLE");
}
