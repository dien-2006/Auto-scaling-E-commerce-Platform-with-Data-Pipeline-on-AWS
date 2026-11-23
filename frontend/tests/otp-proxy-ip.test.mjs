import { test } from "node:test";
import assert from "node:assert/strict";
import { createHmac } from "node:crypto";
import { readFile } from "node:fs/promises";
import ts from "typescript";

const source = await readFile(new URL("../src/lib/auth-proxy.ts", import.meta.url), "utf8");
const { outputText } = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 },
});
const { proxyAuth } = await import(
  `data:text/javascript;base64,${Buffer.from(outputText).toString("base64")}`
);

test("OTP proxy signs Nginx client IP and does not relay forged browser signatures", async () => {
  const names = [
    "INTERNAL_API_URL",
    "MARKETPLACE_PUBLIC_ORIGIN",
    "MARKETPLACE_ADDITIONAL_ORIGINS",
    "MARKETPLACE_TRUST_PROXY_HEADERS",
    "MARKETPLACE_PROXY_SECRET",
    "MARKETPLACE_PROXY_MODE",
  ];
  const previous = Object.fromEntries(names.map((name) => [name, process.env[name]]));
  const previousFetch = globalThis.fetch;
  const key = "test-only-proxy-key-with-at-least-32-characters";
  Object.assign(process.env, {
    INTERNAL_API_URL: "http://backend:8000",
    MARKETPLACE_PUBLIC_ORIGIN: "https://coco.test",
    MARKETPLACE_ADDITIONAL_ORIGINS: "[]",
    MARKETPLACE_TRUST_PROXY_HEADERS: "true",
    MARKETPLACE_PROXY_SECRET: key,
    MARKETPLACE_PROXY_MODE: "nginx",
  });
  const calls = [];
  globalThis.fetch = async (url, init) => {
    calls.push(init.headers);
    return Response.json({ data: {} }, { status: 202 });
  };
  function request(address) {
    return new Request("https://coco.test/api/v1/auth/otp-request", {
      method: "POST",
      headers: {
        origin: "https://coco.test",
        "content-type": "application/json",
        "x-csrf-token": "test-csrf",
        ...(address ? { "x-real-ip": address } : {}),
        "x-forwarded-for": "203.0.113.99",
        "x-marketplace-client-ip": "203.0.113.99",
        "x-marketplace-client-signature": "forged",
      },
      body: JSON.stringify({ purpose: "REGISTER", target: "buyer@example.com" }),
    });
  }
  try {
    for (const address of ["198.51.100.1", "198.51.100.2"]) {
      assert.equal((await proxyAuth(request(address), "otp-request")).status, 202);
      const headers = calls.at(-1);
      assert.equal(headers.get("x-marketplace-client-ip"), address);
      assert.equal(
        headers.get("x-marketplace-client-signature"),
        createHmac("sha256", key).update(`otp-ip-v1:${address}`).digest("hex"),
      );
    }
    const count = calls.length;
    assert.equal((await proxyAuth(request(), "otp-request")).status, 503);
    assert.equal(calls.length, count);
    process.env.MARKETPLACE_PROXY_MODE = "alb";
    assert.equal((await proxyAuth(request("198.51.100.1"), "otp-request")).status, 202);
    assert.equal(calls.at(-1).get("x-marketplace-client-ip"), "203.0.113.99");
    const appended = request("198.51.100.1");
    appended.headers.set("x-forwarded-for", "192.0.2.77, 198.51.100.55");
    assert.equal((await proxyAuth(appended, "otp-request")).status, 202);
    assert.equal(calls.at(-1).get("x-marketplace-client-ip"), "198.51.100.55");
    const invalid = request("198.51.100.1");
    invalid.headers.set("x-forwarded-for", "198.51.100.55, invalid");
    assert.equal((await proxyAuth(invalid, "otp-request")).status, 503);
    const missing = request("198.51.100.1");
    missing.headers.delete("x-forwarded-for");
    assert.equal((await proxyAuth(missing, "otp-request")).status, 503);
    process.env.MARKETPLACE_TRUST_PROXY_HEADERS = "false";
    assert.equal((await proxyAuth(request("198.51.100.1"), "otp-request")).status, 202);
    assert.equal(calls.at(-1).get("x-marketplace-client-ip"), null);
    assert.equal(calls.at(-1).get("x-marketplace-client-signature"), null);
  } finally {
    globalThis.fetch = previousFetch;
    for (const name of names) {
      if (previous[name] === undefined) delete process.env[name];
      else process.env[name] = previous[name];
    }
  }
});
