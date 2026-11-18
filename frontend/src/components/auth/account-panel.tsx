"use client";
import Link from "next/link";
import { useSession } from "@/components/auth/session-provider";
export function AccountPanel() {
  const { account, loading, error, refresh } = useSession();
  if (loading)
    return (
      <div className="shell account-page" role="status">
        Đang tải thông tin tài khoản…
      </div>
    );
  if (!account)
    return (
      <section className="shell account-page">
        <div className="auth-form-card">
          <h1>Tài khoản của bạn</h1>
          <p role={error ? "alert" : "status"}>
            {error || "Vui lòng đăng nhập để xem thông tin tài khoản."}
          </p>
          <Link
            className="primary-button mt-5"
            href="/dang-nhap?returnTo=%2Ftai-khoan"
          >
            Đến trang đăng nhập →
          </Link>
          <button className="account-retry" onClick={() => void refresh()}>
            Kiểm tra lại phiên
          </button>
        </div>
      </section>
    );
  return (
    <div className="shell account-page">
      <section className="auth-form-card">
        <span className="auth-step">TÀI KHOẢN COCO</span>
        <h1>Xin chào, {account.full_name}</h1>
        <dl className="account-details">
          <div>
            <dt>Email</dt>
            <dd>{account.email || "Ch?a c? email"}</dd>
          </div>
          <div>
            <dt>Số điện thoại</dt>
            <dd>{account.phone || "Chưa cung cấp"}</dd>
          </div>
          <div>
            <dt>Vai trò</dt>
            <dd>
              {account.user_role === "ADMIN" ? "Quản trị viên" : "Thành viên"}
            </dd>
          </div>
          <div>
            <dt>Gian hàng</dt>
            <dd>
              {account.owned_shop
                ? {
                    PENDING: "Chờ phê duyệt",
                    APPROVED: "Đã phê duyệt",
                    REJECTED: "Đã từ chối",
                    LOCKED: "Đã khóa",
                  }[account.owned_shop.shop_status]
                : "Chưa đăng ký gian hàng"}
            </dd>
          </div>
        </dl>
        <Link href="/san-pham" className="primary-button">
          Khám phá sản phẩm →
        </Link>
        {account.user_role === "USER" && (
          <>
            <p className="auth-field-hint">
              <Link href="/tai-khoan/dia-chi">Quản lý địa chỉ giao hàng →</Link>
            </p>
            <p className="auth-field-hint">
              <Link href="/gio-hang">Xem giỏ hàng →</Link>
            </p>
            <p className="auth-field-hint">
              <Link href="/kenh-nguoi-ban">
                {account.owned_shop
                  ? "Quản lý gian hàng →"
                  : "Đăng ký gian hàng →"}
              </Link>
            </p>
            <p className="auth-field-hint">
              <Link href="/tai-khoan/don-hang">Lịch sử đơn hàng →</Link>
            </p>
          </>
        )}
        {account.user_role === "ADMIN" && (
          <p className="auth-field-hint">
            <Link href="/admin/users">Quản lý người dùng →</Link>
          </p>
        )}
      </section>
    </div>
  );
}
