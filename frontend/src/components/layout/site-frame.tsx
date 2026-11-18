"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { BrandLogo } from "@/components/layout/brand-logo";
import { ResetFooter } from "@/components/auth/reset-footer";
import { RegisterFooter } from "@/components/auth/register-footer";
import { SellerHeader } from "@/components/seller/seller-header";
export function SiteFrame({
  children,
  header,
  footer,
}: {
  children: ReactNode;
  header: ReactNode;
  footer: ReactNode;
}) {
  const pathname = usePathname();
  const reset = pathname === "/quen-mat-khau";
  const auth = pathname === "/dang-nhap" || pathname === "/dang-ky" || reset;
  const shipping = pathname === "/kenh-nguoi-ban/van-chuyen";
  const seller = pathname === "/kenh-nguoi-ban" || pathname.startsWith("/kenh-nguoi-ban/");
  return (
    <>
      {seller ? (
        <SellerHeader shipping={shipping} />
      ) : auth ? (
        <header
          className={`auth-topbar ${pathname === "/dang-nhap" || reset ? "auth-topbar-login" : "auth-topbar-register"}${reset?" auth-topbar-reset":""}`}
        >
          <div className="shell">
            <BrandLogo />
            {pathname === "/dang-ky" && (
              <form
                className="register-header-search"
                action="/san-pham"
                role="search"
              >
                <label className="sr-only" htmlFor="register-search">
                  Tìm sản phẩm
                </label>
                <input
                  id="register-search"
                  name="q"
                  type="search"
                  maxLength={200}
                  placeholder="Tìm sản phẩm, danh mục…"
                />
                <button aria-label="Tìm kiếm" type="submit">
                  <svg
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth="2"
                    fill="none"
                    aria-hidden="true"
                  >
                    <circle cx="10" cy="10" r="7" />
                    <path d="m15 15 7 7" />
                  </svg>
                </button>
              </form>
            )}
            <nav aria-label="Điều hướng tài khoản">
              {pathname !== "/dang-ky" && (
                <Link href="/#ho-tro" className="auth-help-link">
                  <span aria-hidden="true">?</span>Trung tâm trợ giúp
                </Link>
              )}
              <span className="auth-topbar-divider" aria-hidden="true" />
              <Link
                href={pathname === "/dang-ky" ? "/dang-nhap" : "/tai-khoan"}
              >
                {pathname === "/dang-ky" ? "Đăng nhập" : "Tài khoản của tôi"}
              </Link>
              {pathname === "/dang-ky" && (
                <Link
                  className="auth-nav-active"
                  href="/dang-ky"
                  aria-current="page"
                >
                  Đăng ký
                </Link>
              )}
            </nav>
          </div>
        </header>
      ) : (
        header
      )}
      {children}
      {!auth && !seller && footer}
      {pathname === "/dang-ky" && <RegisterFooter />}
      {reset && <ResetFooter />}
    </>
  );
}
