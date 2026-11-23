import { test } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import ts from "typescript";
const cache = new Map();
async function load(name) {
  if (cache.has(name)) return cache.get(name);
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
    outputText = outputText.replace(m[0], `from "${await load(m[2])}"`);
  const url = `data:text/javascript;base64,${Buffer.from(outputText).toString("base64")}`;
  cache.set(name, url);
  return url;
}
const { proxyPublicProducts, proxySellerProducts, proxySellerShop } =
  await import(await load("auth-proxy"));
const { deleteSellerShop } = await import(await load("seller-shop-client"));
const { deleteSellerProduct } = await import(
  await load("seller-products-client")
);

test("public catalog proxy validates fixed paths/query and never forwards private cookies", async () => {
  const fetch = globalThis.fetch,
    prior = process.env.INTERNAL_API_URL;
  process.env.INTERNAL_API_URL = "http://backend:8000";
  const calls = [];
  globalThis.fetch = async (url, init) => {
    calls.push({ url: String(url), init });
    return Response.json({ items: [], total: 0 });
  };
  try {
    for (const query of [
      "url=https://evil.invalid",
      "page=0",
      "page_size=101",
      "shop_id=0",
      "q=a&q=b",
      "sort=arbitrary",
    ])
      assert.equal(
        (
          await proxyPublicProducts(
            new Request("http://localhost/api/v1/products?" + query),
          )
        ).status,
        400,
      );
    assert.equal(
      (
        await proxyPublicProducts(
          new Request("http://localhost/api/v1/products"),
          "../admin",
        )
      ).status,
      404,
    );
    assert.equal(calls.length, 0);
    const response = await proxyPublicProducts(
      new Request("http://localhost/api/v1/products?page_size=12", {
        headers: {
          Cookie: "marketplace_access=private",
          Authorization: "Bearer private",
        },
      }),
    );
    assert.equal(response.status, 200);
    assert.equal(
      calls[0].url,
      "http://backend:8000/api/v1/products?page_size=12",
    );
    assert.equal(calls[0].init.headers.get("Cookie"), null);
    assert.equal(calls[0].init.headers.get("Authorization"), null);
  } finally {
    globalThis.fetch = fetch;
    if (prior === undefined) delete process.env.INTERNAL_API_URL;
    else process.env.INTERNAL_API_URL = prior;
  }
});

test("shop and product deletion handles204, exact BIGINT identity and never retries response loss", async () => {
  const fetch = globalThis.fetch;
  try {
    for (const remove of [deleteSellerShop, deleteSellerProduct]) {
      let calls = [];
      globalThis.fetch = async (url, init) => {
        calls.push({ url, init });
        return String(url).endsWith("/csrf")
          ? Response.json({ data: { csrf_token: "test-csrf" } })
          : new Response(null, { status: 204 });
      };
      await remove("9007199254740993", new AbortController().signal);
      assert.equal(calls.length, 2);
      assert.equal(calls[1].init.method, "DELETE");
      assert.equal(calls[1].init.body, undefined);
      assert.equal(calls[1].init.headers["X-CSRF-Token"], "test-csrf");
      calls = [];
      globalThis.fetch = async (url, init) => {
        calls.push({ url, init });
        if (String(url).endsWith("/csrf"))
          return Response.json({ data: { csrf_token: "test-csrf" } });
        throw new TypeError("response lost after commit");
      };
      await assert.rejects(
        remove("9007199254740993", new AbortController().signal),
      );
      assert.equal(calls.length, 2);
      await assert.rejects(remove("0", new AbortController().signal));
      assert.equal(calls.length, 2);
    }
  } finally {
    globalThis.fetch = fetch;
  }
});

test("DELETE proxy keeps ownership path, Origin/CSRF, query rejection and bodyless204", async () => {
  const fetch = globalThis.fetch,
    prior = process.env.INTERNAL_API_URL,
    origin = process.env.MARKETPLACE_PUBLIC_ORIGIN;
  process.env.INTERNAL_API_URL = "http://backend:8000";
  process.env.MARKETPLACE_PUBLIC_ORIGIN = "http://localhost";
  const calls = [];
  globalThis.fetch = async (url, init) => {
    calls.push({ url: String(url), init });
    return new Response(null, { status: 204 });
  };
  try {
    for (const proxy of [proxySellerShop, proxySellerProducts]) {
      const path = "http://localhost/api/v1/seller/resource";
      assert.equal(
        (await proxy(new Request(path, { method: "DELETE" }), "1")).status,
        403,
      );
      assert.equal(
        (await proxy(new Request(path + "?owner=2", { method: "DELETE" }), "1"))
          .status,
        400,
      );
      const response = await proxy(
        new Request(path, {
          method: "DELETE",
          headers: {
            Origin: "http://localhost",
            "X-CSRF-Token": "test-csrf",
            Cookie: "marketplace_access=test; other=private",
          },
        }),
        "1",
      );
      assert.equal(response.status, 204);
      assert.equal(await response.text(), "");
      assert.equal(calls.at(-1).init.body, undefined);
      assert.match(calls.at(-1).url, /\/1$/);
      assert.equal(
        calls.at(-1).init.headers.get("Cookie"),
        "marketplace_access=test",
      );
    }
  } finally {
    globalThis.fetch = fetch;
    if (prior === undefined) delete process.env.INTERNAL_API_URL;
    else process.env.INTERNAL_API_URL = prior;
    if (origin === undefined) delete process.env.MARKETPLACE_PUBLIC_ORIGIN;
    else process.env.MARKETPLACE_PUBLIC_ORIGIN = origin;
  }
});
