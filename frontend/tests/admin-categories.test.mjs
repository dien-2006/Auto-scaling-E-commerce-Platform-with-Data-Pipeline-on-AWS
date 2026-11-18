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
const { categoryTreeFrom, blockedParents, fetchAdminCategories, saveCategory } =
  await load("admin-categories-client");
const { proxyAdminCategories } = await load("auth-proxy");
const { safeReturnPath } = await load("auth-contract");
const node = (
  id = "9007199254740993",
  parent = null,
  active = true,
  children = [],
) => ({
  category_id: id,
  parent_category_id: parent,
  category_name: "Danh mục " + id,
  category_slug: "category-" + id,
  is_active: active,
  children,
});
test("Category tree preserves BIGINT/parent identity, computes inherited visibility and rejects duplicates/corruption", () => {
  const root = node(),
    child = node("2", root.category_id);
  root.is_active = false;
  root.children = [child];
  const rows = categoryTreeFrom({ items: [root] });
  assert.equal(rows.length, 2);
  assert.equal(rows[1].is_active, true);
  assert.equal(rows[1].effective_active, false);
  assert.equal(rows[1].depth, 1);
  root.is_active = true;
  assert.equal(categoryTreeFrom({ items: [root] })[1].effective_active, true);
  assert.equal(categoryTreeFrom({ items: [node(), node()] }), null);
  assert.equal(categoryTreeFrom({ items: [node("1", "2")] }), null);
  assert.equal(categoryTreeFrom({ items: [node("1", null, "true")] }), null);
  assert.equal(
    categoryTreeFrom({ items: [node("1", null, true, [node("2", "9")])] }),
    null,
  );
  const clean = categoryTreeFrom({
    items: [{ ...node(), password_hash: "secret" }],
  });
  assert.equal("password_hash" in clean[0], false);
  assert.equal(safeReturnPath("/admin/categories"), "/admin/categories");
  assert.equal(safeReturnPath("/admin/categories/1"), "/");
});
test("Parent choices exclude self and every descendant; the tree depth limit matches the public client", () => {
  const tree = node("1", null, true, [node("2", "1", true, [node("3", "2")])]);
  const rows = categoryTreeFrom({ items: [tree, node("4")] });
  assert.deepEqual([...blockedParents(rows, "1")].sort(), ["1", "2", "3"]);
  assert.deepEqual([...blockedParents(rows, "2")].sort(), ["2", "3"]);
  let root = node("100", "99");
  for (let i = 99; i >= 1; i--)
    root = node(String(i), i === 1 ? null : String(i - 1), true, [root]);
  assert.equal(categoryTreeFrom({ items: [root] }).length, 100);
  let leaf = root;
  while (leaf.children.length) leaf = leaf.children[0];
  leaf.children.push(node("101", "100"));
  assert.equal(categoryTreeFrom({ items: [root] }), null);
});
test("Category client sends allowlisted fields, projects tree errors and never retries a lost mutation", async () => {
  const original = globalThis.fetch,
    signal = new AbortController().signal,
    calls = [],
    input = {
      category_name: "Danh mục",
      category_slug: "danh-muc",
      parent_category_id: null,
      is_active: false,
    };
  try {
    globalThis.fetch = async (url, init) => {
      calls.push({ url, init });
      return Response.json(
        url.endsWith("csrf")
          ? { data: { csrf_token: "token" } }
          : { data: { ...input, category_id: "1", children: [] } },
      );
    };
    assert.equal(
      await saveCategory({ ...input, user_role: "ADMIN" }, null, signal),
      "1",
    );
    assert.deepEqual(JSON.parse(calls[1].init.body), input);
    assert.equal(calls[1].init.method, "POST");
    calls.length = 0;
    globalThis.fetch = async (url) => {
      calls.push(url);
      if (url.endsWith("csrf"))
        return Response.json({ data: { csrf_token: "token" } });
      throw Error("response lost after COMMIT");
    };
    await assert.rejects(saveCategory(input, "1", signal), {
      code: "UNAVAILABLE",
    });
    assert.equal(calls.length, 2);
    globalThis.fetch = async () => Response.json({ items: [node("1", "1")] });
    await assert.rejects(fetchAdminCategories(signal), { code: "UNAVAILABLE" });
    calls.length = 0;
    await assert.rejects(saveCategory(input, "../users", signal), {
      code: "VALIDATION_ERROR",
    });
    assert.equal(calls.length, 0);
  } finally {
    globalThis.fetch = original;
  }
});
test("Category proxy limits methods/IDs/query and applies Origin/CSRF/body/cookie rules", async () => {
  const original = globalThis.fetch,
    oldOrigin = process.env.MARKETPLACE_PUBLIC_ORIGIN,
    oldApi = process.env.INTERNAL_API_URL,
    calls = [];
  process.env.MARKETPLACE_PUBLIC_ORIGIN = "http://localhost";
  process.env.INTERNAL_API_URL = "http://backend:8000";
  try {
    globalThis.fetch = async (url, init) => {
      calls.push({ url: String(url), init });
      return Response.json({ data: node() });
    };
    assert.equal(
      (await proxyAdminCategories(new Request("http://localhost/api"))).status,
      200,
    );
    const headers = {
      Origin: "http://localhost",
      "X-CSRF-Token": "token",
      "Content-Type": "application/json",
      Cookie: "marketplace_access=jwt; unrelated=secret",
    };
    assert.equal(
      (
        await proxyAdminCategories(
          new Request("http://localhost/api", {
            method: "POST",
            headers,
            body: "{}",
          }),
        )
      ).status,
      200,
    );
    assert.equal(calls[1].url, "http://backend:8000/api/v1/admin/categories");
    assert.equal(
      (
        await proxyAdminCategories(
          new Request("http://localhost/api", {
            method: "PATCH",
            headers,
            body: "{}",
          }),
          "1",
        )
      ).status,
      200,
    );
    assert.equal(calls[2].url, "http://backend:8000/api/v1/admin/categories/1");
    assert.equal(calls[2].init.headers.get("Cookie"), "marketplace_access=jwt");
    assert.equal(
      (await proxyAdminCategories(new Request("http://localhost/api?extra=1")))
        .status,
      400,
    );
    assert.equal(
      (
        await proxyAdminCategories(
          new Request("http://localhost/api", { method: "POST" }),
        )
      ).status,
      403,
    );
    assert.equal(
      (
        await proxyAdminCategories(
          new Request("http://localhost/api", { method: "DELETE" }),
          "1",
        )
      ).status,
      405,
    );
    assert.equal(
      (
        await proxyAdminCategories(
          new Request("http://localhost/api", { method: "PATCH", headers }),
          "../users",
        )
      ).status,
      404,
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
