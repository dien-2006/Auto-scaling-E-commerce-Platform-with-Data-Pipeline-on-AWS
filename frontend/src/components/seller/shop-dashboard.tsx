"use client";

import Link from "next/link";
import { ShopAvatar } from "@/components/shop-avatar";
import { CommerceRestriction } from "@/components/auth/commerce-restriction";
import { useRouter } from "next/navigation";
import { SellerRegistration } from "@/components/seller/seller-registration";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { useSession } from "@/components/auth/session-provider";
import {
  fetchSellerShop,
  deleteSellerShop,
  saveSellerShop,
  shopInputError,
  shopStatuses,
  ShopFailure,
  type SellerShop,
  type ShopInput,
} from "@/lib/seller-shop-client";

export function ShopDashboard() {
  const { account, loading, error } = useSession();
  const router = useRouter();
  if (!account)
    return (
      <SellerRegistration
        guest
        loading={loading}
        error={error}
        onSave={async () => {
          router.push("/dang-nhap?returnTo=%2Fkenh-nguoi-ban");
        }}
      />
    );
  if (account.user_role === "ADMIN") return <CommerceRestriction />;
  return <DashboardContent key={account.user_id} ownerId={account.user_id} />;
}

function DashboardContent({ ownerId }: { ownerId: string }) {
  const { refresh, account } = useSession();
  const [result, setResult] = useState<{ shop: SellerShop | null } | null>(
    null,
  );
  const [loadError, setLoadError] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [uncertain, setUncertain] = useState(false);
  const [busy, setBusy] = useState(false);
  const [retry, setRetry] = useState(0);
  const mounted = useRef(false),
    submitting = useRef(false),
    write = useRef<AbortController | null>(null);
  useEffect(() => {
    mounted.current = true;
    const controller = new AbortController();
    void fetchSellerShop(ownerId, controller.signal)
      .then((shop) => {
        if (!controller.signal.aborted) {
          setResult({ shop });
          setUncertain(false);
        }
      })
      .catch((e: unknown) => {
        if (!controller.signal.aborted)
          setLoadError(e instanceof Error ? e.message : "Chưa tải được hồ sơ.");
      });
    return () => {
      mounted.current = false;
      controller.abort();
      write.current?.abort();
    };
  }, [ownerId, retry]);
  function reload() {
    if (submitting.current) return;
    setResult(null);
    setLoadError("");
    setError("");
    setNotice("");
    setRetry((value) => value + 1);
  }
  async function save(input: ShopInput) {
    if (submitting.current || uncertain || !result) return;
    const issue = shopInputError(input, !result.shop);
    if (issue) {
      setError(issue);
      return;
    }
    submitting.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    const controller = new AbortController();
    write.current = controller;
    try {
      const shop = await saveSellerShop(
        result.shop ? "PATCH" : "POST",
        input,
        ownerId,
        controller.signal,
      );
      if (!mounted.current || controller.signal.aborted) return;
      setResult({ shop });
      setNotice(
        result.shop
          ? "Đã lưu thông tin gian hàng."
          : "Đã gửi hồ sơ đăng ký. Gian hàng đang chờ phê duyệt.",
      );
      void refresh();
    } catch (e) {
      if (!mounted.current || controller.signal.aborted) return;
      setError(e instanceof Error ? e.message : "Chưa lưu được hồ sơ.");
      // A response may be lost after COMMIT. Read the existing owner shop before
      // another write; do not claim success or silently submit again.
      if (
        !(e instanceof ShopFailure) ||
        ["UNAVAILABLE", "DEPENDENCY_UNAVAILABLE", "SHOP_EXISTS"].includes(
          e.code,
        )
      )
        setUncertain(true);
    } finally {
      submitting.current = false;
      if (mounted.current) setBusy(false);
    }
  }
  async function removeShop() {
    if (!result?.shop || submitting.current || uncertain) return;
    submitting.current = true;
    setBusy(true);
    setError("");
    const controller = new AbortController();
    write.current = controller;
    try {
      await deleteSellerShop(result.shop.shop_id, controller.signal);
      if (!mounted.current) return;
      setConfirmDelete(false);
      setResult({ shop: null });
      await refresh();
    } catch (e) {
      if (!mounted.current) return;
      setError(
        e instanceof Error ? e.message : "Chưa xác minh được kết quả xóa.",
      );
      if (
        !(e instanceof ShopFailure) ||
        ["UNAVAILABLE", "DEPENDENCY_UNAVAILABLE"].includes(e.code)
      ) {
        setUncertain(true);
        setConfirmDelete(false);
      }
    } finally {
      submitting.current = false;
      if (mounted.current) setBusy(false);
    }
  }
  if (result && !result.shop && !loadError)
    return (
      <SellerRegistration
        phone={account?.phone}
        busy={busy}
        uncertain={uncertain}
        error={error}
        onSave={save}
        onReload={reload}
      />
    );
  const shop = result?.shop,
    status = shop ? shopStatuses[shop.shop_status] : null;
  return (
    <main className="shell seller-page">
      <nav className="seller-breadcrumb" aria-label="Đường dẫn">
        <Link href="/">Trang chủ</Link>
        <span>/</span>
        <span>Kênh người bán</span>
      </nav>
      <div className="seller-workspace">
        <aside className="seller-sidebar">
          <Link href="/kenh-nguoi-ban" className="seller-sidebar-brand">
            <span aria-hidden="true">C</span>
            <div>
              coco Seller<small>Kênh người bán</small>
            </div>
          </Link>
          <nav aria-label="Điều hướng người bán">
            <Link
              className="seller-nav-active"
              href="/kenh-nguoi-ban"
              aria-current="page"
            >
              Gian hàng của tôi
            </Link>
            <Link href="/kenh-nguoi-ban/san-pham">Sản phẩm của tôi</Link>
            <Link href="/kenh-nguoi-ban/don-hang">Đơn bán của tôi</Link>
            <Link href="/tai-khoan/don-hang">Đơn mua của tôi</Link>
            <Link href="/tai-khoan">Tài khoản</Link>
            <Link href="/san-pham">Về trang mua sắm ↗</Link>
          </nav>
          <p>
            Mỗi tài khoản sở hữu một gian hàng. Thông tin hồ sơ được quản lý
            riêng cho chủ shop.
          </p>
        </aside>
        <div className="seller-main">
          <header className="seller-heading">
            <div>
              <span className="seller-eyebrow">KHÔNG GIAN NGƯỜI BÁN</span>
              <h1>{shop ? "Gian hàng của tôi" : "Đăng ký gian hàng"}</h1>
              <p>
                {shop
                  ? "Chăm chút hồ sơ, sẵn sàng kết nối cùng khách hàng."
                  : "Tạo dấu ấn của bạn trong thế giới sức khỏe & làm đẹp."}
              </p>
            </div>
            <button
              className="seller-outline-button"
              onClick={reload}
              disabled={busy}
            >
              Tải lại hồ sơ
            </button>
          </header>
          {loadError ? (
            <section className="seller-card seller-error">
              <h2>Chưa tải được gian hàng</h2>
              <p role="alert">{loadError}</p>
              <button className="primary-button" onClick={reload}>
                Thử lại
              </button>
              <Link href="/dang-nhap?returnTo=%2Fkenh-nguoi-ban">
                Đăng nhập lại
              </Link>
            </section>
          ) : !result ? (
            <p className="seller-card" role="status">
              Đang tải hồ sơ gian hàng…
            </p>
          ) : (
            <>
              {shop && status ? (
                <section
                  className={`seller-status-banner seller-status-${shop.shop_status.toLowerCase()}`}
                >
                  <ShopAvatar key={shop.logo_url} src={shop.logo_url} name={shop.shop_name} />
                  <div>
                    <span className="seller-status-label">{status.label}</span>
                    <h2>{shop.shop_name}</h2>
                    <p>{status.message}</p>
                  </div>
                  {shop.shop_status === "APPROVED" && (
                    <Link
                      className="seller-outline-button"
                      href={`/gian-hang/${encodeURIComponent(shop.shop_slug)}`}
                    >
                      Xem trang shop ↗
                    </Link>
                  )}
                </section>
              ) : (
                <section className="seller-onboarding">
                  <div>
                    <span>01</span>
                    <strong>Đăng ký hồ sơ</strong>
                  </div>
                  <div>
                    <span>02</span>
                    <strong>Admin phê duyệt</strong>
                  </div>
                  <div>
                    <span>03</span>
                    <strong>Sẵn sàng bán hàng</strong>
                  </div>
                </section>
              )}
              <div className="seller-profile-grid">
                <section className="seller-card" id="ho-so">
                  <header className="seller-card-heading">
                    <h2>
                      {shop ? "Thông tin gian hàng" : "Hồ sơ gian hàng mới"}
                    </h2>
                    <p>
                      {shop
                        ? `Mã gian hàng #${shop.shop_id}`
                        : "Thông tin rõ ràng giúp khách hàng nhận biết gian hàng của bạn."}
                    </p>
                  </header>
                  {error && (
                    <p className="seller-form-error" role="alert">
                      {error}
                    </p>
                  )}
                  {notice && (
                    <p className="seller-form-success" role="status">
                      {notice}
                    </p>
                  )}
                  {uncertain && (
                    <div className="seller-uncertain">
                      <p>
                        Chưa xác minh được kết quả lần lưu vừa rồi. Tải lại hồ
                        sơ trước khi tiếp tục.
                      </p>
                      <button
                        className="seller-outline-button"
                        onClick={reload}
                      >
                        Kiểm tra hồ sơ đã lưu
                      </button>
                    </div>
                  )}
                  <ShopForm
                    key={shop ? `${shop.shop_id}:${shop.updated_at}` : "new"}
                    shop={shop ?? null}
                    disabled={busy || uncertain}
                    busy={busy}
                    onSave={save}
                  />
                  {shop && (
                    <section
                      className="seller-delete-panel"
                      aria-label="Xóa gian hàng"
                    >
                      <p>
                        Chỉ xóa gian hàng chưa có sản phẩm hoặc dữ liệu liên
                        quan. Lịch sử đơn hàng được giữ nguyên.
                      </p>
                      {confirmDelete ? (
                        <>
                          <p>Xóa vĩnh viễn gian hàng “{shop.shop_name}”?</p>
                          <button
                            disabled={busy || uncertain}
                            className="primary-button"
                            onClick={() => void removeShop()}
                          >
                            Xác nhận xóa gian hàng
                          </button>
                          <button
                            disabled={busy}
                            className="seller-outline-button"
                            onClick={() => setConfirmDelete(false)}
                          >
                            Giữ gian hàng
                          </button>
                        </>
                      ) : (
                        <button
                          disabled={busy || uncertain}
                          className="seller-outline-button"
                          onClick={() => setConfirmDelete(true)}
                        >
                          Xóa gian hàng
                        </button>
                      )}
                    </section>
                  )}
                </section>
                <aside className="seller-guidance">
                  <section className="seller-card">
                    <h2>Hồ sơ & phê duyệt</h2>
                    <ul>
                      <li>Mỗi tài khoản có tối đa một gian hàng.</li>
                      <li>Gian hàng mới cần được Admin duyệt trước khi bán.</li>
                      <li>Đường dẫn được giữ cố định sau đăng ký.</li>
                      <li>Mô tả và email liên hệ có thể để trống.</li>
                    </ul>
                  </section>
                  <section className="seller-card">
                    <h2>Tài khoản của bạn</h2>
                    <p>
                      Tiếp tục mua sắm và theo dõi đơn mua bằng cùng tài khoản
                      đang sở hữu gian hàng.
                    </p>
                    <Link href="/tai-khoan">Quản lý tài khoản →</Link>
                  </section>
                </aside>
              </div>
            </>
          )}
        </div>
      </div>
    </main>
  );
}

function ShopForm({
  shop,
  disabled,
  busy,
  onSave,
}: {
  shop: SellerShop | null;
  disabled: boolean;
  busy: boolean;
  onSave: (input: ShopInput) => Promise<void>;
}) {
  const [name, setName] = useState(shop?.shop_name ?? ""),
    [slug, setSlug] = useState(shop?.shop_slug ?? ""),
    [description, setDescription] = useState(shop?.description ?? ""),
    [email, setEmail] = useState(shop?.contact_email ?? "");
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void onSave({
      shop_name: name,
      ...(shop ? {} : { shop_slug: slug.trim() }),
      description: description.trim() || null,
      contact_email: email.trim() || null,
    });
  }
  return (
    <form onSubmit={submit} className="seller-shop-form">
      <fieldset disabled={disabled}>
        <legend className="sr-only">Hồ sơ gian hàng</legend>
        <label htmlFor="seller-shop-name">
          Tên gian hàng <span aria-hidden="true">*</span>
        </label>
        <input
          id="seller-shop-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          placeholder="Ví dụ: An Nhiên Beauty"
          autoComplete="organization"
          aria-describedby="seller-name-hint"
        />
        <small id="seller-name-hint">Từ 1 đến 150 ký tự.</small>
        <label htmlFor="seller-shop-slug">
          Đường dẫn gian hàng {!shop && <span aria-hidden="true">*</span>}
        </label>
        <div className="seller-slug-field">
          <span>/gian-hang/</span>
          <input
            id="seller-shop-slug"
            value={slug}
            onChange={(e) => setSlug(e.target.value)}
            readOnly={!!shop}
            required={!shop}
            pattern={shop ? undefined : "[a-z0-9]+(-[a-z0-9]+)*"}
            maxLength={shop ? undefined : 160}
            placeholder="an-nhien-beauty"
            aria-describedby="seller-slug-hint"
          />
        </div>
        <small id="seller-slug-hint">
          {shop
            ? "Đường dẫn đã đăng ký, không thể chỉnh sửa."
            : "Chữ thường không dấu, số và dấu gạch nối. Không thể đổi sau đăng ký."}
        </small>
        <label htmlFor="seller-shop-description">Mô tả gian hàng</label>
        <textarea
          id="seller-shop-description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Giới thiệu phong cách và sản phẩm của gian hàng…"
          rows={5}
          aria-describedby="seller-description-hint"
        />
        <small id="seller-description-hint">
          Tối đa 5.000 ký tự. Nội dung hiển thị dạng văn bản.
        </small>
        <label htmlFor="seller-shop-email">Email liên hệ</label>
        <input
          id="seller-shop-email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="shop@example.com"
          autoComplete="email"
          maxLength={255}
        />
        <small>
          Email này chỉ nằm trong hồ sơ riêng của bạn và quản trị viên.
        </small>
        <div className="seller-form-actions">
          <button type="submit" className="primary-button" disabled={disabled}>
            {busy ? "Đang lưu…" : shop ? "Lưu thay đổi" : "Đăng ký gian hàng"}
          </button>
          {!shop && <p>Hồ sơ được tạo với trạng thái Chờ phê duyệt.</p>}
        </div>
      </fieldset>
    </form>
  );
}
