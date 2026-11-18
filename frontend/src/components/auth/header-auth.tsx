"use client";
import Link from "next/link";
import { useState } from "react";
import { useSession } from "@/components/auth/session-provider";
export function HeaderAuth() {
  const { account, loading, logout } = useSession();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function signOut() {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      await logout();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Chưa thể đăng xuất.");
    } finally {
      setBusy(false);
    }
  }
  if (loading)
    return (
      <span className="auth-header-status" role="status">
        Đang kiểm tra phiên…
      </span>
    );
  return (
    <div className="header-auth-links">
      {account ? (
        <>
          <Link href="/tai-khoan" className="header-user-name">
            {account.full_name}
          </Link>
          <button disabled={busy} onClick={signOut}>
            {busy ? "Đang đăng xuất…" : "Đăng xuất"}
          </button>
        </>
      ) : (
        <>
          <Link href="/dang-ky">Đăng ký</Link>
          <Link href="/dang-nhap">Đăng nhập</Link>
        </>
      )}
      {error && (
        <p role="alert" className="header-auth-error">
          {error}
        </p>
      )}
    </div>
  );
}
