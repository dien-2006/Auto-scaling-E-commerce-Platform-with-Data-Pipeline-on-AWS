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
const { orderPageFrom, fetchOrders, fetchOrder } = await import(
  await moduleURL("orders-client")
);
const { proxyOrders } = await import(await moduleURL("auth-proxy"));
const summary = () => ({
  order_id: "9007199254740993",
  total_amount: "12.34",
  payment_method: "COD",
  created_at: "2026-11-10T00:00:00Z",
  recipient_name: "private",
  shop_orders: [
    {
      shop_order_id: "2",
      shop_id: "3",
      shop_name: "Shop",
      order_status: "PENDING",
      subtotal: "12.34",
      items: ["private"],
    },
  ],
});
const page = () => ({ items: [summary()], page: 1, page_size: 12, total: 1 });
test("history accepts discounted totals while rejecting incorrect arithmetic", () => {
  const data = page();
  Object.assign(data.items[0], {
    discount_amount: "1.23",
    shipping_fee: "0.00",
    total_amount: "11.11",
  });
  assert.equal(orderPageFrom(data).items[0].discount_amount, "1.23");
  data.items[0].total_amount = "11.12";
  assert.equal(orderPageFrom(data), null);
});

test("order history validates exact money, BIGINT IDs, statuses and projects away private detail", () => {
  const parsed = orderPageFrom(page());
  assert.equal(parsed.items[0].order_id, "9007199254740993");
  assert.equal("recipient_name" in parsed.items[0], false);
  assert.equal("items" in parsed.items[0].shop_orders[0], false);
  for (const mutate of [
    (p) => (p.items[0].total_amount = "12.35"),
    (p) => (p.items[0].shop_orders[0].order_status = "FAKE"),
    (p) => (p.items[0].order_id = 9007199254740993),
    (p) => p.items.push(p.items[0]),
    (p) => p.items[0].shop_orders.push(p.items[0].shop_orders[0]),
    (p) => (p.page_size = 101),
    (p) => (p.total = -1),
    (p) => (p.items[0].created_at = "bad"),
  ]) {
    const bad = page();
    mutate(bad);
    assert.equal(orderPageFrom(bad), null);
  }
  assert.deepEqual(
    orderPageFrom({ items: [], page: 2, page_size: 12, total: 1 }),
    { items: [], page: 2, page_size: 12, total: 1 },
  );
});

test("private orders proxy validates paths and query allowlist before forwarding only safe cookies", async () => {
  const original = globalThis.fetch;
  const env = { internal: process.env.INTERNAL_API_URL };
  process.env.INTERNAL_API_URL = "http://backend:8000";
  let calls = [];
  globalThis.fetch = async (url, init) => {
    calls.push({ url: String(url), init });
    return Response.json(page());
  };
  try {
    for (const query of [
      "?page=0",
      "?page=1&page=2",
      "?buyer_user_id=99",
      "?page_size=101",
      "?q=x",
      "?page=1.5",
      "?page=2147483648",
    ])
      assert.equal(
        (
          await proxyOrders(
            new Request(`http://localhost/api/v1/orders${query}`),
          )
        ).status,
        400,
      );
    assert.equal(
      (
        await proxyOrders(
          new Request("http://localhost/api/v1/orders", { method: "POST" }),
        )
      ).status,
      405,
    );
    for (const id of ["../checkout", "0", "9223372036854775808"])
      assert.equal(
        (await proxyOrders(new Request("http://localhost/api/v1/orders"), id))
          .status,
        404,
      );
    assert.equal(
      (
        await proxyOrders(
          new Request("http://localhost/api/v1/orders/4?page=1"),
          "4",
        )
      ).status,
      400,
    );
    assert.equal(calls.length, 0);
    const response = await proxyOrders(
      new Request("http://localhost/api/v1/orders?page=2&page_size=12", {
        headers: {
          Cookie: "unrelated=secret; marketplace_access=test",
          Authorization: "Bearer discarded",
        },
      }),
    );
    assert.equal(response.status, 200);
    assert.equal(response.headers.get("cache-control"), "no-store");
    assert.equal(
      calls[0].url,
      "http://backend:8000/api/v1/orders?page=2&page_size=12",
    );
    assert.equal(
      calls[0].init.headers.get("cookie"),
      "marketplace_access=test",
    );
    assert.equal(calls[0].init.headers.get("authorization"), null);
    assert.equal(calls[0].init.cache, "no-store");
    await proxyOrders(
      new Request("http://localhost/api/v1/orders/9007199254740993"),
      "9007199254740993",
    );
    assert.equal(
      calls[1].url,
      "http://backend:8000/api/v1/orders/9007199254740993",
    );
  } finally {
    globalThis.fetch = original;
    if (env.internal === undefined) delete process.env.INTERNAL_API_URL;
    else process.env.INTERNAL_API_URL = env.internal;
  }
});

test("orders client separates server failure from empty data and rejects mismatched detail or pagination", async () => {
  const original = globalThis.fetch;
  let calls = 0;
  globalThis.fetch = async () => {
    calls++;
    return Response.json({ error: { code: "NOT_FOUND" } }, { status: 404 });
  };
  try {
    await assert.rejects(fetchOrder("1"), (e) => e.code === "NOT_FOUND");
    assert.equal(calls, 1);
    await assert.rejects(fetchOrder("../checkout"));
    await assert.rejects(fetchOrders(0));
    assert.equal(calls, 1);
    globalThis.fetch = async () => Response.json({ ...page(), page: 2 });
    await assert.rejects(fetchOrders(1));
    globalThis.fetch = async () => Response.json({ data: {} });
    await assert.rejects(fetchOrder("1"));
    globalThis.fetch = async () =>
      Response.json({ items: [], page: 1, page_size: 12, total: 0 });
    assert.equal((await fetchOrders(1)).total, 0);
    globalThis.fetch = async () => {
      throw new TypeError("offline");
    };
    await assert.rejects(fetchOrders(1));
  } finally {
    globalThis.fetch = original;
  }
});
