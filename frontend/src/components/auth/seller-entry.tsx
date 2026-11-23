"use client";
import Link from "next/link";
import { useSession } from "@/components/auth/session-provider";
import type { ReactNode } from "react";

export function SellerEntry({ children }: { children: ReactNode }) {
  const { account } = useSession();
  return account?.user_role === "ADMIN" ? (
    <Link href="/admin" className="header-seller-link">
      Trang quản trị
    </Link>
  ) : (
    <Link href="/kenh-nguoi-ban" className="header-seller-link">
      {children}
    </Link>
  );
}
