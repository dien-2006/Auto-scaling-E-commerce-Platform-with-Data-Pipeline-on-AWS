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
const { adminUserFrom, fetchAdminUsers, changeUserStatus } =
  await load("admin-users-client");
const { proxyAdminUsers } = await load("auth-proxy");
const { safeReturnPath } = await load("auth-contract");
const user = (status = "ACTIVE") => ({
  user_id: "9007199254740993",
  email: "test@example.com",
  full_name: "User",
  phone: null,
  user_role: "USER",
  user_status: status,
  created_at: "2026-11-11T00:00:00Z",
});
test("admin user projection preserves BIGINT, status and nullable phone while stripping credentials", () => {
  assert.deepEqual(
    adminUserFrom({ ...user(), password_hash: "secret", token: "secret" }),
    user(),
  );
  for (const row of [
    { ...user(), user_id: 9007199254740993 },
    { ...user(), user_role: "SELLER" },
    { ...user(), user_status: "PENDING" },
    { ...user(), created_at: "invalid" },
  ])
    assert.equal(adminUserFrom(row), null);
  assert.equal(safeReturnPath("/admin/users"), "/admin/users");
  assert.equal(safeReturnPath("/admin/users/../../other"), "/");
});
test("admin client validates pagination/filter/duplicates and encodes literal search", async () => {
  const original = globalThis.fetch,
    signal = new AbortController().signal,
    calls = [];
  try {
    globalThis.fetch = async (url) => {
      calls.push(url);
      return Response.json({
        items: [user()],
        page: 1,
        page_size: 24,
        total: 1,
      });
    };
    assert.equal(
      (await fetchAdminUsers(1, "a&status=LOCKED", "ACTIVE", signal)).items
        .length,
      1,
    );
    assert.match(calls[0], /q=a%26status%3DLOCKED/);
    await assert.rejects(fetchAdminUsers(2, "", "", signal), {
      code: "UNAVAILABLE",
    });
    await assert.rejects(fetchAdminUsers(1, "", "LOCKED", signal), {
      code: "UNAVAILABLE",
    });
    globalThis.fetch = async () =>
      Response.json({
        items: [user(), user()],
        page: 1,
        page_size: 24,
        total: 2,
      });
    await assert.rejects(fetchAdminUsers(1, "", "", signal), {
      code: "UNAVAILABLE",
    });
  } finally {
    globalThis.fetch = original;
  }
});
test("status client posts only status with CSRF and never retries ambiguous mutation", async () => {
  const original = globalThis.fetch,
    signal = new AbortController().signal,
    calls = [];
  try {
    globalThis.fetch = async (url, init) => {
      calls.push({ url, init });
      return Response.json(
        url.endsWith("csrf")
          ? { data: { csrf_token: "token" } }
          : { data: user("LOCKED") },
      );
    };
    assert.equal(
      (await changeUserStatus(user().user_id, "LOCKED", signal)).user_status,
      "LOCKED",
    );
    assert.deepEqual(JSON.parse(calls[1].init.body), { user_status: "LOCKED" });
    assert.equal(calls[1].init.headers["X-CSRF-Token"], "token");
    calls.length = 0;
    globalThis.fetch = async (url, init) => {
      calls.push({ url, init });
      if (url.endsWith("csrf"))
        return Response.json({ data: { csrf_token: "token" } });
      throw Error("response lost after commit");
    };
    await assert.rejects(changeUserStatus(user().user_id, "LOCKED", signal), {
      code: "UNAVAILABLE",
    });
    assert.equal(calls.length, 2);
    calls.length = 0;
    await assert.rejects(changeUserStatus("../auth/me", "LOCKED", signal), {
      code: "NOT_FOUND",
    });
    assert.equal(calls.length, 0);
  } finally {
    globalThis.fetch = original;
  }
});
test("admin proxy confines query, status route, IDs, methods, cookies and Origin/CSRF", async () => {
  const original = globalThis.fetch,
    oldOrigin = process.env.MARKETPLACE_PUBLIC_ORIGIN,
    oldApi = process.env.INTERNAL_API_URL,
    calls = [];
  process.env.MARKETPLACE_PUBLIC_ORIGIN = "http://localhost";
  process.env.INTERNAL_API_URL = "http://backend:8000";
  try {
    globalThis.fetch = async (url, init) => {
      calls.push({ url: String(url), init });
      return Response.json({ data: user() });
    };
    assert.equal(
      (
        await proxyAdminUsers(
          new Request("http://localhost/api?q=a%25&status=ACTIVE&page=1"),
        )
      ).status,
      200,
    );
    assert.equal(
      calls[0].url,
      "http://backend:8000/api/v1/admin/users?q=a%25&status=ACTIVE&page=1",
    );
    for (const query of [
      "other=1",
      "status=ADMIN",
      "status=ACTIVE&status=LOCKED",
      "page=0",
      "page_size=101",
      "q=" + "a".repeat(201),
    ])
      assert.equal(
        (await proxyAdminUsers(new Request("http://localhost/api?" + query)))
          .status,
        400,
      );
    const headers = {
      Origin: "http://localhost",
      "X-CSRF-Token": "token",
      "Content-Type": "application/json",
      Cookie: "marketplace_access=jwt; private=secret",
    };
    assert.equal(
      (
        await proxyAdminUsers(
          new Request("http://localhost/api", {
            method: "PATCH",
            headers,
            body: '{"user_status":"LOCKED"}',
          }),
          "1",
        )
      ).status,
      200,
    );
    assert.equal(
      calls[1].url,
      "http://backend:8000/api/v1/admin/users/1/status",
    );
    assert.equal(calls[1].init.headers.get("Cookie"), "marketplace_access=jwt");
    assert.equal(
      (
        await proxyAdminUsers(
          new Request("http://localhost/api", { method: "PATCH" }),
          "1",
        )
      ).status,
      403,
    );
    assert.equal(
      (
        await proxyAdminUsers(
          new Request("http://localhost/api", { method: "DELETE" }),
          "1",
        )
      ).status,
      405,
    );
    assert.equal(
      (
        await proxyAdminUsers(
          new Request("http://localhost/api", { method: "PATCH", headers }),
          "../auth/me",
        )
      ).status,
      404,
    );
    assert.equal(calls.length, 2);
  } finally {
    globalThis.fetch = original;
    if (oldOrigin === undefined) delete process.env.MARKETPLACE_PUBLIC_ORIGIN;
    else process.env.MARKETPLACE_PUBLIC_ORIGIN = oldOrigin;
    if (oldApi === undefined) delete process.env.INTERNAL_API_URL;
    else process.env.INTERNAL_API_URL = oldApi;
  }
});
