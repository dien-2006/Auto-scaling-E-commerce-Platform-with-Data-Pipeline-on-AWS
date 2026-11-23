import type { Metadata } from "next";
import { ShippingSetup } from "@/components/seller/shipping-setup";
export const metadata: Metadata = {
  title: "Cài đặt vận chuyển — Bản xem trước",
  robots: { index: false },
};
export default function Page() {
  return <ShippingSetup />;
}
