"use client";
import Link from "next/link";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { AdminNavigation } from "@/components/admin/admin-navigation";
import { useSession } from "@/components/auth/session-provider";
import { formatVnd } from "@/lib/categories";
import {
  fetchAdminProducts,
  hideAdminProduct,
  AdminProductFailure,
  type AdminProduct,
  type AdminProductPage,
} from "@/lib/admin-products-client";

export function AdminProducts() {
  const { account, loading, error, refresh } = useSession();
  return (
    <main className="shell admin-users-page admin-products-page">
      <nav className="seller-breadcrumb" aria-label="Đường dẫn">
        <Link href="/">Trang chủ</Link>
        <span>/</span>
        <span>Quản trị sản phẩm</span>
      </nav>
      <header className="seller-heading">
        <div>
          <p className="seller-eyebrow">COCO · QUẢN TRỊ</p>
          <h1>Kiểm duyệt sản phẩm</h1>
          <p>Tìm sản phẩm trong các gian hàng và ẩn sản phẩm vi phạm.</p>
        </div>
        <Link className="seller-outline-button" href="/tai-khoan">
          Tài khoản của tôi
        </Link>
      </header>
      <AdminNavigation active="products" />
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
            href="/dang-nhap?returnTo=%2Fadmin%2Fproducts"
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
          <p>Chỉ quản trị viên được kiểm duyệt sản phẩm.</p>
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
  const [filters, setFilters] = useState({
      q: "",
      shop: "",
      active: "",
      page: 1,
    }),
    [retry, setRetry] = useState(0),
    [result, setResult] = useState<AdminProductPage | null>(null),
    [selected, setSelected] = useState<AdminProduct | null>(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [uncertain, setUncertain] = useState(false);
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
    void fetchAdminProducts(
      filters.page,
      filters.q,
      filters.shop,
      filters.active,
      c.signal,
    )
      .then((value) => {
        if (!c.signal.aborted) setResult(value);
      })
      .catch((e: unknown) => {
        if (c.signal.aborted) return;
        setResult(null);
        setSelected(null);
        setError(
          e instanceof Error ? e.message : "Chưa tải được danh sách sản phẩm.",
        );
        if (
          e instanceof AdminProductFailure &&
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
    setSelected(null);
    setError("");
    setNotice("");
    setUncertain(false);
    setRetry((v) => v + 1);
  }
  function search(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (submitting.current) return;
    const d = new FormData(e.currentTarget),
      shop = String(d.get("shop") ?? "").trim();
    if (
      shop &&
      (!/^[1-9]\d{0,18}$/.test(shop) ||
        BigInt(shop) > BigInt("9223372036854775807"))
    ) {
      setError("Mã shop phải là số nguyên dương hợp lệ.");
      return;
    }
    setResult(null);
    setSelected(null);
    setError("");
    setNotice("");
    setUncertain(false);
    setFilters({
      q: String(d.get("q") ?? "").trim(),
      shop,
      active: String(d.get("active") ?? ""),
      page: 1,
    });
  }
  async function hide() {
    if (!selected || submitting.current || uncertain) return;
    submitting.current = true;
    setBusy(true);
    setError("");
    const c = new AbortController();
    write.current = c;
    try {
      await hideAdminProduct(selected.product_id, c.signal);
      if (!mounted.current) return;
      setResult(null);
      setSelected(null);
      setNotice("Đã ẩn sản phẩm.");
      setRetry((v) => v + 1);
    } catch (e) {
      if (!mounted.current) return;
      setResult(null);
      setSelected(null);
      setUncertain(true);
      setError(e instanceof Error ? e.message : "Chưa xác minh được kết quả.");
      if (
        e instanceof AdminProductFailure &&
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
  function page(delta: number) {
    if (submitting.current) return;
    setResult(null);
    setSelected(null);
    setNotice("");
    setFilters((v) => ({ ...v, page: v.page + delta }));
  }
  return (
    <div className="admin-users-content">
      <form className="admin-user-filters" onSubmit={search}>
        <label htmlFor="admin-product-query">
          Tìm sản phẩm
          <input
            id="admin-product-query"
            name="q"
            type="search"
            maxLength={200}
            placeholder="Tên sản phẩm hoặc SKU"
            disabled={busy}
          />
        </label>
        <label htmlFor="admin-product-shop">
          Mã shop
          <input
            id="admin-product-shop"
            name="shop"
            type="text"
            inputMode="numeric"
            maxLength={19}
            placeholder="Tất cả shop"
            disabled={busy}
          />
        </label>
        <label htmlFor="admin-product-active">
          Trạng thái
          <select
            id="admin-product-active"
            name="active"
            aria-label="Trạng thái sản phẩm"
            disabled={busy}
          >
            <option value="">Tất cả</option>
            <option value="true">Đang bật</option>
            <option value="false">Đã ẩn</option>
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
        Sản phẩm đang bật chỉ xuất hiện công khai khi shop và danh mục đủ điều
        kiện. Ẩn sản phẩm không hủy đơn cũ hoặc hoàn tồn. Hiện chưa có chức năng
        bật lại.
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
      {selected && (
        <section
          className="seller-card admin-user-confirm"
          aria-labelledby="admin-product-confirm-title"
        >
          <h2 id="admin-product-confirm-title">Xác nhận ẩn sản phẩm</h2>
          <p>
            <strong>{selected.product_name}</strong> · SKU {selected.sku} · #
            {selected.product_id}
          </p>
          <p>
            Shop: {selected.shop.shop_name} (#{selected.shop.shop_id}). Sản phẩm
            không còn được mua mới; thông tin đơn đã đặt được giữ nguyên.
          </p>
          <button
            className="primary-button"
            disabled={busy}
            onClick={() => void hide()}
          >
            {busy ? "Đang lưu…" : "Xác nhận ẩn"}
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
          <p className="seller-card" role="status">
            Đang tải danh sách sản phẩm…
          </p>
        )
      ) : (
        <>
          <p>
            {result.total} sản phẩm · Trang {result.page}
          </p>
          {!result.items.length ? (
            <section className="seller-card">
              <h2>Không có sản phẩm phù hợp</h2>
              <p>Thay đổi từ khóa, shop hoặc trạng thái tìm kiếm.</p>
            </section>
          ) : (
            <ul className="admin-shop-list">
              {result.items.map((p) => (
                <li key={p.product_id} className="seller-card">
                  <header className="seller-heading">
                    <div>
                      <h2>{p.product_name}</h2>
                      <p>
                        SKU {p.sku} · #{p.product_id}
                      </p>
                    </div>
                    <span
                      className={`admin-shop-status ${p.is_active ? "status-approved" : "status-locked"}`}
                    >
                      {p.is_active ? "Đang bật" : "Đã ẩn"}
                    </span>
                  </header>
                  <dl className="admin-shop-details">
                    <div>
                      <dt>Gian hàng</dt>
                      <dd>
                        {p.shop.shop_name} (#{p.shop.shop_id})
                      </dd>
                    </div>
                    <div>
                      <dt>Danh mục</dt>
                      <dd>#{p.category_id}</dd>
                    </div>
                    <div>
                      <dt>Giá bán</dt>
                      <dd>{formatVnd(p.price)}</dd>
                    </div>
                    <div>
                      <dt>Tồn kho</dt>
                      <dd>{p.available_quantity}</dd>
                    </div>
                    <div>
                      <dt>Cập nhật lúc</dt>
                      <dd>{new Date(p.updated_at).toLocaleString("vi-VN")}</dd>
                    </div>
                  </dl>
                  <p className="admin-shop-description">
                    {p.description || "Chưa có mô tả sản phẩm."}
                  </p>
                  <div
                    className="admin-product-images"
                    aria-label="Ảnh sản phẩm"
                  >
                    {p.images.length ? (
                      p.images.map((image, index) =>
                        image.url ? (
                          <a
                            key={image.product_image_id}
                            href={image.url}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            Xem ảnh {index + 1}
                            {image.is_primary ? " (ảnh chính)" : ""}
                          </a>
                        ) : (
                          <span key={image.product_image_id}>
                            Ảnh {index + 1} chưa có đường dẫn
                          </span>
                        ),
                      )
                    ) : (
                      <span>Chưa có ảnh sản phẩm.</span>
                    )}
                  </div>
                  <div className="admin-shop-actions">
                    {p.is_active ? (
                      <button
                        className="seller-outline-button"
                        disabled={busy || uncertain}
                        onClick={() => {
                          setSelected(p);
                          setNotice("");
                        }}
                      >
                        Ẩn sản phẩm
                      </button>
                    ) : (
                      <small>Sản phẩm đã ẩn; chưa hỗ trợ bật lại.</small>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
          <nav
            className="buyer-order-pagination"
            aria-label="Phân trang sản phẩm quản trị"
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
