"use client";
import Link from "next/link";
import { BrandLogo } from "@/components/layout/brand-logo";
import { useSession } from "@/components/auth/session-provider";
import { SellerIcon } from "@/components/seller/seller-icon";

export function SellerHeader({ shipping = false }: { shipping?: boolean }) {
  const { account, loading } = useSession();
  if (shipping)
    return (
      <header className="shipping-header">
        <div className="shipping-header-inner">
          <div className="shipping-header-brand">
            <BrandLogo />
            <span className="shipping-header-divider" aria-hidden="true" />
            <Link
              href="/kenh-nguoi-ban"
              className="shipping-seller-badge"
              aria-label="COCO Seller"
            >
              <strong>COCO</strong>
              <span>Seller</span>
            </Link>
          </div>
          <nav aria-label="Kênh người bán">
            <details className="seller-header-notice">
              <summary aria-label="Thông báo">
                <SellerIcon name="bell" />
              </summary>
              <p>
                Cài đặt vận chuyển đang ở bản xem trước, chưa được lưu hoặc áp
                dụng.
              </p>
            </details>
            <span className="shipping-header-divider" aria-hidden="true" />
            <Link href="/kenh-nguoi-ban">
              <span className="shipping-header-store-icon">
                <SellerIcon name="shop" />
              </span>
              Đăng ký bán hàng
            </Link>
          </nav>
        </div>
      </header>
    );
  return (
    <header className="seller-registration-header">
      <div className="seller-registration-header-inner">
        <BrandLogo />
        <form action="/san-pham" role="search" className="seller-header-search">
          <label className="sr-only" htmlFor="seller-search">
            Tìm sản phẩm
          </label>
          <input
            id="seller-search"
            type="search"
            name="q"
            maxLength={200}
            placeholder="Tìm sản phẩm, thương hiệu hoặc danh mục…"
          />
          <button aria-label="Tìm kiếm" type="submit">
            <SellerIcon name="search" />
          </button>
        </form>
        <nav
          aria-label="Điều hướng tài khoản"
          className="seller-header-actions"
        >
          <details className="seller-header-notice">
            <summary aria-label="Thông báo">
              <SellerIcon name="bell" />
            </summary>
            <p>
              Đăng nhập để xem trạng thái hồ sơ gian hàng trong Kênh người bán.
            </p>
          </details>
          <span className="seller-header-divider" aria-hidden="true" />
          {loading ? (
            <span role="status" className="seller-header-session">
              Đang kiểm tra phiên…
            </span>
          ) : account ? (
            <>
              {account.user_role === "USER" && (
                <Link href="/tai-khoan/don-hang">Đơn mua</Link>
              )}
              <Link href="/tai-khoan" className="seller-header-account">
                <SellerIcon name="account" />
                <span>{account.full_name}</span>
              </Link>
            </>
          ) : (
            <>
              <Link
                href="/dang-nhap?returnTo=%2Fkenh-nguoi-ban"
                className="seller-header-account"
              >
                <SellerIcon name="account" />
                <span>Đăng nhập</span>
              </Link>
              <Link
                href="/dang-ky?returnTo=%2Fkenh-nguoi-ban"
                className="seller-header-register"
              >
                <SellerIcon name="adduser" />
                <span>Đăng ký</span>
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
