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
const contract = await import(await moduleURL("checkout-contract"));
const { submitCheckout, lookupCheckout, CheckoutFailure } = await import(
  await moduleURL("checkout-client")
);
const { proxyCheckout } = await import(await moduleURL("auth-proxy"));
const key = "c5f0654b-38cd-4ffa-9bb3-5c084c0c2d4b";

test("saved checkout lookup uses GET only, distinguishes missing and rejects unknown results", async () => {
  const old = globalThis.fetch;
  const calls = [];
  try {
    globalThis.fetch = async (url, init) => {
      calls.push({ url, init });
      return Response.json({ data: null });
    };
    assert.equal(await lookupCheckout(key), null);
    assert.equal(calls.length, 1);
    assert.equal(calls[0].url, "/api/v1/orders/checkout-status");
    assert.equal(calls[0].init.body, undefined);
    assert.equal(calls[0].init.headers["Idempotency-Key"], key);
    globalThis.fetch = async () => Response.json({ data: order() });
    assert.equal((await lookupCheckout(key)).order_id, order().order_id);
    for (const [body, status] of [
      [{}, 200],
      [{ data: {} }, 200],
      [{ error: { code: "UNAVAILABLE" } }, 503],
    ]) {
      globalThis.fetch = async () => Response.json(body, { status });
      await assert.rejects(lookupCheckout(key));
    }
  } finally {
    globalThis.fetch = old;
  }
});
const payload = () => ({
  address_id: "9007199254740993",
  payment_method: "COD",
  items: [
    {
      product_id: "9007199254740994",
      quantity: 2,
      expected_unit_price: "12.34",
    },
  ],
});
const intent = () => ({
  version: 1,
  user_id: "9007199254740995",
  key,
  payload: payload(),
});
const order = () => ({
  order_id: "9007199254740996",
  total_amount: "24.68",
  payment_method: "COD",
  created_at: "2026-11-10T00:00:00Z",
  recipient_name: "Mai",
  phone: "0901234567",
  shipping_address: "Private address",
  shop_orders: [
    {
      shop_order_id: "17",
      shop_id: "18",
      shop_name: "Shop",
      order_status: "PENDING",
      subtotal: "24.68",
      items: [
        {
          order_item_id: "19",
          product_id: "9007199254740994",
          product_name: "Serum",
          unit_price: "12.34",
          quantity: 2,
          line_total: "24.68",
          password_hash: "private",
        },
      ],
    },
  ],
  user_id: "private",
  token: "private",
});
test("checkout payload validates exact IDs/price, COD, full intent shape and numeric limits", () => {
  assert.equal(
    contract.checkoutPayloadFrom(payload()).address_id,
    "9007199254740993",
  );
  for (const mutate of [
    (p) => (p.payment_method = "CARD"),
    (p) => (p.address_id = 4),
    (p) => (p.items[0].quantity = 1.5),
    (p) => (p.items[0].expected_unit_price = 12.34),
    (p) => (p.items[0].expected_unit_price = "1e2"),
    (p) => p.items.push({ ...p.items[0] }),
    (p) => (p.user_id = "17"),
    (p) => (p.items[0].quantity = 0),
    (p) => (p.items[0].product_id = "9223372036854775808"),
  ]) {
    const p = payload();
    mutate(p);
    assert.equal(contract.checkoutPayloadFrom(p), null);
  }
  const tooLarge = payload();
  tooLarge.items[0].expected_unit_price = "999999999999.99";
  assert.equal(contract.checkoutPayloadFrom(tooLarge), null);
  const free = payload();
  free.items[0].expected_unit_price = "0.00";
  assert.ok(contract.checkoutPayloadFrom(free));
});
test("order projection checks arithmetic, IDs, status and private extras before success", () => {
  const result = contract.orderFrom(order());
  assert.equal(result.order_id, "9007199254740996");
  assert.equal("token" in result, false);
  assert.equal("password_hash" in result.shop_orders[0].items[0], false);
  for (const mutate of [
    (v) => (v.total_amount = "24.69"),
    (v) => (v.shop_orders[0].subtotal = "24.69"),
    (v) => (v.shop_orders[0].items[0].line_total = "24.69"),
    (v) => (v.shop_orders[0].order_status = "PAID"),
    (v) => v.shop_orders.push({ ...v.shop_orders[0] }),
    (v) => v.shop_orders[0].items.push({ ...v.shop_orders[0].items[0] }),
    (v) => (v.payment_method = "CARD"),
    (v) => (v.created_at = "invalid"),
    (v) => (v.order_id = "0"),
  ]) {
    const v = order();
    mutate(v);
    assert.equal(contract.orderFrom(v), null);
  }
});
test("coupon intent survives recovery and discounted order arithmetic remains exact", () => {
  const p = payload();
  p.coupon_code = " CODE ";
  p.expected_coupon_discount = "2.47";
  assert.equal(contract.checkoutPayloadFrom(p).coupon_code, "CODE");
  const v = order();
  v.discount_amount = "2.47";
  v.shipping_fee = "0.00";
  v.total_amount = "22.21";
  assert.equal(contract.orderFrom(v).discount_amount, "2.47");
  v.total_amount = "22.20";
  assert.equal(contract.orderFrom(v), null);
  p.coupon_code = " ";
  assert.equal(contract.checkoutPayloadFrom(p), null);
});
test("checkout intent preserves key/payload across reload and isolates accounts without PII", () => {
  const data = new Map(),
    storage = {
      getItem: (k) => data.get(k) ?? null,
      setItem: (k, v) => data.set(k, v),
      removeItem: (k) => data.delete(k),
    };
  const original = intent();
  assert.equal(contract.readIntent(storage, original.user_id), null);
  contract.saveIntent(storage, original);
  assert.deepEqual(contract.readIntent(storage, original.user_id), original);
  assert.equal(contract.readIntent(storage, "99"), null);
  const serialized = [...data.values()][0];
  for (const pii of [
    "phone",
    "recipient_name",
    "shipping_address",
    "product_name",
    "token",
  ])
    assert.equal(serialized.includes(pii), false);
  assert.equal(
    contract.intentFrom({ ...original, phone: "secret" }, original.user_id),
    null,
  );
  assert.equal(contract.intentFrom(original, "99"), null);
  const repaired = intent();
  repaired.payload.items[0].expected_unit_price = "11.00";
  contract.saveIntent(storage, repaired);
  assert.equal(contract.readIntent(storage, repaired.user_id).key, key);
  contract.clearIntent(storage, original.user_id);
  assert.equal(contract.readIntent(storage, original.user_id), null);
  assert.throws(() =>
    contract.saveIntent(
      { getItem: () => null, setItem: () => {}, removeItem: () => {} },
      intent(),
    ),
  );
  assert.throws(() =>
    contract.readIntent(
      { getItem: () => "malformed", setItem: () => {}, removeItem: () => {} },
      original.user_id,
    ),
  );
});
test("checkout proxy accepts only fixed POST route, UUID, same origin; forwards key and bounds body", async () => {
  const oldFetch = globalThis.fetch,
    oldApi = process.env.INTERNAL_API_URL,
    oldOrigin = process.env.MARKETPLACE_PUBLIC_ORIGIN;
  process.env.INTERNAL_API_URL = "http://backend:8000";
  process.env.MARKETPLACE_PUBLIC_ORIGIN = "https://coco.test";
  let calls = 0;
  globalThis.fetch = async (url, init) => {
    calls++;
    assert.equal(String(url), "http://backend:8000/api/v1/orders/checkout");
    assert.equal(init.headers.get("Idempotency-Key"), key);
    assert.equal(init.headers.get("cookie"), "marketplace_access=jwt");
    assert.equal(init.headers.has("Authorization"), false);
    assert.equal(init.cache, "no-store");
    assert.equal(init.redirect, "error");
    return new Response(JSON.stringify({ data: order() }), { status: 201 });
  };
  function request({
    method = "POST",
    origin = "https://coco.test",
    id = key,
    body = "{}",
  } = {}) {
    return new Request("https://coco.test/api/v1/orders/checkout", {
      method,
      headers: {
        origin,
        "idempotency-key": id,
        "x-csrf-token": "signed",
        "content-type": "application/json",
        cookie: "analytics=private; marketplace_access=jwt",
        Authorization: "Bearer private",
      },
      ...(method === "POST" ? { body } : {}),
    });
  }
  try {
    assert.equal((await proxyCheckout(request({ method: "GET" }))).status, 405);
    assert.equal((await proxyCheckout(request({ id: "../bad" }))).status, 400);
    assert.equal(
      (await proxyCheckout(request({ origin: "https://evil.test" }))).status,
      403,
    );
    assert.equal(
      (await proxyCheckout(request({ body: "x".repeat(131073) }))).status,
      413,
    );
    assert.equal(calls, 0);
    const response = await proxyCheckout(request({ body: "x".repeat(100000) }));
    assert.equal(response.status, 201);
    assert.equal(response.headers.get("cache-control"), "no-store");
    assert.equal(calls, 1);
  } finally {
    globalThis.fetch = oldFetch;
    if (oldApi === undefined) delete process.env.INTERNAL_API_URL;
    else process.env.INTERNAL_API_URL = oldApi;
    if (oldOrigin === undefined) delete process.env.MARKETPLACE_PUBLIC_ORIGIN;
    else process.env.MARKETPLACE_PUBLIC_ORIGIN = oldOrigin;
  }
});
test("checkout client retries only when called explicitly and uses identical intent for ambiguous results", async () => {
  const oldFetch = globalThis.fetch;
  let attempts = 0;
  const sent = [];
  globalThis.fetch = async (url, init) => {
    if (url.endsWith("/csrf"))
      return new Response('{"data":{"csrf_token":"signed"}}');
    attempts++;
    sent.push({ key: init.headers["Idempotency-Key"], body: init.body });
    return attempts === 1
      ? new Response('{"error":{"code":"DEPENDENCY_UNAVAILABLE"}}', {
          status: 503,
        })
      : new Response(JSON.stringify({ data: order() }), { status: 200 });
  };
  try {
    await assert.rejects(
      submitCheckout(intent()),
      (e) => e instanceof CheckoutFailure && !e.repairAllowed,
    );
    assert.equal(attempts, 1);
    const result = await submitCheckout(intent());
    assert.equal(result.replayed, true);
    assert.deepEqual(sent[0], sent[1]);
  } finally {
    globalThis.fetch = oldFetch;
  }
});
test("checkout client distinguishes repairable business failures and refuses malformed success", async () => {
  const oldFetch = globalThis.fetch;
  try {
    for (const [status, body, repair] of [
      [409, { error: { code: "PRICE_CHANGED" } }, true],
      [409, { error: { code: "OUT_OF_STOCK" } }, true],
      [401, { error: { code: "TOKEN_EXPIRED" } }, false],
      [403, { error: { code: "CSRF_FAILED" } }, false],
      [201, { data: { order_id: "1" } }, false],
    ]) {
      globalThis.fetch = async (url) =>
        url.endsWith("/csrf")
          ? new Response('{"data":{"csrf_token":"signed"}}')
          : new Response(JSON.stringify(body), { status });
      await assert.rejects(
        submitCheckout(intent()),
        (e) => e instanceof CheckoutFailure && e.repairAllowed === repair,
      );
    }
  } finally {
    globalThis.fetch = oldFetch;
  }
});

test("scoped coupon intent preserves two COCO slots, shop codes and confirmed freight", () => {
  const v = {
    ...payload(),
    payment_method: "BANK_TRANSFER",
    shipping_method: "COCOEXPRESS",
    coco_coupon_code: "COCO10",
    shipping_coupon_code: "SHIP50",
    shop_coupons: [{ shop_id: "17", code: "SHOP10" }],
    expected_coupon_discount: "2.47",
    expected_shipping_fee: "30000.00",
    expected_shipping_discount: "30000.00",
  };
  assert.deepEqual(contract.checkoutPayloadFrom(v), v);
  assert.equal(
    contract.checkoutPayloadFrom({ ...v, shipping_coupon_code: "COCO10" }),
    null,
  );
  assert.equal(
    contract.checkoutPayloadFrom({
      ...v,
      shop_coupons: [...v.shop_coupons, ...v.shop_coupons],
    }),
    null,
  );
  assert.equal(
    contract.checkoutPayloadFrom({ ...v, expected_shipping_fee: 30000 }),
    null,
  );
  const result = {
    ...order(),
    payment_method: "BANK_TRANSFER",
    discount_amount: "2.47",
    shipping_fee: "30000.00",
    shipping_discount_amount: "30000.00",
    total_amount: "30022.21",
    payment_status: "PENDING",
  };
  assert.equal(contract.orderFrom(result).payment_method, "BANK_TRANSFER");
  assert.equal(contract.orderFrom(result).shipping_discount_amount, "30000.00");
});


test("checkout UUID supports HTTP crypto without randomUUID and keeps secure entropy", () => {
  const onlyRandomValues = {getRandomValues: array => crypto.getRandomValues(array)};
  const keys = Array.from({length:100}, () => contract.checkoutKey(onlyRandomValues));
  assert.equal(new Set(keys).size,100);
  assert.ok(keys.every(key => /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(key)));
  assert.throws(() => contract.checkoutKey({}), /Secure random/);
});


test("buy now payload preserves explicit scope and rejects multiple products", () => {
  const v={purchase_mode:"BUY_NOW",address_id:"1",payment_method:"COD",items:[{product_id:"2",quantity:3,expected_unit_price:"12.34"}]};
  assert.equal(contract.checkoutPayloadFrom(v).purchase_mode,"BUY_NOW");
  assert.equal(contract.checkoutPayloadFrom({...v,items:[...v.items,{...v.items[0],product_id:"3"}]}),null);
  assert.equal(contract.checkoutPayloadFrom({...v,purchase_mode:"UNKNOWN"}),null);
});


test("buy now review reads only the chosen product and calculates exact money without cart access", async () => {
  const {buyNowReview} = await import(await moduleURL("buy-now-client"));
  const old = globalThis.fetch;
  const calls=[];
  globalThis.fetch=async path=>{
    calls.push(path);
    return Response.json({data:{product_id:"297",product_name:"Chosen",price:"12.34",available_quantity:5,primary_image_url:null,shop:{shop_id:"2",shop_name:"Shop",shop_slug:"shop"}}});
  };
  try {
    const review=await buyNowReview({product:"297",quantity:2});
    assert.deepEqual(calls,["/api/v1/products/297"]);
    assert.equal(review.shops.length,1);
    assert.equal(review.shops[0].items[0].quantity,2);
    assert.equal(review.total_amount,"24.68");
  } finally {globalThis.fetch=old;}
});


test("coupon wallet persists per account, deduplicates and drops expired/malformed codes", async () => {
  const {readCoupons,saveCoupon}=await import(await moduleURL("coupon-wallet"));
  const data=new Map();const storage={getItem:k=>data.get(k)??null,setItem:(k,v)=>data.set(k,v)};
  const offer={code:"COCO10",expires_at:new Date(Date.now()+3600000).toISOString()};
  assert.equal(saveCoupon(storage,"1",offer).length,1);
  assert.equal(saveCoupon(storage,"1",offer).length,1);
  assert.equal(readCoupons(storage,"2").length,0);
  assert.equal(readCoupons(storage,"1")[0].code,"COCO10");
  assert.equal(readCoupons(storage,"1",Date.now()+7200000).length,0);
  data.set("coco.coupons.v1:1","invalid");
  assert.deepEqual(readCoupons(storage,"1"),[]);
});
