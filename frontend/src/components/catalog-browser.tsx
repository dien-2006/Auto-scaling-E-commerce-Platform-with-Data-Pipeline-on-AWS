import Link from "next/link";
import { getCategories, getProductPage } from "@/lib/catalog-api";
import { matchBeautyCategories } from "@/lib/categories";
import {
  catalogHref as buildCatalogHref,
  paginationPages,
  type CatalogFilters,
} from "@/lib/catalog-query";
import { CatalogFailure } from "@/components/home/catalog-feedback";
import { LiveProductCard } from "@/components/home/live-product-card";
import { CatalogSortBar } from "@/components/catalog-sort-bar";
import { CatalogExtraFilters } from "@/components/catalog-extra-filters";

export async function CatalogBrowser({
  filters,
  valid,
  shopId,
  basePath = "/san-pham",
}: {
  filters: CatalogFilters;
  valid: boolean;
  shopId?: string;
  basePath?: string;
}) {
  const catalogHref = (
    current: CatalogFilters,
    changes: Partial<CatalogFilters> = {},
  ) => buildCatalogHref(current, changes, basePath);
  const categories = valid
    ? await getCategories()
    : { ok: true as const, data: [] };
  if (!categories.ok) return <CatalogFailure />;
  const mapped = matchBeautyCategories(categories.data);
  const selected = mapped.find((item) => item.slug === filters.category);
  const unavailable = Boolean(filters.category && !selected?.actual);
  const result =
    valid && !unavailable
      ? await getProductPage({
          categoryId: selected?.actual?.category_id,
          shopId,
          query: filters.q,
          page: filters.page,
          pageSize: filters.pageSize,
          sort: filters.sort,
        })
      : null;
  const pages = result?.ok
    ? Math.ceil(result.data.total / filters.pageSize)
    : 0;
  const items = result?.ok ? result.data.items : [];
  return (
    <div className="catalog-layout">
      <aside className="catalog-sidebar" aria-label="Bộ lọc sản phẩm">
        <h2 className="catalog-filter-title">
          <svg
            width="17"
            height="17"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            aria-hidden="true"
          >
            <path d="M3 4h18l-7 8v7l-4 2v-9L3 4Z" />
          </svg>
          Bộ lọc tìm kiếm
        </h2>
        <h3 className="catalog-filter-subtitle">Danh mục sản phẩm</h3>
        <nav aria-label="Lọc danh mục">
          <Link
            href={catalogHref(filters, { category: "" })}
            className={`filter-link ${!filters.category ? "selected" : ""}`}
            aria-current={!filters.category ? "page" : undefined}
          >
            Tất cả sản phẩm
          </Link>
          {mapped.map((item) => (
            <Link
              key={item.key}
              href={catalogHref(filters, { category: item.slug })}
              aria-current={filters.category === item.slug ? "page" : undefined}
              className={`filter-link ${filters.category === item.slug ? "selected" : ""}`}
            >
              {item.name}
            </Link>
          ))}
        </nav>
        <form action={basePath} method="get" className="catalog-filter-form">
          <label htmlFor="catalog-q">Tìm theo tên sản phẩm</label>
          <input
            id="catalog-q"
            type="search"
            name="q"
            maxLength={200}
            defaultValue={filters.q}
            placeholder="Ví dụ: serum dưỡng ẩm"
            key={filters.q}
          />
          {filters.category && (
            <input type="hidden" name="danh-muc" value={filters.category} />
          )}
          <input type="hidden" name="sort" value={filters.sort} />
          <label htmlFor="catalog-page-size">Sản phẩm mỗi trang</label>
          <select
            id="catalog-page-size"
            name="page_size"
            defaultValue={filters.pageSize}
            key={filters.pageSize}
          >
            <option value="12">12 sản phẩm</option>
            <option value="24">24 sản phẩm</option>
            <option value="48">48 sản phẩm</option>
          </select>
          <button type="submit" className="primary-button">
            Áp dụng bộ lọc ↗
          </button>
          <Link
            href={basePath}
            className="text-center text-xs text-brand underline"
          >
            Xóa tất cả bộ lọc
          </Link>
        </form>
        <CatalogExtraFilters />
      </aside>
      <section aria-label="Kết quả sản phẩm" className="min-w-0">
        <div className="catalog-results-bar">
          <div>
            <h2>
              {selected?.name ??
                (filters.category
                  ? "Danh mục không tồn tại"
                  : "Tất cả sản phẩm")}
            </h2>
            {filters.q && <p>Kết quả cho “{filters.q}”</p>}
          </div>
          {result?.ok && (
            <p role="status">
              {new Intl.NumberFormat("vi-VN").format(result.data.total)} sản
              phẩm · Trang {filters.page}
              {pages > 0 && ` / ${pages}`}
            </p>
          )}
        </div>
        <CatalogSortBar filters={filters} basePath={basePath} />
        {!valid ? (
          <div role="alert" className="catalog-message">
            <h3 className="text-lg font-semibold">Bộ lọc không hợp lệ</h3>
            <p className="mt-3 text-sm text-muted">
              Vui lòng chọn cách sắp xếp, số trang hoặc từ khóa hợp lệ rồi thử
              lại.
            </p>
            <Link className="primary-button mt-5" href={basePath}>
              Đặt lại bộ lọc
            </Link>
          </div>
        ) : unavailable ? (
          <div className="catalog-message">
            <h3 className="text-lg font-semibold">Danh mục chưa có sẵn</h3>
            <p className="mt-3 text-sm text-muted">
              Bạn có thể chọn một danh mục khác hoặc xem tất cả sản phẩm.
            </p>
            <Link href={basePath} className="primary-button mt-5">
              Xem tất cả sản phẩm ↗
            </Link>
          </div>
        ) : result && !result.ok ? (
          <CatalogFailure />
        ) : items.length ? (
          <div className="grid grid-cols-2 gap-3 sm:gap-5 xl:grid-cols-3">
            {items.map((product) => (
              <LiveProductCard key={product.product_id} product={product} />
            ))}
          </div>
        ) : (
          <div className="catalog-message">
            <span className="text-4xl text-brand" aria-hidden="true">
              ⌕
            </span>
            <h3 className="mt-4 text-xl font-semibold">
              {result?.ok && result.data.total > 0
                ? "Trang này chưa có sản phẩm"
                : "Chưa tìm thấy sản phẩm phù hợp"}
            </h3>
            <p className="mt-3 text-sm leading-7 text-muted">
              {filters.page > 1
                ? "Hãy quay về trang đầu hoặc thay đổi bộ lọc để tiếp tục khám phá."
                : "Thử từ khóa khác hoặc quay lại khi các gian hàng cập nhật sản phẩm."}
            </p>
            <Link
              href={
                filters.page > 1 ? catalogHref(filters, { page: 1 }) : basePath
              }
              className="primary-button mt-5"
            >
              {filters.page > 1 ? "Về trang đầu" : "Xem tất cả sản phẩm"} ↗
            </Link>
          </div>
        )}
        {result?.ok && pages > 1 && (
          <nav aria-label="Phân trang sản phẩm" className="catalog-pagination">
            {filters.page > 1 && (
              <Link
                href={catalogHref(filters, {
                  page: Math.min(filters.page - 1, pages),
                })}
                aria-label="Trang trước"
              >
                ←
              </Link>
            )}
            {paginationPages(filters.page, pages).map(
              (page, index, numbers) => (
                <span key={page} className="inline-flex items-center gap-2">
                  {index > 0 && page - numbers[index - 1] > 1 && (
                    <span aria-hidden="true">…</span>
                  )}
                  <Link
                    href={catalogHref(filters, { page })}
                    aria-current={page === filters.page ? "page" : undefined}
                    aria-label={`Trang ${page}`}
                  >
                    {page}
                  </Link>
                </span>
              ),
            )}
            {filters.page < pages && (
              <Link
                href={catalogHref(filters, { page: filters.page + 1 })}
                aria-label="Trang sau"
              >
                →
              </Link>
            )}
          </nav>
        )}
      </section>
    </div>
  );
}
