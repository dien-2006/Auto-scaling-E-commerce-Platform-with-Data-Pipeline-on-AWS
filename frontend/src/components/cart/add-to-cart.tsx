"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useRef, useState, type FormEvent } from "react";
import { useSession } from "@/components/auth/session-provider";
import { changeCart } from "@/lib/cart-client";

export function AddToCart({
  productId,
  shopId,
  availableQuantity,
}: {
  productId: string;
  shopId: string;
  availableQuantity: number;
}) {
  const router = useRouter();
  const { account, loading } = useSession();
  const [quantity, setQuantity] = useState("1");
  const [buying, setBuying] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const guard = useRef(false);
  const admin = account?.user_role === "ADMIN";
  const self = account?.owned_shop?.shop_id === shopId;
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (guard.current || !account || admin || self || availableQuantity === 0) return;
    const submitter = (event.nativeEvent as SubmitEvent).submitter;
    const buyNow = submitter instanceof HTMLButtonElement && submitter.value === "buy-now";
    setBuying(buyNow);
    guard.current = true;
    setBusy(true);
    setError("");
    setSuccess(false);
    try {
      if (buyNow) {
        router.push(`/thanh-toan?product=${productId}&quantity=${Number(quantity)}`);
      } else {
        await changeCart("POST", productId, Number(quantity));
        setSuccess(true);
      }
    } catch (e) {
      setError(
        `${e instanceof Error ? e.message : "Chưa thêm được sản phẩm."} Nếu mất kết nối, kiểm tra giỏ trước khi thêm lại.`,
      );
    } finally {
      guard.current = false;
      setBusy(false);
    }
  }
  return (
    <div className="cart-add-panel">
      {admin ? (
        <p>Tài khoản Admin không được mua hàng.</p>
      ) : !account && !loading ? (
        <>
          <p>Đăng nhập để lưu sản phẩm vào giỏ hàng.</p>
          <Link
            className="primary-button"
            href={`/dang-nhap?returnTo=${encodeURIComponent(`/san-pham/${productId}`)}`}
          >
            Đăng nhập để thêm vào giỏ
          </Link>
        </>
      ) : (
        <form onSubmit={submit}>
          <label htmlFor={`cart-quantity-${productId}`}>Số lượng</label>
          <div className="cart-add-actions">
            <input
              id={`cart-quantity-${productId}`}
              type="number"
              min="1"
              max={Math.max(1, availableQuantity)}
              step="1"
              required
              value={quantity}
              onChange={(event) => {
                setQuantity(event.target.value);
                setSuccess(false);
              }}
              disabled={busy || loading || self || availableQuantity === 0}
            />
            <button
              className="primary-button"
              disabled={busy || loading || self || availableQuantity === 0}
              type="submit"
            >
              {busy
                ? "Đang thêm…"
                : loading
                  ? "Đang kiểm tra phiên…"
                  : availableQuantity === 0
                    ? "Tạm hết hàng"
                    : "Thêm vào giỏ"}
            </button>
            <button
              className="primary-button buy-now-button"
              type="submit"
              name="action"
              value="buy-now"
              disabled={busy || loading || self || availableQuantity === 0}
            >
              {busy && buying ? "Đang chuẩn bị…" : "Mua ngay"}
            </button>
          </div>
        </form>
      )}
      {self && <p>Bạn không thể mua sản phẩm từ shop của mình.</p>}
      {error && (
        <p role="alert" className="cart-error">
          {error}
        </p>
      )}
      {success && (
        <p role="status">
          Đã thêm sản phẩm. <Link href="/gio-hang">Xem giỏ hàng →</Link>
        </p>
      )}
      <p className="auth-field-hint">
        Thêm vào giỏ không giữ hàng. Giá và tồn kho được kiểm tra lại trên
        server.
      </p>
    </div>
  );
}
