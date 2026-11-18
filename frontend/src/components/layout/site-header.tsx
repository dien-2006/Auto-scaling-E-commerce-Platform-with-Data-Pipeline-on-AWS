import { HeaderAuth } from "@/components/auth/header-auth";
import { SellerEntry } from "@/components/auth/seller-entry";
import { HeaderCart } from "@/components/cart/header-cart";
import Link from "next/link";
import type { ReactNode } from "react";
import { BrandLogo } from "@/components/layout/brand-logo";
import { beautyCategories } from "@/lib/categories";
import { siteBrand } from "@/lib/site-brand";

type IconName = "seller" | "bell" | "help" | "cart" | "search";
function HeaderIcon({ name }: { name: IconName }) {
  const paths = {
    seller: (
      <>
        <path d="M3 10h18l-2-6H5l-2 6Zm2 0v10h14V10M9 20v-6h6v6" />
        <path d="M3 10a3 3 0 0 0 6 0 3 3 0 0 0 6 0 3 3 0 0 0 6 0" />
      </>
    ),
    bell: <path d="M5 16h14l-2-3V9a5 5 0 0 0-10 0v4l-2 3ZM10 20h4M12 2v2" />,
    help: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M9.5 9a2.5 2.5 0 1 1 4 2c-1 .6-1.5 1-1.5 2M12 17h.01" />
      </>
    ),
    cart: (
      <>
        <path d="M2 3h3l3 13h11l3-10H6" />
        <circle cx="9" cy="21" r="1" />
        <circle cx="19" cy="21" r="1" />
      </>
    ),
    search: (
      <>
        <circle cx="10.5" cy="10.5" r="6.5" />
        <path d="m16 16 5 5" />
      </>
    ),
  };
  return (
    <svg
      width="22"
      height="22"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.65"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name]}
    </svg>
  );
}

function HeaderMenu({
  label,
  icon,
  children,
}: {
  label: string;
  icon?: IconName;
  children: ReactNode;
}) {
  return (
    <details
      className={`header-menu ${!icon ? "header-auth-menu" : ""}`}
      name="header-utilities"
    >
      <summary>
        {icon && <HeaderIcon name={icon} />}
        <span>{label}</span>
      </summary>
      <div className="header-menu-panel">{children}</div>
    </details>
  );
}

export function SiteHeader() {
  return (
    <header className="market-header">
      <div className="header-utility">
        <div className="shell header-utility-inner">
          <div className="header-utility-left">
            <SellerEntry>
              <HeaderIcon name="seller" /> Kênh người bán
            </SellerEntry>
          </div>
          <nav aria-label="Tiện ích">
            <HeaderMenu label="Thông báo" icon="bell">
              <h2>Thông báo</h2>
              <p>
                Thông báo cá nhân sẽ được cung cấp sau khi chức năng tài khoản
                được hoàn thiện.
              </p>
            </HeaderMenu>
            <HeaderMenu label="Hỗ trợ" icon="help">
              <h2>Chúng tôi có thể giúp gì?</h2>
              <p>
                Bạn có thể tìm sản phẩm theo tên hoặc chọn danh mục trên trang
                chủ. Website hỗ trợ đặt hàng COD mô phỏng, chưa tích hợp thanh
                toán tiền thật.
              </p>
              <Link href="/#danh-muc">Khám phá danh mục →</Link>
              <Link href="/#ve-chung-toi">Về {siteBrand.name} →</Link>
            </HeaderMenu>
            <span className="utility-auth-divider" aria-hidden="true" />
            <HeaderAuth />
          </nav>
        </div>
      </div>
      <div className="shell header-main">
        <BrandLogo />
        <div className="header-search-area">
          <form action="/san-pham" role="search" className="header-search">
            <label htmlFor="site-search" className="sr-only">
              Tìm kiếm sản phẩm
            </label>
            <input
              id="site-search"
              name="q"
              type="search"
              maxLength={200}
              placeholder="Tìm sản phẩm sức khỏe và làm đẹp…"
            />
            <button type="submit" aria-label="Tìm kiếm">
              <HeaderIcon name="search" />
            </button>
          </form>
          <nav
            className="header-search-suggestions"
            aria-label="Gợi ý tìm kiếm"
          >
            {beautyCategories
              .slice(0, 2)
              .concat(beautyCategories.slice(5))
              .map((category) => (
                <Link
                  key={category.key}
                  href={`/san-pham?danh-muc=${category.slug}`}
                >
                  {category.name}
                </Link>
              ))}
          </nav>
        </div>
        <div className="header-actions">
          <HeaderCart />
        </div>
      </div>
    </header>
  );
}
