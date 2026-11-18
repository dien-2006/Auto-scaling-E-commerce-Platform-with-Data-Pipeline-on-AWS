"use client";
import Link from "next/link";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { useSession } from "@/components/auth/session-provider";
import { ProductImages } from "@/components/seller/product-images";
import { InventoryPanel } from "@/components/seller/inventory-panel";
import type { Category } from "@/lib/catalog-api";
import { formatVnd } from "@/lib/categories";
import {
  fetchSellerShop,
  ShopFailure,
  type SellerShop,
} from "@/lib/seller-shop-client";
import {
  fetchSellerProducts,
  writeSellerProduct,
  deleteSellerProduct,
  ProductFailure,
  type ProductInput,
  type SellerPage,
  type SellerProduct,
} from "@/lib/seller-products-client";

export function SellerProducts({
  categories,
}: {
  categories: Category[] | null;
}) {
  const { account, loading } = useSession();
  return (
    <div className="shell seller-page">
      <nav className="seller-breadcrumb" aria-label="Đường dẫn">
        <Link href="/kenh-nguoi-ban">Gian hàng của tôi</Link>
        <span>/</span>
        <span>Sản phẩm</span>
      </nav>
      {loading ? (
        <p role="status">Đang kiểm tra phiên đăng nhập…</p>
      ) : !account ? (
        <section className="seller-card">
          <h1>Quản lý sản phẩm</h1>
          <p>Đăng nhập bằng tài khoản sở hữu gian hàng.</p>
          <Link href="/dang-nhap?returnTo=%2Fkenh-nguoi-ban%2Fsan-pham">
            Đăng nhập
          </Link>
        </section>
      ) : (
        <OwnerProducts
          key={account.user_id}
          ownerId={account.user_id}
          categories={categories}
        />
      )}
    </div>
  );
}
function OwnerProducts({
  ownerId,
  categories,
}: {
  ownerId: string;
  categories: Category[] | null;
}) {
  const { refresh } = useSession();
  const [imageProduct, setImageProduct] = useState<SellerProduct | null>(null);
  const [deleteMode, setDeleteMode] = useState(false);
  const [stockProduct, setStockProduct] = useState<SellerProduct | null>(null);
  const [shop, setShop] = useState<SellerShop | null>(null),
    [page, setPage] = useState<SellerPage | null>(null);
  const [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [busy, setBusy] = useState(false),
    [uncertain, setUncertain] = useState(false);
  const [query, setQuery] = useState({ q: "", active: "", page: 1 }),
    [retry, setRetry] = useState(0);
  const [selection, setSelection] = useState<SellerProduct | "new" | null>(
      null,
    ),
    [confirmHide, setConfirmHide] = useState<SellerProduct | null>(null);
  const submitting = useRef(false),
    mounted = useRef(false),
    write = useRef<AbortController | null>(null);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      write.current?.abort();
    };
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    void (async () => {
      const owned = await fetchSellerShop(ownerId, controller.signal);
      if (controller.signal.aborted) return;
      if (!owned)
        throw new Error(
          "Bạn chưa đăng ký gian hàng. Trở về gian hàng để đăng ký.",
        );
      setShop(owned);
      if (owned.shop_status !== "APPROVED")
        throw new Error(
          "Gian hàng cần được phê duyệt và đang hoạt động để quản lý sản phẩm.",
        );
      const params = new URLSearchParams({
        q: query.q,
        page: String(query.page),
        page_size: "24",
        ...(query.active ? { is_active: query.active } : {}),
      });
      const result = await fetchSellerProducts(
        owned.shop_id,
        params,
        controller.signal,
      );
      if (!controller.signal.aborted) {
        setPage(result);
        setUncertain(false);
      }
    })().catch((e: unknown) => {
      if (!controller.signal.aborted) {
        setError(e instanceof Error ? e.message : "Chưa tải được sản phẩm.");
        if (
          (e instanceof ProductFailure || e instanceof ShopFailure) &&
          [
            "AUTH_REQUIRED",
            "TOKEN_EXPIRED",
            "INVALID_TOKEN",
            "USER_LOCKED",
            "SHOP_NOT_APPROVED",
            "FORBIDDEN",
          ].includes(e.code)
        ) {
          setShop(null);
          setPage(null);
          setSelection(null);
          setStockProduct(null);
          setImageProduct(null);
          setConfirmHide(null);
          void refresh();
        }
      }
    });
    return () => controller.abort();
  }, [ownerId, query, retry, refresh]);
  function reload() {
    if (submitting.current) return;
    setError("");
    setNotice("");
    setPage(null);
    setSelection(null);
    setStockProduct(null);
    setImageProduct(null);
    setConfirmHide(null);
    setRetry((v) => v + 1);
  }
  async function save(
    input?: ProductInput,
    product?: SellerProduct,
    hide = false,
    remove = false,
  ) {
    if (!shop || !page || submitting.current || uncertain) return;
    submitting.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    const controller = new AbortController();
    write.current = controller;
    try {
      if (remove && product)
        await deleteSellerProduct(product.product_id, controller.signal);
      else
        await writeSellerProduct(
          shop.shop_id,
          controller.signal,
          input,
          product?.product_id,
          hide,
        );
      if (!mounted.current) return;
      setNotice(
        remove
          ? "Đã xóa sản phẩm."
          : hide
            ? "Đã ẩn sản phẩm."
            : product
              ? "Đã lưu sản phẩm."
              : "Đã tạo sản phẩm và tồn kho ban đầu.",
      );
      setSelection(null);
      setStockProduct(null);
      setImageProduct(null);
      setConfirmHide(null);
      setPage(null);
      setRetry((v) => v + 1);
    } catch (e) {
      if (!mounted.current) return;
      setError(e instanceof Error ? e.message : "Chưa xác minh được kết quả.");
      // An unavailable response may follow a successful COMMIT. Require a read,
      // never automatically repeat a create/patch/hide.
      if (
        !(e instanceof ProductFailure) ||
        ["UNAVAILABLE", "DEPENDENCY_UNAVAILABLE"].includes(e.code)
      )
        setUncertain(true);
      if (
        e instanceof ProductFailure &&
        [
          "AUTH_REQUIRED",
          "TOKEN_EXPIRED",
          "INVALID_TOKEN",
          "USER_LOCKED",
          "SHOP_NOT_APPROVED",
          "FORBIDDEN",
        ].includes(e.code)
      ) {
        setSelection(null);
        setStockProduct(null);
        setImageProduct(null);
        setConfirmHide(null);
        setPage(null);
        setShop(null);
        void refresh();
      }
    } finally {
      submitting.current = false;
      if (mounted.current) setBusy(false);
    }
  }
  return (
    <div className="seller-workspace">
      <aside className="seller-sidebar">
        <nav aria-label="Điều hướng người bán">
          <Link href="/kenh-nguoi-ban">Gian hàng của tôi</Link>
          <Link
            className="seller-nav-active"
            aria-current="page"
            href="/kenh-nguoi-ban/san-pham"
          >
            Sản phẩm của tôi
          </Link>
          <Link href="/san-pham">Về trang mua sắm ↗</Link>
          <Link href="/kenh-nguoi-ban/don-hang">Đơn bán của tôi</Link>
        </nav>
      </aside>
      <div className="seller-main">
        <header className="seller-heading">
          <div>
            <span className="seller-eyebrow">
              {shop?.shop_name || "KÊNH NGƯỜI BÁN"}
            </span>
            <h1>Sản phẩm của tôi</h1>
            <p>Thêm sản phẩm, cập nhật thông tin và quản lý hiển thị.</p>
          </div>
          <button
            className="seller-outline-button"
            onClick={reload}
            disabled={busy}
          >
            Tải lại danh sách
          </button>
        </header>
        {error && (
          <p role="alert" className="seller-card seller-form-error">
            {error}
          </p>
        )}
        {notice && (
          <p role="status" className="seller-form-success">
            {notice}
          </p>
        )}
        {uncertain && (
          <p className="seller-card">
            Kết quả lưu chưa rõ. Tải lại danh sách và kiểm tra SKU trước khi tạo
            hoặc lưu lại.
          </p>
        )}
        {categories === null && (
          <p role="alert">
            Chưa tải được danh mục.{" "}
            <button onClick={() => window.location.reload()}>
              Tải lại trang
            </button>
          </p>
        )}
        {!page ? (
          !error && (
            <p role="status" className="seller-card">
              Đang tải danh sách sản phẩm…
            </p>
          )
        ) : (
          <>
            <form
              className="seller-product-filters seller-card"
              onSubmit={(e) => {
                e.preventDefault();
                if (busy) return;
                const data = new FormData(e.currentTarget);
                setPage(null);
                setError("");
                setSelection(null);
                setStockProduct(null);
                setImageProduct(null);
                setQuery({
                  q: String(data.get("q") || ""),
                  active: String(data.get("active") || ""),
                  page: 1,
                });
              }}
            >
              <label>
                Tên sản phẩm
                <input
                  name="q"
                  type="search"
                  maxLength={200}
                  defaultValue={query.q}
                />
              </label>
              <label>
                Hiển thị
                <select name="active" defaultValue={query.active}>
                  <option value="">Tất cả</option>
                  <option value="true">Đang bật</option>
                  <option value="false">Đã ẩn</option>
                </select>
              </label>
              <button className="seller-outline-button" disabled={busy}>
                Tìm kiếm
              </button>
              <button
                type="button"
                className="primary-button"
                disabled={busy || uncertain || !categories?.length}
                onClick={() => {
                  setSelection("new");
                  setStockProduct(null);
                  setImageProduct(null);
                  setConfirmHide(null);
                }}
              >
                Thêm sản phẩm
              </button>
            </form>
            {stockProduct && (
              <InventoryPanel
                key={stockProduct.product_id}
                productId={stockProduct.product_id}
                name={stockProduct.product_name}
                onClose={() => setStockProduct(null)}
                onSnapshot={(inventory) =>
                  setPage((value) =>
                    value
                      ? {
                          ...value,
                          items: value.items.map((item) =>
                            item.product_id === inventory.product_id
                              ? {
                                  ...item,
                                  available_quantity: inventory.quantity,
                                }
                              : item,
                          ),
                        }
                      : value,
                  )
                }
              />
            )}
            {imageProduct && shop && (
              <ProductImages
                key={imageProduct.product_id}
                productId={imageProduct.product_id}
                shopId={shop.shop_id}
                name={imageProduct.product_name}
                enabled={page.image_upload_enabled}
                onClose={() => setImageProduct(null)}
              />
            )}
            {selection && (
              <section className="seller-card">
                <h2>
                  {selection === "new"
                    ? "Thêm sản phẩm mới"
                    : "Chỉnh sửa sản phẩm"}
                </h2>
                <ProductForm
                  key={
                    selection === "new"
                      ? "new"
                      : `${selection.product_id}:${selection.updated_at}`
                  }
                  product={selection === "new" ? undefined : selection}
                  categories={categories || []}
                  disabled={busy || uncertain || !categories}
                  onSave={(input) =>
                    save(input, selection === "new" ? undefined : selection)
                  }
                  onCancel={() => setSelection(null)}
                />
              </section>
            )}
            {confirmHide && (
              <section className="seller-card" aria-labelledby="hide-title">
                <h2 id="hide-title">
                  {deleteMode ? "Xóa" : "Ẩn"} “{confirmHide.product_name}”?
                </h2>
                <p>
                  {deleteMode
                    ? "Xóa vĩnh viễn chỉ khi chưa có giỏ hàng, đơn hoặc lịch sử liên quan; nếu đã sử dụng hãy chọn Ẩn sản phẩm."
                    : "Sản phẩm sẽ ngừng hiển thị công khai. Hiện chưa hỗ trợ bật lại."}
                </p>
                <button
                  className="primary-button"
                  disabled={busy || uncertain}
                  onClick={() =>
                    void save(undefined, confirmHide, !deleteMode, deleteMode)
                  }
                >
                  {deleteMode ? "Xác nhận xóa sản phẩm" : "Xác nhận ẩn"}
                </button>{" "}
                <button
                  className="seller-outline-button"
                  disabled={busy}
                  onClick={() => setConfirmHide(null)}
                >
                  Giữ sản phẩm
                </button>
              </section>
            )}
            <section className="seller-card">
              <h2>
                Danh sách sản phẩm <small>({page.total})</small>
              </h2>
              {!page.items.length ? (
                <p>Không có sản phẩm trong trang hoặc bộ lọc này.</p>
              ) : (
                <ul className="seller-product-list">
                  {page.items.map((item) => (
                    <li key={item.product_id}>
                      <div>
                        <strong>{item.product_name}</strong>
                        <small>
                          SKU: {item.sku} · #{item.product_id}
                        </small>
                        <span>
                          {item.is_active ? "Đang bật" : "Đã ẩn"} · Tồn kho:{" "}
                          {item.available_quantity}
                        </span>
                        <span>{formatVnd(item.price)}</span>
                      </div>
                      <div>
                        <button
                          className="seller-outline-button"
                          disabled={busy || uncertain}
                          onClick={() => {
                            setSelection(item);
                            setStockProduct(null);
                            setImageProduct(null);
                            setConfirmHide(null);
                          }}
                        >
                          Chỉnh sửa
                        </button>
                        <button
                          className="seller-outline-button"
                          disabled={busy || uncertain}
                          onClick={() => {
                            setSelection(null);
                            setStockProduct(null);
                            setImageProduct(null);
                            setConfirmHide(null);
                            setStockProduct(item);
                          }}
                        >
                          Điều chỉnh tồn
                        </button>
                        <button
                          className="seller-outline-button"
                          disabled={busy || uncertain}
                          onClick={() => {
                            setSelection(null);
                            setStockProduct(null);
                            setImageProduct(null);
                            setConfirmHide(null);
                            setImageProduct(item);
                          }}
                        >
                          Quản lý ảnh
                        </button>
                        <button
                          className="seller-outline-button"
                          disabled={busy || uncertain}
                          onClick={() => {
                            setDeleteMode(true);
                            setConfirmHide(item);
                            setSelection(null);
                            setStockProduct(null);
                            setImageProduct(null);
                          }}
                        >
                          Xóa sản phẩm
                        </button>
                        {item.is_active && (
                          <button
                            className="seller-outline-button"
                            disabled={busy || uncertain}
                            onClick={() => {
                              setDeleteMode(false);
                              setConfirmHide(item);
                              setSelection(null);
                              setStockProduct(null);
                              setImageProduct(null);
                            }}
                          >
                            Ẩn sản phẩm
                          </button>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
              <nav
                className="seller-product-pagination"
                aria-label="Phân trang sản phẩm"
              >
                <button
                  disabled={busy || query.page === 1}
                  onClick={() => {
                    setPage(null);
                    setSelection(null);
                    setStockProduct(null);
                    setImageProduct(null);
                    setQuery((v) => ({ ...v, page: v.page - 1 }));
                  }}
                >
                  Trang trước
                </button>
                <span>Trang {page.page}</span>
                <button
                  disabled={busy || page.page * page.page_size >= page.total}
                  onClick={() => {
                    setPage(null);
                    setSelection(null);
                    setStockProduct(null);
                    setImageProduct(null);
                    setQuery((v) => ({ ...v, page: v.page + 1 }));
                  }}
                >
                  Trang sau
                </button>
              </nav>
            </section>
            <p>
              Sản phẩm chỉ xuất hiện công khai khi danh mục và toàn bộ danh mục
              cha còn hoạt động.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
function flatten(
  items: Category[],
  prefix = "",
): { id: string; label: string }[] {
  return items.flatMap((c) => [
    { id: c.category_id, label: prefix + c.category_name },
    ...flatten(c.children, prefix + "— "),
  ]);
}
function ProductForm({
  product,
  categories,
  disabled,
  onSave,
  onCancel,
}: {
  product?: SellerProduct;
  categories: Category[];
  disabled: boolean;
  onSave: (input: ProductInput) => Promise<void>;
  onCancel: () => void;
}) {
  const options = flatten(categories);
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    void onSave({
      product_name: String(data.get("product_name")),
      sku: String(data.get("sku")),
      category_id: String(data.get("category_id")),
      description: String(data.get("description") || "").trim() || null,
      price: String(data.get("price")),
      ...(!product
        ? { initial_quantity: Number(data.get("initial_quantity")) }
        : {}),
    });
  }
  return (
    <form onSubmit={submit} className="seller-shop-form">
      <fieldset disabled={disabled}>
        <legend className="sr-only">Thông tin sản phẩm</legend>
        <label>
          Tên sản phẩm
          <input
            name="product_name"
            required
            maxLength={200}
            defaultValue={product?.product_name}
          />
        </label>
        <label>
          SKU
          <input
            name="sku"
            required
            maxLength={64}
            defaultValue={product?.sku}
          />
        </label>
        <label htmlFor="seller-product-category">Danh mục</label>
        <select
          id="seller-product-category"
          name="category_id"
          required
          defaultValue={product?.category_id || ""}
        >
          <option value="" disabled>
            Chọn danh mục
          </option>
          {product && !options.some((o) => o.id === product.category_id) && (
            <option value={product.category_id} disabled>
              Danh mục cũ đã bị ẩn — chọn danh mục khác
            </option>
          )}
          {options.map((o) => (
            <option key={o.id} value={o.id}>
              {o.label}
            </option>
          ))}
        </select>
        <label>
          Mô tả
          <textarea
            name="description"
            maxLength={5000}
            rows={4}
            defaultValue={product?.description || ""}
          />
        </label>
        <label>
          Giá (VND)
          <input
            name="price"
            required
            inputMode="decimal"
            pattern="[0-9]{1,12}([.][0-9]{1,2})?"
            title="Giá không âm, tối đa 12 chữ số và 2 chữ số thập phân; dùng dấu chấm."
            defaultValue={product?.price}
          />
        </label>
        {!product && (
          <label>
            Tồn kho ban đầu
            <input
              name="initial_quantity"
              type="number"
              min={0}
              max={2147483647}
              step={1}
              required
              defaultValue={0}
            />
          </label>
        )}
        <div className="seller-form-actions">
          <button className="primary-button" disabled={disabled}>
            Lưu sản phẩm
          </button>
          <button
            className="seller-outline-button"
            type="button"
            disabled={disabled}
            onClick={onCancel}
          >
            Đóng
          </button>
        </div>
      </fieldset>
    </form>
  );
}
