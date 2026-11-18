import { notFound } from "next/navigation";
import { SellerOrders } from "@/components/seller/seller-orders";
export const dynamic = "force-dynamic";
export const metadata = { title: "Chi tiết đơn bán" };
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  if (!/^[1-9]\d{0,18}$/.test(id) || BigInt(id) > BigInt("9223372036854775807"))
    notFound();
  return <SellerOrders id={id} />;
}
