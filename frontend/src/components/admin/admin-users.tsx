"use client";
import Link from "next/link";
import { AdminNavigation } from "@/components/admin/admin-navigation";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { useSession } from "@/components/auth/session-provider";
import {
  fetchAdminUsers,
  changeUserStatus,
  AdminUserFailure,
  type AdminUser,
  type AdminUserPage,
} from "@/lib/admin-users-client";

export function AdminUsers() {
  const { account, loading, error, refresh } = useSession();
  return (
    <main className="shell admin-users-page">
      <nav className="seller-breadcrumb" aria-label="Đường dẫn">
        <Link href="/">Trang chủ</Link>
        <span>/</span>
        <span>Quản trị người dùng</span>
      </nav>
      <header className="seller-heading">
        <div>
          <p className="seller-eyebrow">COCO · QUẢN TRỊ</p>
          <h1>Quản lý người dùng</h1>
          <p>Tìm tài khoản, kiểm tra trạng thái và quản lý quyền truy cập.</p>
        </div>
        <Link className="seller-outline-button" href="/tai-khoan">
          Tài khoản của tôi
        </Link>
      </header>
      <AdminNavigation active="users" />
      {loading && !account ? (
        <p className="seller-card" role="status">
          Đang kiểm tra quyền truy cập…
        </p>
      ) : !account ? (
        <section className="seller-card">
          <p role={error ? "alert" : undefined}>
            {error || "Đăng nhập bằng tài khoản quản trị viên."}
          </p>
          <Link
            className="primary-button"
            href="/dang-nhap?returnTo=%2Fadmin%2Fusers"
          >
            Đăng nhập
          </Link>
          <button
            className="seller-outline-button"
            onClick={() => void refresh()}
          >
            Kiểm tra lại phiên
          </button>
        </section>
      ) : account.user_role !== "ADMIN" ? (
        <section className="seller-card">
          <h2>Không có quyền truy cập</h2>
          <p>Chỉ quản trị viên được quản lý người dùng.</p>
          <Link href="/">Về trang chủ</Link>
        </section>
      ) : (
        <Content key={account.user_id} />
      )}
    </main>
  );
}
function Content() {
  const { refresh } = useSession();
  const [filters, setFilters] = useState({ q: "", status: "", page: 1 }),
    [retry, setRetry] = useState(0),
    [result, setResult] = useState<AdminUserPage | null>(null),
    [error, setError] = useState(""),
    [selected, setSelected] = useState<AdminUser | null>(null),
    [busy, setBusy] = useState(false),
    [uncertain, setUncertain] = useState(false),
    [notice, setNotice] = useState("");
  const mounted = useRef(true),
    submitting = useRef(false),
    write = useRef<AbortController | null>(null);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      write.current?.abort();
    };
  }, []);
  function failure(e: unknown) {
    setError(
      e instanceof Error ? e.message : "Chưa tải được danh sách người dùng.",
    );
    if (
      e instanceof AdminUserFailure &&
      [
        "AUTH_REQUIRED",
        "TOKEN_EXPIRED",
        "INVALID_TOKEN",
        "USER_LOCKED",
        "FORBIDDEN",
      ].includes(e.code)
    ) {
      setResult(null);
      setSelected(null);
      void refresh();
    }
  }
  useEffect(() => {
    const c = new AbortController();
    void fetchAdminUsers(filters.page, filters.q, filters.status, c.signal)
      .then((value) => {
        if (!c.signal.aborted) setResult(value);
      })
      .catch((e: unknown) => {
        if (!c.signal.aborted) {
          setResult(null);
          setSelected(null);
          setError(
            e instanceof Error
              ? e.message
              : "Chưa tải được danh sách người dùng.",
          );
          if (
            e instanceof AdminUserFailure &&
            [
              "AUTH_REQUIRED",
              "TOKEN_EXPIRED",
              "INVALID_TOKEN",
              "USER_LOCKED",
              "FORBIDDEN",
            ].includes(e.code)
          )
            void refresh();
        }
      });
    return () => c.abort();
  }, [filters, retry, refresh]);
  function reload() {
    if (submitting.current) return;
    setResult(null);
    setSelected(null);
    setError("");
    setNotice("");
    setUncertain(false);
    setRetry((v) => v + 1);
  }
  function search(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (submitting.current) return;
    const data = new FormData(e.currentTarget);
    setResult(null);
    setSelected(null);
    setError("");
    setNotice("");
    setUncertain(false);
    setFilters({
      q: String(data.get("q") ?? "").trim(),
      status: String(data.get("status") ?? ""),
      page: 1,
    });
  }
  async function save() {
    if (!selected || submitting.current || uncertain) return;
    submitting.current = true;
    setBusy(true);
    setError("");
    const c = new AbortController();
    write.current = c;
    try {
      await changeUserStatus(
        selected.user_id,
        selected.user_status === "ACTIVE" ? "LOCKED" : "ACTIVE",
        c.signal,
      );
      if (!mounted.current) return;
      setSelected(null);
      setResult(null);
      setNotice("Đã cập nhật trạng thái tài khoản.");
      setRetry((v) => v + 1);
    } catch (e) {
      if (mounted.current) {
        setSelected(null);
        setResult(null);
        setUncertain(true);
        failure(e);
      }
    } finally {
      submitting.current = false;
      if (mounted.current) setBusy(false);
    }
  }
  return (
    <div className="admin-users-content">
      <form onSubmit={search} className="admin-user-filters">
        <label htmlFor="admin-user-query">
          Tìm người dùng
          <input
            id="admin-user-query"
            name="q"
            type="search"
            maxLength={200}
            defaultValue={filters.q}
            placeholder="Tên, email hoặc số điện thoại"
            disabled={busy}
          />
        </label>
        <label htmlFor="admin-user-status">
          Trạng thái
          <select
            id="admin-user-status"
            aria-label="Trạng thái"
            name="status"
            defaultValue=""
            disabled={busy}
          >
            <option value="">Tất cả</option>
            <option value="ACTIVE">Hoạt động</option>
            <option value="LOCKED">Đã khóa</option>
          </select>
        </label>
        <button className="primary-button" disabled={busy}>
          Tìm kiếm
        </button>
        <button
          className="seller-outline-button"
          type="button"
          onClick={reload}
          disabled={busy}
        >
          Tải lại danh sách
        </button>
      </form>
      {notice && (
        <p role="status" className="seller-form-success">
          {notice}
        </p>
      )}
      {error && (
        <section className="seller-card">
          <p role="alert">{error}</p>
          {uncertain && (
            <p>
              Kết quả có thể đã được lưu. Tải lại danh sách và kiểm tra trước
              khi thực hiện thao tác mới.
            </p>
          )}
          <button className="primary-button" onClick={reload}>
            Thử lại
          </button>
        </section>
      )}
      {selected && (
        <section
          className="seller-card admin-user-confirm"
          aria-labelledby="admin-user-confirm-title"
        >
          <h2 id="admin-user-confirm-title">
            {selected.user_status === "ACTIVE"
              ? "Xác nhận khóa tài khoản"
              : "Xác nhận mở khóa tài khoản"}
          </h2>
          <p>
            <strong>{selected.full_name}</strong> · {selected.email || selected.phone}
          </p>
          <p>
            {selected.user_status === "ACTIVE"
              ? "Tài khoản bị khóa sẽ không truy cập được các chức năng cần đăng nhập. Gian hàng và đơn cũ vẫn được giữ."
              : "Tài khoản có thể truy cập lại nếu phiên đăng nhập hợp lệ. Trạng thái gian hàng không thay đổi."}
          </p>
          <button
            className="primary-button"
            disabled={busy}
            onClick={() => void save()}
          >
            {busy ? "Đang lưu…" : "Xác nhận thay đổi"}
          </button>
          <button
            className="seller-outline-button"
            disabled={busy}
            onClick={() => setSelected(null)}
          >
            Quay lại
          </button>
        </section>
      )}
      {!result ? (
        !error && (
          <p role="status" className="seller-card">
            Đang tải danh sách người dùng…
          </p>
        )
      ) : (
        <>
          <p>
            {result.total} người dùng · Trang {result.page}
          </p>
          {!result.items.length ? (
            <section className="seller-card">
              <h2>Không có người dùng phù hợp</h2>
              <p>Thay đổi từ khóa hoặc trạng thái tìm kiếm.</p>
            </section>
          ) : (
            <ul className="admin-user-list">
              {result.items.map((user) => (
                <li key={user.user_id} className="seller-card">
                  <div className="admin-user-identity">
                    <strong>{user.full_name}</strong>
                    <span>{user.email || user.phone}</span>
                    <span>{user.phone || "Chưa có số điện thoại"}</span>
                    <small>
                      #{user.user_id} · Tạo{" "}
                      {new Date(user.created_at).toLocaleString("vi-VN")}
                    </small>
                  </div>
                  <div className="admin-user-badges">
                    <span>
                      {user.user_role === "ADMIN"
                        ? "Quản trị viên"
                        : "Người dùng"}
                    </span>
                    <span
                      className={`admin-user-status status-${user.user_status.toLowerCase()}`}
                    >
                      {user.user_status === "ACTIVE" ? "Hoạt động" : "Đã khóa"}
                    </span>
                  </div>
                  <button
                    className="seller-outline-button"
                    disabled={busy || uncertain || user.user_role === "ADMIN"}
                    onClick={() => {
                      setSelected(user);
                      setNotice("");
                    }}
                  >
                    {user.user_role === "ADMIN"
                      ? "Admin chỉ xem"
                      : user.user_status === "ACTIVE"
                        ? "Khóa tài khoản"
                        : "Mở khóa tài khoản"}
                  </button>
                </li>
              ))}
            </ul>
          )}
          <nav
            className="buyer-order-pagination"
            aria-label="Phân trang người dùng"
          >
            <button
              className="seller-outline-button"
              disabled={busy || filters.page === 1}
              onClick={() => {
                setResult(null);
                setSelected(null);
                setFilters((v) => ({ ...v, page: v.page - 1 }));
              }}
            >
              Trang trước
            </button>
            <span>Trang {result.page}</span>
            <button
              className="seller-outline-button"
              disabled={busy || filters.page * 24 >= result.total}
              onClick={() => {
                setResult(null);
                setSelected(null);
                setFilters((v) => ({ ...v, page: v.page + 1 }));
              }}
            >
              Trang sau
            </button>
          </nav>
        </>
      )}
    </div>
  );
}
