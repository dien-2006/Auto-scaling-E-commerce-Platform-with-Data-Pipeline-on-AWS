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
const { proxyShopping } = await load("auth-proxy");
const { quoteCoupon, createReview, myReview, productReviews } =
  await load("shopping-client");
test("shopping proxy confines routes, query and methods; public reviews omit private cookies", async () => {
  const previous = globalThis.fetch,
    api = process.env.INTERNAL_API_URL,
    origin = process.env.MARKETPLACE_PUBLIC_ORIGIN;
  const calls = [];
  process.env.INTERNAL_API_URL = "http://backend:8000";
  process.env.MARKETPLACE_PUBLIC_ORIGIN = "http://localhost";
  globalThis.fetch = async (url, init) => {
    calls.push({ url: String(url), init });
    return Response.json({ items: [] });
  };
  try {
    const req = (method = "GET", query = "", headers = {}) =>
      new Request("http://localhost/api/test" + query, { method, headers });
    assert.equal(
      (await proxyShopping(req(), "review", "../auth/me")).status,
      404,
    );
    assert.equal(
      (await proxyShopping(req("DELETE"), "review", "1")).status,
      405,
    );
    assert.equal((await proxyShopping(req("POST"), "review", "1")).status, 403);
    assert.equal(
      (await proxyShopping(req("POST", "?role=ADMIN"), "coupon")).status,
      400,
    );
    assert.equal(
      (await proxyShopping(req("GET", "?page=1&page=2"), "public-reviews", "1"))
        .status,
      400,
    );
    assert.equal(
      (await proxyShopping(req("GET", "?page_size=51"), "public-reviews", "1"))
        .status,
      400,
    );
    assert.equal(calls.length, 0);
    assert.equal(
      (
        await proxyShopping(
          req("GET", "?page=2", {
            Cookie: "marketplace_access=private",
            Authorization: "private",
          }),
          "public-reviews",
          "9007199254740993",
        )
      ).status,
      200,
    );
    assert.equal(
      calls[0].url,
      "http://backend:8000/api/v1/products/9007199254740993/reviews?page=2",
    );
    assert.equal(calls[0].init.headers.has("Cookie"), false);
    assert.equal(calls[0].init.headers.has("Authorization"), false);
  } finally {
    globalThis.fetch = previous;
    if (api === undefined) delete process.env.INTERNAL_API_URL;
    else process.env.INTERNAL_API_URL = api;
    if (origin === undefined) delete process.env.MARKETPLACE_PUBLIC_ORIGIN;
    else process.env.MARKETPLACE_PUBLIC_ORIGIN = origin;
  }
});
test("review mutation uses CSRF and never retries after a lost response", async () => {
  const old = globalThis.fetch;
  let writes = 0;
  globalThis.fetch = async (path, init) => {
    if (path.endsWith("/csrf"))
      return Response.json({ data: { csrf_token: "signed" } });
    writes++;
    assert.equal(init.headers["X-CSRF-Token"], "signed");
    throw new Error("lost after commit");
  };
  try {
    await assert.rejects(createReview("1", 5, "Good"));
    assert.equal(writes, 1);
    await assert.rejects(createReview("1", 6, "bad"));
    assert.equal(writes, 1);
    globalThis.fetch = async () =>
      Response.json({
        data: {
          review_id: "9007199254740993",
          rating: 5,
          comment: "Good",
          created_at: "2026-11-15T00:00:00Z",
        },
      });
    assert.equal((await myReview("1")).review_id, "9007199254740993");
    globalThis.fetch = async () => Response.json({ data: null });
    assert.equal(await myReview("1"), null);
  } finally {
    globalThis.fetch = old;
  }
});
test("coupon errors and invalid review responses remain visible", async () => {
  const old = globalThis.fetch;
  try {
    globalThis.fetch = async (path) =>
      path.endsWith("/csrf")
        ? Response.json({ data: { csrf_token: "signed" } })
        : Response.json(
            { error: { code: "COUPON_CUSTOMER_LIMIT" } },
            { status: 409 },
          );
    await assert.rejects(quoteCoupon("CODE"), /hết lượt/);
    globalThis.fetch = async () =>
      Response.json({
        items: [{ rating: 9 }],
        total: 1,
        page: 1,
        page_size: 10,
        average_rating: "9",
      });
    await assert.rejects(productReviews("1", 1));
  } finally {
    globalThis.fetch = old;
  }
});
