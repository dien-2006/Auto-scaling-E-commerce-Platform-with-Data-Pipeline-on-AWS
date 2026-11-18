import { getCategories } from "@/lib/catalog-api";
import { SellerProducts } from "@/components/seller/seller-products";
export const dynamic = "force-dynamic";
export const metadata = { title: "Sản phẩm của gian hàng" };
export default async function Page() {
  const result = await getCategories();
  return <SellerProducts categories={result.ok ? result.data : null} />;
}
