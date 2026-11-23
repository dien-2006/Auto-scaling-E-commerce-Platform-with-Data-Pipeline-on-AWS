import { SellerOrders } from "@/components/seller/seller-orders";
export const dynamic = "force-dynamic";
export const metadata = { title: "Đơn hàng của gian hàng" };
export default function Page() {
  return <SellerOrders />;
}
