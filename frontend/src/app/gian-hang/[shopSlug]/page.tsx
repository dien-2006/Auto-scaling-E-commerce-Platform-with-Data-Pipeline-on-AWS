import type { Metadata } from "next";
import Link from "next/link";
import { cache, Suspense } from "react";
import { notFound } from "next/navigation";
import { getPublicShop } from "@/lib/catalog-api";
import { catalogHref, parseCatalogQuery } from "@/lib/catalog-query";
import { CatalogBrowser } from "@/components/catalog-browser";
import { CatalogSkeleton } from "@/components/home/catalog-feedback";
import { ResourceFailure } from "@/components/resource-failure";
import { ShopAvatar } from "@/components/shop-avatar";

export const dynamic = "force-dynamic";
const loadShop = cache(getPublicShop);
export async function generateMetadata({
  params,
}: {
  params: Promise<{ shopSlug: string }>;
}): Promise<Metadata> {
  const { shopSlug } = await params;
  const result = await loadShop(shopSlug);
  return {
    title: result.ok
      ? result.data.shop_name
      : result.notFound
        ? "Không tìm thấy gian hàng"
        : "Gian hàng",
  };
}
export default async function ShopPage({
  params,
  searchParams,
}: {
  params: Promise<{ shopSlug: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { shopSlug } = await params;
  const result = await loadShop(shopSlug);
  if (!result.ok) {
    if (result.notFound) notFound();
    return <ResourceFailure kind="gian hàng" />;
  }
  const shop = result.data;
  const { filters, valid } = parseCatalogQuery(await searchParams);
  const basePath = `/gian-hang/${encodeURIComponent(shop.shop_slug)}`;
  return (
    <div className="shell py-7 sm:py-10">
      <nav aria-label="Đường dẫn" className="resource-breadcrumb">
        <Link href="/">Trang chủ</Link>
        <span>/</span>
        <Link href="/san-pham">Sản phẩm</Link>
        <span>/</span>
        <span>{shop.shop_name}</span>
      </nav>
      <section className="shop-profile">
        <ShopAvatar
          key={shop.shop_id}
          src={shop.logo_url}
          name={shop.shop_name}
        />
        <div>
          <p className="eyebrow">GIAN HÀNG TRÊN COCO</p>
          <h1>{shop.shop_name}</h1>
          <p className="shop-description">
            {shop.description?.trim() ||
              "Gian hàng chưa cung cấp thông tin giới thiệu."}
          </p>
        </div>
      </section>
      <Suspense
        key={`${catalogHref(filters, {}, basePath)}:${valid}`}
        fallback={<CatalogSkeleton />}
      >
        <CatalogBrowser
          filters={filters}
          valid={valid}
          shopId={shop.shop_id}
          basePath={basePath}
        />
      </Suspense>
    </div>
  );
}
