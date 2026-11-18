const endpoints: Record<string, string> = {
  "otp-options": "GET",
  "otp-request": "POST",
  "otp-verify": "POST",
  "otp-register": "POST",
  "password-reset": "POST",
  "otp-login": "POST",
  csrf: "GET",
  me: "GET",
  register: "POST",
  login: "POST",
  logout: "POST",
};
const cookieNames = new Set([
  "marketplace_access",
  "marketplace_csrf",
  "__Host-marketplace_access",
  "__Host-marketplace_csrf",
]);
function fail(status: number, code: string): Response {
  return Response.json(
    { error: { code } },
    { status, headers: { "Cache-Control": "no-store" } },
  );
}
function origin(value: string | undefined): URL {
  if (!value) throw new Error("Missing origin");
  const parsed = new URL(value);
  if (
    !["http:", "https:"].includes(parsed.protocol) ||
    parsed.username ||
    parsed.password ||
    parsed.pathname !== "/" ||
    parsed.search ||
    parsed.hash
  )
    throw new Error("Invalid origin");
  return parsed;
}
export async function proxyAuth(
  request: Request,
  endpoint: string,
): Promise<Response> {
  if (!Object.hasOwn(endpoints, endpoint)) return fail(404, "NOT_FOUND");
  if (request.method !== endpoints[endpoint])
    return fail(405, "METHOD_NOT_ALLOWED");
  return proxyPrivate(
    request,
    `/api/v1/auth/${endpoint}`,
    request.method === "POST" && endpoint !== "logout",
  );
}
export async function proxySellerShop(
  request: Request,
  shopId?: string,
): Promise<Response> {
  if (
    shopId !== undefined &&
    (!/^[1-9]\d{0,18}$/.test(shopId) ||
      BigInt(shopId) > BigInt("9223372036854775807"))
  )
    return fail(404, "NOT_FOUND");
  if (
    !(shopId ? ["DELETE"] : ["GET", "POST", "PATCH"]).includes(request.method)
  )
    return fail(405, "METHOD_NOT_ALLOWED");
  return proxyPrivate(
    request,
    `/api/v1/seller/shop${shopId ? `/${shopId}` : ""}`,
    !["GET", "DELETE"].includes(request.method),
    { bodyLimit: 32768 },
  );
}
export async function proxyPublicProducts(
  request: Request,
  productId?: string,
): Promise<Response> {
  if (request.method !== "GET") return fail(405, "METHOD_NOT_ALLOWED");
  const validId = (v: string) =>
    /^[1-9]\d{0,18}$/.test(v) && BigInt(v) <= BigInt("9223372036854775807");
  if (productId !== undefined && !validId(productId))
    return fail(404, "NOT_FOUND");
  const query = new URL(request.url).searchParams;
  if (productId && query.size) return fail(400, "INVALID_REQUEST");
  for (const key of query.keys()) {
    const values = query.getAll(key),
      value = values[0];
    if (
      values.length !== 1 ||
      !["q", "category_id", "shop_id", "page", "page_size", "sort"].includes(
        key,
      )
    )
      return fail(400, "INVALID_REQUEST");
    if (
      (key === "q" && value.length > 200) ||
      (["category_id", "shop_id"].includes(key) && !validId(value)) ||
      (key === "sort" &&
        !["newest", "price_asc", "price_desc"].includes(value)) ||
      (["page", "page_size"].includes(key) &&
        (!/^[1-9]\d{0,9}$/.test(value) ||
          Number(value) > (key === "page" ? 2147483647 : 100)))
    )
      return fail(400, "INVALID_REQUEST");
  }
  // Catalog is public: do not forward browser cookies or Authorization to the backend.
  return proxyPrivate(
    new Request(request.url, { method: "GET" }),
    `/api/v1/products${productId ? `/${productId}` : ""}${query.size ? `?${query}` : ""}`,
    false,
    { allowQuery: true },
  );
}

export async function proxyAddresses(
  request: Request,
  id?: string,
): Promise<Response> {
  if (
    id !== undefined &&
    (!/^[1-9]\d{0,18}$/.test(id) || BigInt(id) > BigInt("9223372036854775807"))
  )
    return fail(404, "NOT_FOUND");
  if (
    !(id === undefined ? ["GET", "POST"] : ["PATCH", "DELETE"]).includes(
      request.method,
    )
  )
    return fail(405, "METHOD_NOT_ALLOWED");
  return proxyPrivate(
    request,
    `/api/v1/addresses${id === undefined ? "" : `/${id}`}`,
    ["POST", "PATCH"].includes(request.method),
  );
}
export async function proxyCart(
  request: Request,
  route: "cart" | "items" | "item",
  id?: string,
): Promise<Response> {
  if (
    route === "item" &&
    (!id ||
      !/^[1-9]\d{0,18}$/.test(id) ||
      BigInt(id) > BigInt("9223372036854775807"))
  )
    return fail(404, "NOT_FOUND");
  const methods = { cart: ["GET"], items: ["POST"], item: ["PATCH", "DELETE"] };
  if (!Object.hasOwn(methods, route)) return fail(404, "NOT_FOUND");
  if (!methods[route].includes(request.method))
    return fail(405, "METHOD_NOT_ALLOWED");
  return proxyPrivate(
    request,
    `/api/v1/cart${route === "cart" ? "" : route === "items" ? "/items" : `/items/${id}`}`,
    ["POST", "PATCH"].includes(request.method),
  );
}
export async function proxyCheckoutOptions(
  request: Request,
  quote = false,
): Promise<Response> {
  if (request.method !== (quote ? "POST" : "GET"))
    return fail(405, "METHOD_NOT_ALLOWED");
  return proxyPrivate(
    request,
    quote ? "/api/v1/checkout/quote" : "/api/v1/checkout/options",
    quote,
    { bodyLimit: 131072 },
  );
}

export async function proxyShopping(
  request: Request,
  route: "coupon" | "review" | "public-reviews",
  id?: string,
): Promise<Response> {
  if (
    route !== "coupon" &&
    (!id ||
      !/^[1-9]\d{0,18}$/.test(id) ||
      BigInt(id) > BigInt("9223372036854775807"))
  )
    return fail(404, "NOT_FOUND");
  const allowed =
    route === "coupon"
      ? ["POST"]
      : route === "review"
        ? ["GET", "POST"]
        : ["GET"];
  if (!allowed.includes(request.method)) return fail(405, "METHOD_NOT_ALLOWED");
  if (route === "public-reviews") {
    const query = new URL(request.url).searchParams;
    for (const key of query.keys()) {
      const value = query.get(key) || "";
      if (
        query.getAll(key).length !== 1 ||
        !["page", "page_size"].includes(key) ||
        !/^[1-9]\d{0,9}$/.test(value) ||
        Number(value) > (key === "page" ? 2147483647 : 50)
      )
        return fail(400, "INVALID_REQUEST");
    }
    return proxyPrivate(
      new Request(request.url, { method: "GET" }),
      `/api/v1/products/${id}/reviews${query.size ? `?${query}` : ""}`,
      false,
      { allowQuery: true },
    );
  }
  return proxyPrivate(
    request,
    route === "coupon"
      ? "/api/v1/coupons/quote"
      : `/api/v1/order-items/${id}/review`,
    request.method === "POST",
  );
}

export async function proxyCheckout(
  request: Request,
  statusOnly = false,
): Promise<Response> {
  if (request.method !== (statusOnly ? "GET" : "POST"))
    return fail(405, "METHOD_NOT_ALLOWED");
  const key = request.headers.get("idempotency-key");
  if (
    !key ||
    !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(key)
  )
    return fail(400, "INVALID_REQUEST");
  return proxyPrivate(
    request,
    statusOnly ? "/api/v1/orders/checkout-status" : "/api/v1/orders/checkout",
    !statusOnly,
    {
      bodyLimit: 131072,
      idempotencyKey: key,
    },
  );
}
export async function proxyAdminShops(
  request: Request,
  id?: string,
): Promise<Response> {
  if (
    id !== undefined &&
    (!/^[1-9]\d{0,18}$/.test(id) || BigInt(id) > BigInt("9223372036854775807"))
  )
    return fail(404, "NOT_FOUND");
  if (request.method !== (id ? "PATCH" : "GET"))
    return fail(405, "METHOD_NOT_ALLOWED");
  const query = new URL(request.url).searchParams;
  if (id && query.size) return fail(400, "INVALID_REQUEST");
  for (const key of query.keys()) {
    const values = query.getAll(key),
      value = values[0],
      limit = key === "page" ? 2147483647 : key === "page_size" ? 100 : 0;
    if (
      values.length !== 1 ||
      (key === "q"
        ? value.length > 200
        : key === "status"
          ? !["PENDING", "APPROVED", "REJECTED", "LOCKED"].includes(value)
          : !/^[1-9]\d{0,9}$/.test(value) || Number(value) > limit)
    )
      return fail(400, "INVALID_REQUEST");
  }
  return proxyPrivate(
    request,
    `/api/v1/admin/shops${id ? `/${id}/status` : ""}${query.size ? `?${query}` : ""}`,
    !!id,
    { allowQuery: true },
  );
}
export async function proxyAdminProducts(
  request: Request,
  id?: string,
): Promise<Response> {
  if (
    id !== undefined &&
    (!/^[1-9]\d{0,18}$/.test(id) || BigInt(id) > BigInt("9223372036854775807"))
  )
    return fail(404, "NOT_FOUND");
  if (request.method !== (id ? "POST" : "GET"))
    return fail(405, "METHOD_NOT_ALLOWED");
  const query = new URL(request.url).searchParams;
  if (id && query.size) return fail(400, "INVALID_REQUEST");
  for (const key of query.keys()) {
    const values = query.getAll(key),
      value = values[0];
    if (values.length !== 1) return fail(400, "INVALID_REQUEST");
    if (key === "q") {
      if (value.length > 200) return fail(400, "INVALID_REQUEST");
    } else if (key === "is_active") {
      if (!["true", "false"].includes(value))
        return fail(400, "INVALID_REQUEST");
    } else if (key === "shop_id") {
      if (
        !/^[1-9]\d{0,18}$/.test(value) ||
        BigInt(value) > BigInt("9223372036854775807")
      )
        return fail(400, "INVALID_REQUEST");
    } else if (
      !["page", "page_size"].includes(key) ||
      !/^[1-9]\d{0,9}$/.test(value) ||
      Number(value) > (key === "page" ? 2147483647 : 100)
    )
      return fail(400, "INVALID_REQUEST");
  }
  return proxyPrivate(
    request,
    `/api/v1/admin/products${id ? `/${id}/hide` : ""}${query.size ? `?${query}` : ""}`,
    false,
    { allowQuery: true },
  );
}
export async function proxyAdminCategories(
  request: Request,
  id?: string,
): Promise<Response> {
  if (
    id !== undefined &&
    (!/^[1-9]\d{0,18}$/.test(id) || BigInt(id) > BigInt("9223372036854775807"))
  )
    return fail(404, "NOT_FOUND");
  if (
    !(id
      ? request.method === "PATCH"
      : ["GET", "POST"].includes(request.method))
  )
    return fail(405, "METHOD_NOT_ALLOWED");
  return proxyPrivate(
    request,
    `/api/v1/admin/categories${id ? `/${id}` : ""}`,
    request.method !== "GET",
  );
}
export async function proxyOrders(
  request: Request,
  id?: string,
): Promise<Response> {
  if (request.method !== "GET") return fail(405, "METHOD_NOT_ALLOWED");
  if (
    id !== undefined &&
    (!/^[1-9]\d{0,18}$/.test(id) || BigInt(id) > BigInt("9223372036854775807"))
  )
    return fail(404, "NOT_FOUND");
  const query = new URL(request.url).searchParams;
  if (id !== undefined && query.size) return fail(400, "INVALID_REQUEST");
  for (const name of query.keys()) {
    const values = query.getAll(name);
    const limit = name === "page" ? 2147483647 : name === "page_size" ? 100 : 0;
    if (
      values.length !== 1 ||
      !/^[1-9]\d{0,9}$/.test(values[0]) ||
      Number(values[0]) > limit
    )
      return fail(400, "INVALID_REQUEST");
  }
  return proxyPrivate(
    request,
    `/api/v1/orders${id ? `/${id}` : ""}${query.size ? `?${query}` : ""}`,
    false,
    { allowQuery: true },
  );
}
export async function proxyAdminUsers(
  request: Request,
  id?: string,
): Promise<Response> {
  if (
    id !== undefined &&
    (!/^[1-9]\d{0,18}$/.test(id) || BigInt(id) > BigInt("9223372036854775807"))
  )
    return fail(404, "NOT_FOUND");
  if (request.method !== (id ? "PATCH" : "GET"))
    return fail(405, "METHOD_NOT_ALLOWED");
  const query = new URL(request.url).searchParams;
  if (id && query.size) return fail(400, "INVALID_REQUEST");
  for (const key of query.keys()) {
    const values = query.getAll(key),
      value = values[0],
      limit = key === "page" ? 2147483647 : key === "page_size" ? 100 : 0;
    if (
      values.length !== 1 ||
      (key === "q"
        ? value.length > 200
        : key === "status"
          ? !["ACTIVE", "LOCKED"].includes(value)
          : !/^[1-9]\d{0,9}$/.test(value) || Number(value) > limit)
    )
      return fail(400, "INVALID_REQUEST");
  }
  return proxyPrivate(
    request,
    `/api/v1/admin/users${id ? `/${id}/status` : ""}${query.size ? `?${query}` : ""}`,
    !!id,
    { allowQuery: true },
  );
}
export async function proxySellerOrders(
  request: Request,
  id?: string,
  change = false,
): Promise<Response> {
  if (
    id !== undefined &&
    (!/^[1-9]\d{0,18}$/.test(id) || BigInt(id) > BigInt("9223372036854775807"))
  )
    return fail(404, "NOT_FOUND");
  if (request.method !== (change ? "PATCH" : "GET") || (change && !id))
    return fail(405, "METHOD_NOT_ALLOWED");
  const query = new URL(request.url).searchParams;
  if (id && query.size) return fail(400, "INVALID_REQUEST");
  for (const name of query.keys()) {
    const values = query.getAll(name),
      limit = name === "page" ? 2147483647 : name === "page_size" ? 100 : 0;
    if (
      values.length !== 1 ||
      (name === "status"
        ? ![
            "PENDING",
            "CONFIRMED",
            "SHIPPING",
            "COMPLETED",
            "CANCELLED",
          ].includes(values[0])
        : !/^[1-9]\d{0,9}$/.test(values[0]) || Number(values[0]) > limit)
    )
      return fail(400, "INVALID_REQUEST");
  }
  return proxyPrivate(
    request,
    `/api/v1/seller/orders${id ? `/${id}${change ? "/status" : ""}` : ""}${query.size ? `?${query}` : ""}`,
    change,
    { allowQuery: true },
  );
}
export async function proxyCancelOrder(
  request: Request,
  orderId: string,
  shopOrderId: string,
): Promise<Response> {
  if (
    [orderId, shopOrderId].some(
      (v) =>
        !/^[1-9]\d{0,18}$/.test(v) || BigInt(v) > BigInt("9223372036854775807"),
    )
  )
    return fail(404, "NOT_FOUND");
  if (request.method !== "POST") return fail(405, "METHOD_NOT_ALLOWED");
  return proxyPrivate(
    request,
    `/api/v1/orders/${orderId}/shop-orders/${shopOrderId}/cancel`,
    false,
  );
}
export async function proxySellerProducts(
  request: Request,
  id?: string,
  hide = false,
): Promise<Response> {
  if (
    id !== undefined &&
    (!/^[1-9]\d{0,18}$/.test(id) || BigInt(id) > BigInt("9223372036854775807"))
  )
    return fail(404, "NOT_FOUND");
  if (
    !(
      hide ? ["POST"] : id ? ["GET", "PATCH", "DELETE"] : ["GET", "POST"]
    ).includes(request.method) ||
    (hide && !id)
  )
    return fail(405, "METHOD_NOT_ALLOWED");
  const query = new URL(request.url).searchParams;
  if (query.size && (id || request.method !== "GET"))
    return fail(400, "INVALID_REQUEST");
  for (const key of query.keys()) {
    const values = query.getAll(key),
      value = values[0];
    if (
      values.length !== 1 ||
      !(key === "q"
        ? Array.from(value).length <= 200
        : key === "is_active"
          ? /^(true|false)$/.test(value)
          : ["page", "page_size"].includes(key) &&
            /^[1-9]\d{0,9}$/.test(value) &&
            Number(value) <= (key === "page" ? 2147483647 : 100))
    )
      return fail(400, "INVALID_REQUEST");
  }
  return proxyPrivate(
    request,
    `/api/v1/seller/products${id ? `/${id}` : ""}${hide ? "/hide" : ""}${query.size ? `?${query}` : ""}`,
    !["GET", "DELETE"].includes(request.method) && !hide,
    { bodyLimit: 32768, allowQuery: true },
  );
}
export async function proxyProductImages(
  request: Request,
  productId: string,
  resource?: string,
): Promise<Response> {
  const validId = (id: string) =>
    /^[1-9]\d{0,18}$/.test(id) && BigInt(id) <= BigInt("9223372036854775807");
  if (
    !validId(productId) ||
    (resource !== undefined && resource !== "upload-url" && !validId(resource))
  )
    return fail(404, "NOT_FOUND");
  const methods =
    resource === undefined || resource === "upload-url"
      ? ["POST"]
      : ["PATCH", "DELETE"];
  if (!methods.includes(request.method)) return fail(405, "METHOD_NOT_ALLOWED");
  return proxyPrivate(
    request,
    `/api/v1/seller/products/${productId}/images${resource ? `/${resource}` : ""}`,
    request.method !== "DELETE",
  );
}
export async function proxyInventory(
  request: Request,
  productId: string,
  adjustment = false,
): Promise<Response> {
  if (
    !/^[1-9]\d{0,18}$/.test(productId) ||
    BigInt(productId) > BigInt("9223372036854775807")
  )
    return fail(404, "NOT_FOUND");
  if (request.method !== (adjustment ? "POST" : "GET"))
    return fail(405, "METHOD_NOT_ALLOWED");
  const expected = request.headers.get("x-expected-quantity");
  if (
    adjustment &&
    (!expected ||
      !/^(0|[1-9]\d{0,9})$/.test(expected) ||
      Number(expected) > 2147483647)
  )
    return fail(400, "INVALID_REQUEST");
  return proxyPrivate(
    request,
    `/api/v1/seller/products/${productId}/inventory${adjustment ? "/adjustments" : ""}`,
    adjustment,
    { expectedQuantity: adjustment ? expected! : undefined },
  );
}
async function proxyPrivate(
  request: Request,
  path: string,
  hasBody: boolean,
  options: {
    bodyLimit?: number;
    idempotencyKey?: string;
    allowQuery?: boolean;
    expectedQuantity?: string;
  } = {},
): Promise<Response> {
  if (new URL(request.url).search && !options.allowQuery)
    return fail(400, "INVALID_REQUEST");
  try {
    const upstream = origin(process.env.INTERNAL_API_URL);
    const headers = new Headers({ Accept: "application/json" });
    if (options.expectedQuantity !== undefined)
      headers.set("X-Expected-Quantity", options.expectedQuantity);
    if (options.idempotencyKey)
      headers.set("Idempotency-Key", options.idempotencyKey);
    if (!["GET", "HEAD"].includes(request.method)) {
      const publicOrigin = origin(process.env.MARKETPLACE_PUBLIC_ORIGIN).origin;
      const extra: unknown = JSON.parse(
        process.env.MARKETPLACE_ADDITIONAL_ORIGINS || "[]",
      );
      if (
        !Array.isArray(extra) ||
        extra.length > 10 ||
        extra.some((value) => typeof value !== "string")
      )
        throw new Error("Invalid additional origins");
      const allowedOrigins = new Set([
        publicOrigin,
        ...extra.map((value) => origin(value).origin),
      ]);
      const supplied = request.headers.get("origin");
      const referer = request.headers.get("referer");
      if (
        supplied
          ? !allowedOrigins.has(supplied)
          : !referer || !allowedOrigins.has(new URL(referer).origin)
      )
        return fail(403, "CSRF_FAILED");
      if (!request.headers.get("x-csrf-token")) return fail(403, "CSRF_FAILED");
      if (supplied) headers.set("Origin", supplied);
      if (referer) headers.set("Referer", referer);
      headers.set("X-CSRF-Token", request.headers.get("x-csrf-token")!);
    }
    const cookies = (request.headers.get("cookie") ?? "")
      .split(";")
      .map((c) => c.trim())
      .filter((c) => cookieNames.has(c.split("=", 1)[0]));
    if (cookies.length) headers.set("Cookie", cookies.join("; "));
    const requestId = request.headers.get("x-request-id");
    if (requestId && /^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/.test(requestId))
      headers.set("X-Request-ID", requestId);
    let body: string | undefined;
    const bodyLimit = options.bodyLimit ?? 8192;
    if (hasBody) {
      if (
        !request.headers
          .get("content-type")
          ?.toLowerCase()
          .startsWith("application/json")
      )
        return fail(415, "INVALID_REQUEST");
      if (Number(request.headers.get("content-length")) > bodyLimit)
        return fail(413, "INVALID_REQUEST");
      // Stream limit also handles chunked requests without allocating an unbounded body.
      const reader = request.body?.getReader();
      const chunks: Uint8Array[] = [];
      let size = 0;
      if (reader)
        for (;;) {
          const next = await reader.read();
          if (next.done) break;
          size += next.value.byteLength;
          if (size > bodyLimit) {
            await reader.cancel();
            return fail(413, "INVALID_REQUEST");
          }
          chunks.push(next.value);
        }
      const bytes = new Uint8Array(size);
      let offset = 0;
      for (const chunk of chunks) {
        bytes.set(chunk, offset);
        offset += chunk.length;
      }
      body = new TextDecoder().decode(bytes);
      headers.set("Content-Type", "application/json");
    }
    const response = await fetch(new URL(path, upstream), {
      method: request.method,
      headers,
      body,
      redirect: "error",
      cache: "no-store",
      signal: AbortSignal.timeout(15000),
    });
    const out = new Headers({
      "Cache-Control": "no-store",
      "Content-Type": "application/json",
      Vary: "Cookie",
    });
    for (const cookie of response.headers.getSetCookie()) {
      if (cookieNames.has(cookie.split("=", 1)[0]))
        out.append("Set-Cookie", cookie);
    }
    const id = response.headers.get("x-request-id");
    if (id) out.set("X-Request-ID", id);
    return new Response(
      response.status === 204 ? null : await response.text(),
      { status: response.status, headers: out },
    );
  } catch {
    return fail(503, "DEPENDENCY_UNAVAILABLE");
  }
}
