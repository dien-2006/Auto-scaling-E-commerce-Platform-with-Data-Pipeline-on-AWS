"use client";
import { useRef, useState } from "react";
import type { CartData } from "@/lib/cart-contract";
import { formatVnd } from "@/lib/categories";
import {
  quoteChoices,
  type CheckoutOptions,
  type QuotedChoices,
  type OptionsSelection,
} from "@/lib/checkout-options-client";

export function CheckoutChoices({
  options,
  cart,
  directItem,
  selectedProducts,
  disabled,
  onChange,
}: {
  options: CheckoutOptions;
  cart: CartData;
  directItem?: OptionsSelection["direct_item"];
  selectedProducts?: string[];
  disabled: boolean;
  onChange: (v: QuotedChoices | null) => void;
}) {
  const [shipping, setShipping] = useState("STANDARD");
  const [payment, setPayment] = useState("COD");
  const [shops, setShops] = useState<Record<string, string>>({});
  const [coco, setCoco] = useState("");
  const [freight, setFreight] = useState("");
  const [quote, setQuote] = useState<QuotedChoices | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const guard = useRef(false);
  function changed() {
    setQuote(null);
    setError("");
    onChange(null);
  }
  async function apply() {
    if (guard.current || disabled) return;
    guard.current = true;
    setBusy(true);
    setError("");
    setQuote(null);
    onChange(null);
    const selection: OptionsSelection = {
      shipping_method: shipping as OptionsSelection["shipping_method"],
      payment_method: payment as OptionsSelection["payment_method"],
      ...(directItem ? { direct_item: directItem } : {}),
      ...(selectedProducts ? { selected_product_ids: selectedProducts } : {}),
      shop_coupons: cart.shops
        .filter((s) => shops[s.shop_id]?.trim())
        .map((s) => ({ shop_id: s.shop_id, code: shops[s.shop_id].trim() })),
      ...(coco.trim() ? { coco_coupon_code: coco.trim() } : {}),
      ...(freight.trim() ? { shipping_coupon_code: freight.trim() } : {}),
    };
    try {
      const result = await quoteChoices(selection);
      if (
        result.subtotal !== cart.total_amount ||
        result.shipping.length !== cart.shops.length ||
        !cart.shops.every((s) =>
          result.shipping.some((r) => r.shop_id === s.shop_id),
        )
      )
        throw new Error(
          "Giỏ hàng đã thay đổi. Hãy tải lại thông tin thanh toán.",
        );
      const value = { selection, quote: result };
      setQuote(value);
      onChange(value);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Chưa tính được tổng tiền.");
    } finally {
      guard.current = false;
      setBusy(false);
    }
  }
  return (
    <section
      className="order-panel checkout-choices"
      aria-labelledby="checkout-choices-title"
    >
      <h2 id="checkout-choices-title">Vận chuyển, thanh toán và ưu đãi</h2>
      <fieldset disabled={disabled || busy}>
        <legend>Phương thức vận chuyển</legend>
        <p>
          Cước cố định cho mỗi shop. Đơn có {cart.shops.length} shop sẽ tính
          cước riêng cho từng shop.
        </p>
        {options.shipping_methods.map((m) => (
          <label className="checkout-option" key={m.code}>
            <input
              type="radio"
              name="shipping-method"
              value={m.code}
              checked={shipping === m.code}
              disabled={!m.enabled}
              onChange={() => {
                setShipping(m.code);
                changed();
              }}
            />
            <span>
              <strong>{m.label}</strong>
              <small>
                {m.fee_per_shop !== null
                  ? `${formatVnd(m.fee_per_shop)} / shop`
                  : m.reason}
              </small>
            </span>
          </label>
        ))}
      </fieldset>
      <fieldset disabled={disabled || busy}>
        <legend>Phương thức thanh toán</legend>
        {options.payment_methods.map((m) => (
          <label className="checkout-option" key={m.code}>
            <input
              type="radio"
              name="payment-method"
              value={m.code}
              checked={payment === m.code}
              disabled={!m.enabled}
              onChange={() => {
                setPayment(m.code);
                changed();
              }}
            />
            <span>
              <strong>{m.label}</strong>
              {m.reason && <small>{m.reason}</small>}
            </span>
          </label>
        ))}
        {payment === "BANK_TRANSFER" && (
          <p>
            Đơn sẽ chờ xác nhận thanh toán. Nội dung chuyển khoản được cấp sau
            khi đặt hàng; chưa tự động ghi nhận đã trả tiền.
          </p>
        )}
      </fieldset>
      <fieldset disabled={disabled || busy}>
        <legend>Mã giảm giá</legend>
        {cart.shops.map((shop) => (
          <label className="checkout-code-field" key={shop.shop_id}>
            Mã shop {shop.shop_name}
            <input
              value={shops[shop.shop_id] || ""}
              maxLength={50}
              placeholder="Mỗi shop tối đa 1 mã"
              onChange={(e) => {
                setShops((v) => ({ ...v, [shop.shop_id]: e.target.value }));
                changed();
              }}
            />
          </label>
        ))}
        <label className="checkout-code-field">
          Mã COCO giảm tiền hàng
          <input
            value={coco}
            maxLength={50}
            placeholder="Tối đa 1 mã toàn sàn"
            onChange={(e) => {
              setCoco(e.target.value);
              changed();
            }}
          />
        </label>
        <label className="checkout-code-field">
          Mã COCO giảm phí vận chuyển
          <input
            value={freight}
            maxLength={50}
            placeholder="Tối đa 1 mã vận chuyển"
            onChange={(e) => {
              setFreight(e.target.value);
              changed();
            }}
          />
        </label>
        <p>
          Áp mã shop trước, mã COCO tiền hàng sau. Mã vận chuyển giảm riêng trên
          cước.
        </p>
        <button
          className="secondary-button"
          type="button"
          onClick={() => void apply()}
        >
          {busy ? "Đang tính…" : "Áp dụng và tính tổng tiền"}
        </button>
      </fieldset>
      {error && (
        <p role="alert" className="cart-error">
          {error}
        </p>
      )}
      {quote && (
        <div className="checkout-quote" role="status">
          {quote.quote.applied_coupons.map((c) => (
            <p key={c.code}>
              {c.code}: −{formatVnd(c.discount_amount)}{" "}
              {c.coupon_type === "SHIPPING" ? "cước vận chuyển" : "tiền hàng"}
            </p>
          ))}
          <p>Tiền hàng: {formatVnd(quote.quote.subtotal)}</p>
          <p>Giảm tiền hàng: −{formatVnd(quote.quote.discount_amount)}</p>
          <p>
            Giảm phí vận chuyển: −
            {formatVnd(quote.quote.shipping_discount_amount)}
          </p>
          <p>Cước còn trả: {formatVnd(quote.quote.shipping_fee)}</p>
          <strong>
            Tổng thanh toán: {formatVnd(quote.quote.total_amount)}
          </strong>
        </div>
      )}
    </section>
  );
}
