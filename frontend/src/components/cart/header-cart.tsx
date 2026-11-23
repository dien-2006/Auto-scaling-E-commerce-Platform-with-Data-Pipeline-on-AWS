"use client";
import Link from "next/link";
import { useSession } from "@/components/auth/session-provider";
import { useCart } from "@/components/cart/use-cart";
function CartIcon() {
  return (
    <svg
      width="30"
      height="30"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      aria-hidden="true"
    >
      <path d="M2 3h3l3 13h11l3-10H6" />
      <circle cx="9" cy="21" r="1" />
      <circle cx="19" cy="21" r="1" />
    </svg>
  );
}
function PrivateCartLink() {
  const { cart, error, loading } = useCart();
  const count = cart?.shops.reduce((sum, shop) => sum + shop.items.length, 0);
  return (
    <Link
      href="/gio-hang"
      className="header-cart-link"
      aria-label={`Giỏ hàng${loading ? ", đang cập nhật" : error ? ", chưa tải được số sản phẩm" : `, ${count} sản phẩm`}`}
    >
      <CartIcon />
      <span>Giỏ hàng</span>
      {!loading && !error && count !== undefined && (
        <span className="cart-count">{count}</span>
      )}
    </Link>
  );
}
export function HeaderCart() {
  const { account } = useSession();
  if (account?.user_role === "ADMIN")
    return (
      <Link href="/admin" className="header-cart-link">
        Quản trị
      </Link>
    );
  return account ? (
    <PrivateCartLink key={account.user_id} />
  ) : (
    <Link href="/gio-hang" className="header-cart-link">
      <CartIcon />
      <span>Giỏ hàng</span>
    </Link>
  );
}
