import { Suspense } from "react";
import { HomeCatalog } from "@/components/home/home-catalog";
import { CatalogSkeleton } from "@/components/home/catalog-feedback";
import { ShoppingHighlights } from "@/components/home/shopping-highlights";
import { CampaignBanners } from "@/components/home/campaign-banners";

export const dynamic = "force-dynamic";

export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const query =
    typeof params.q === "string" ? params.q.trim().slice(0, 200) : "";
  const selected =
    typeof params["danh-muc"] === "string" ? params["danh-muc"] : "";
  return (
    <div className="shell coco-home py-4 sm:py-5">
      <CampaignBanners />
      <ShoppingHighlights />
      <Suspense key={`${selected}:${query}`} fallback={<CatalogSkeleton />}>
        <HomeCatalog query={query} selected={selected} />
      </Suspense>
    </div>
  );
}
