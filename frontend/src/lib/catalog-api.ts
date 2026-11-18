/** Imported only by Server Components. Never pass INTERNAL_API_URL into client props. */
export type Category = {
  category_id: string;
  category_name: string;
  category_slug: string;
  children: Category[];
};
export type PublicProduct = {
  product_id: string;
  product_name: string;
  category_id: string;
  price: string;
  currency: "VND";
  primary_image_url: string | null;
  in_stock: boolean;
  shop: { shop_id: string; shop_name: string; shop_slug: string };
};
export type ApiResult<T> = { ok: true; data: T } | { ok: false };
export type ResourceResult<T> =
  | { ok: true; data: T }
  | { ok: false; notFound: boolean };
export type ProductImage = {
  product_image_id: string;
  url: string | null;
  is_primary: boolean;
  sort_order: number;
};
export type ProductDetail = PublicProduct & {
  description: string | null;
  sku: string;
  images: ProductImage[];
  available_quantity: number;
};
export type PublicShop = {
  shop_id: string;
  shop_name: string;
  shop_slug: string;
  description: string | null;
  logo_url: string | null;
};
class MissingResource extends Error {}
type ProductPage = { items: PublicProduct[]; total: number };
export type ProductPageOptions = {
  categoryId?: string;
  shopId?: string;
  query?: string;
  page?: number;
  pageSize?: number;
  sort?: "newest" | "price_asc" | "price_desc";
};

const record = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null;
const id = (value: unknown): value is string =>
  typeof value === "string" &&
  /^[1-9]\d{0,18}$/.test(value) &&
  BigInt(value) <= BigInt("9223372036854775807");
const shopSlug = (value: unknown): value is string =>
  typeof value === "string" &&
  value.trim().length > 0 &&
  value.length <= 160 &&
  value !== "." &&
  value !== ".." &&
  !/[\/\\\u0000-\u001f]/.test(value);
export const safeImageUrl = (value: unknown): value is string => {
  if (typeof value !== "string") return false;
  try {
    const url = new URL(value);
    return url.protocol === "https:" && !url.username && !url.password;
  } catch {
    return false;
  }
};
function category(value: unknown, depth = 0): value is Category {
  return (
    depth < 100 &&
    record(value) &&
    id(value.category_id) &&
    typeof value.category_name === "string" &&
    typeof value.category_slug === "string" &&
    Array.isArray(value.children) &&
    value.children.every((child) => category(child, depth + 1))
  );
}
function product(value: unknown): value is PublicProduct {
  return (
    record(value) &&
    id(value.product_id) &&
    id(value.category_id) &&
    typeof value.product_name === "string" &&
    typeof value.price === "string" &&
    /^\d{1,12}(\.\d{1,2})?$/.test(value.price) &&
    value.currency === "VND" &&
    typeof value.in_stock === "boolean" &&
    (value.primary_image_url === null ||
      safeImageUrl(value.primary_image_url)) &&
    record(value.shop) &&
    id(value.shop.shop_id) &&
    typeof value.shop.shop_name === "string" &&
    shopSlug(value.shop.shop_slug)
  );
}

async function read(path: string): Promise<unknown> {
  const configured = process.env.INTERNAL_API_URL;
  if (!configured) throw new Error("Catalog unavailable");
  const origin = new URL(configured);
  if (
    !["http:", "https:"].includes(origin.protocol) ||
    origin.username ||
    origin.password ||
    origin.pathname !== "/" ||
    origin.search ||
    origin.hash
  )
    throw new Error("Catalog unavailable");
  const response = await fetch(new URL(path, origin), {
    cache: "no-store",
    redirect: "error",
    signal: AbortSignal.timeout(5000),
    headers: { Accept: "application/json" },
  });
  if (response.status === 404) throw new MissingResource();
  if (!response.ok) throw new Error("Catalog unavailable");
  return response.json();
}

export async function getCategories(): Promise<ApiResult<Category[]>> {
  try {
    const payload: unknown = await read("/api/v1/categories");
    if (
      !record(payload) ||
      !Array.isArray(payload.items) ||
      !payload.items.every((item) => category(item))
    )
      return { ok: false };
    return { ok: true, data: payload.items };
  } catch {
    return { ok: false };
  }
}

export async function getProducts(
  categoryId: string,
  query: string,
): Promise<ApiResult<ProductPage>> {
  if (!id(categoryId)) return { ok: false };
  return getProductPage({ categoryId, query, pageSize: 12 });
}

export async function getProductPage(
  options: ProductPageOptions,
): Promise<ApiResult<ProductPage>> {
  const {
    categoryId,
    shopId,
    query = "",
    page = 1,
    pageSize = 24,
    sort = "newest",
  } = options;
  if (
    (categoryId !== undefined && !id(categoryId)) ||
    (shopId !== undefined && !id(shopId)) ||
    query.length > 200 ||
    !Number.isInteger(page) ||
    page < 1 ||
    page > 2147483647 ||
    !Number.isInteger(pageSize) ||
    pageSize < 1 ||
    pageSize > 100 ||
    !["newest", "price_asc", "price_desc"].includes(sort)
  )
    return { ok: false };
  try {
    const params = new URLSearchParams({
      ...(categoryId ? { category_id: categoryId } : {}),
      ...(shopId ? { shop_id: shopId } : {}),
      q: query,
      page: String(page),
      page_size: String(pageSize),
      sort,
    });
    const payload: unknown = await read(`/api/v1/products?${params}`);
    if (
      !record(payload) ||
      !Array.isArray(payload.items) ||
      payload.items.length > pageSize ||
      !payload.items.every(product) ||
      (shopId !== undefined &&
        payload.items.some((item) => item.shop.shop_id !== shopId)) ||
      !Number.isSafeInteger(payload.total) ||
      Number(payload.total) < payload.items.length ||
      (payload.items.length > 0 &&
        Number(payload.total) < (page - 1) * pageSize + payload.items.length) ||
      (payload.page !== undefined && payload.page !== page) ||
      (payload.page_size !== undefined && payload.page_size !== pageSize)
    )
      return { ok: false };
    return {
      ok: true,
      data: {
        items: payload.items.map((item) => ({
          product_id: item.product_id,
          product_name: item.product_name,
          category_id: item.category_id,
          price: item.price,
          currency: item.currency,
          primary_image_url: item.primary_image_url,
          in_stock: item.in_stock,
          shop: {
            shop_id: item.shop.shop_id,
            shop_name: item.shop.shop_name,
            shop_slug: item.shop.shop_slug,
          },
        })),
        total: Number(payload.total),
      },
    };
  } catch {
    return { ok: false };
  }
}

function projectProduct(item: PublicProduct): PublicProduct {
  return {
    product_id: item.product_id,
    product_name: item.product_name,
    category_id: item.category_id,
    price: item.price,
    currency: item.currency,
    primary_image_url: item.primary_image_url,
    in_stock: item.in_stock,
    shop: {
      shop_id: item.shop.shop_id,
      shop_name: item.shop.shop_name,
      shop_slug: item.shop.shop_slug,
    },
  };
}

export async function getProductDetail(
  productId: string,
): Promise<ResourceResult<ProductDetail>> {
  if (!id(productId)) return { ok: false, notFound: true };
  try {
    const payload: unknown = await read(`/api/v1/products/${productId}`);
    if (!record(payload) || !product(payload.data))
      return { ok: false, notFound: false };
    const item = payload.data as PublicProduct & Record<string, unknown>;
    const validImages =
      Array.isArray(item.images) &&
      item.images.every(
        (image) =>
          record(image) &&
          id(image.product_image_id) &&
          (image.url === null || safeImageUrl(image.url)) &&
          typeof image.is_primary === "boolean" &&
          Number.isSafeInteger(image.sort_order) &&
          Number(image.sort_order) >= 0,
      );
    if (
      item.product_id !== productId ||
      !(item.description === null || typeof item.description === "string") ||
      typeof item.sku !== "string" ||
      !Number.isInteger(item.available_quantity) ||
      Number(item.available_quantity) < 0 ||
      Number(item.available_quantity) > 2147483647 ||
      item.in_stock !== Number(item.available_quantity) > 0 ||
      !validImages
    )
      return { ok: false, notFound: false };
    return {
      ok: true,
      data: {
        ...projectProduct(item),
        description: item.description as string | null,
        sku: item.sku,
        available_quantity: Number(item.available_quantity),
        images: (item.images as ProductImage[]).map((image) => ({
          product_image_id: image.product_image_id,
          url: image.url,
          is_primary: image.is_primary,
          sort_order: image.sort_order,
        })),
      },
    };
  } catch (error) {
    return { ok: false, notFound: error instanceof MissingResource };
  }
}

export async function getPublicShop(
  slug: string,
): Promise<ResourceResult<PublicShop>> {
  if (!shopSlug(slug)) return { ok: false, notFound: true };
  try {
    const payload: unknown = await read(
      `/api/v1/shops/${encodeURIComponent(slug)}`,
    );
    if (!record(payload) || !record(payload.data))
      return { ok: false, notFound: false };
    const shop = payload.data;
    if (
      !id(shop.shop_id) ||
      typeof shop.shop_name !== "string" ||
      !shopSlug(shop.shop_slug) ||
      shop.shop_slug !== slug ||
      !(shop.description === null || typeof shop.description === "string") ||
      !(shop.logo_url === null || safeImageUrl(shop.logo_url))
    )
      return { ok: false, notFound: false };
    return {
      ok: true,
      data: {
        shop_id: shop.shop_id,
        shop_name: shop.shop_name,
        shop_slug: shop.shop_slug,
        description: shop.description,
        logo_url: shop.logo_url,
      },
    };
  } catch (error) {
    return { ok: false, notFound: error instanceof MissingResource };
  }
}
