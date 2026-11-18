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
  ]) {
    const url = await moduleURL(match[2]);
    outputText = outputText.replace(match[0], `from ${JSON.stringify(url)}`);
  }
  const url = `data:text/javascript;base64,${Buffer.from(outputText).toString("base64")}`;
  urls.set(name, url);
  return url;
}
const { sellerShopFrom, shopInputError, fetchSellerShop, saveSellerShop } =
  await import(await moduleURL("seller-shop-client"));
const { proxySellerShop } = await import(await moduleURL("auth-proxy"));
const { safeReturnPath } = await import(await moduleURL("auth-contract"));
const shop = () => ({
  shop_id: "9007199254740993",
  owner_user_id: "9007199254740994",
  shop_name: "Shop",
  shop_slug: "my-shop",
  description: null,
  contact_email: null,
  logo_url: null,
  shop_status: "PENDING",
  created_at: "2026-11-10T00:00:00Z",
  updated_at: "2026-11-10T00:00:00Z",
  logo_key: "private/key",
  password_hash: "discarded",
});
const input = () => ({
  shop_name: "Shop",
  shop_slug: "my-shop",
  description: null,
  contact_email: null,
});

test("seller private projection enforces exact owner/BIGINT/status and strips raw storage keys", () => {
  const parsed = sellerShopFrom(shop(), "9007199254740994");
  assert.equal(parsed.shop_id, "9007199254740993");
  assert.equal("logo_key" in parsed, false);
  assert.equal("password_hash" in parsed, false);
  assert.equal(sellerShopFrom(shop(), "9007199254740995"), null);
  for (const change of [
    { shop_id: 9007199254740993 },
    { shop_status: "SELLER" },
    { logo_url: "javascript:alert(1)" },
    { created_at: "bad" },
  ])
    assert.equal(
      sellerShopFrom({ ...shop(), ...change }, "9007199254740994"),
      null,
    );
  for (const status of ["PENDING", "APPROVED", "REJECTED", "LOCKED"])
    assert.ok(
      sellerShopFrom({ ...shop(), shop_status: status }, "9007199254740994"),
    );
});

test("shop input enforces create slug/name/description bounds and keeps safe seller return URL", () => {
  assert.equal(shopInputError(input(), true), null);
  assert.equal(
    shopInputError({ ...input(), shop_slug: undefined }, false),
    null,
  );
  for (const change of [
    { shop_name: " " },
    { shop_name: "x".repeat(151) },
    { shop_slug: "../other" },
    { shop_slug: "Upper" },
    { shop_slug: "a--b" },
    { description: "x".repeat(5001) },
    { contact_email: "bad" },
  ])
    assert.ok(shopInputError({ ...input(), ...change }, true));
  assert.equal(safeReturnPath("/kenh-nguoi-ban"), "/kenh-nguoi-ban");
  for (const value of [
    "//hostile.invalid",
    "/kenh-nguoi-ban-evil",
    "/kenh-nguoi-ban%5cother",
  ])
    assert.equal(safeReturnPath(value), "/");
});

test("seller proxy confines methods/query/target/cookies and protects every write with Origin/CSRF/body limit", async () => {
  const original = globalThis.fetch,
    previous = process.env.INTERNAL_API_URL,
    publicOrigin = process.env.MARKETPLACE_PUBLIC_ORIGIN;
  process.env.INTERNAL_API_URL = "http://backend:8000";
  process.env.MARKETPLACE_PUBLIC_ORIGIN = "http://localhost";
  let calls = [];
  globalThis.fetch = async (url, init) => {
    calls.push({ url: String(url), init });
    return Response.json({ data: shop() });
  };
  const request = (method, headers = {}, body) =>
    new Request("http://localhost/api/v1/seller/shop", {
      method,
      headers,
      ...(body ? { body } : {}),
    });
  try {
    assert.equal((await proxySellerShop(request("DELETE"))).status, 405);
    assert.equal(
      (
        await proxySellerShop(
          new Request("http://localhost/api/v1/seller/shop?owner_user_id=1"),
        )
      ).status,
      400,
    );
    for (const method of ["POST", "PATCH"]) {
      assert.equal(
        (
          await proxySellerShop(
            request(method, { "Content-Type": "application/json" }, "{}"),
          )
        ).status,
        403,
      );
      assert.equal(
        (
          await proxySellerShop(
            request(
              method,
              {
                Origin: "https://hostile.invalid",
                "X-CSRF-Token": "test",
                "Content-Type": "application/json",
              },
              "{}",
            ),
          )
        ).status,
        403,
      );
    }
    assert.equal(calls.length, 0);
    const headers = {
      Origin: "http://localhost",
      "X-CSRF-Token": "test",
      "Content-Type": "application/json",
      Cookie: "marketplace_access=token; other=private",
    };
    assert.equal(
      (await proxySellerShop(request("POST", headers, "x".repeat(32769))))
        .status,
      413,
    );
    const response = await proxySellerShop(
      request(
        "PATCH",
        headers,
        JSON.stringify({ description: "x".repeat(10000) }),
      ),
    );
    assert.equal(response.headers.get("cache-control"), "no-store");
    assert.equal(calls[0].url, "http://backend:8000/api/v1/seller/shop");
    assert.equal(
      calls[0].init.headers.get("cookie"),
      "marketplace_access=token",
    );
    assert.equal(calls[0].init.headers.get("x-csrf-token"), "test");
  } finally {
    globalThis.fetch = original;
    if (previous === undefined) delete process.env.INTERNAL_API_URL;
    else process.env.INTERNAL_API_URL = previous;
    if (publicOrigin === undefined)
      delete process.env.MARKETPLACE_PUBLIC_ORIGIN;
    else process.env.MARKETPLACE_PUBLIC_ORIGIN = publicOrigin;
  }
});

test("shop client distinguishes absent shop from failures; writes only allowlisted fields, no automatic retry", async () => {
  const original = globalThis.fetch;
  let calls = [];
  globalThis.fetch = async (url, init) => {
    calls.push({ url, init });
    if (url.endsWith("/csrf"))
      return Response.json({ data: { csrf_token: "signed" } });
    return Response.json(
      { data: shop() },
      { status: init?.method === "POST" ? 201 : 200 },
    );
  };
  try {
    const saved = await saveSellerShop(
      "POST",
      {
        ...input(),
        owner_user_id: "1",
        shop_status: "APPROVED",
        logo_key: "private",
      },
      "9007199254740994",
    );
    assert.equal(saved.shop_status, "PENDING");
    const body = JSON.parse(calls[1].init.body);
    assert.deepEqual(Object.keys(body).sort(), [
      "contact_email",
      "description",
      "shop_name",
      "shop_slug",
    ]);
    assert.equal(calls[1].init.headers["X-CSRF-Token"], "signed");
    calls = [];
    await saveSellerShop("PATCH", input(), "9007199254740994");
    assert.equal("shop_slug" in JSON.parse(calls[1].init.body), false);
    globalThis.fetch = async () =>
      Response.json({ error: { code: "NOT_FOUND" } }, { status: 404 });
    assert.equal(await fetchSellerShop("9007199254740994"), null);
    globalThis.fetch = async () =>
      Response.json(
        { error: { code: "DEPENDENCY_UNAVAILABLE" } },
        { status: 503 },
      );
    await assert.rejects(fetchSellerShop("9007199254740994"));
    globalThis.fetch = async () => Response.json({ data: shop() });
    await assert.rejects(fetchSellerShop("1"));
    calls = [];
    globalThis.fetch = async (url, init) => {
      calls.push({ url, init });
      if (url.endsWith("/csrf"))
        return Response.json({ data: { csrf_token: "signed" } });
      throw new TypeError("response lost after commit");
    };
    await assert.rejects(saveSellerShop("POST", input(), "9007199254740994"));
    assert.equal(calls.filter((c) => c.init?.method === "POST").length, 1);
  } finally {
    globalThis.fetch = original;
  }
});

const { suggestedShopSlug } = await import(
  await moduleURL("seller-registration")
);
test("registration derives a bounded Vietnamese slug while allowing explicit correction", () => {
  assert.equal(suggestedShopSlug(" An Nhiên Đẹp & Khỏe "), "an-nhien-dep-khoe");
  assert.equal(suggestedShopSlug("COCO --- Shop 2026!"), "coco-shop-2026");
  assert.equal(suggestedShopSlug("💙💙"), "");
  const long = suggestedShopSlug("coco ".repeat(60));
  assert.ok(long.length <= 160 && !long.endsWith("-"));
  assert.equal(
    shopInputError(
      {
        shop_name: "💙",
        shop_slug: "",
        description: null,
        contact_email: null,
      },
      true,
    ) !== null,
    true,
  );
});
