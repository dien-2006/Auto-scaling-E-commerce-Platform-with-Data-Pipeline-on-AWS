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
  for (const match of [
    ...outputText.matchAll(/from (["'])@\/lib\/([^"']+)\1/g),
  ])
    outputText = outputText.replace(
      match[0],
      `from ${JSON.stringify(await moduleURL(match[2]))}`,
    );
  const url = `data:text/javascript;base64,${Buffer.from(outputText).toString("base64")}`;
  urls.set(name, url);
  return url;
}
const { adminShopFrom, fetchAdminShops, changeShopStatus } = await import(
  await moduleURL("admin-shops-client")
);
const { proxyAdminShops } = await import(await moduleURL("auth-proxy"));
const { safeReturnPath } = await import(await moduleURL("auth-contract"));
const shop = (status = "PENDING") => ({
  shop_id: "9007199254740993",
  owner_user_id: "9007199254740994",
  shop_name: "Shop",
  shop_slug: "test-shop",
  description: null,
  contact_email: "shop@example.com",
  logo_url: null,
  shop_status: status,
  created_at: "2026-11-11T00:00:00Z",
  updated_at: "2026-11-11T00:00:00Z",
});
test("Admin shop projection preserves exact IDs, private contact and status without raw keys", () => {
  assert.deepEqual(
    adminShopFrom({ ...shop(), logo_key: "secret", password_hash: "secret" }),
    shop(),
  );
  assert.equal(adminShopFrom({ ...shop(), owner_user_id: 1 }), null);
  assert.equal(adminShopFrom({ ...shop(), shop_status: "ACTIVE" }), null);
  const logoUrl = "https://images.example/logo/1.png?signature=test-only";
  assert.deepEqual(
    adminShopFrom({
      ...shop(),
      logo_url: logoUrl,
      logo_key: "secret",
      password_hash: "secret",
    }),
    { ...shop(), logo_url: logoUrl },
  );
  for (const unsafeUrl of [
    "http://images.example/logo/1.png",
    "javascript:alert(1)",
    "data:image/png;base64,AA==",
    "https://user:password@images.example/logo/1.png",
    "not-a-url",
  ]) {
    assert.equal(adminShopFrom({ ...shop(), logo_url: unsafeUrl }), null);
  }
  assert.equal(safeReturnPath("/admin/shops"), "/admin/shops");
  assert.equal(safeReturnPath("/admin/shops/mutate"), "/");
});
test("Admin shop pages validate pagination/filter/unique IDs and encode search literally", async () => {
  const original = globalThis.fetch,
    calls = [],
    signal = new AbortController().signal;
  try {
    globalThis.fetch = async (url) => {
      calls.push(url);
      return Response.json({
        items: [shop()],
        page: 1,
        page_size: 24,
        total: 1,
      });
    };
    assert.equal(
      (await fetchAdminShops(1, "a&status=LOCKED", "PENDING", signal)).items
        .length,
      1,
    );
    assert.match(calls[0], /q=a%26status%3DLOCKED/);
    await assert.rejects(fetchAdminShops(2, "", "", signal), {
      code: "UNAVAILABLE",
    });
    await assert.rejects(fetchAdminShops(1, "", "LOCKED", signal), {
      code: "UNAVAILABLE",
    });
    globalThis.fetch = async () =>
      Response.json({
        items: [shop(), shop()],
        page: 1,
        page_size: 24,
        total: 2,
      });
    await assert.rejects(fetchAdminShops(1, "", "", signal), {
      code: "UNAVAILABLE",
    });
  } finally {
    globalThis.fetch = original;
  }
});
test("Shop transition sends expected status with CSRF, validates identity and never retries lost responses", async () => {
  const original = globalThis.fetch,
    calls = [],
    signal = new AbortController().signal;
  try {
    globalThis.fetch = async (url, init) => {
      calls.push({ url, init });
      return Response.json(
        url.endsWith("csrf")
          ? { data: { csrf_token: "token" } }
          : { data: shop("APPROVED") },
      );
    };
    assert.equal(
      (await changeShopStatus(shop(), "APPROVED", signal)).shop_status,
      "APPROVED",
    );
    assert.deepEqual(JSON.parse(calls[1].init.body), {
      expected_status: "PENDING",
      shop_status: "APPROVED",
    });
    assert.equal(calls[1].init.credentials, "same-origin");
    calls.length = 0;
    globalThis.fetch = async (url) => {
      calls.push(url);
      if (url.endsWith("csrf"))
        return Response.json({ data: { csrf_token: "token" } });
      throw Error("response lost after commit");
    };
    await assert.rejects(changeShopStatus(shop(), "REJECTED", signal), {
      code: "UNAVAILABLE",
    });
    assert.equal(calls.length, 2);
  } finally {
    globalThis.fetch = original;
  }
});
test("Admin shop proxy limits filters/path/method/headers and protects status mutation", async () => {
  const original = globalThis.fetch,
    oldOrigin = process.env.MARKETPLACE_PUBLIC_ORIGIN,
    oldApi = process.env.INTERNAL_API_URL,
    calls = [];
  process.env.MARKETPLACE_PUBLIC_ORIGIN = "http://localhost";
  process.env.INTERNAL_API_URL = "http://backend:8000";
  try {
    globalThis.fetch = async (url, init) => {
      calls.push({ url: String(url), init });
      return Response.json({ data: shop() });
    };
    assert.equal(
      (
        await proxyAdminShops(
          new Request("http://localhost/api?q=a%25&status=PENDING&page=1"),
        )
      ).status,
      200,
    );
    assert.equal(
      calls[0].url,
      "http://backend:8000/api/v1/admin/shops?q=a%25&status=PENDING&page=1",
    );
    for (const query of [
      "other=1",
      "status=ACTIVE",
      "status=PENDING&status=LOCKED",
      "page=0",
      "page_size=101",
    ])
      assert.equal(
        (await proxyAdminShops(new Request("http://localhost/api?" + query)))
          .status,
        400,
      );
    const headers = {
      Origin: "http://localhost",
      "X-CSRF-Token": "token",
      "Content-Type": "application/json",
      Cookie: "marketplace_access=jwt; unrelated=secret",
    };
    assert.equal(
      (
        await proxyAdminShops(
          new Request("http://localhost/api", {
            method: "PATCH",
            headers,
            body: '{"expected_status":"PENDING","shop_status":"APPROVED"}',
          }),
          "1",
        )
      ).status,
      200,
    );
    assert.equal(
      calls[1].url,
      "http://backend:8000/api/v1/admin/shops/1/status",
    );
    assert.equal(calls[1].init.headers.get("Cookie"), "marketplace_access=jwt");
    assert.equal(
      (
        await proxyAdminShops(
          new Request("http://localhost/api", { method: "PATCH" }),
          "1",
        )
      ).status,
      403,
    );
    assert.equal(
      (
        await proxyAdminShops(
          new Request("http://localhost/api", {
            method: "PATCH",
            headers: { ...headers, Origin: "https://hostile.invalid" },
          }),
          "1",
        )
      ).status,
      403,
    );
    assert.equal(
      (
        await proxyAdminShops(
          new Request("http://localhost/api", { method: "DELETE" }),
          "1",
        )
      ).status,
      405,
    );
    assert.equal(
      (
        await proxyAdminShops(
          new Request("http://localhost/api", { method: "PATCH", headers }),
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
