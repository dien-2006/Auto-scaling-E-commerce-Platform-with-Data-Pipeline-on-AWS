import { test } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import ts from "typescript";

const source = await readFile(
  new URL("../src/lib/catalog-query.ts", import.meta.url),
  "utf8",
);
const { outputText } = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.ESNext,
    target: ts.ScriptTarget.ES2022,
  },
});
const {
  parseCatalogQuery,
  catalogHref,
  paginationPages,
  defaultCatalogFilters,
} = await import(
  `data:text/javascript;base64,${Buffer.from(outputText).toString("base64")}`
);

test("default and encoded query URL round-trip without losing filters", () => {
  assert.deepEqual(parseCatalogQuery({}), {
    valid: true,
    filters: defaultCatalogFilters,
  });
  const parsed = parseCatalogQuery({
    q: " serum & 100%_ ",
    "danh-muc": "nuoc-hoa",
    sort: "price_desc",
    page: "3",
    page_size: "48",
  });
  assert.equal(parsed.valid, true);
  const url = new URL(catalogHref(parsed.filters), "http://localhost");
  assert.equal(url.searchParams.get("q"), "serum & 100%_");
  assert.deepEqual(
    parseCatalogQuery(Object.fromEntries(url.searchParams)),
    parsed,
  );
});
test("filter/search/sort/size changes reset page while pagination preserves intent", () => {
  const initial = {
    ...defaultCatalogFilters,
    q: "serum",
    category: "nuoc-hoa",
    page: 9,
  };
  for (const changes of [
    { q: "cream" },
    { category: "trang-diem" },
    { sort: "price_asc" },
    { pageSize: 12 },
  ]) {
    const url = new URL(catalogHref(initial, changes), "http://localhost");
    assert.equal(url.searchParams.has("page"), false);
  }
  const url = new URL(catalogHref(initial, { page: 10 }), "http://localhost");
  assert.equal(url.searchParams.get("page"), "10");
  assert.equal(url.searchParams.get("q"), "serum");
  assert.equal(url.searchParams.get("danh-muc"), "nuoc-hoa");
});
test("invalid and duplicate URL parameters never silently become an unfiltered query", () => {
  for (const input of [
    { page: "0" },
    { page: "-1" },
    { page: "1.5" },
    { page: "1e3" },
    { page: "2147483648" },
    { page_size: "100" },
    { sort: "name" },
    { q: ["a", "b"] },
    { sort: ["newest"] },
    { "danh-muc": "../../private" },
    { q: "x".repeat(201) },
  ])
    assert.equal(parseCatalogQuery(input).valid, false, JSON.stringify(input));
  assert.equal(
    parseCatalogQuery({
      page: "2147483647",
      q: "x".repeat(200),
      page_size: "48",
    }).valid,
    true,
  );
});
test("pagination stays bounded even with very large totals and past-end pages", () => {
  assert.deepEqual(paginationPages(1, 4), [1, 2, 4]);
  assert.deepEqual(paginationPages(5, 1000000), [1, 4, 5, 6, 1000000]);
  assert.deepEqual(paginationPages(10, 3), [1, 3]);
  assert.deepEqual(paginationPages(1, 0), []);
});

test("shop sort/pagination stay inside the same shop URL and keep filters", () => {
  const filters = {
    ...defaultCatalogFilters,
    q: "serum",
    category: "nuoc-hoa",
    page: 4,
  };
  const url = new URL(
    catalogHref(filters, { sort: "price_asc" }, "/gian-hang/my-shop"),
    "http://localhost",
  );
  assert.equal(url.pathname, "/gian-hang/my-shop");
  assert.equal(url.searchParams.get("q"), "serum");
  assert.equal(url.searchParams.get("danh-muc"), "nuoc-hoa");
  assert.equal(url.searchParams.has("page"), false);
  assert.equal(
    new URL(
      catalogHref(filters, { page: 5 }, "/gian-hang/my-shop"),
      "http://localhost",
    ).searchParams.get("page"),
    "5",
  );
});
