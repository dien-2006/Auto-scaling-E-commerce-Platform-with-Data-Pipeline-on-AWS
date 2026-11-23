import { test } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import ts from "typescript";
async function load(name) {
  const { outputText } = ts.transpileModule(await readFile(new URL(`../src/lib/${name}.ts`, import.meta.url), "utf8"), { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 } });
  return import(`data:text/javascript;base64,${Buffer.from(outputText).toString("base64")}`);
}
const { inventoryFrom, adjustInventory, readInventory } = await load("inventory-client");
const { safeReturnPath } = await load("auth-contract");
const { proxyInventory } = await load("auth-proxy");
const row = (quantity = 10) => ({ product_id: "9007199254740993", quantity, updated_at: "2026-11-10T00:00:00Z" });
test("normal login returns home; explicit account, seller and cart destinations survive", () => {
  for (const v of [undefined, null, [], ["/tai-khoan"], "", "//hostile.invalid"]) assert.equal(safeReturnPath(v), "/");
  for (const v of ["/tai-khoan", "/kenh-nguoi-ban/san-pham", "/gio-hang"]) assert.equal(safeReturnPath(v), v);
});
test("inventory validates identity and bounded integer stock while stripping private fields", () => {
  assert.deepEqual(inventoryFrom({ ...row(), owner: "private" }, row().product_id), row());
  for (const quantity of [-1, 1.5, true, "1", 2147483648]) assert.equal(inventoryFrom(row(quantity), row().product_id), null);
  assert.equal(inventoryFrom(row(), "1"), null);
});
test("adjustment sends delta and expected quantity; ambiguous responses never cause retries", async () => {
  const original = globalThis.fetch, calls = [], signal = new AbortController().signal;
  try {
    globalThis.fetch = async (url, init) => { calls.push({ url, init }); return Response.json(url.endsWith("csrf") ? { data: { csrf_token: "token" } } : { data: row(12) }); };
    assert.equal((await adjustInventory(row().product_id, 10, 2, signal)).quantity, 12);
    assert.equal(calls[1].init.headers["X-Expected-Quantity"], "10");
    assert.deepEqual(JSON.parse(calls[1].init.body), { delta: 2 });
    assert.equal(calls[1].init.credentials, "same-origin");
    calls.length = 0;
    globalThis.fetch = async (url) => { calls.push(url); if (url.endsWith("csrf")) return Response.json({ data: { csrf_token: "token" } }); throw Error("lost response after commit"); };
    await assert.rejects(adjustInventory(row().product_id, 10, 2, signal), { code: "UNAVAILABLE" });
    assert.equal(calls.length, 2);
    calls.length = 0;
    await assert.rejects(adjustInventory(row().product_id, 0, -1, signal), { code: "VALIDATION_ERROR" });
    await assert.rejects(readInventory("../auth/me", signal), { code: "NOT_FOUND" });
    assert.equal(calls.length, 0);
  } finally { globalThis.fetch = original; }
});
test("inventory proxy confines target, precondition, method, query and CSRF", async () => {
  const original = globalThis.fetch, saved = { ...process.env }, calls = [];
  process.env.MARKETPLACE_PUBLIC_ORIGIN = "http://localhost";
  process.env.INTERNAL_API_URL = "http://backend:8000";
  try {
    globalThis.fetch = async (url, init) => { calls.push({ url: String(url), init }); return Response.json({ data: row() }); };
    const headers = { Origin: "http://localhost", "Content-Type": "application/json", "X-CSRF-Token": "token", Cookie: "marketplace_access=jwt; unrelated=secret", "X-Expected-Quantity": "10" };
    const request = (extra = {}, query = "") => new Request("http://localhost/api/v1/seller/products/1/inventory/adjustments" + query, { method: "POST", headers: { ...headers, ...extra }, body: '{"delta":2}' });
    assert.equal((await proxyInventory(request(), "1", true)).status, 200);
    assert.equal(calls[0].url, "http://backend:8000/api/v1/seller/products/1/inventory/adjustments");
    assert.equal(calls[0].init.headers.get("X-Expected-Quantity"), "10");
    assert.equal(calls[0].init.headers.get("Cookie"), "marketplace_access=jwt");
    for (const value of ["", "-1", "01", "2147483648", "10,10"]) assert.equal((await proxyInventory(request({ "X-Expected-Quantity": value }), "1", true)).status, 400);
    assert.equal((await proxyInventory(request({ Origin: "https://hostile.invalid" }), "1", true)).status, 403);
    assert.equal((await proxyInventory(request({}, "?other=1"), "1", true)).status, 400);
    assert.equal((await proxyInventory(request(), "../auth/me", true)).status, 404);
    assert.equal(calls.length, 1);
  } finally { globalThis.fetch = original; for (const key of ["MARKETPLACE_PUBLIC_ORIGIN", "INTERNAL_API_URL"]) { if (saved[key] === undefined) delete process.env[key]; else process.env[key] = saved[key]; } }
});
