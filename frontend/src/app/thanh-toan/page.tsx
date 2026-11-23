import type { Metadata } from "next";
import { CheckoutPanel } from "@/components/checkout/checkout-panel";
export const metadata: Metadata = {
  title: "Thanh toán | coco",
  robots: { index: false, follow: false },
};
export const dynamic = "force-dynamic";
export default async function Page({searchParams}: {searchParams: Promise<{product?: string; quantity?: string; selected?: string}>}) {
  const params = await searchParams;
  if (params.selected !== undefined) {
    const ids = params.selected.split(",");
    if (params.product || !ids.length || ids.length > 1000 || new Set(ids).size !== ids.length || ids.some(id => !/^[1-9]\d{0,18}$/.test(id) || BigInt(id)>BigInt("9223372036854775807"))) return <p role="alert">Danh sách sản phẩm đã chọn không hợp lệ.</p>;
    return <CheckoutPanel selectedProducts={ids} />;
  }
  if (params.product !== undefined || params.quantity !== undefined) {
    if (!params.product || !/^[1-9]\d{0,18}$/.test(params.product) || BigInt(params.product)>BigInt("9223372036854775807") || !params.quantity || !/^[1-9]\d{0,9}$/.test(params.quantity) || Number(params.quantity)>2147483647) return <p role="alert">Thông tin mua ngay không hợp lệ. Vui lòng chọn lại sản phẩm.</p>;
    return <CheckoutPanel buyNow={{product:params.product,quantity:Number(params.quantity)}} />;
  }
  return <CheckoutPanel />;
}
