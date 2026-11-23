import type { Metadata } from "next";
import { AccountPanel } from "@/components/auth/account-panel";
export const metadata: Metadata = {
  title: "Tài khoản",
  robots: { index: false },
};
export const dynamic = "force-dynamic";
export default function Page() {
  return <AccountPanel />;
}
