import { test } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import ts from "typescript";
const urls = new Map();
async function moduleURL(name) {
  if (urls.has(name)) return urls.get(name);
  let { outputText } = ts.transpileModule(
    await readFile(new URL(`../src/lib/${name}.ts`, import.meta.url), "utf8"),
    {
      compilerOptions: {
        module: ts.ModuleKind.ESNext,
        target: ts.ScriptTarget.ES2022,
      },
    },
  );
  for (const m of [...outputText.matchAll(/from (["'])@\/lib\/([^"']+)\1/g)])
    outputText = outputText.replace(
      m[0],
      `from ${JSON.stringify(await moduleURL(m[2]))}`,
    );
  const url = `data:text/javascript;base64,${Buffer.from(outputText).toString("base64")}`;
  urls.set(name, url);
  return url;
}
const { adminProductFrom, fetchAdminProducts, hideAdminProduct } = await import(
  await moduleURL("admin-products-client")
);
const { proxyAdminProducts } = await import(await moduleURL("auth-proxy"));
const { safeReturnPath } = await import(await moduleURL("auth-contract"));
const row = (active = true) => ({
  product_id: "9007199254740993",
  category_id: "2",
  product_name: "Product",
  sku: "SKU",
  description: null,
  price: "12.34",
  is_active: active,
  available_quantity: 10,
  created_at: "2026-11-11T00:00:00Z",
  updated_at: "2026-11-11T00:00:00Z",
  shop: {
    shop_id: "9007199254740994",
    shop_name: "Shop",
    shop_slug: "test-shop",
  },
  images: [],
});
test("Admin product projection validates IDs/exact prices/stock/images and removes unrelated private data", () => {
  assert.deepEqual(
    adminProductFrom({
      ...row(),
      password_hash: "secret",
      image_key: "secret",
    }),
    row(),
  );
  assert.equal(adminProductFrom({ ...row(), price: 12.34 }), null);
  assert.equal(adminProductFrom({ ...row(), available_quantity: -1 }), null);
  assert.equal(
    adminProductFrom({
      ...row(),
      images: [
        {
          product_image_id: "1",
          url: "javascript:alert(1)",
          is_primary: true,
          sort_order: 0,
        },
      ],
    }),
    null,
  );
  assert.equal(safeReturnPath("/admin/products"), "/admin/products");
  assert.equal(safeReturnPath("/admin/products/1/hide"), "/");
});
test("Admin product client verifies page, shop filter, active state and duplicate identities", async () => {
  const original = globalThis.fetch,
    calls = [],
    signal = new AbortController().signal;
  try {
    globalThis.fetch = async (url) => {
      calls.push(url);
      return Response.json({
        items: [row()],
        page: 1,
        page_size: 24,
        total: 1,
      });
    };
    assert.equal(
      (
        await fetchAdminProducts(
          1,
          "a&is_active=false",
          row().shop.shop_id,
          "true",
          signal,
        )
      ).items.length,
      1,
    );
    assert.match(calls[0], /q=a%26is_active%3Dfalse/);
    await assert.rejects(fetchAdminProducts(2, "", "", "", signal), {
      code: "UNAVAILABLE",
    });
    await assert.rejects(fetchAdminProducts(1, "", "1", "", signal), {
      code: "UNAVAILABLE",
    });
    await assert.rejects(fetchAdminProducts(1, "", "", "false", signal), {
      code: "UNAVAILABLE",
    });
    globalThis.fetch = async () =>
      Response.json({
        items: [row(), row()],
        page: 1,
        page_size: 24,
        total: 2,
      });
    await assert.rejects(fetchAdminProducts(1, "", "", "", signal), {
      code: "UNAVAILABLE",
    });
  } finally {
    globalThis.fetch = original;
  }
});
test("Hide sends no arbitrary fields and does not retry a response lost after COMMIT", async () => {
  const original = globalThis.fetch,
    calls = [],
    signal = new AbortController().signal;
  try {
    globalThis.fetch = async (url, init) => {
      calls.push({ url, init });
      return Response.json(
        url.endsWith("csrf")
          ? { data: { csrf_token: "token" } }
          : { data: row(false) },
      );
    };
    assert.equal(
      (await hideAdminProduct(row().product_id, signal)).is_active,
      false,
    );
    assert.equal(calls[1].init.method, "POST");
    assert.equal(calls[1].init.body, undefined);
    assert.equal(calls[1].init.headers["X-CSRF-Token"], "token");
    calls.length = 0;
    globalThis.fetch = async (url) => {
      calls.push(url);
      if (url.endsWith("csrf"))
        return Response.json({ data: { csrf_token: "token" } });
      throw Error("response lost");
    };
    await assert.rejects(hideAdminProduct(row().product_id, signal), {
      code: "UNAVAILABLE",
    });
    assert.equal(calls.length, 2);
  } finally {
    globalThis.fetch = original;
  }
});
test("Admin product proxy confines filters, methods, IDs, cookies and CSRF/Origin", async () => {
  const original = globalThis.fetch,
    oldOrigin = process.env.MARKETPLACE_PUBLIC_ORIGIN,
    oldApi = process.env.INTERNAL_API_URL,
    calls = [];
  process.env.MARKETPLACE_PUBLIC_ORIGIN = "http://localhost";
  process.env.INTERNAL_API_URL = "http://backend:8000";
  try {
    globalThis.fetch = async (url, init) => {
      calls.push({ url: String(url), init });
      return Response.json({ data: row(false) });
    };
    assert.equal(
      (
        await proxyAdminProducts(
          new Request(
            "http://localhost/api?q=a%25&shop_id=1&is_active=false&page=1",
          ),
        )
      ).status,
      200,
    );
    assert.equal(
      calls[0].url,
      "http://backend:8000/api/v1/admin/products?q=a%25&shop_id=1&is_active=false&page=1",
    );
    for (const q of [
      "extra=1",
      "shop_id=0",
      "shop_id=9223372036854775808",
      "is_active=yes",
      "page=0",
      "page_size=101",
      "is_active=true&is_active=false",
    ])
      assert.equal(
        (await proxyAdminProducts(new Request("http://localhost/api?" + q)))
          .status,
        400,
      );
    const headers = {
      Origin: "http://localhost",
      "X-CSRF-Token": "token",
      Cookie: "marketplace_access=jwt; unrelated=secret",
    };
    assert.equal(
      (
        await proxyAdminProducts(
          new Request("http://localhost/api", { method: "POST", headers }),
          "1",
        )
      ).status,
      200,
    );
    assert.equal(
      calls[1].url,
      "http://backend:8000/api/v1/admin/products/1/hide",
    );
    assert.equal(calls[1].init.headers.get("Cookie"), "marketplace_access=jwt");
    assert.equal(
      (
        await proxyAdminProducts(
          new Request("http://localhost/api", { method: "POST" }),
          "1",
        )
      ).status,
      403,
    );
    assert.equal(
      (
        await proxyAdminProducts(
          new Request("http://localhost/api", { method: "PATCH" }),
          "1",
        )
      ).status,
      405,
    );
    assert.equal(
      (
        await proxyAdminProducts(
          new Request("http://localhost/api", { method: "POST", headers }),
          "../auth/me",
        )
      ).status,
      404,
    );
    assert.equal(calls.length, 2);
  } finally {
    globalThis.fetch = original;
    if (oldOrigin === undefined) delete process.env.MARKETPLACE_PUBLIC_ORIGIN;
    else process.env.MARKETPLACE_PUBLIC_ORIGIN = oldOrigin;
    if (oldApi === undefined) delete process.env.INTERNAL_API_URL;
    else process.env.INTERNAL_API_URL = oldApi;
  }
});
