import { afterEach, test } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import ts from "typescript";

const load = async (path) => {
  const source = await readFile(new URL(path, import.meta.url), "utf8");
  const { outputText } = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.ESNext,
      target: ts.ScriptTarget.ES2022,
    },
  });
  return import(
    `data:text/javascript;base64,${Buffer.from(outputText).toString("base64")}`
  );
};
const {
  getCategories,
  getProducts,
  getProductPage,
  getProductDetail,
  getPublicShop,
  safeImageUrl,
} = await load("../src/lib/catalog-api.ts");
const { beautyCategories, categoryMatchKey, matchBeautyCategories, formatVnd } =
  await load("../src/lib/categories.ts");
const originalFetch = globalThis.fetch;
const originalOrigin = process.env.INTERNAL_API_URL;
afterEach(() => {
  globalThis.fetch = originalFetch;
  if (originalOrigin === undefined) delete process.env.INTERNAL_API_URL;
  else process.env.INTERNAL_API_URL = originalOrigin;
});

const resourceProduct = () => ({
  product_id: "9007199254740993",
  product_name: "Serum thật",
  category_id: "17",
  price: "999999999999.99",
  currency: "VND",
  primary_image_url: null,
  in_stock: true,
  shop: {
    shop_id: "9007199254740994",
    shop_name: "Shop",
    shop_slug: "shop-test",
    contact_email: "private@example.test",
  },
  sku: "sku-1",
  description: null,
  available_quantity: 7,
  images: [
    {
      product_image_id: "9007199254740995",
      url: null,
      is_primary: true,
      sort_order: 0,
      image_key: "private/object",
    },
  ],
  password_hash: "private-password",
});
test("resource 404 is distinct from HTTP/JSON/timeout failure", async () => {
  process.env.INTERNAL_API_URL = "http://backend:8000";
  for (const status of [404, 500, 503]) {
    globalThis.fetch = async () =>
      new Response("private upstream body", { status });
    assert.deepEqual(await getProductDetail("17"), {
      ok: false,
      notFound: status === 404,
    });
    assert.deepEqual(await getPublicShop("shop-test"), {
      ok: false,
      notFound: status === 404,
    });
  }
  for (const response of [
    async () => new Response("invalid json"),
    async () => {
      throw new DOMException("private host", "TimeoutError");
    },
  ]) {
    globalThis.fetch = response;
    assert.deepEqual(await getProductDetail("17"), {
      ok: false,
      notFound: false,
    });
  }
});
test("invalid product ID/shop path fails before fetch", async () => {
  let calls = 0;
  globalThis.fetch = async () => {
    calls++;
    throw new Error("Unexpected");
  };
  for (const value of [
    "0",
    "001",
    "-1",
    "old-preview-slug",
    "9223372036854775808",
  ])
    assert.deepEqual(await getProductDetail(value), {
      ok: false,
      notFound: true,
    });
  for (const value of ["", ".", "..", "../private", "a\\b", "x".repeat(161)])
    assert.deepEqual(await getPublicShop(value), { ok: false, notFound: true });
  assert.equal(calls, 0);
});
test("detail keeps Decimal/BIGINT/stock but strips all private fields", async () => {
  respond({ data: resourceProduct() });
  const result = await getProductDetail("9007199254740993");
  assert.equal(result.ok, true);
  assert.equal(result.data.price, "999999999999.99");
  assert.equal(result.data.images[0].product_image_id, "9007199254740995");
  assert.equal(result.data.available_quantity, 7);
  assert.equal(JSON.stringify(result).includes("private"), false);
});
test("mismatched identity, invalid stock and unsafe gallery images are not accepted", async () => {
  const original = resourceProduct();
  for (const changes of [
    { product_id: "18" },
    { available_quantity: -1 },
    { available_quantity: 0 },
    { available_quantity: 2147483648 },
    { images: [{ ...original.images[0], url: "javascript:alert(1)" }] },
    { images: [{ ...original.images[0], sort_order: -1 }] },
    { sku: null },
  ]) {
    respond({ data: { ...original, ...changes } });
    assert.deepEqual(await getProductDetail(original.product_id), {
      ok: false,
      notFound: false,
    });
  }
  respond({
    data: {
      ...original,
      in_stock: false,
      available_quantity: 0,
      description: "",
    },
  });
  assert.equal((await getProductDetail(original.product_id)).ok, true);
});
test("shop slug is encoded as one path segment and private fields are projected away", async () => {
  process.env.INTERNAL_API_URL = "http://backend:8000";
  const slug = "shop đẹp?literal";
  globalThis.fetch = async (input) => {
    const url = new URL(input);
    assert.equal(url.pathname, "/api/v1/shops/" + encodeURIComponent(slug));
    assert.equal(url.search, "");
    return Response.json({
      data: {
        shop_id: "17",
        shop_name: "Shop",
        shop_slug: slug,
        description: null,
        logo_url: null,
        owner_user_id: "private-owner",
        contact_email: "private-email",
      },
    });
  };
  const result = await getPublicShop(slug);
  assert.equal(result.ok, true);
  assert.equal(JSON.stringify(result).includes("private"), false);
});
test("shop catalog request carries exact shop ID and rejects cross-shop rows", async () => {
  process.env.INTERNAL_API_URL = "http://backend:8000";
  globalThis.fetch = async (input) => {
    assert.equal(
      new URL(input).searchParams.get("shop_id"),
      "9007199254740994",
    );
    return Response.json({
      items: [resourceProduct()],
      total: 1,
      page: 1,
      page_size: 24,
    });
  };
  assert.equal((await getProductPage({ shopId: "9007199254740994" })).ok, true);
  respond({ items: [resourceProduct()], total: 1 });
  assert.deepEqual(await getProductPage({ shopId: "999" }), { ok: false });
});

test("category mapping uses unique slug first and rejects ambiguous names", () => {
  const category = (id, name, slug, children = []) => ({
    category_id: id,
    category_name: name,
    category_slug: slug,
    children,
  });
  const ambiguous = [
    category("17", "ChamSocDaMat", "one"),
    category("18", "Chăm sóc da mặt", "two"),
  ];
  assert.equal(matchBeautyCategories(ambiguous)[0].actual, undefined);
  const exact = category("9007199254740993", "Other label", "cham-soc-da-mat");
  assert.equal(
    matchBeautyCategories([...ambiguous, exact])[0].actual.category_id,
    "9007199254740993",
  );
  assert.equal(
    matchBeautyCategories([category("30", "Parent", "parent", [exact])])[0]
      .actual.category_id,
    "9007199254740993",
  );
});

test("paginated request preserves page/sort/size and doesn't add absent category ID", async () => {
  process.env.INTERNAL_API_URL = "http://backend:8000";
  globalThis.fetch = async (input) => {
    const url = new URL(input);
    assert.equal(url.searchParams.get("page"), "3");
    assert.equal(url.searchParams.get("page_size"), "48");
    assert.equal(url.searchParams.get("sort"), "price_desc");
    assert.equal(url.searchParams.has("category_id"), false);
    return Response.json({ items: [], total: 60, page: 3, page_size: 48 });
  };
  assert.deepEqual(
    await getProductPage({ page: 3, pageSize: 48, sort: "price_desc" }),
    { ok: true, data: { items: [], total: 60 } },
  );
});

test("invalid pagination and mismatched response metadata fail closed", async () => {
  let calls = 0;
  process.env.INTERNAL_API_URL = "http://backend:8000";
  globalThis.fetch = async () => {
    calls++;
    return Response.json({ items: [], total: 0, page: 99, page_size: 24 });
  };
  for (const options of [
    { page: 0 },
    { page: 2147483648 },
    { page: 1.2 },
    { pageSize: 101 },
    { pageSize: 0 },
    { sort: "arbitrary" },
    { query: "x".repeat(201) },
  ])
    assert.deepEqual(await getProductPage(options), { ok: false });
  assert.equal(calls, 0);
  assert.deepEqual(await getProductPage({ page: 1 }), { ok: false });
});
const respond = (payload) => {
  process.env.INTERNAL_API_URL = "http://backend:8000";
  globalThis.fetch = async () => Response.json(payload);
};

test("taxonomy matches names/slugs without guessing database IDs", () => {
  assert.equal(beautyCategories.length, 6);
  assert.equal(
    categoryMatchKey("Chăm sóc da mặt"),
    categoryMatchKey("ChamSocDaMat"),
  );
  assert.equal(
    categoryMatchKey("dung-cu-phu-kien-lam-dep"),
    categoryMatchKey("DungCuPhuKienLamDep"),
  );
  assert.equal(formatVnd("999999999999.99"), "999.999.999.999,99 ₫");
  assert.equal(formatVnd("100.00"), "100 ₫");
});
test("missing or unsafe server origin fails closed without network calls", async () => {
  let calls = 0;
  globalThis.fetch = async () => {
    calls++;
    throw new Error("Unexpected");
  };
  for (const origin of [
    undefined,
    "file:///tmp",
    "http://user:password@backend:8000",
    "http://backend/api?secret=x",
  ]) {
    if (origin === undefined) delete process.env.INTERNAL_API_URL;
    else process.env.INTERNAL_API_URL = origin;
    assert.deepEqual(await getCategories(), { ok: false });
  }
  assert.equal(calls, 0);
});
test("empty API categories are successful, malformed responses are errors", async () => {
  respond({ items: [] });
  assert.deepEqual(await getCategories(), { ok: true, data: [] });
  for (const payload of [
    {},
    { items: [{ category_id: "1", children: [] }] },
    {
      items: [
        {
          category_id: 9007199254740993,
          category_name: "Name",
          category_slug: "name",
          children: [],
        },
      ],
    },
  ]) {
    respond(payload);
    assert.deepEqual(await getCategories(), { ok: false });
  }
});
test("HTTP/JSON/timeout failures do not become a successful empty catalog", async () => {
  process.env.INTERNAL_API_URL = "http://backend:8000";
  for (const fake of [
    async () => new Response("private", { status: 503 }),
    async () => new Response("bad json"),
    async () => {
      throw new DOMException("private-host", "TimeoutError");
    },
  ]) {
    globalThis.fetch = fake;
    assert.deepEqual(await getCategories(), { ok: false });
    assert.deepEqual(await getProducts("17", "serum"), { ok: false });
  }
});
test("products request uses actual BIGINT ID, encoded query, no-store and timeout", async () => {
  process.env.INTERNAL_API_URL = "http://backend:8000";
  globalThis.fetch = async (input, init) => {
    const url = new URL(input);
    assert.equal(url.origin, "http://backend:8000");
    assert.equal(url.searchParams.get("category_id"), "9007199254740993");
    assert.equal(url.searchParams.get("q"), "serum & 100%_");
    assert.equal(init.cache, "no-store");
    assert.equal(init.redirect, "error");
    assert.ok(init.signal instanceof AbortSignal);
    return Response.json({ items: [], total: 0 });
  };
  assert.deepEqual(await getProducts("9007199254740993", "serum & 100%_"), {
    ok: true,
    data: { items: [], total: 0 },
  });
});
test("invalid IDs and unsafe image schemes are rejected", async () => {
  for (const value of ["0", "-1", "abc", "9223372036854775808"])
    assert.deepEqual(await getProducts(value, ""), { ok: false });
  for (const value of [
    "javascript:alert(1)",
    "data:image/svg+xml,a",
    "http://host/x",
    "https://user:pass@host/x",
  ])
    assert.equal(safeImageUrl(value), false);
  assert.equal(safeImageUrl("https://images.example.test/product.jpg"), true);
});
test("product response validates Decimal strings, total and required public fields", async () => {
  const item = {
    product_id: "9007199254740993",
    category_id: "17",
    product_name: "Serum",
    price: "285000.00",
    currency: "VND",
    primary_image_url: null,
    in_stock: true,
    shop: { shop_id: "20", shop_name: "Shop", shop_slug: "shop" },
  };
  respond({ items: [item], total: 1 });
  assert.equal((await getProducts("17", "")).ok, true);
  for (const payload of [
    { items: [{ ...item, price: 285000 }], total: 1 },
    { items: [item], total: 0 },
    { items: [{ ...item, shop: null }], total: 1 },
  ]) {
    respond(payload);
    assert.deepEqual(await getProducts("17", ""), { ok: false });
  }
});
