import { test } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import ts from "typescript";
const { outputText } = ts.transpileModule(
  await readFile(new URL("../src/lib/auth-proxy.ts", import.meta.url), "utf8"),
  {
    compilerOptions: {
      module: ts.ModuleKind.ESNext,
      target: ts.ScriptTarget.ES2022,
    },
  },
);
const { proxyAuth } = await import(
  `data:text/javascript;base64,${Buffer.from(outputText).toString("base64")}`
);
test("login proxy accepts explicit localhost alias and canonical LAN, preserves Origin and still enforces CSRF", async () => {
  const original = globalThis.fetch,
    previous = { ...process.env };
  process.env.INTERNAL_API_URL = "http://backend:8000";
  process.env.MARKETPLACE_PUBLIC_ORIGIN = "http://192.168.110.101:3001";
  process.env.MARKETPLACE_ADDITIONAL_ORIGINS = '["http://localhost:3001"]';
  const calls = [];
  globalThis.fetch = async (url, init) => {
    calls.push({ url: String(url), init });
    return Response.json(
      { error: { code: "VALIDATION_ERROR" } },
      { status: 422 },
    );
  };
  const request = (source, csrf = "token", referer = false) =>
    new Request("http://localhost:3001/api/v1/auth/login", {
      method: "POST",
      headers: {
        ...(referer ? { Referer: source + "/dang-nhap" } : { Origin: source }),
        "X-CSRF-Token": csrf,
        "Content-Type": "application/json",
        Cookie: "marketplace_csrf=token;unrelated=secret",
      },
      body: "{}",
    });
  try {
    for (const source of [
      "http://localhost:3001",
      "http://192.168.110.101:3001",
    ]) {
      assert.equal((await proxyAuth(request(source), "login")).status, 422);
      assert.equal(calls.at(-1).init.headers.get("Origin"), source);
      assert.equal(
        calls.at(-1).init.headers.get("Cookie"),
        "marketplace_csrf=token",
      );
      assert.equal(
        (await proxyAuth(request(source, "token", true), "login")).status,
        422,
      );
    }
    for (const source of [
      "https://evil.test",
      "http://localhost:3002",
      "http://localhost:3001.evil.test",
      "null",
    ])
      assert.equal((await proxyAuth(request(source), "login")).status, 403);
    assert.equal(
      (await proxyAuth(request("http://localhost:3001", ""), "login")).status,
      403,
    );
    assert.equal(calls.length, 4);
    for (const setting of [
      '["*"]',
      '["http://localhost:3001/path"]',
      '["http://user:pass@localhost:3001"]',
      "null",
      "{}",
      "[123]",
    ]) {
      process.env.MARKETPLACE_ADDITIONAL_ORIGINS = setting;
      assert.equal(
        (await proxyAuth(request("http://localhost:3001"), "login")).status,
        503,
      );
    }
    assert.equal(calls.length, 4);
  } finally {
    globalThis.fetch = original;
    for (const key of [
      "INTERNAL_API_URL",
      "MARKETPLACE_PUBLIC_ORIGIN",
      "MARKETPLACE_ADDITIONAL_ORIGINS",
    ]) {
      if (previous[key] === undefined) delete process.env[key];
      else process.env[key] = previous[key];
    }
  }
});
