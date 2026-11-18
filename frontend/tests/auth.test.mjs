import { test } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import ts from "typescript";
async function moduleAt(name) {
  const source = await readFile(
    new URL(`../src/lib/${name}.ts`, import.meta.url),
    "utf8",
  );
  const { outputText } = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.ESNext,
      target: ts.ScriptTarget.ES2022,
    },
  });
  return import(
    `data:text/javascript;base64,${Buffer.from(outputText).toString("base64")}`
  );
}
const { safeReturnPath, accountFrom } = await moduleAt("auth-contract");
const { validRegistrationPassword } = await moduleAt("auth-contract");

test("registration password requires over eight characters, uppercase, digit and punctuation/symbol", () => {
  for (const password of [
    "Abcd1!xy",
    "abcdef1!x",
    "Abcdefg!x",
    "Abcdef12x",
    "Abcdef12 ",
    "A1!" + "x".repeat(126),
  ])
    assert.equal(validRegistrationPassword(password), false);
  for (const password of [
    "Abcde1!xy",
    "ABCDEF1!G",
    "  Abcd1!xy  ",
    "Abcde12🙂x",
  ])
    assert.equal(validRegistrationPassword(password), true);
});
const { proxyAuth, proxyAddresses } = await moduleAt("auth-proxy");
const { addressFrom } = await moduleAt("address-contract");

test("address projection validates BIGINT and never returns owner or private extras", () => {
  const input = {
    address_id: "9007199254740993",
    recipient_name: "Mai",
    phone: "0901234567",
    address_line: "12 Nguyễn Huệ",
    ward: null,
    district: null,
    city: "Hà Nội",
    is_default: true,
    created_at: "2026-11-10T00:00:00Z",
    user_id: "private",
  };
  assert.equal(addressFrom(input).address_id, input.address_id);
  assert.equal("user_id" in addressFrom(input), false);
  for (const patch of [
    { address_id: "9223372036854775808" },
    { address_id: 2 },
    { is_default: "true" },
    { phone: null },
    { created_at: "invalid" },
  ])
    assert.equal(addressFrom({ ...input, ...patch }), null);
});

test("private address proxy enforces methods, IDs, origin and CSRF for PATCH and DELETE", async () => {
  const previousFetch = globalThis.fetch;
  const previousApi = process.env.INTERNAL_API_URL;
  const previousOrigin = process.env.MARKETPLACE_PUBLIC_ORIGIN;
  process.env.INTERNAL_API_URL = "http://backend:8000";
  process.env.MARKETPLACE_PUBLIC_ORIGIN = "https://coco.test";
  const calls = [];
  globalThis.fetch = async (url, init) => {
    calls.push({ url: String(url), ...init });
    return new Response(null, { status: 204 });
  };
  const req = (method, origin = "https://coco.test", token = "signed") =>
    new Request("https://coco.test/api/v1/addresses/17", {
      method,
      headers: {
        origin,
        "x-csrf-token": token,
        "content-type": "application/json",
        cookie:
          "analytics=private; marketplace_access=access; marketplace_csrf=signed",
      },
      ...(method === "PATCH" || method === "POST" ? { body: "{}" } : {}),
    });
  try {
    for (const method of ["PATCH", "DELETE"]) {
      assert.equal(
        (await proxyAddresses(req(method, "https://evil.test"), "17")).status,
        403,
      );
      assert.equal(
        (await proxyAddresses(req(method, "https://coco.test", ""), "17"))
          .status,
        403,
      );
    }
    for (const id of [
      "../auth/me",
      "0",
      "9223372036854775808",
      "https://evil.test",
    ])
      assert.equal((await proxyAddresses(req("DELETE"), id)).status, 404);
    assert.equal((await proxyAddresses(req("POST"), "17")).status, 405);
    assert.equal((await proxyAddresses(req("GET"), "17")).status, 405);
    assert.equal(calls.length, 0);
    assert.equal((await proxyAddresses(req("PATCH"), "17")).status, 204);
    assert.equal((await proxyAddresses(req("DELETE"), "17")).status, 204);
    assert.equal(calls[0].url, "http://backend:8000/api/v1/addresses/17");
    assert.equal(calls[0].body, "{}");
    assert.equal(calls[1].body, undefined);
    assert.equal(
      calls[0].headers.get("cookie"),
      "marketplace_access=access; marketplace_csrf=signed",
    );
    assert.equal(calls[0].cache, "no-store");
    assert.equal(calls[0].redirect, "error");
  } finally {
    globalThis.fetch = previousFetch;
    if (previousApi === undefined) delete process.env.INTERNAL_API_URL;
    else process.env.INTERNAL_API_URL = previousApi;
    if (previousOrigin === undefined)
      delete process.env.MARKETPLACE_PUBLIC_ORIGIN;
    else process.env.MARKETPLACE_PUBLIC_ORIGIN = previousOrigin;
  }
});
test("return URL stays in known internal pages and rejects redirect bypasses", () => {
  for (const bad of [
    "https://evil.test",
    "//evil.test",
    "/\\evil.test",
    "/%2f%2fevil.test",
    "/san-pham%0aLocation:evil",
    "/api/v1/auth/logout",
    "/dang-nhap",
    "/san-pham/../../api",
    ["/san-pham"],
    "/%zz",
  ])
    assert.equal(safeReturnPath(bad), "/");
  for (const good of [
    "/",
    "/san-pham?q=serum",
    "/gian-hang/shop",
    "/san-pham/17",
    "/gio-hang",
    "/tai-khoan",
  ])
    assert.equal(safeReturnPath(good), good);
});
test("account projection preserves BIGINT and excludes hashes and tokens", () => {
  const user = {
    user_id: "9007199254740993",
    email: "a@example.com",
    full_name: "Test",
    phone: null,
    user_role: "USER",
    user_status: "ACTIVE",
    owned_shop: {
      shop_id: "9007199254740994",
      shop_status: "LOCKED",
      owner_user_id: "secret",
    },
    password_hash: "private",
    access_token: "private",
  };
  const account = accountFrom(user);
  assert.equal(account.user_id, user.user_id);
  assert.equal(JSON.stringify(account).includes("private"), false);
  assert.equal("owner_user_id" in account.owned_shop, false);
  for (const change of [
    { user_id: "0" },
    { user_status: "LOCKED" },
    { user_role: "SELLER" },
    { owned_shop: {} },
  ])
    assert.equal(accountFrom({ ...user, ...change }), null);
});
test("auth proxy confines target/method/source, filters headers and relays cookies", async () => {
  const previousFetch = globalThis.fetch;
  const previousApi = process.env.INTERNAL_API_URL;
  const previousOrigin = process.env.MARKETPLACE_PUBLIC_ORIGIN;
  process.env.INTERNAL_API_URL = "http://backend:8000";
  process.env.MARKETPLACE_PUBLIC_ORIGIN = "https://coco.test";
  let calls = 0;
  globalThis.fetch = async (url, options) => {
    calls++;
    assert.equal(String(url), "http://backend:8000/api/v1/auth/login");
    assert.equal(options.redirect, "error");
    assert.equal(options.cache, "no-store");
    assert.equal(
      options.headers.get("cookie"),
      "marketplace_access=abc; marketplace_csrf=def",
    );
    assert.equal(options.headers.has("authorization"), false);
    assert.equal(options.headers.get("origin"), "https://coco.test");
    const headers = new Headers({ "Content-Type": "application/json" });
    headers.append("Set-Cookie", "marketplace_access=jwt; HttpOnly; Path=/");
    headers.append("Set-Cookie", "marketplace_csrf=signed; Path=/");
    headers.append("Set-Cookie", "unrelated=value");
    return new Response('{"data":{}}', { headers });
  };
  const req = (origin = "https://coco.test", body = "{}") =>
    new Request("https://coco.test/api/v1/auth/login", {
      method: "POST",
      body,
      headers: {
        origin,
        "content-type": "application/json",
        "x-csrf-token": "def",
        cookie:
          "analytics=private; marketplace_access=abc; marketplace_csrf=def",
        Authorization: "Bearer private",
      },
    });
  try {
    assert.equal(
      (await proxyAuth(req("https://evil.test"), "login")).status,
      403,
    );
    assert.equal((await proxyAuth(req(), "https://evil.test")).status, 404);
    assert.equal((await proxyAuth(req(), "me")).status, 405);
    assert.equal(
      (await proxyAuth(req("https://coco.test", "a".repeat(8193)), "login"))
        .status,
      413,
    );
    assert.equal(calls, 0);
    const response = await proxyAuth(req(), "login");
    assert.equal(response.status, 200);
    assert.equal(response.headers.getSetCookie().length, 2);
    assert.equal(response.headers.get("cache-control"), "no-store");
    globalThis.fetch = async () => {
      throw new Error("private DSN");
    };
    const failure = await proxyAuth(req(), "login");
    assert.equal(failure.status, 503);
    assert.equal((await failure.text()).includes("private"), false);
  } finally {
    globalThis.fetch = previousFetch;
    if (previousApi === undefined) delete process.env.INTERNAL_API_URL;
    else process.env.INTERNAL_API_URL = previousApi;
    if (previousOrigin === undefined)
      delete process.env.MARKETPLACE_PUBLIC_ORIGIN;
    else process.env.MARKETPLACE_PUBLIC_ORIGIN = previousOrigin;
  }
});
