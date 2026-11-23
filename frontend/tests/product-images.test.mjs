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
const { imagesFrom, readImages, uploadImage, updateImage } = await load(
  "product-images-client",
);
const { proxyProductImages } = await load("auth-proxy");
const signal = new AbortController().signal;
const image = () => ({
  product_image_id: "9007199254740993",
  product_id: "2",
  url: "https://images.invalid/test.png?sig=temp",
  is_primary: true,
  sort_order: 0,
  image_key: "private/key",
});
test("image projection preserves IDs and rejects duplicate/unsafe/ambiguous images", () => {
  assert.equal(imagesFrom([image()])[0].image_key, undefined);
  assert.equal(imagesFrom([image()])[0].product_image_id, "9007199254740993");
  for (const changes of [
    { url: "http://images.invalid/test.png" },
    { url: "https://user:secret@images.invalid/test.png" },
    { sort_order: -1 },
    { is_primary: "true" },
    { product_image_id: "9223372036854775808" },
  ])
    assert.equal(imagesFrom([{ ...image(), ...changes }]), null);
  assert.equal(imagesFrom([image(), image()]), null);
  assert.equal(
    imagesFrom([image(), { ...image(), product_image_id: "2" }]),
    null,
  );
});
test("image proxy confines resource/method/query and requires Origin plus CSRF", async () => {
  const oldFetch = globalThis.fetch,
    oldApi = process.env.INTERNAL_API_URL,
    oldOrigin = process.env.MARKETPLACE_PUBLIC_ORIGIN;
  process.env.INTERNAL_API_URL = "http://backend:8000";
  process.env.MARKETPLACE_PUBLIC_ORIGIN = "http://localhost";
  const calls = [];
  globalThis.fetch = async (url, init) => {
    calls.push({ url: String(url), init });
    return Response.json({ data: image() });
  };
  try {
    const req = (method, headers = {}, query = "") =>
      new Request("http://localhost/api/v1/seller/products/2/images" + query, {
        method,
        headers,
      });
    assert.equal(
      (await proxyProductImages(req("POST"), "2", "../../auth/me")).status,
      404,
    );
    assert.equal(
      (await proxyProductImages(req("GET"), "2", "upload-url")).status,
      405,
    );
    assert.equal(
      (await proxyProductImages(req("POST"), "2", "upload-url")).status,
      403,
    );
    assert.equal(
      (await proxyProductImages(req("DELETE"), "2", "3")).status,
      403,
    );
    assert.equal(
      (await proxyProductImages(req("POST", {}, "?owner=1"), "2")).status,
      400,
    );
    assert.equal(calls.length, 0);
    const response = await proxyProductImages(
      req("DELETE", {
        Origin: "http://localhost",
        "X-CSRF-Token": "test",
        Cookie: "marketplace_access=session;unrelated=private",
      }),
      "2",
      "3",
    );
    assert.equal(response.status, 200);
    assert.equal(
      calls[0].url,
      "http://backend:8000/api/v1/seller/products/2/images/3",
    );
    assert.equal(
      calls[0].init.headers.get("Cookie"),
      "marketplace_access=session",
    );
  } finally {
    globalThis.fetch = oldFetch;
    if (oldApi === undefined) delete process.env.INTERNAL_API_URL;
    else process.env.INTERNAL_API_URL = oldApi;
    if (oldOrigin === undefined) delete process.env.MARKETPLACE_PUBLIC_ORIGIN;
    else process.env.MARKETPLACE_PUBLIC_ORIGIN = oldOrigin;
  }
});
test("direct S3 upload omits auth credentials; finalization uses CSRF and validated response", async () => {
  const old = globalThis.fetch,
    calls = [];
  const key = "uploads/1/2/" + "a".repeat(32) + ".png";
  globalThis.fetch = async (path, init) => {
    calls.push({ path, init });
    if (path.endsWith("/csrf"))
      return Response.json({ data: { csrf_token: "test" } });
    if (path.endsWith("/upload-url"))
      return Response.json({
        upload_url: "https://storage.invalid/upload",
        fields: { key, policy: "signed" },
        image_key: key,
        expires_at: new Date(Date.now() + 300000).toISOString(),
      });
    if (path.startsWith("https://")) {
      assert.equal(init.credentials, "omit");
      assert.equal(init.referrerPolicy, "no-referrer");
      assert.equal(init.headers, undefined);
      assert.equal(init.body.get("file").name, "photo.png");
      return new Response(null, { status: 204 });
    }
    assert.equal(init.headers["X-CSRF-Token"], "test");
    assert.equal(JSON.parse(init.body).image_key, key);
    return Response.json({ data: image() }, { status: 201 });
  };
  try {
    await uploadImage(
      "2",
      new File(["pngbytes"], "photo.png", { type: "image/png" }),
      true,
      signal,
    );
    assert.equal(
      calls.filter((c) => c.path === "/api/v1/seller/products/2/images").length,
      1,
    );
  } finally {
    globalThis.fetch = old;
  }
});
test("failed writes never automatically repeat; missing storage and bad file are visible errors", async () => {
  const old = globalThis.fetch;
  let writes = 0;
  globalThis.fetch = async (path) => {
    if (path.endsWith("/csrf"))
      return Response.json({ data: { csrf_token: "test" } });
    writes++;
    return Response.json(
      { error: { code: "STORAGE_NOT_CONFIGURED" } },
      { status: 503 },
    );
  };
  try {
    await assert.rejects(
      uploadImage(
        "2",
        new File(["svg"], "x.svg", { type: "image/svg+xml" }),
        false,
        signal,
      ),
      /hợp lệ/,
    );
    assert.equal(writes, 0);
    await assert.rejects(
      uploadImage(
        "2",
        new File(["png"], "x.png", { type: "image/png" }),
        false,
        signal,
      ),
      /Chưa cấu hình/,
    );
    assert.equal(writes, 1);
    globalThis.fetch = async (path) =>
      path.endsWith("/csrf")
        ? Response.json({ data: { csrf_token: "test" } })
        : (writes++, Promise.reject(new Error("lost after COMMIT")));
    await assert.rejects(updateImage("2", "3", signal, { is_primary: true }));
    assert.equal(writes, 2);
    globalThis.fetch = async () =>
      Response.json({
        data: { product_id: "2", shop: { shop_id: "other" }, images: [] },
      });
    await assert.rejects(readImages("2", "1", signal));
  } finally {
    globalThis.fetch = old;
  }
});
