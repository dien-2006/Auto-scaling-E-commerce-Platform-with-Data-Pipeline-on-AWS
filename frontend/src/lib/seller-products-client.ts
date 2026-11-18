export type SellerProduct = {
  product_id: string;
  category_id: string;
  product_name: string;
  sku: string;
  description: string | null;
  price: string;
  is_active: boolean;
  available_quantity: number;
  created_at: string;
  updated_at: string;
  shop: { shop_id: string };
};
export type ProductInput = {
  product_name: string;
  sku: string;
  category_id: string;
  description: string | null;
  price: string;
  initial_quantity?: number;
};
export type SellerPage = {
  items: SellerProduct[];
  page: number;
  page_size: number;
  total: number;
  image_upload_enabled: boolean;
};
const record = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);
const id = (v: unknown): v is string =>
  typeof v === "string" &&
  /^[1-9]\d{0,18}$/.test(v) &&
  BigInt(v) <= BigInt("9223372036854775807");
export function sellerProductFrom(
  v: unknown,
  shopId: string,
): SellerProduct | null {
  if (
    !record(v) ||
    !id(v.product_id) ||
    !id(v.category_id) ||
    !record(v.shop) ||
    v.shop.shop_id !== shopId ||
    typeof v.product_name !== "string" ||
    typeof v.sku !== "string" ||
    !(v.description === null || typeof v.description === "string") ||
    typeof v.price !== "string" ||
    !/^\d{1,12}(\.\d{1,2})?$/.test(v.price) ||
    typeof v.is_active !== "boolean" ||
    !Number.isInteger(v.available_quantity) ||
    Number(v.available_quantity) < 0 ||
    Number(v.available_quantity) > 2147483647 ||
    typeof v.created_at !== "string" ||
    !Number.isFinite(Date.parse(v.created_at)) ||
    typeof v.updated_at !== "string" ||
    !Number.isFinite(Date.parse(v.updated_at))
  )
    return null;
  return {
    product_id: v.product_id,
    category_id: v.category_id,
    product_name: v.product_name,
    sku: v.sku,
    description: v.description,
    price: v.price,
    is_active: v.is_active,
    available_quantity: Number(v.available_quantity),
    created_at: v.created_at,
    updated_at: v.updated_at,
    shop: { shop_id: shopId },
  };
}
export class ProductFailure extends Error {
  constructor(public code: string) {
    super(
      (
        {
          SKU_EXISTS: "SKU đã tồn tại trong gian hàng.",
          PRODUCT_IN_USE:
            "Sản phẩm có giỏ hàng, đơn hoặc lịch sử liên quan. Hãy dùng Ẩn sản phẩm.",
          INVALID_CATEGORY:
            "Danh mục đã bị ẩn hoặc không hợp lệ. Hãy tải lại trang.",
          SHOP_NOT_APPROVED: "Gian hàng cần được phê duyệt và đang hoạt động.",
          FORBIDDEN: "Bạn chưa có gian hàng hoặc không có quyền truy cập.",
          AUTH_REQUIRED: "Vui lòng đăng nhập lại.",
          TOKEN_EXPIRED: "Phiên đăng nhập đã hết hạn.",
          USER_LOCKED: "Tài khoản đã bị khóa.",
          CSRF_FAILED: "Phiên xác thực đã thay đổi. Hãy tải lại để kiểm tra.",
          VALIDATION_ERROR: "Kiểm tra lại thông tin sản phẩm.",
          NOT_FOUND: "Không tìm thấy sản phẩm trong gian hàng của bạn.",
        } as Record<string, string>
      )[code] ??
        "Chưa xác minh được kết quả. Tải lại danh sách trước khi tiếp tục.",
    );
  }
}
async function request(path: string, signal: AbortSignal, init?: RequestInit) {
  try {
    const response = await fetch(path, {
      ...init,
      signal: AbortSignal.any([signal, AbortSignal.timeout(20000)]),
      credentials: "same-origin",
      cache: "no-store",
    });
    const value: unknown =
      response.status === 204 ? null : await response.json();
    if (!response.ok)
      throw new ProductFailure(
        record(value) &&
          record(value.error) &&
          typeof value.error.code === "string"
          ? value.error.code
          : "UNAVAILABLE",
      );
    return { value, status: response.status };
  } catch (e) {
    if (e instanceof ProductFailure) throw e;
    throw new ProductFailure("UNAVAILABLE");
  }
}
export async function deleteSellerProduct(
  productId: string,
  signal: AbortSignal,
): Promise<void> {
  if (!id(productId)) throw new ProductFailure("NOT_FOUND");
  const { value: csrf } = await request("/api/v1/auth/csrf", signal);
  if (
    !record(csrf) ||
    !record(csrf.data) ||
    typeof csrf.data.csrf_token !== "string"
  )
    throw new ProductFailure("UNAVAILABLE");
  const { status } = await request(
    `/api/v1/seller/products/${productId}`,
    signal,
    { method: "DELETE", headers: { "X-CSRF-Token": csrf.data.csrf_token } },
  );
  if (status !== 204) throw new ProductFailure("UNAVAILABLE");
}

export async function fetchSellerProducts(
  shopId: string,
  query: URLSearchParams,
  signal: AbortSignal,
): Promise<SellerPage> {
  const { value } = await request(`/api/v1/seller/products?${query}`, signal);
  if (
    !record(value) ||
    !Array.isArray(value.items) ||
    !Number.isSafeInteger(value.total) ||
    Number(value.total) < 0 ||
    value.page !== Number(query.get("page") || 1) ||
    value.page_size !== Number(query.get("page_size") || 24) ||
    value.items.length > Number(value.page_size)
  )
    throw new ProductFailure("UNAVAILABLE");
  const items = value.items.map((v) => sellerProductFrom(v, shopId));
  if (items.some((v) => !v)) throw new ProductFailure("UNAVAILABLE");
  return {
    items: items as SellerProduct[],
    total: Number(value.total),
    page: Number(value.page),
    page_size: Number(value.page_size),
    image_upload_enabled: value.image_upload_enabled === true,
  };
}
export async function writeSellerProduct(
  shopId: string,
  signal: AbortSignal,
  input?: ProductInput,
  productId?: string,
  hide = false,
) {
  if (productId !== undefined && !id(productId))
    throw new ProductFailure("NOT_FOUND");
  const { value: csrf } = await request("/api/v1/auth/csrf", signal);
  if (
    !record(csrf) ||
    !record(csrf.data) ||
    typeof csrf.data.csrf_token !== "string"
  )
    throw new ProductFailure("UNAVAILABLE");
  const body = input
    ? {
        sku: input.sku.trim(),
        category_id: input.category_id,
        product_name: input.product_name.trim(),
        description: input.description?.trim() || null,
        price: input.price,
        ...(!productId ? { initial_quantity: input.initial_quantity } : {}),
      }
    : undefined;
  const { value, status } = await request(
    `/api/v1/seller/products${productId ? `/${productId}` : ""}${hide ? "/hide" : ""}`,
    signal,
    {
      method: productId && !hide ? "PATCH" : "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrf.data.csrf_token,
      },
      ...(body ? { body: JSON.stringify(body) } : {}),
    },
  );
  const item = sellerProductFrom(record(value) ? value.data : null, shopId);
  if (
    !item ||
    status !== (!productId ? 201 : 200) ||
    (productId && item.product_id !== productId) ||
    (hide && item.is_active)
  )
    throw new ProductFailure("UNAVAILABLE");
  return item;
}
