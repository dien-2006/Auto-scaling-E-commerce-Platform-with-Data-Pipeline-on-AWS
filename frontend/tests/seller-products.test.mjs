import { test } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import ts from "typescript";
async function load(name) {
  const { outputText } = ts.transpileModule(
    await readFile(new URL(`../src/lib/${name}.ts`, import.meta.url), "utf8"),
    {
      compilerOptions: {
        module: ts.ModuleKind.ESNext,
        target: ts.ScriptTarget.ES2022,
      },
    },
  );
  return import(
    `data:text/javascript;base64,${Buffer.from(outputText).toString("base64")}`
  );
}
const { sellerProductFrom, fetchSellerProducts, writeSellerProduct } =
  await load("seller-products-client");
const { proxySellerProducts } = await load("auth-proxy");
const shopId = "9007199254740993";
const item = () => ({
  product_id: "9007199254740994",
  category_id: "9007199254740995",
  product_name: "Serum",
  sku: "SKU",
  description: null,
  price: "999999999999.99",
  is_active: true,
  available_quantity: 7,
  created_at: "2026-11-10T00:00:00Z",
  updated_at: "2026-11-10T00:00:00Z",
  shop: { shop_id: shopId, owner_user_id: "secret" },
  image_key: "secret",
});
test("seller product projection preserves exact price and IDs, enforces owner shop, strips extras", () => {
  const result = sellerProductFrom(item(), shopId);
  assert.equal(result.price, "999999999999.99");
  assert.equal(result.product_id, item().product_id);
  assert.equal(result.image_key, undefined);
  assert.deepEqual(result.shop, { shop_id: shopId });
  for (const change of [
    { price: 1 },
    { price: "NaN" },
    { price: "1000000000000" },
    { product_id: "9223372036854775808" },
    { shop: { shop_id: "1" } },
    { available_quantity: -1 },
    { available_quantity: 1.5 },
    { is_active: "false" },
    { updated_at: "bad" },
  ])
    assert.equal(sellerProductFrom({ ...item(), ...change }, shopId), null);
});
test("seller product proxy confines query, method, ID, origin and CSRF", async () => {
  const original = globalThis.fetch,
    oldOrigin = process.env.MARKETPLACE_PUBLIC_ORIGIN,
    oldApi = process.env.INTERNAL_API_URL;
  process.env.MARKETPLACE_PUBLIC_ORIGIN = "http://localhost";
  process.env.INTERNAL_API_URL = "http://backend:8000";
  const calls = [];
  globalThis.fetch = async (url, init) => {
    calls.push({ url: String(url), init });
    return Response.json({ data: item() });
  };
  try {
    for (const query of [
      "shop_id=1",
      "q=a&q=b",
      "is_active=1",
      "page=0",
      "page_size=101",
      "page=2147483648",
    ])
      assert.equal(
        (
          await proxySellerProducts(
            new Request(`http://localhost/api/v1/seller/products?${query}`),
          )
        ).status,
        400,
      );
    assert.equal(
      (
        await proxySellerProducts(
          new Request("http://localhost/api/v1/seller/products"),
          "1/../../auth/me",
        )
      ).status,
      404,
    );
    for (const method of ["POST", "PATCH"])
      assert.equal(
        (
          await proxySellerProducts(
            new Request("http://localhost/api/v1/seller/products", { method }),
            method === "PATCH" ? "1" : undefined,
          )
        ).status,
        403,
      );
    assert.equal(
      (
        await proxySellerProducts(
          new Request("http://localhost/api/v1/seller/products", {
            method: "PUT",
          }),
          "1",
        )
      ).status,
      405,
    );
    assert.equal(calls.length, 0);
    const headers = {
      Origin: "http://localhost",
      "X-CSRF-Token": "test",
      Cookie: "other=private; marketplace_access=jwt",
    };
    assert.equal(
      (
        await proxySellerProducts(
          new Request("http://localhost/api/v1/seller/products", {
            method: "POST",
            headers,
          }),
          "1",
          true,
        )
      ).status,
      200,
    );
    assert.equal(
      calls[0].url,
      "http://backend:8000/api/v1/seller/products/1/hide",
    );
    assert.equal(calls[0].init.headers.get("Cookie"), "marketplace_access=jwt");
    await proxySellerProducts(
      new Request(
        "http://localhost/api/v1/seller/products?q=a%25&is_active=false&page=2",
      ),
    );
    assert.match(calls[1].url, /q=a%25&is_active=false&page=2$/);
  } finally {
    globalThis.fetch = original;
    if (oldOrigin === undefined) delete process.env.MARKETPLACE_PUBLIC_ORIGIN;
    else process.env.MARKETPLACE_PUBLIC_ORIGIN = oldOrigin;
    if (oldApi === undefined) delete process.env.INTERNAL_API_URL;
    else process.env.INTERNAL_API_URL = oldApi;
  }
});
test("seller client rejects malformed pages and failed writes, never automatically retries", async () => {
  const original = globalThis.fetch,
    signal = new AbortController().signal;
  const query = new URLSearchParams({ page: "1", page_size: "24" });
  try {
    globalThis.fetch = async () =>
      Response.json({ items: [item()], page: 1, page_size: 24, total: 1 });
    assert.equal(
      (await fetchSellerProducts(shopId, query, signal)).items.length,
      1,
    );
    globalThis.fetch = async () =>
      Response.json({ items: [item()], page: 2, page_size: 24, total: 1 });
    await assert.rejects(fetchSellerProducts(shopId, query, signal));
    let writes = 0;
    globalThis.fetch = async (path, init) => {
      if (path.endsWith("/csrf"))
        return Response.json({ data: { csrf_token: "token" } });
      writes++;
      const body = JSON.parse(init.body);
      assert.equal(body.is_active, undefined);
      assert.equal(body.shop_id, undefined);
      assert.equal(body.price, "12.34");
      throw new Error("Lost response after COMMIT");
    };
    await assert.rejects(
      writeSellerProduct(shopId, signal, {
        product_name: "Serum",
        sku: "SKU",
        category_id: "1",
        price: "12.34",
        description: null,
        initial_quantity: 5,
        is_active: true,
        shop_id: "bad",
      }),
    );
    assert.equal(writes, 1);
  } finally {
    globalThis.fetch = original;
  }
});
