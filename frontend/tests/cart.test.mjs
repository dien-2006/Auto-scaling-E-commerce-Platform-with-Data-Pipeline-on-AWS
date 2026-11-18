import { test } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import ts from "typescript";
async function load(name) {
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
const { cartFrom } = await load("cart-contract");
const { proxyCart } = await load("auth-proxy");
function sample() {
  return {
    shops: [
      {
        shop_id: "9007199254740993",
        shop_name: "Shop",
        shop_slug: "shop",
        subtotal: "246.90",
        items: [
          {
            cart_item_id: "9007199254740994",
            product_id: "9007199254740995",
            product_name: "Serum",
            quantity: 2,
            unit_price: "123.45",
            line_total: "246.90",
            available_quantity: 5,
            is_available: true,
            unavailable_reason: null,
            primary_image_url: null,
            password_hash: "private",
          },
        ],
      },
    ],
    total_amount: "246.90",
    owner_user_id: "private",
  };
}
test("cart projection preserves exact BIGINT and Decimal totals and strips private fields", () => {
  const data = sample(),
    cart = cartFrom(data);
  assert.equal(cart.shops[0].shop_id, data.shops[0].shop_id);
  assert.equal(cart.total_amount, "246.90");
  assert.equal(JSON.stringify(cart).includes("private"), false);
  assert.deepEqual(cartFrom({ shops: [], total_amount: "0.00" }), {
    shops: [],
    total_amount: "0.00",
  });
});
test("cart rejects incorrect totals, duplicate lines, invalid quantities and unsafe images", () => {
  for (const mutate of [
    (v) => (v.total_amount = "246.91"),
    (v) => (v.shops[0].subtotal = "246.89"),
    (v) => (v.shops[0].items[0].line_total = "246.91"),
    (v) => (v.shops[0].items[0].quantity = 0),
    (v) => (v.shops[0].items[0].quantity = 1.5),
    (v) => (v.shops[0].items[0].available_quantity = 1),
    (v) => (v.shops[0].items[0].cart_item_id = "9223372036854775808"),
    (v) => (v.shops[0].items[0].primary_image_url = "javascript:alert(1)"),
    (v) => v.shops[0].items.push({ ...v.shops[0].items[0] }),
    (v) => (v.shops[0].items[0].unavailable_reason = "UNKNOWN"),
  ]) {
    const v = sample();
    mutate(v);
    assert.equal(cartFrom(v), null);
  }
  const hidden = sample();
  hidden.shops[0].items[0].is_available = false;
  hidden.shops[0].items[0].unavailable_reason = "HIDDEN_PRODUCT";
  assert.ok(cartFrom(hidden));
});
test("derived cart totals use arbitrary precision without overflowing stored-price precision", () => {
  const data = sample(),
    line = data.shops[0].items[0];
  line.unit_price = "999999999999.99";
  line.quantity = 2147483647;
  line.available_quantity = 2147483647;
  line.line_total = "2147483646999978525163.53";
  data.shops[0].subtotal = line.line_total;
  data.total_amount = line.line_total;
  assert.ok(cartFrom(data));
});
test("cart proxy confines routes/methods/IDs and protects every unsafe request", async () => {
  const oldFetch = globalThis.fetch,
    oldApi = process.env.INTERNAL_API_URL,
    oldOrigin = process.env.MARKETPLACE_PUBLIC_ORIGIN;
  process.env.INTERNAL_API_URL = "http://backend:8000";
  process.env.MARKETPLACE_PUBLIC_ORIGIN = "https://coco.test";
  const calls = [];
  globalThis.fetch = async (url, init) => {
    calls.push({ url: String(url), init });
    return new Response('{"data":{}}');
  };
  function req(method, origin = "https://coco.test") {
    return new Request("https://coco.test/api/v1/cart", {
      method,
      headers: {
        origin,
        "x-csrf-token": "signed",
        "content-type": "application/json",
        cookie: "marketplace_access=secret; analytics=private",
      },
      ...(["POST", "PATCH"].includes(method) ? { body: "{}" } : {}),
    });
  }
  try {
    for (const [method, route] of [
      ["POST", "items"],
      ["PATCH", "item"],
      ["DELETE", "item"],
    ])
      assert.equal(
        (await proxyCart(req(method, "https://evil.test"), route, "17")).status,
        403,
      );
    assert.equal(
      (await proxyCart(req("DELETE"), "item", "../auth/me")).status,
      404,
    );
    assert.equal((await proxyCart(req("GET"), "item", "17")).status, 405);
    assert.equal((await proxyCart(req("POST"), "cart")).status, 405);
    assert.equal(calls.length, 0);
    assert.equal((await proxyCart(req("GET"), "cart")).status, 200);
    assert.equal((await proxyCart(req("POST"), "items")).status, 200);
    assert.equal((await proxyCart(req("PATCH"), "item", "17")).status, 200);
    assert.equal((await proxyCart(req("DELETE"), "item", "17")).status, 200);
    assert.deepEqual(
      calls.map((c) => c.url),
      [
        "http://backend:8000/api/v1/cart",
        "http://backend:8000/api/v1/cart/items",
        "http://backend:8000/api/v1/cart/items/17",
        "http://backend:8000/api/v1/cart/items/17",
      ],
    );
    assert.equal(
      calls[1].init.headers.get("cookie"),
      "marketplace_access=secret",
    );
    assert.equal(calls[1].init.redirect, "error");
    assert.equal(calls[1].init.cache, "no-store");
  } finally {
    globalThis.fetch = oldFetch;
    if (oldApi === undefined) delete process.env.INTERNAL_API_URL;
    else process.env.INTERNAL_API_URL = oldApi;
    if (oldOrigin === undefined) delete process.env.MARKETPLACE_PUBLIC_ORIGIN;
    else process.env.MARKETPLACE_PUBLIC_ORIGIN = oldOrigin;
  }
});
