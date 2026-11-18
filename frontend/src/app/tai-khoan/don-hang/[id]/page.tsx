import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { BuyerOrders } from "@/components/orders/buyer-orders";
import { validOrderId } from "@/lib/orders-client";
export const metadata: Metadata = {
  title: "Chi tiết đơn hàng",
  robots: { index: false },
};
export const dynamic = "force-dynamic";
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  if (!validOrderId(id)) notFound();
  return <BuyerOrders id={id} />;
}
