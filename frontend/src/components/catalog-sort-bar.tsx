"use client";

import Link from "next/link";
import { useTransition } from "react";
import { useRouter } from "next/navigation";
import {
  catalogHref,
  type CatalogFilters,
  type CatalogSort,
} from "@/lib/catalog-query";

export function CatalogSortBar({
  filters,
  basePath = "/san-pham",
}: {
  filters: CatalogFilters;
  basePath?: string;
}) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  return (
    <div className="catalog-sort-wrap">
      <nav aria-label="Sắp xếp sản phẩm" className="catalog-sort-bar">
        <span className="catalog-sort-label">Sắp xếp theo</span>
        <button
          type="button"
          disabled
          aria-describedby="ranking-unavailable"
          className="sort-choice sort-unavailable"
        >
          Phổ biến <span>Sắp có</span>
        </button>
        <Link
          href={catalogHref(filters, { sort: "newest" }, basePath)}
          aria-current={filters.sort === "newest" ? "page" : undefined}
          className="sort-choice"
        >
          Mới nhất
        </Link>
        <button
          type="button"
          disabled
          aria-describedby="ranking-unavailable"
          className="sort-choice sort-unavailable"
        >
          Bán chạy <span>Sắp có</span>
        </button>
        <label className="catalog-price-sort">
          <span className="sr-only">Sắp xếp giá</span>
          <select
            aria-label="Sắp xếp giá"
            disabled={pending}
            value={filters.sort}
            onChange={(event) => {
              const sort = event.target.value as CatalogSort;
              startTransition(() =>
                router.push(catalogHref(filters, { sort }, basePath)),
              );
            }}
          >
            <option value="newest">Giá</option>
            <option value="price_asc">Giá: Thấp đến cao</option>
            <option value="price_desc">Giá: Cao đến thấp</option>
          </select>
        </label>
        {pending && (
          <span role="status" className="text-xs text-muted">
            Đang sắp xếp…
          </span>
        )}
      </nav>
      <p id="ranking-unavailable" className="sort-availability-note">
        Phổ biến và Bán chạy sẽ mở khi có dữ liệu xếp hạng.
      </p>
    </div>
  );
}
