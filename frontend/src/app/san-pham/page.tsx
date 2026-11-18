import { CategoryNavigation } from "@/components/category-navigation";
import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { CatalogBrowser } from "@/components/catalog-browser";
import { CatalogSkeleton } from "@/components/home/catalog-feedback";
import { parseCatalogQuery, catalogHref } from "@/lib/catalog-query";
import { CatalogBanner } from "@/components/catalog-banner";

export const metadata: Metadata = { title: "Sản phẩm" };
export const dynamic = "force-dynamic";

export default async function ProductsPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { filters, valid } = parseCatalogQuery(await searchParams);
  return (
    <div className="shell storefront-page"><div className="storefront-sidebar"><CategoryNavigation /></div><div className="storefront-content">
      <nav aria-label="Đường dẫn" className="mb-6 text-xs text-muted">
        <Link href="/">Trang chủ</Link> / Sản phẩm
      </nav>
      <CatalogBanner />
      <Suspense
        key={`${catalogHref(filters)}:${valid}`}
        fallback={<CatalogSkeleton />}
      >
        <CatalogBrowser filters={filters} valid={valid} />
      </Suspense>
    </div></div>
  );
}
