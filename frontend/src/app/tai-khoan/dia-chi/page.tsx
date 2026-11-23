import type { Metadata } from "next";
import { safeReturnPath } from "@/lib/auth-contract";
import { AddressPanel } from "@/components/auth/address-panel";
export const metadata: Metadata = {
  title: "Địa chỉ giao hàng | coco",
  robots: { index: false, follow: false },
};
export const dynamic = "force-dynamic";
export default async function AddressPage({searchParams}: {searchParams: Promise<{returnTo?: string}>}) {
  const params = await searchParams;
  return <AddressPanel returnTo={safeReturnPath(params.returnTo).split("?")[0] === "/thanh-toan" ? safeReturnPath(params.returnTo) : "/tai-khoan"} />;
}
