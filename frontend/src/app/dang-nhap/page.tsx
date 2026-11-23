import type { Metadata } from "next";
import { AuthGate } from "@/components/auth/auth-gate";
import { safeReturnPath } from "@/lib/auth-contract";
export const metadata: Metadata = {
  title: "Đăng nhập",
  robots: { index: false },
};
export default async function Page({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  return (
    <AuthGate
      mode="login"
      returnTo={safeReturnPath(params.returnTo)}
      registered={params.registered === "1"}
    />
  );
}
