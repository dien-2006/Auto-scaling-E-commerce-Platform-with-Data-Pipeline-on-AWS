"use client";
import Link from "next/link";
import { CommerceRestriction } from "@/components/auth/commerce-restriction";
import Image from "next/image";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { useSession } from "@/components/auth/session-provider";
import { useCart } from "@/components/cart/use-cart";
import { changeCart } from "@/lib/cart-client";
import { cartReasons, type CartItem } from "@/lib/cart-contract";
import { formatVnd } from "@/lib/categories";
export function CartPanel() {
  const { account, loading, error } = useSession();
  if (loading && !account)
    return (
      <div className="shell account-page" role="status">
        Đang kiểm tra phiên đăng nhập…
      </div>
    );
  if (!account)
    return (
      <section className="shell account-page">
        <h1>Giỏ hàng của bạn</h1>
        <p role={error ? "alert" : "status"}>
          {error || "Đăng nhập để xem giỏ hàng và mua sắm từ nhiều shop."}
        </p>
        <Link className="primary-button" href="/dang-nhap?returnTo=%2Fgio-hang">
          Đăng nhập để xem giỏ
        </Link>
      </section>
    );
  if (account.user_role === "ADMIN") return <CommerceRestriction />;
  return <CartBook key={account.user_id} />;
}
function CartBook() {
  const [excluded, setExcluded] = useState<string[]>([]);
  const { cart, loading, error, reload } = useCart();
  const [busy, setBusy] = useState(false),
    [mutationError, setMutationError] = useState(""),
    [notice, setNotice] = useState("");
  const guard = useRef(false),
    alertRef = useRef<HTMLParagraphElement>(null);
  const message = mutationError || error;
  useEffect(() => {
    if (message) alertRef.current?.focus();
  }, [message]);
  async function mutate(
    method: "PATCH" | "DELETE",
    id: string,
    quantity?: number,
  ) {
    if (guard.current) return;
    guard.current = true;
    setBusy(true);
    setMutationError("");
    setNotice("");
    try {
      await changeCart(method, id, quantity);
      setNotice(
        method === "DELETE"
          ? "Đã xóa sản phẩm khỏi giỏ."
          : "Đã cập nhật số lượng.",
      );
    } catch (e) {
      setMutationError(
        `${e instanceof Error ? e.message : "Chưa xác nhận được thay đổi."} Hãy tải lại giỏ trước khi thử lại nếu kết nối bị gián đoạn.`,
      );
    } finally {
      guard.current = false;
      setBusy(false);
    }
  }
  const rows = cart?.shops.flatMap((shop) => shop.items) || [];
  const chosen = rows.filter(item => item.is_available && !excluded.includes(item.product_id));
  const amount = chosen.reduce((sum,item) => {const [w,f=""]=item.line_total.split(".");return sum+BigInt(w)*BigInt(100)+BigInt(f.padEnd(2,"0"));},BigInt(0));
  const chosenTotal = `${amount/BigInt(100)}.${String(amount%BigInt(100)).padStart(2,"0")}`;
  return (
    <div className="shell order-layout-page live-cart-page">
      <nav className="resource-breadcrumb" aria-label="Đường dẫn">
        <Link href="/">Trang chủ</Link>
        <span>›</span>
        <span>Giỏ hàng</span>
      </nav>
      <div className="live-cart-heading">
        <div>
          <span className="auth-step">MUA SẮM CÙNG COCO</span>
          <h1>Giỏ hàng của bạn</h1>
          <p>Sản phẩm được nhóm theo từng gian hàng.</p>
        </div>
        <Link href="/san-pham" className="coco-outline-link">
          ← Tiếp tục mua sắm
        </Link>
      </div>
      {message && (
        <p role="alert" tabIndex={-1} ref={alertRef} className="cart-error">
          {message}
        </p>
      )}
      {notice && (
        <p role="status" className="cart-notice">
          {notice}
        </p>
      )}
      <button
        className="account-retry"
        disabled={busy || loading}
        onClick={() => {
          setMutationError("");
          setNotice("");
          reload();
        }}
      >
        Tải lại giỏ hàng
      </button>
      {loading ? (
        <div className="cart-loading" role="status">
          Đang tải giá, tồn kho và giỏ hàng…
        </div>
      ) : !cart ? (
        <section className="order-panel">
          <h2>Chưa tải được giỏ hàng</h2>
          <p>
            Vui lòng thử tải lại. Nếu phiên hết hạn, hãy{" "}
            <Link href="/dang-nhap?returnTo=%2Fgio-hang">đăng nhập lại</Link>.
          </p>
        </section>
      ) : rows.length === 0 ? (
        <section className="order-panel cart-empty">
          <div aria-hidden="true">🛍</div>
          <h2>Giỏ hàng của bạn đang trống</h2>
          <p>Khám phá sáu danh mục chăm sóc sức khỏe và làm đẹp tại coco.</p>
          <Link className="primary-button" href="/san-pham">
            Khám phá sản phẩm →
          </Link>
        </section>
      ) : (
        <div className="order-layout-grid">
          <div className="live-cart-shops">
            <label className="cart-select-all"><input type="checkbox" checked={chosen.length>0 && chosen.length===rows.filter(i=>i.is_available).length} disabled={busy || loading} onChange={event=>setExcluded(event.target.checked?[]:rows.map(i=>i.product_id))} />Chọn tất cả</label>
            {cart.shops.map((shop) => (
              <section
                className="order-panel cart-shop"
                key={shop.shop_id}
                aria-label={`Gian hàng ${shop.shop_name}`}
              >
                <div className="cart-shop-heading">
                  <h2>
                    <Link
                      href={`/gian-hang/${encodeURIComponent(shop.shop_slug)}`}
                    >
                      {shop.shop_name} ↗
                    </Link>
                  </h2>
                  <span>{shop.items.length} sản phẩm</span>
                </div>
                <ul>
                  {shop.items.map((item) => (
                    <CartRow
                      key={`${item.cart_item_id}:${item.quantity}`}
                      item={item}
                      checked={chosen.some(i=>i.product_id===item.product_id)}
                      onSelect={checked=>setExcluded(old=>checked?old.filter(id=>id!==item.product_id):[...old,item.product_id])}
                      disabled={busy || loading}
                      onUpdate={(quantity) =>
                        void mutate("PATCH", item.cart_item_id, quantity)
                      }
                      onDelete={() => void mutate("DELETE", item.cart_item_id)}
                    />
                  ))}
                </ul>
                <p className="cart-shop-subtotal">
                  Tạm tính gian hàng <strong>{formatVnd(shop.subtotal)}</strong>
                </p>
              </section>
            ))}
          </div>
          <aside className="order-panel order-summary">
            <h2>Tóm tắt giỏ hàng</h2>
            <dl>
              <div>
                <dt>Sản phẩm</dt>
                <dd>{chosen.length}</dd>
              </div>
              <div>
                <dt>Gian hàng</dt>
                <dd>{cart.shops.filter(shop=>shop.items.some(item=>chosen.includes(item))).length}</dd>
              </div>
            </dl>
            <div className="order-total">
              <strong>Tạm tính</strong>
              <span>{formatVnd(chosenTotal)}</span>
            </div>
            {rows.some((item) => !item.is_available) && (
              <p className="cart-warning">
                Có sản phẩm chưa thể mua. Hãy kiểm tra thông báo ở từng dòng.
              </p>
            )}
            {chosen.length>0 ? <Link href={`/thanh-toan?selected=${chosen.map(i=>i.product_id).join(",")}`} className="order-submit">Thanh toán ({chosen.length}) →</Link> : <button className="order-submit" disabled>Chọn sản phẩm để thanh toán</button>}
            <Link href="/tai-khoan/dia-chi" className="order-help">
              Quản lý địa chỉ giao hàng →
            </Link>
          </aside>
        </div>
      )}
    </div>
  );
}
function CartRow({
  checked, onSelect,
  item,
  disabled,
  onUpdate,
  onDelete,
}: {
  checked: boolean;
  onSelect: (checked:boolean)=>void;
  item: CartItem;
  disabled: boolean;
  onUpdate: (quantity: number) => void;
  onDelete: () => void;
}) {
  const [quantity, setQuantity] = useState(String(item.quantity));
  const [confirm, setConfirm] = useState(false),
    [imageFailed, setImageFailed] = useState(false);
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onUpdate(Number(quantity));
  }
  return (
    <li
      className={`cart-line ${item.is_available ? "" : "cart-line-unavailable"}`}
    >
      <input className="cart-item-checkbox" type="checkbox" aria-label={`Chọn ${item.product_name}`} checked={checked} onChange={event=>onSelect(event.target.checked)} disabled={disabled || !item.is_available} />
      <div className="cart-line-image">
        {item.primary_image_url && !imageFailed ? (
          <Image
            unoptimized
            width={100}
            height={100}
            src={item.primary_image_url}
            alt={item.product_name}
            onError={() => setImageFailed(true)}
          />
        ) : (
          <span>
            Chưa có
            <br />
            hình ảnh
          </span>
        )}
      </div>
      <div className="cart-line-product">
        <h3>
          <Link href={`/san-pham/${item.product_id}`}>{item.product_name}</Link>
        </h3>
        <p>
          Đơn giá: <strong>{formatVnd(item.unit_price)}</strong>
        </p>
        <p>
          Tồn kho hiện tại:{" "}
          {new Intl.NumberFormat("vi-VN").format(item.available_quantity)}
        </p>
        {item.unavailable_reason && (
          <p className="cart-warning">{cartReasons[item.unavailable_reason]}</p>
        )}
      </div>
      <form className="cart-quantity-form" onSubmit={submit}>
        <label htmlFor={`cart-item-${item.cart_item_id}`}>
          Số lượng<span className="sr-only"> của {item.product_name}</span>
        </label>
        <input
          id={`cart-item-${item.cart_item_id}`}
          type="number"
          min="1"
          max="2147483647"
          step="1"
          required
          value={quantity}
          disabled={disabled}
          onChange={(event) => setQuantity(event.target.value)}
        />
        <button
          type="submit"
          disabled={disabled || Number(quantity) === item.quantity}
        >
          Cập nhật
        </button>
      </form>
      <div className="cart-line-total">
        <strong>{formatVnd(item.line_total)}</strong>
        <button
          className="cart-remove"
          disabled={disabled}
          onClick={() => setConfirm(true)}
        >
          Xóa<span className="sr-only"> {item.product_name}</span>
        </button>
      </div>
      {confirm && (
        <div
          className="cart-delete-confirm"
          role="group"
          aria-label={`Xác nhận xóa ${item.product_name}`}
        >
          <p>Xóa sản phẩm này khỏi giỏ?</p>
          <button disabled={disabled} onClick={onDelete}>
            Xác nhận xóa
          </button>
          <button disabled={disabled} onClick={() => setConfirm(false)}>
            Giữ lại
          </button>
        </div>
      )}
    </li>
  );
}
