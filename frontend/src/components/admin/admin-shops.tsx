"use client";
import Link from "next/link";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { AdminNavigation } from "@/components/admin/admin-navigation";
import { useSession } from "@/components/auth/session-provider";
import { shopStatuses } from "@/lib/seller-shop-client";
import {
  fetchAdminShops,
  changeShopStatus,
  AdminShopFailure,
  type AdminShop,
  type AdminShopPage,
  type ShopStatus,
} from "@/lib/admin-shops-client";

export function AdminShops() {
  const { account, loading, error, refresh } = useSession();
  return (
    <main className="shell admin-users-page admin-shops-page">
      <nav className="seller-breadcrumb" aria-label="Đường dẫn">
        <Link href="/">Trang chủ</Link>
        <span>/</span>
        <span>Quản trị gian hàng</span>
      </nav>
      <header className="seller-heading">
        <div>
          <p className="seller-eyebrow">COCO · QUẢN TRỊ</p>
          <h1>Phê duyệt gian hàng</h1>
          <p>
            Xem hồ sơ, duyệt hoặc từ chối đăng ký và khóa gian hàng đang bán.
          </p>
        </div>
        <Link className="seller-outline-button" href="/tai-khoan">
          Tài khoản của tôi
        </Link>
      </header>
      <AdminNavigation active="shops" />
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
            href="/dang-nhap?returnTo=%2Fadmin%2Fshops"
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
          <p>Chỉ quản trị viên được phê duyệt gian hàng.</p>
          <Link href="/">Về trang chủ</Link>
        </section>
      ) : (
        <Content key={account.user_id} />
      )}
    </main>
  );
}
type Selection = { shop: AdminShop; target: ShopStatus };
function Content() {
  const { refresh } = useSession();
  const [filters, setFilters] = useState({ q: "", status: "", page: 1 }),
    [retry, setRetry] = useState(0),
    [result, setResult] = useState<AdminShopPage | null>(null),
    [error, setError] = useState(""),
    [selection, setSelection] = useState<Selection | null>(null),
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
  useEffect(() => {
    const c = new AbortController();
    void fetchAdminShops(filters.page, filters.q, filters.status, c.signal)
      .then((value) => {
        if (!c.signal.aborted) setResult(value);
      })
      .catch((e: unknown) => {
        if (c.signal.aborted) return;
        setResult(null);
        setSelection(null);
        setError(
          e instanceof Error ? e.message : "Chưa tải được danh sách gian hàng.",
        );
        if (
          e instanceof AdminShopFailure &&
          [
            "AUTH_REQUIRED",
            "TOKEN_EXPIRED",
            "INVALID_TOKEN",
            "USER_LOCKED",
            "FORBIDDEN",
          ].includes(e.code)
        )
          void refresh();
      });
    return () => c.abort();
  }, [filters, retry, refresh]);
  function reload() {
    if (submitting.current) return;
    setResult(null);
    setSelection(null);
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
    setSelection(null);
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
    if (!selection || submitting.current || uncertain) return;
    submitting.current = true;
    setBusy(true);
    setError("");
    const c = new AbortController();
    write.current = c;
    try {
      await changeShopStatus(selection.shop, selection.target, c.signal);
      if (!mounted.current) return;
      setResult(null);
      setSelection(null);
      setNotice("Đã cập nhật trạng thái gian hàng.");
      setRetry((v) => v + 1);
    } catch (e) {
      if (!mounted.current) return;
      setResult(null);
      setSelection(null);
      setUncertain(true);
      setError(
        e instanceof Error
          ? e.message
          : "Chưa xác minh được kết quả. Hãy tải lại danh sách.",
      );
      if (
        e instanceof AdminShopFailure &&
        [
          "AUTH_REQUIRED",
          "TOKEN_EXPIRED",
          "INVALID_TOKEN",
          "USER_LOCKED",
          "FORBIDDEN",
        ].includes(e.code)
      )
        void refresh();
    } finally {
      submitting.current = false;
      if (mounted.current) setBusy(false);
    }
  }
  function choose(shop: AdminShop, target: ShopStatus) {
    setSelection({ shop, target });
    setNotice("");
  }
  function page(offset: number) {
    if (submitting.current) return;
    setResult(null);
    setSelection(null);
    setNotice("");
    setFilters((v) => ({ ...v, page: v.page + offset }));
  }
  return (
    <div className="admin-users-content">
      <form className="admin-user-filters" onSubmit={search}>
        <label htmlFor="admin-shop-query">
          Tìm gian hàng
          <input
            id="admin-shop-query"
            name="q"
            type="search"
            maxLength={200}
            placeholder="Tên, đường dẫn hoặc email liên hệ"
            disabled={busy}
          />
        </label>
        <label htmlFor="admin-shop-status">
          Trạng thái
          <select
            id="admin-shop-status"
            name="status"
            aria-label="Trạng thái gian hàng"
            disabled={busy}
          >
            <option value="">Tất cả</option>
            {Object.entries(shopStatuses).map(([key, status]) => (
              <option key={key} value={key}>
                {status.label}
              </option>
            ))}
          </select>
        </label>
        <button className="primary-button" disabled={busy}>
          Tìm kiếm
        </button>
        <button
          type="button"
          className="seller-outline-button"
          disabled={busy}
          onClick={reload}
        >
          Tải lại danh sách
        </button>
      </form>
      <p className="admin-shop-policy">
        Gian hàng bị khóa không nhận đơn mới; chủ shop đang hoạt động vẫn xử lý
        được đơn cũ. Hiện chưa có mở khóa hoặc gửi duyệt lại.
      </p>
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
      {selection && (
        <section
          className="seller-card admin-user-confirm"
          aria-labelledby="admin-shop-confirm-title"
        >
          <h2 id="admin-shop-confirm-title">
            Xác nhận{" "}
            {selection.target === "APPROVED"
              ? "phê duyệt"
              : selection.target === "REJECTED"
                ? "từ chối"
                : "khóa"}{" "}
            gian hàng
          </h2>
          <p>
            <strong>{selection.shop.shop_name}</strong> · #
            {selection.shop.shop_id}
          </p>
          <p>
            Từ {shopStatuses[selection.shop.shop_status].label} sang{" "}
            <strong>{shopStatuses[selection.target].label}</strong>.
          </p>
          <p>
            {selection.target === "APPROVED"
              ? "Gian hàng được phép bán sản phẩm đủ điều kiện."
              : selection.target === "REJECTED"
                ? "Hồ sơ không được duyệt. Hiện chưa hỗ trợ gửi lại hồ sơ."
                : "Chặn đơn mới và chỉnh sửa sản phẩm/tồn kho. Đơn đã đặt được giữ nguyên, không tự hủy hoặc hoàn tồn."}
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
            onClick={() => setSelection(null)}
          >
            Quay lại
          </button>
        </section>
      )}
      {!result ? (
        !error && (
          <p role="status" className="seller-card">
            Đang tải danh sách gian hàng…
          </p>
        )
      ) : (
        <>
          <p>
            {result.total} gian hàng · Trang {result.page}
          </p>
          {!result.items.length ? (
            <section className="seller-card">
              <h2>Không có gian hàng phù hợp</h2>
              <p>Thay đổi từ khóa, trạng thái hoặc trang tìm kiếm.</p>
            </section>
          ) : (
            <ul className="admin-shop-list">
              {result.items.map((shop) => (
                <li key={shop.shop_id} className="seller-card">
                  <header className="seller-heading">
                    <div>
                      <h2>{shop.shop_name}</h2>
                      <p>
                        /{shop.shop_slug} · #{shop.shop_id}
                      </p>
                    </div>
                    <span
                      className={`admin-shop-status status-${shop.shop_status.toLowerCase()}`}
                    >
                      {shopStatuses[shop.shop_status].label}
                    </span>
                  </header>
                  <dl className="admin-shop-details">
                    <div>
                      <dt>Chủ gian hàng</dt>
                      <dd>#{shop.owner_user_id}</dd>
                    </div>
                    <div>
                      <dt>Email liên hệ</dt>
                      <dd>{shop.contact_email || "Chưa cung cấp"}</dd>
                    </div>
                    <div>
                      <dt>Đăng ký lúc</dt>
                      <dd>
                        {new Date(shop.created_at).toLocaleString("vi-VN")}
                      </dd>
                    </div>
                    <div>
                      <dt>Cập nhật lúc</dt>
                      <dd>
                        {new Date(shop.updated_at).toLocaleString("vi-VN")}
                      </dd>
                    </div>
                  </dl>
                  <p className="admin-shop-description">
                    {shop.description || "Chưa có mô tả gian hàng."}
                  </p>
                  <div className="admin-shop-actions">
                    {shop.shop_status === "PENDING" ? (
                      <>
                        <button
                          className="primary-button"
                          disabled={busy || uncertain}
                          onClick={() => choose(shop, "APPROVED")}
                        >
                          Phê duyệt
                        </button>
                        <button
                          className="seller-outline-button"
                          disabled={busy || uncertain}
                          onClick={() => choose(shop, "REJECTED")}
                        >
                          Từ chối
                        </button>
                      </>
                    ) : shop.shop_status === "APPROVED" ? (
                      <>
                        <button
                          className="seller-outline-button"
                          disabled={busy || uncertain}
                          onClick={() => choose(shop, "LOCKED")}
                        >
                          Khóa gian hàng
                        </button>
                        <Link
                          href={`/gian-hang/${encodeURIComponent(shop.shop_slug)}`}
                        >
                          Xem trang shop
                        </Link>
                      </>
                    ) : (
                      <small>
                        {shop.shop_status === "LOCKED"
                          ? "Chưa hỗ trợ mở khóa gian hàng."
                          : "Chưa hỗ trợ duyệt lại hồ sơ đã từ chối."}
                      </small>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
          <nav
            className="buyer-order-pagination"
            aria-label="Phân trang gian hàng"
          >
            <button
              className="seller-outline-button"
              disabled={busy || filters.page === 1}
              onClick={() => page(-1)}
            >
              Trang trước
            </button>
            <span>Trang {result.page}</span>
            <button
              className="seller-outline-button"
              disabled={busy || filters.page * 24 >= result.total}
              onClick={() => page(1)}
            >
              Trang sau
            </button>
          </nav>
        </>
      )}
    </div>
  );
}
