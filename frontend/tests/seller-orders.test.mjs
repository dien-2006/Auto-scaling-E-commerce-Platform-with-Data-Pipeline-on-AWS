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
const {
  sellerOrderFrom,
  fetchSellerOrder,
  fetchSellerOrders,
  changeShopOrder,
} = await import(await moduleURL("seller-orders-client"));
const { proxySellerOrders, proxyCancelOrder } = await import(
  await moduleURL("auth-proxy")
);
const detail = (status = "PENDING") => ({
  shop_order_id: "9007199254740993",
  order_id: "9007199254740994",
  shop_id: "9007199254740995",
  order_status: status,
  subtotal: "12.34",
  created_at: "2026-11-11T00:00:00Z",
  updated_at: "2026-11-11T00:00:00Z",
  recipient_name: "Buyer",
  phone: "0900000000",
  shipping_address: "Test address",
  payment_method: "COD",
  items: [
    {
      order_item_id: "5",
      product_id: "6",
      product_name: "Snapshot",
      unit_price: "12.34",
      quantity: 1,
      line_total: "12.34",
    },
  ],
  buyer_user_id: "private",
  total_amount: "999",
  shop_orders: ["other shop"],
});
test("seller order projection validates exact money, snapshot lines and shop identity without sibling data", () => {
  const value = sellerOrderFrom(detail(), detail().shop_id, true);
  assert.equal(value.shop_order_id, detail().shop_order_id);
  assert.equal(value.items[0].line_total, "12.34");
  for (const key of ["buyer_user_id", "total_amount", "shop_orders"])
    assert.equal(key in value, false);
  assert.equal(sellerOrderFrom(detail(), "1", true), null);
  assert.equal(
    sellerOrderFrom({ ...detail(), subtotal: "13" }, detail().shop_id, true),
    null,
  );
  assert.equal(sellerOrderFrom({ ...detail(), order_status: "UNKNOWN" }), null);
  assert.equal("phone" in sellerOrderFrom(detail()), false);
});
test("seller reads reject mismatched pages, IDs and cross-shop records", async () => {
  const original = globalThis.fetch,
    signal = new AbortController().signal;
  try {
    globalThis.fetch = async () => Response.json({ data: detail() });
    assert.equal(
      (await fetchSellerOrder(detail().shop_order_id, detail().shop_id, signal))
        .recipient_name,
      "Buyer",
    );
    await assert.rejects(fetchSellerOrder("1", detail().shop_id, signal), {
      code: "UNAVAILABLE",
    });
    globalThis.fetch = async () =>
      Response.json({ items: [detail()], page: 1, page_size: 24, total: 1 });
    assert.equal(
      (await fetchSellerOrders(detail().shop_id, 1, "PENDING", signal)).items
        .length,
      1,
    );
    await assert.rejects(fetchSellerOrders("1", 1, "", signal), {
      code: "UNAVAILABLE",
    });
    await assert.rejects(fetchSellerOrders(detail().shop_id, 2, "", signal), {
      code: "UNAVAILABLE",
    });
  } finally {
    globalThis.fetch = original;
  }
});
test("status mutation sends expected state; buyer cancel sends no arbitrary fields; lost response never retries", async () => {
  const original = globalThis.fetch,
    calls = [],
    signal = new AbortController().signal;
  try {
    globalThis.fetch = async (url, init) => {
      calls.push({ url, init });
      return Response.json(
        url.endsWith("csrf")
          ? { data: { csrf_token: "token" } }
          : { data: detail("CONFIRMED") },
      );
    };
    await changeShopOrder(detail(), "CONFIRMED", signal);
    assert.deepEqual(JSON.parse(calls[1].init.body), {
      expected_status: "PENDING",
      status: "CONFIRMED",
    });
    assert.equal(calls[1].init.method, "PATCH");
    assert.equal(calls[1].init.credentials, "same-origin");
    calls.length = 0;
    globalThis.fetch = async (url, init) => {
      calls.push({ url, init });
      if (url.endsWith("csrf"))
        return Response.json({ data: { csrf_token: "token" } });
      throw Error("response lost after commit");
    };
    await assert.rejects(changeShopOrder(detail(), "CANCELLED", signal, true), {
      code: "UNAVAILABLE",
    });
    assert.equal(calls.length, 2);
    assert.equal(calls[1].init.method, "POST");
    assert.equal(calls[1].init.body, undefined);
    assert.equal(
      calls[1].url,
      `/api/v1/orders/${detail().order_id}/shop-orders/${detail().shop_order_id}/cancel`,
    );
  } finally {
    globalThis.fetch = original;
  }
});
test("seller and cancellation proxies constrain IDs, methods, filters, query and write security", async () => {
  const original = globalThis.fetch,
    oldOrigin = process.env.MARKETPLACE_PUBLIC_ORIGIN,
    oldApi = process.env.INTERNAL_API_URL,
    calls = [];
  process.env.MARKETPLACE_PUBLIC_ORIGIN = "http://localhost";
  process.env.INTERNAL_API_URL = "http://backend:8000";
  const headers = {
    Origin: "http://localhost",
    "Content-Type": "application/json",
    "X-CSRF-Token": "token",
    Cookie: "marketplace_access=jwt; other=secret",
  };
  try {
    globalThis.fetch = async (url, init) => {
      calls.push({ url: String(url), init });
      return Response.json({ data: detail() });
    };
    assert.equal(
      (
        await proxySellerOrders(
          new Request("http://localhost/api?status=PENDING&page=1"),
        )
      ).status,
      200,
    );
    assert.equal(
      calls[0].url,
      "http://backend:8000/api/v1/seller/orders?status=PENDING&page=1",
    );
    for (const query of [
      "status=INVALID",
      "status=PENDING&status=CONFIRMED",
      "page=0",
      "page_size=101",
      "other=1",
    ])
      assert.equal(
        (await proxySellerOrders(new Request("http://localhost/api?" + query)))
          .status,
        400,
      );
    assert.equal(
      (
        await proxySellerOrders(
          new Request("http://localhost/api", {
            method: "PATCH",
            headers,
            body: "{}",
          }),
          "1",
          true,
        )
      ).status,
      200,
    );
    assert.equal(calls[1].init.headers.get("Cookie"), "marketplace_access=jwt");
    assert.equal(
      (
        await proxyCancelOrder(
          new Request("http://localhost/api", { method: "POST", headers }),
          "1",
          "2",
        )
      ).status,
      200,
    );
    assert.equal(
      calls[2].url,
      "http://backend:8000/api/v1/orders/1/shop-orders/2/cancel",
    );
    assert.equal(
      (
        await proxyCancelOrder(
          new Request("http://localhost/api", { method: "POST" }),
          "1",
          "2",
        )
      ).status,
      403,
    );
    assert.equal(
      (
        await proxyCancelOrder(
          new Request("http://localhost/api", { method: "POST", headers }),
          "../auth/me",
          "2",
        )
      ).status,
      404,
    );
    assert.equal(
      (
        await proxySellerOrders(
          new Request("http://localhost/api", { method: "DELETE" }),
          "1",
        )
      ).status,
      405,
    );
    assert.equal(calls.length, 3);
  } finally {
    globalThis.fetch = original;
    if (oldOrigin === undefined) delete process.env.MARKETPLACE_PUBLIC_ORIGIN;
    else process.env.MARKETPLACE_PUBLIC_ORIGIN = oldOrigin;
    if (oldApi === undefined) delete process.env.INTERNAL_API_URL;
    else process.env.INTERNAL_API_URL = oldApi;
  }
});


test("seller detail projects buyer display name without account identifiers", () => {
  const value = sellerOrderFrom({...detail(), buyer_name:"Buyer display name"}, detail().shop_id, true);
  assert.equal(value.buyer_name, "Buyer display name");
  assert.equal("buyer_user_id" in value, false);
  assert.equal(sellerOrderFrom({...detail(), buyer_name:42}, detail().shop_id, true), null);
});
