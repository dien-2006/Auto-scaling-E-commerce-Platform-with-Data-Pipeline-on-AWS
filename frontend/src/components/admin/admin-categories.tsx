"use client";
import Link from "next/link";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { AdminNavigation } from "@/components/admin/admin-navigation";
import { useSession } from "@/components/auth/session-provider";
import { suggestedShopSlug } from "@/lib/seller-registration";
import {
  fetchAdminCategories,
  saveCategory,
  blockedParents,
  AdminCategoryFailure,
  type AdminCategory,
  type CategoryInput,
} from "@/lib/admin-categories-client";

export function AdminCategories() {
  const { account, loading, error, refresh } = useSession();
  return (
    <main className="shell admin-users-page">
      <nav className="seller-breadcrumb" aria-label="Đường dẫn">
        <Link href="/">Trang chủ</Link>
        <span>/</span>
        <span>Quản trị danh mục</span>
      </nav>
      <header className="seller-heading">
        <div>
          <p className="seller-eyebrow">COCO · QUẢN TRỊ</p>
          <h1>Quản lý danh mục</h1>
          <p>Tạo danh mục, sắp xếp nhánh và quản lý hiển thị trong cửa hàng.</p>
        </div>
        <Link className="seller-outline-button" href="/tai-khoan">
          Tài khoản của tôi
        </Link>
      </header>
      <AdminNavigation active="categories" />
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
            href="/dang-nhap?returnTo=%2Fadmin%2Fcategories"
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
          <p>Chỉ quản trị viên được quản lý danh mục.</p>
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
  const [rows, setRows] = useState<AdminCategory[] | null>(null),
    [selection, setSelection] = useState<AdminCategory | "new" | null>(null),
    [retry, setRetry] = useState(0),
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
    void fetchAdminCategories(c.signal)
      .then((value) => {
        if (!c.signal.aborted) setRows(value);
      })
      .catch((e: unknown) => {
        if (c.signal.aborted) return;
        setRows(null);
        setSelection(null);
        setError(
          e instanceof Error ? e.message : "Chưa tải được cây danh mục.",
        );
        if (
          e instanceof AdminCategoryFailure &&
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
  }, [retry, refresh]);
  function reload() {
    if (submitting.current) return;
    setRows(null);
    setSelection(null);
    setError("");
    setNotice("");
    setUncertain(false);
    setRetry((v) => v + 1);
  }
  async function save(input: CategoryInput) {
    if (!selection || submitting.current || uncertain) return;
    submitting.current = true;
    setBusy(true);
    setError("");
    const c = new AbortController();
    write.current = c;
    try {
      await saveCategory(
        input,
        selection === "new" ? null : selection.category_id,
        c.signal,
      );
      if (!mounted.current) return;
      setRows(null);
      setSelection(null);
      setNotice("Đã lưu danh mục.");
      setRetry((v) => v + 1);
    } catch (e) {
      if (!mounted.current) return;
      setRows(null);
      setSelection(null);
      setUncertain(true);
      setError(e instanceof Error ? e.message : "Chưa xác minh được kết quả.");
      if (
        e instanceof AdminCategoryFailure &&
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
  return (
    <div className="admin-users-content">
      <div className="admin-category-toolbar">
        <button
          className="primary-button"
          disabled={busy || !rows || uncertain}
          onClick={() => {
            setSelection("new");
            setNotice("");
          }}
        >
          Thêm danh mục
        </button>
        <button
          className="seller-outline-button"
          disabled={busy}
          onClick={reload}
        >
          Tải lại cây danh mục
        </button>
      </div>
      <p className="admin-shop-policy">
        Tắt một danh mục sẽ ẩn cả nhánh khỏi mua sắm. Danh mục con và sản phẩm
        vẫn được giữ nguyên. Không xóa danh mục hoặc thay đổi đơn cũ.
      </p>
      {error && (
        <section className="seller-card">
          <p role="alert">{error}</p>
          {uncertain && (
            <p>
              Kết quả có thể đã được lưu. Tải lại cây và kiểm tra tên/đường dẫn
              trước khi thao tác mới; hệ thống không tự gửi lại.
            </p>
          )}
          <button className="primary-button" onClick={reload}>
            Thử lại
          </button>
        </section>
      )}
      {notice && (
        <p className="seller-form-success" role="status">
          {notice}
        </p>
      )}
      {selection && rows && (
        <CategoryForm
          key={selection === "new" ? "new" : selection.category_id}
          initial={selection === "new" ? null : selection}
          rows={rows}
          busy={busy}
          onSave={save}
          onCancel={() => setSelection(null)}
        />
      )}
      {!rows ? (
        !error && (
          <p className="seller-card" role="status">
            Đang tải cây danh mục…
          </p>
        )
      ) : !rows.length ? (
        <section className="seller-card">
          <h2>Chưa có danh mục</h2>
          <p>Thêm danh mục đầu tiên để Seller có thể phân loại sản phẩm.</p>
        </section>
      ) : (
        <>
          <p>
            {rows.length} danh mục ·{" "}
            {rows.filter((r) => r.parent_category_id === null).length} danh mục
            gốc
          </p>
          <ul className="admin-category-list" aria-label="Cây danh mục">
            {rows.map((r) => (
              <li
                key={r.category_id}
                className="seller-card"
                style={{ marginInlineStart: `${Math.min(r.depth, 5) * 12}px` }}
              >
                <div className="admin-category-row">
                  <div>
                    <small>
                      Cấp {r.depth + 1} · #{r.category_id}
                    </small>
                    <h2>{r.category_name}</h2>
                    <p>/{r.category_slug}</p>
                    <p className="admin-category-path">{r.path}</p>
                  </div>
                  <div className="admin-category-state">
                    <span
                      className={`admin-shop-status ${r.is_active ? "status-approved" : "status-locked"}`}
                    >
                      {r.is_active ? "Đang bật" : "Đã tắt"}
                    </span>
                    {r.is_active && !r.effective_active && (
                      <small>Ẩn do danh mục cha đang tắt</small>
                    )}
                    <button
                      className="seller-outline-button"
                      disabled={busy || uncertain}
                      onClick={() => {
                        setSelection(r);
                        setNotice("");
                      }}
                    >
                      Chỉnh sửa
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
function CategoryForm({
  initial,
  rows,
  busy,
  onSave,
  onCancel,
}: {
  initial: AdminCategory | null;
  rows: AdminCategory[];
  busy: boolean;
  onSave: (input: CategoryInput) => Promise<void>;
  onCancel: () => void;
}) {
  const [name, setName] = useState(initial?.category_name ?? ""),
    [slug, setSlug] = useState(initial?.category_slug ?? ""),
    [review, setReview] = useState<CategoryInput | null>(null);
  const editedSlug = useRef(!!initial),
    blocked = initial
      ? blockedParents(rows, initial.category_id)
      : new Set<string>();
  function prepare(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const d = new FormData(e.currentTarget);
    setReview({
      category_name: name.trim(),
      category_slug: slug.trim(),
      parent_category_id: String(d.get("parent") ?? "") || null,
      is_active: d.get("active") === "on",
    });
  }
  const parent = review?.parent_category_id
    ? rows.find((r) => r.category_id === review.parent_category_id)
    : null;
  return (
    <section
      className="seller-card admin-category-form"
      aria-labelledby="category-form-title"
    >
      <header className="seller-heading">
        <h2 id="category-form-title">
          {initial ? "Sửa danh mục" : "Thêm danh mục mới"}
        </h2>
        <button
          className="seller-outline-button"
          disabled={busy}
          onClick={onCancel}
        >
          Đóng chỉnh sửa
        </button>
      </header>
      <form onSubmit={prepare}>
        <fieldset disabled={busy || !!review}>
          <label htmlFor="category-name">Tên danh mục</label>
          <input
            id="category-name"
            value={name}
            maxLength={120}
            required
            onChange={(e) => {
              setName(e.target.value);
              if (!editedSlug.current)
                setSlug(
                  suggestedShopSlug(e.target.value)
                    .slice(0, 140)
                    .replace(/-+$/, ""),
                );
            }}
          />
          <label htmlFor="category-slug">Đường dẫn danh mục</label>
          <input
            id="category-slug"
            value={slug}
            maxLength={140}
            pattern="[a-z0-9]+(-[a-z0-9]+)*"
            required
            onChange={(e) => {
              editedSlug.current = true;
              setSlug(e.target.value);
            }}
          />
          <small>
            Chữ thường không dấu, số và dấu gạch nối; duy nhất trong hệ thống.
            Đổi đường dẫn sẽ thay liên kết lọc danh mục.
          </small>
          <label htmlFor="category-parent">Danh mục cha</label>
          <select
            id="category-parent"
            name="parent"
            aria-label="Danh mục cha"
            defaultValue={initial?.parent_category_id ?? ""}
          >
            <option value="">Không có — danh mục gốc</option>
            {rows
              .filter((r) => !blocked.has(r.category_id))
              .map((r) => (
                <option key={r.category_id} value={r.category_id}>
                  {r.path}
                  {!r.effective_active ? " (đang ẩn)" : ""}
                </option>
              ))}
          </select>
          <label className="admin-category-check">
            <input
              type="checkbox"
              name="active"
              defaultChecked={initial?.is_active ?? true}
            />
            Bật danh mục
          </label>
          <button className="primary-button" disabled={busy || !!review}>
            Kiểm tra thay đổi
          </button>
        </fieldset>
      </form>
      {review && (
        <div className="admin-user-confirm">
          <h3>Xác nhận lưu danh mục</h3>
          <p>
            <strong>{review.category_name}</strong> · /{review.category_slug}
          </p>
          <p>
            Danh mục cha: {parent?.path ?? "Không có — danh mục gốc"}. Trạng
            thái: {review.is_active ? "Đang bật" : "Đã tắt"}.
          </p>
          {!review.is_active && (
            <p>
              Cả nhánh sẽ không xuất hiện công khai. Sản phẩm và đơn đã đặt
              không bị xóa.
            </p>
          )}
          {review.is_active && parent && !parent.effective_active && (
            <p>Danh mục vẫn ẩn khỏi mua sắm vì một danh mục cha đang tắt.</p>
          )}
          <button
            className="primary-button"
            disabled={busy}
            onClick={() => void onSave(review)}
          >
            {busy ? "Đang lưu…" : "Xác nhận lưu"}
          </button>
          <button
            className="seller-outline-button"
            disabled={busy}
            onClick={() => setReview(null)}
          >
            Sửa lại
          </button>
        </div>
      )}
    </section>
  );
}
