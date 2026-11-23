"use client";
import Link from "next/link";
import { readCoupons, type SavedCoupon } from "@/lib/coupon-wallet";
import { buyNowReview, type BuyNow } from "@/lib/buy-now-client";
import { CommerceRestriction } from "@/components/auth/commerce-restriction";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { useSession } from "@/components/auth/session-provider";
import { fetchCart } from "@/lib/cart-client";
import { listAddresses } from "@/lib/address-client";
import type { CartData } from "@/lib/cart-contract";
import type { ShippingAddress } from "@/lib/address-contract";
import {
  CheckoutFailure,
  lookupCheckout,
  submitCheckout,
} from "@/lib/checkout-client";
import {
  checkoutBlock,
  checkoutKey,
  checkoutPayloadFrom,
  readIntent,
  saveIntent,
  clearIntent,
  orderStatuses,
  paymentLabels,
  type CheckoutIntent,
  type CheckoutOrder,
} from "@/lib/checkout-contract";
import { formatVnd } from "@/lib/categories";
import { quoteCoupon, type CouponQuote } from "@/lib/shopping-client";

import {
  fetchCheckoutOptions,
  type CheckoutOptions,
  type QuotedChoices,
} from "@/lib/checkout-options-client";
import { CheckoutChoices } from "@/components/checkout/checkout-choices";
import { PaymentNotice } from "@/components/checkout/payment-notice";
type Review = {
  cart: CartData;
  addresses: ShippingAddress[];
  options: CheckoutOptions;
};
async function loadReview(buyNow?: BuyNow, selectedProducts?: string[]): Promise<Review> {
  const [cart, addresses, options] = await Promise.all([
    buyNow ? buyNowReview(buyNow) : fetchCart(),
    listAddresses(),
    fetchCheckoutOptions(),
  ]);
  if (selectedProducts) {
    const shops = cart.shops.map(shop => ({...shop,items:shop.items.filter(item => selectedProducts.includes(item.product_id))})).filter(shop => shop.items.length);
    if (shops.flatMap(shop=>shop.items).length !== selectedProducts.length) throw new Error("Sản phẩm đã chọn đã thay đổi. Vui lòng quay lại giỏ hàng.");
    const total = (values: string[]) => {
      const amount = values.reduce((sum,value)=>{const [w,f=""]=value.split(".");return sum+BigInt(w)*BigInt(100)+BigInt(f.padEnd(2,"0"));},BigInt(0));
      return `${amount/BigInt(100)}.${String(amount%BigInt(100)).padStart(2,"0")}`;
    };
    for (const shop of shops) shop.subtotal=total(shop.items.map(item=>item.line_total));
    return {cart:{shops,total_amount:total(shops.map(shop=>shop.subtotal))},addresses,options};
  }
  return { cart, addresses, options };
}
const initialAddress = (addresses: ShippingAddress[], preferred = "") =>
  addresses.find((a) => a.address_id === preferred)?.address_id ||
  addresses.find((a) => a.is_default)?.address_id ||
  addresses[0]?.address_id ||
  "";

export function CheckoutPanel({buyNow, selectedProducts}: {buyNow?: BuyNow; selectedProducts?: string[]}) {
  const target = buyNow ? `/thanh-toan?product=${buyNow.product}&quantity=${buyNow.quantity}` : selectedProducts ? `/thanh-toan?selected=${selectedProducts.join(",")}` : "/thanh-toan";
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
        <h1>Thanh toán</h1>
        <p role={error ? "alert" : "status"}>
          {error || "Vui lòng đăng nhập để chọn địa chỉ và đặt hàng."}
        </p>
        <Link
          className="primary-button"
          href={`/dang-nhap?returnTo=${encodeURIComponent(target)}`}
        >
          Đăng nhập để thanh toán
        </Link>
      </section>
    );
  if (account.user_role === "ADMIN") return <CommerceRestriction />;
  return <CheckoutFlow key={`${account.user_id}:${buyNow?.product}:${buyNow?.quantity}:${selectedProducts?.join(",")}`} userId={account.user_id} buyNow={buyNow} selectedProducts={selectedProducts} />;
}

function CheckoutFlow({ userId, buyNow, selectedProducts }: { userId: string; buyNow?: BuyNow; selectedProducts?: string[] }) {
  const checkoutReturn = buyNow ? `/thanh-toan?product=${buyNow.product}&quantity=${buyNow.quantity}` : selectedProducts ? `/thanh-toan?selected=${selectedProducts.join(",")}` : "/thanh-toan";
  const addressHref = `/tai-khoan/dia-chi?returnTo=${encodeURIComponent(checkoutReturn)}`;
  const [savedCoupons,setSavedCoupons] = useState<SavedCoupon[]>([]);
  useEffect(()=>{let active=true;Promise.resolve().then(()=>{try{const codes=readCoupons(localStorage,userId);if(active)setSavedCoupons(codes);}catch{}});return()=>{active=false;};},[userId]);
  const [phase, setPhase] = useState<
    "loading" | "review" | "recovery" | "success" | "blocked"
  >("loading");
  const [review, setReview] = useState<Review | null>(null);
  const [selected, setSelected] = useState("");
  const [intent, setIntent] = useState<CheckoutIntent | null>(null);
  const [order, setOrder] = useState<CheckoutOrder | null>(null);
  const [replayed, setReplayed] = useState(false);
  const [error, setError] = useState("");
  const [previousOrderId, setPreviousOrderId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [choices, setChoices] = useState<QuotedChoices | null>(null);
  const [couponCode, setCouponCode] = useState("");
  const [coupon, setCoupon] = useState<CouponQuote | null>(null);
  const [couponBusy, setCouponBusy] = useState(false);
  const couponGuard = useRef(false);
  const guard = useRef(false),
    alertRef = useRef<HTMLParagraphElement>(null),
    mounted = useRef(true),
    generation = useRef(0);

  useEffect(() => {
    let active = true;
    mounted.current = true;
    void Promise.resolve()
      .then(() => {
        try {
          return readIntent(sessionStorage, userId);
        } catch {
          throw new Error(
            "Không đọc được yêu cầu lưu trong phiên. Chưa thể xác minh đơn trước đó; vui lòng không tạo lại đơn bằng một yêu cầu khác.",
          );
        }
      })
      .then(async (saved) => {
        if (!active) return;
        if (saved) {
          setIntent(saved);
          const previous = await lookupCheckout(saved.key);
          if (!previous) {
            if ((saved.payload.purchase_mode === "SELECTED_CART") !== !!selectedProducts || (selectedProducts && saved.payload.items.map(i=>i.product_id).sort().join(",") !== [...selectedProducts].sort().join(","))) throw new Error("Có yêu cầu thanh toán khác chưa xác nhận. Vui lòng quay lại giỏ hàng trước để kiểm tra.");
            if (saved && (saved.payload.purchase_mode === "BUY_NOW") !== !!buyNow) throw new Error("Có yêu cầu đặt hàng chưa xác nhận. Hãy quay lại luồng thanh toán trước để kiểm tra.");
            if (saved && buyNow && (saved.payload.items[0].product_id !== buyNow.product || saved.payload.items[0].quantity !== buyNow.quantity)) throw new Error("Có yêu cầu mua ngay khác chưa xác nhận. Hãy quay lại sản phẩm trước để kiểm tra.");
          }
          if (!active) return;
          if (previous) {
            clearIntent(sessionStorage, userId);
            setIntent(null);
            setPreviousOrderId(previous.order_id);
            window.dispatchEvent(new Event("coco:cart-changed"));
          }
        }
        const data = await loadReview(buyNow, selectedProducts);
        if (active) {
          setReview(data);
          setSelected(initialAddress(data.addresses));
          setPhase("review");
        }
      })
      .catch((failure) => {
        if (active) {
          setError(
            failure instanceof Error
              ? failure.message
              : "Không tải được thông tin thanh toán.",
          );
          setPhase("blocked");
        }
      });
    return () => {
      active = false;
      mounted.current = false;
    };
  }, [userId, buyNow, selectedProducts]);
  useEffect(() => {
    if (error) alertRef.current?.focus();
  }, [error]);

  async function refreshReview(retained: CheckoutIntent | null = intent) {
    if (guard.current) return;
    const current = ++generation.current;
    setPhase("loading");
    setError("");
    setCoupon(null);
    setChoices(null);
    try {
      const data = await loadReview(buyNow, selectedProducts);
      if (!mounted.current || current !== generation.current) return;
      setReview(data);
      setSelected(
        initialAddress(
          data.addresses,
          retained?.payload.address_id || selected,
        ),
      );
      setPhase("review");
    } catch (failure) {
      if (!mounted.current || current !== generation.current) return;
      setError(
        failure instanceof Error
          ? failure.message
          : "Không tải được thông tin thanh toán.",
      );
      setPhase(retained ? "recovery" : "blocked");
    }
  }
  async function place(pending: CheckoutIntent) {
    if (guard.current) return;
    guard.current = true;
    setBusy(true);
    setError("");
    try {
      try {
        saveIntent(sessionStorage, pending);
      } catch {
        setError(
          "Trình duyệt chưa lưu được yêu cầu trong phiên. Lần gửi này chưa được thực hiện. Hãy cho phép session storage rồi thử lại.",
        );
        return;
      }
      setIntent(pending);
      try {
        const result = await submitCheckout(pending);
        // Creation is confirmed even while the seller has not confirmed fulfillment.
        // Keep the intent only for an unknown HTTP outcome, never for a pending shop order.
        try {
          clearIntent(sessionStorage, userId);
        } catch {
          // Recovery can safely replay this key if browser storage is unavailable.
        }
        setIntent(null);
        window.dispatchEvent(new Event("coco:cart-changed"));
        if (mounted.current) {
          setOrder(result.order);
          setReplayed(result.replayed);
          setPhase("success");
        }
      } catch (failure) {
        if (mounted.current) {
          setError(
            failure instanceof Error
              ? failure.message
              : "Chưa xác nhận được kết quả đặt hàng.",
          );
          setPhase(
            failure instanceof CheckoutFailure &&
              failure.repairAllowed &&
              review
              ? "review"
              : "recovery",
          );
        }
      }
    } finally {
      guard.current = false;
      if (mounted.current) setBusy(false);
    }
  }
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (
      !review ||
      guard.current ||
      couponGuard.current ||
      checkoutBlock(review.cart) ||
      (review.options.enabled && !choices)
    )
      return;
    const payload = checkoutPayloadFrom({
      ...(buyNow ? {purchase_mode:"BUY_NOW"} : selectedProducts ? {purchase_mode:"SELECTED_CART"} : {}),
      address_id: selected,
      payment_method: choices?.selection.payment_method || "COD",
      ...(choices
        ? {
            shipping_method: choices.selection.shipping_method,
            shop_coupons: choices.selection.shop_coupons,
            coco_coupon_code: choices.selection.coco_coupon_code,
            shipping_coupon_code: choices.selection.shipping_coupon_code,
            expected_coupon_discount: choices.quote.discount_amount,
            expected_shipping_fee: choices.quote.shipping_fee,
            expected_shipping_discount: choices.quote.shipping_discount_amount,
          }
        : {}),
      ...(coupon
        ? {
            coupon_code: coupon.code,
            expected_coupon_discount: coupon.discount_amount,
          }
        : {}),
      items: review.cart.shops.flatMap((shop) =>
        shop.items.map((item) => ({
          product_id: item.product_id,
          quantity: item.quantity,
          expected_unit_price: item.unit_price,
        })),
      ),
    });
    if (!payload) {
      setError("Vui lòng chọn địa chỉ hợp lệ và kiểm tra giới hạn giỏ hàng.");
      return;
    }
    try {
      void place({
        version: 1,
        user_id: userId,
        key: intent?.key || checkoutKey(),
        payload,
      });
    } catch {
      setError(
        "Không tạo được mã yêu cầu an toàn. Chưa gửi đơn hàng; vui lòng thử lại trên trình duyệt hỗ trợ HTTPS hoặc localhost.",
      );
    }
  }
  async function newPurchase() {
    if (phase !== "success" || guard.current) return;
    try {
      clearIntent(sessionStorage, userId);
    } catch {
      setError(
        "Chưa xóa được yêu cầu đã xác nhận. Vui lòng tải lại trước khi bắt đầu lượt mới.",
      );
      return;
    }
    setIntent(null);
    setOrder(null);
    setPreviousOrderId(null);
    await refreshReview(null);
  }
  async function applyCoupon() {
    if (couponGuard.current || guard.current || !couponCode.trim()) return;
    couponGuard.current = true;
    setCouponBusy(true);
    setError("");
    setCoupon(null);
    try {
      const direct = buyNow && review?.cart.shops[0]?.items[0];
      const result = await quoteCoupon(couponCode.trim(), direct ? {product_id:direct.product_id, quantity:direct.quantity, expected_unit_price:direct.unit_price} : undefined, selectedProducts);
      if (!mounted.current) return;
      if (!review || result.subtotal !== review.cart.total_amount) {
        setError("Giỏ hàng đã thay đổi. Hãy tải lại thông tin thanh toán.");
        return;
      }
      setCoupon(result);
    } catch (failure) {
      if (mounted.current)
        setError(
          failure instanceof Error ? failure.message : "Chưa áp dụng được mã.",
        );
    } finally {
      couponGuard.current = false;
      if (mounted.current) setCouponBusy(false);
    }
  }
  const block = review ? checkoutBlock(review.cart) : null;
  return (
    <div className="shell order-layout-page checkout-page">
      <nav className="resource-breadcrumb" aria-label="Đường dẫn">
        <Link href="/">Trang chủ</Link>
        <span>›</span>
        <Link href="/gio-hang">Giỏ hàng</Link>
        <span>›</span>
        <span>Thanh toán</span>
      </nav>
      <div className="checkout-heading">
        <span className="auth-step">HOÀN TẤT MUA SẮM CÙNG COCO</span>
        <h1>Thanh toán</h1>
        <p>Kiểm tra người nhận và sản phẩm trước khi đặt hàng.</p>
      </div>
      {error && (
        <p className="cart-error" role="alert" tabIndex={-1} ref={alertRef}>
          {error}
        </p>
      )}
      {phase === "loading" && (
        <div className="cart-loading" role="status">
          Đang tải thông tin thanh toán…
        </div>
      )}
      {phase === "blocked" && (
        <section className="order-panel">
          <h2>Chưa thể mở thanh toán</h2>
          <p>Vui lòng kiểm tra kết nối hoặc đăng nhập lại để tiếp tục.</p>
          <div className="checkout-links">
            <Link
              href="/thanh-toan"
              onClick={(event) => {
                event.preventDefault();
                window.location.reload();
              }}
            >
              Tải lại trang
            </Link>
            <Link href={`/dang-nhap?returnTo=${encodeURIComponent(checkoutReturn)}`}>Đăng nhập lại</Link>
            <Link href="/gio-hang">Về giỏ hàng</Link>
          </div>
        </section>
      )}
      {phase === "recovery" && (
        <section className="order-panel">
          <h2>Chưa kiểm tra được đơn hàng</h2>
          <p>Vui lòng kiểm tra lại kết quả đặt hàng trước khi tiếp tục.</p>
          <div className="checkout-links">
            <button
              type="button"
              className="primary-button"
              disabled={busy}
              onClick={() => window.location.reload()}
            >
              Kiểm tra lại
            </button>
            <Link href="/tai-khoan/don-hang">Xem đơn mua</Link>
          </div>
        </section>
      )}
      {phase === "review" && previousOrderId && (
        <p role="status">
          Đơn{" "}
          <Link href={`/tai-khoan/don-hang/${previousOrderId}`}>
            #{previousOrderId}
          </Link>{" "}
          đã được ghi nhận. Bạn có thể tiếp tục mua sắm.
        </p>
      )}
      {phase === "success" && order && (
        <OrderConfirmation
          order={order}
          replayed={replayed}
          onNew={() => void newPurchase()}
        />
      )}
      {phase === "review" &&
        review &&
        (review.cart.shops.length === 0 ? (
          <section className="order-panel cart-empty">
            <h2>Giỏ hàng đang trống</h2>
            <p>Thêm sản phẩm vào giỏ trước khi thanh toán.</p>
            <Link className="primary-button" href="/san-pham">
              Khám phá sản phẩm →
            </Link>
          </section>
        ) : (
          <form
            className="checkout-form order-layout-grid"
            onSubmit={submit}
            aria-busy={busy}
          >
            <fieldset disabled={busy} className="checkout-main">
              <section className="order-panel">
                <div className="checkout-section-heading">
                  <h2>Địa chỉ giao hàng</h2>
                  <Link href={addressHref}>Quản lý địa chỉ ↗</Link>
                </div>
                {review.addresses.length ? (
                  <div
                    className="checkout-addresses"
                    role="radiogroup"
                    aria-label="Chọn địa chỉ giao hàng"
                  >
                    {review.addresses.map((address) => (
                      <label
                        className={`checkout-address ${selected === address.address_id ? "checkout-address-selected" : ""}`}
                        key={address.address_id}
                      >
                        <input
                          type="radio"
                          name="address"
                          required
                          value={address.address_id}
                          checked={selected === address.address_id}
                          onChange={() => setSelected(address.address_id)}
                        />
                        <span>
                          <strong>{address.recipient_name}</strong>
                          <span>{address.phone}</span>
                          <span>
                            {[
                              address.address_line,
                              address.ward,
                              address.district,
                              address.city,
                            ]
                              .filter(Boolean)
                              .join(", ")}
                          </span>
                          {address.is_default && <small>Mặc định</small>}
                        </span>
                      </label>
                    ))}
                  </div>
                ) : (
                  <div className="checkout-no-address">
                    <p>Bạn chưa có địa chỉ giao hàng.</p>
                    <Link className="primary-button" href={addressHref}>
                      Thêm địa chỉ giao hàng →
                    </Link>
                  </div>
                )}
              </section>
              {review.options.enabled ? (
                <CheckoutChoices
                  options={review.options}
                  cart={review.cart}
                  directItem={buyNow ? {
                    product_id: review.cart.shops[0].items[0].product_id,
                    quantity: review.cart.shops[0].items[0].quantity,
                    expected_unit_price: review.cart.shops[0].items[0].unit_price,
                  } : undefined}
                  selectedProducts={selectedProducts}
                  disabled={busy}
                  onChange={setChoices}
                />
              ) : (
                <section className="order-panel">
                  <h2>Phương thức thanh toán</h2>
                  <label className="checkout-cod">
                    <input
                      type="radio"
                      name="payment"
                      value="COD"
                      checked
                      readOnly
                    />
                    <span>
                      <strong>Thanh toán khi nhận hàng (COD)</strong>
                      <span>
                        COD mô phỏng · Chưa tích hợp thanh toán tiền thật.
                      </span>
                    </span>
                  </label>
                  <p>
                    Thanh toán khi nhận hàng. Phí vận chuyển hiện là 0đ; mã giảm
                    giá chỉ áp dụng trên hàng hóa đủ điều kiện.
                  </p>
                </section>
              )}
              <button
                type="button"
                className="account-retry"
                onClick={() => void refreshReview()}
              >
                Tải lại thông tin thanh toán
              </button>
              <Link href="/gio-hang" className="coco-outline-link">
                ← Sửa giỏ hàng
              </Link>
            </fieldset>
            <aside className="order-panel checkout-summary">
              <h2>Kiểm tra đơn hàng</h2>
              {review.cart.shops.map((shop) => (
                <section className="checkout-shop" key={shop.shop_id}>
                  <h3>{shop.shop_name}</h3>
                  <ul>
                    {shop.items.map((item) => (
                      <li key={item.cart_item_id}>
                        <div>
                          <span>{item.product_name}</span>
                          <small>
                            {formatVnd(item.unit_price)} × {item.quantity}
                          </small>
                          {!item.is_available && (
                            <strong className="cart-warning">
                              Chưa đủ điều kiện mua
                            </strong>
                          )}
                        </div>
                        <strong>{formatVnd(item.line_total)}</strong>
                      </li>
                    ))}
                  </ul>
                  <p>
                    Tạm tính shop <strong>{formatVnd(shop.subtotal)}</strong>
                  </p>
                </section>
              ))}
              <div className="order-total">
                <strong>
                  {choices ? "Tổng thanh toán" : "Tổng tiền sản phẩm"}
                </strong>
                <span>
                  {formatVnd(
                    choices?.quote.total_amount || review.cart.total_amount,
                  )}
                </span>
              </div>
              {!review.options.enabled && (
                <div className="coupon-entry">
                  {savedCoupons.length>0 && <label>Mã đã lưu<select aria-label="Chọn mã đã lưu" value={savedCoupons.some(c=>c.code===couponCode)?couponCode:""} onChange={event=>{setCouponCode(event.target.value);setCoupon(null);}} disabled={busy || couponBusy}><option value="">Chọn mã</option>{savedCoupons.map(c=><option value={c.code} key={c.code}>{c.code}</option>)}</select></label>}
                  <label htmlFor="coupon-code">Mã giảm giá (tối đa 1 mã)</label>
                  <div>
                    <input
                      id="coupon-code"
                      value={couponCode}
                      maxLength={50}
                      disabled={busy || couponBusy}
                      onChange={(e) => {
                        setCouponCode(e.target.value);
                        setCoupon(null);
                      }}
                      placeholder="Nhập mã giảm giá"
                    />
                    <button
                      type="button"
                      className="secondary-button"
                      disabled={busy || couponBusy || !couponCode.trim()}
                      onClick={() => void applyCoupon()}
                    >
                      {couponBusy ? "Đang kiểm tra…" : "Áp dụng"}
                    </button>
                  </div>
                  {coupon && (
                    <div role="status">
                      <p>
                        Mã {coupon.code}: giảm{" "}
                        {formatVnd(coupon.discount_amount)}
                      </p>
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => {
                          setCoupon(null);
                          setCouponCode("");
                        }}
                      >
                        Bỏ mã
                      </button>
                      <p>
                        <strong>
                          Cần thanh toán: {formatVnd(coupon.total_amount)}
                        </strong>
                      </p>
                    </div>
                  )}
                  <small>Mã được kiểm tra lại khi đặt hàng thành công.</small>
                </div>
              )}
              <p>
                Server kiểm tra lại giá và tồn kho khi xác nhận. Đơn được tách
                theo từng gian hàng.
              </p>
              {block && (
                <p className="cart-warning" role="status">
                  {block}
                </p>
              )}
              <button
                className="order-submit"
                type="submit"
                disabled={
                  busy ||
                  couponBusy ||
                  (review.options.enabled && !choices) ||
                  Boolean(block) ||
                  !review.addresses.some(
                    (address) => address.address_id === selected,
                  )
                }
              >
                {busy
                  ? "Đang đặt hàng…"
                  : choices?.selection.payment_method &&
                      choices.selection.payment_method !== "COD"
                    ? "Đặt hàng và chuyển khoản"
                    : "Đặt hàng COD"}
              </button>
              <p className="checkout-submit-note">
                Nhấn đặt hàng sẽ lưu đơn, kiểm tra ưu đãi và giữ tồn kho. Đơn
                trả trước chưa được coi là đã thanh toán.
              </p>
            </aside>
          </form>
        ))}
    </div>
  );
}

function OrderConfirmation({
  order,
  replayed,
  onNew,
}: {
  order: CheckoutOrder;
  replayed: boolean;
  onNew: () => void;
}) {
  return (
    <section
      className="checkout-confirmation"
      aria-labelledby="checkout-success-title"
    >
      <div className="checkout-success-banner">
        <span aria-hidden="true">✓</span>
        <div>
          <h2 id="checkout-success-title">Đơn hàng đã được ghi nhận</h2>
          <Link href={`/tai-khoan/don-hang/${order.order_id}`}>
            Theo dõi đơn hàng →
          </Link>
          <p>
            {replayed
              ? "Đã xác minh đơn có sẵn. Yêu cầu gửi lại không tạo thêm đơn."
              : "Cảm ơn bạn đã mua sắm cùng coco."}
          </p>
        </div>
      </div>
      <div className="order-layout-grid">
        <div className="checkout-main">
          <section className="order-panel">
            <h3>Thông tin đơn hàng</h3>
            <dl className="checkout-order-details">
              <div>
                <dt>Mã đơn</dt>
                <dd>#{order.order_id}</dd>
              </div>
              <div>
                <dt>Ngày tạo</dt>
                <dd>
                  {new Intl.DateTimeFormat("vi-VN", {
                    dateStyle: "medium",
                    timeStyle: "short",
                  }).format(new Date(order.created_at))}
                </dd>
              </div>
              <div>
                <dt>Phương thức</dt>
                <dd>{paymentLabels[order.payment_method]}</dd>
              </div>
            </dl>
          </section>
          <section className="order-panel">
            <h3>Người nhận</h3>
            <p>
              <strong>{order.recipient_name}</strong> · {order.phone}
            </p>
            <p>{order.shipping_address}</p>
          </section>
        </div>
        <div className="order-panel checkout-summary">
          <h3>Sản phẩm trong đơn</h3>
          {order.shop_orders.map((shop) => (
            <section key={shop.shop_order_id} className="checkout-shop">
              <h4>
                {shop.shop_name}{" "}
                <span className="checkout-shop-status">
                  {orderStatuses[shop.order_status]}
                </span>
              </h4>
              <ul>
                {shop.items.map((item) => (
                  <li key={item.order_item_id}>
                    <div>
                      <span>{item.product_name}</span>
                      <small>
                        {formatVnd(item.unit_price)} × {item.quantity}
                      </small>
                    </div>
                    <strong>{formatVnd(item.line_total)}</strong>
                  </li>
                ))}
              </ul>
              <p>
                Tổng đơn shop <strong>{formatVnd(shop.subtotal)}</strong>
              </p>
            </section>
          ))}
          <div className="order-total">
            <strong>Tổng thanh toán</strong>
            <span>{formatVnd(order.total_amount)}</span>
          </div>
          {order.discount_amount && (
            <p>Đã giảm: {formatVnd(order.discount_amount)}</p>
          )}
          {order.shipping_discount_amount && (
            <p>Đã giảm cước: {formatVnd(order.shipping_discount_amount)}</p>
          )}
          <PaymentNotice
            orderId={order.order_id}
            method={order.payment_method}
            status={order.payment_status}
          />
          {order.shipping_fee && (
            <p>Phí vận chuyển: {formatVnd(order.shipping_fee)}</p>
          )}
        </div>
      </div>
      <div className="checkout-success-actions">
        <Link href="/san-pham" className="primary-button">
          Tiếp tục mua sắm →
        </Link>
        <button className="coco-outline-link" onClick={onNew}>
          Bắt đầu lượt thanh toán mới
        </button>
      </div>
      <p className="auth-field-hint">
        Đơn đã được lưu. Bạn có thể tiếp tục đặt sản phẩm khác ngay cả khi đơn
        này đang chờ shop xác nhận.
      </p>
    </section>
  );
}
