export const catalogSorts = ["newest", "price_asc", "price_desc"] as const;
export type CatalogSort = (typeof catalogSorts)[number];
export type CatalogFilters = {
  q: string;
  category: string;
  sort: CatalogSort;
  page: number;
  pageSize: number;
};
export const defaultCatalogFilters: CatalogFilters = {
  q: "",
  category: "",
  sort: "newest",
  page: 1,
  pageSize: 24,
};

export function parseCatalogQuery(
  params: Record<string, string | string[] | undefined>,
): { filters: CatalogFilters; valid: boolean } {
  const filters = { ...defaultCatalogFilters };
  let valid = true;
  const read = (key: string) => {
    const value = params[key];
    if (Array.isArray(value)) {
      valid = false;
      return "";
    }
    return value ?? "";
  };
  const q = read("q").trim();
  if (q.length > 200) valid = false;
  filters.q = q.slice(0, 200);
  const category = read("danh-muc");
  if (category && !/^[a-z0-9-]{1,140}$/.test(category)) valid = false;
  filters.category = category.slice(0, 140);
  const sort = read("sort");
  if (sort && !catalogSorts.includes(sort as CatalogSort)) valid = false;
  else if (sort) filters.sort = sort as CatalogSort;
  for (const [key, field] of [
    ["page", "page"],
    ["page_size", "pageSize"],
  ] as const) {
    const value = read(key);
    if (!value) continue;
    const number = Number(value);
    if (
      !/^\d+$/.test(value) ||
      !Number.isSafeInteger(number) ||
      number < 1 ||
      (key === "page" ? number > 2147483647 : ![12, 24, 48].includes(number))
    )
      valid = false;
    else filters[field] = number;
  }
  return { filters, valid };
}

/** Changing a search/filter/sort starts at page one; explicit pagination preserves all filters. */
export function catalogHref(
  current: CatalogFilters,
  changes: Partial<CatalogFilters> = {},
  basePath = "/san-pham",
): string {
  const next = { ...current, ...changes };
  if (
    ["q", "category", "sort", "pageSize"].some((key) => key in changes) &&
    !("page" in changes)
  )
    next.page = 1;
  const params = new URLSearchParams();
  if (next.q) params.set("q", next.q);
  if (next.category) params.set("danh-muc", next.category);
  if (next.sort !== "newest") params.set("sort", next.sort);
  if (next.pageSize !== 24) params.set("page_size", String(next.pageSize));
  if (next.page !== 1) params.set("page", String(next.page));
  return `${basePath}${params.size ? `?${params}` : ""}`;
}

export function paginationPages(page: number, totalPages: number): number[] {
  return [...new Set([1, page - 1, page, page + 1, totalPages])]
    .filter((value) => value >= 1 && value <= totalPages)
    .sort((a, b) => a - b);
}
