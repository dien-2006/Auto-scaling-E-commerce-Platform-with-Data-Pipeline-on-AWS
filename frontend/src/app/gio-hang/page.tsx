import type { Metadata } from "next";
import { CartPanel } from "@/components/cart/cart-panel";
export const metadata: Metadata = {
  title: "Giỏ hàng | coco",
  robots: { index: false, follow: false },
};
export const dynamic = "force-dynamic";
export default function Page() {
  return <CartPanel />;
}
