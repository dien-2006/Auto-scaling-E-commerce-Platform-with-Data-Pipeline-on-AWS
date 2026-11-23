import type { Metadata } from "next";
import Link from "next/link";
import { BuyerOrders } from "@/components/orders/buyer-orders";
export const metadata: Metadata = {
  title: "Đơn hàng của tôi",
  robots: { index: false },
};
export const dynamic = "force-dynamic";
export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ page?: string | string[] }>;
}) {
  const value = (await searchParams).page;
  if (
    value !== undefined &&
    (typeof value !== "string" ||
      !/^[1-9]\d{0,9}$/.test(value) ||
      Number(value) > 2147483647)
  )
    return (
      <main className="shell buyer-orders-page">
        <h1>Trang đơn hàng không hợp lệ</h1>
        <Link href="/tai-khoan/don-hang">Về danh sách đơn hàng</Link>
      </main>
    );
  return <BuyerOrders page={value ? Number(value) : 1} />;
}
