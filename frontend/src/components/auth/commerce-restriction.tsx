import Link from "next/link";

export function CommerceRestriction() {
  return (
    <section className="shell account-page">
      <h1>Tài khoản dành cho quản trị</h1>
      <p>
        Tài khoản Admin không được mua hàng hoặc tạo gian hàng. Vui lòng dùng
        tài khoản thành viên riêng nếu cần mua bán.
      </p>
      <Link className="primary-button" href="/admin">
        Đến trang quản trị →
      </Link>
    </section>
  );
}
