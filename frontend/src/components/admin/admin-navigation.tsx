import Link from "next/link";
export function AdminNavigation({
  active,
}: {
  active: "users" | "shops" | "products" | "categories";
}) {
  return (
    <nav className="admin-navigation" aria-label="Điều hướng quản trị">
      <Link
        href="/admin/users"
        aria-current={active === "users" ? "page" : undefined}
      >
        Người dùng
      </Link>
      <Link
        href="/admin/shops"
        aria-current={active === "shops" ? "page" : undefined}
      >
        Gian hàng
      </Link>
      <Link
        href="/admin/products"
        aria-current={active === "products" ? "page" : undefined}
      >
        Sản phẩm
      </Link>
      <Link
        href="/admin/categories"
        aria-current={active === "categories" ? "page" : undefined}
      >
        Danh mục
      </Link>
    </nav>
  );
}
