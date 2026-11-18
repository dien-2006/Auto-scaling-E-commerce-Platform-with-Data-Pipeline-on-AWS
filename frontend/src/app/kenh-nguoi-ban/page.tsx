import type { Metadata } from "next";
import { ShopDashboard } from "@/components/seller/shop-dashboard";
export const metadata: Metadata = {
  title: "Kênh người bán",
  robots: { index: false },
};
export const dynamic = "force-dynamic";
export default function Page() {
  return <ShopDashboard />;
}
