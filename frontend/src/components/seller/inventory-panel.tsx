"use client";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { useSession } from "@/components/auth/session-provider";
import {
  adjustInventory,
  readInventory,
  InventoryFailure,
  type Inventory,
} from "@/lib/inventory-client";

export function InventoryPanel({
  productId,
  name,
  onClose,
  onSnapshot,
}: {
  productId: string;
  name: string;
  onClose: () => void;
  onSnapshot: (inventory: Inventory) => void;
}) {
  const { refresh } = useSession();
  const [inventory, setInventory] = useState<Inventory | null>(null),
    [review, setReview] = useState<{ expected: number; delta: number } | null>(
      null,
    ),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [busy, setBusy] = useState(false),
    [uncertain, setUncertain] = useState(false),
    [retry, setRetry] = useState(0);
  const mounted = useRef(false),
    submitting = useRef(false),
    write = useRef<AbortController | null>(null),
    snapshot = useRef(onSnapshot);
  useEffect(() => {
    snapshot.current = onSnapshot;
  }, [onSnapshot]);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      write.current?.abort();
    };
  }, []);
  useEffect(() => {
    const c = new AbortController();
    void readInventory(productId, c.signal)
      .then((value) => {
        if (!c.signal.aborted) {
          setInventory(value);
          setUncertain(false);
          snapshot.current(value);
        }
      })
      .catch((e: unknown) => {
        if (!c.signal.aborted) {
          setError(e instanceof Error ? e.message : "Chưa đọc được tồn kho.");
          if (
            e instanceof InventoryFailure &&
            [
              "AUTH_REQUIRED",
              "TOKEN_EXPIRED",
              "INVALID_TOKEN",
              "USER_LOCKED",
              "SHOP_NOT_APPROVED",
              "FORBIDDEN",
            ].includes(e.code)
          )
            void refresh();
        }
      });
    return () => c.abort();
  }, [productId, retry, refresh]);
  function reload() {
    if (submitting.current) return;
    setInventory(null);
    setReview(null);
    setError("");
    setNotice("");
    setRetry((v) => v + 1);
  }
  function prepare(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!inventory || busy || uncertain) return;
    const data = new FormData(e.currentTarget),
      amount = Number(data.get("amount")),
      delta = data.get("direction") === "decrease" ? -amount : amount;
    if (
      !Number.isInteger(amount) ||
      amount < 1 ||
      amount > 2147483647 ||
      inventory.quantity + delta < 0 ||
      inventory.quantity + delta > 2147483647
    ) {
      setError(
        "Kiểm tra số lượng điều chỉnh. Tồn kho sau thay đổi không được âm hoặc vượt 2147483647.",
      );
      return;
    }
    setError("");
    setNotice("");
    setReview({ expected: inventory.quantity, delta });
  }
  async function save() {
    if (!review || !inventory || uncertain || submitting.current) return;
    submitting.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    const c = new AbortController();
    write.current = c;
    try {
      const value = await adjustInventory(
        productId,
        review.expected,
        review.delta,
        c.signal,
      );
      if (!mounted.current) return;
      setInventory(value);
      setReview(null);
      snapshot.current(value);
      setNotice("Đã cập nhật tồn kho.");
    } catch (e) {
      if (!mounted.current) return;
      setError(e instanceof Error ? e.message : "Chưa xác minh được kết quả.");
      setReview(null);
      setUncertain(true);
      if (
        e instanceof InventoryFailure &&
        [
          "AUTH_REQUIRED",
          "TOKEN_EXPIRED",
          "INVALID_TOKEN",
          "USER_LOCKED",
          "SHOP_NOT_APPROVED",
          "FORBIDDEN",
        ].includes(e.code)
      ) {
        setInventory(null);
        void refresh();
      }
    } finally {
      submitting.current = false;
      if (mounted.current) setBusy(false);
    }
  }
  return (
    <section
      className="seller-card seller-inventory"
      aria-labelledby="seller-inventory-title"
    >
      <header className="seller-heading">
        <div>
          <h2 id="seller-inventory-title">Điều chỉnh tồn kho — {name}</h2>
          <p>Giỏ hàng chưa giữ chỗ. Số lượng có thể thay đổi khi có đơn mua.</p>
        </div>
        <button
          className="seller-outline-button"
          disabled={busy}
          onClick={onClose}
        >
          Đóng tồn kho
        </button>
      </header>
      {error && (
        <p role="alert" className="seller-form-error">
          {error}
        </p>
      )}
      {notice && (
        <p role="status" className="seller-form-success">
          {notice}
        </p>
      )}
      <button
        className="seller-outline-button"
        disabled={busy}
        onClick={reload}
      >
        Tải lại tồn kho
      </button>
      {uncertain && (
        <p role="status">
          Cần tải lại tồn kho, kiểm tra kết quả và lập điều chỉnh mới. Hệ thống
          không tự gửi lại lần điều chỉnh vừa rồi.
        </p>
      )}
      {!inventory ? (
        !error && <p role="status">Đang đọc tồn kho…</p>
      ) : (
        <>
          <dl className="seller-inventory-summary">
            <div>
              <dt>Tồn kho hiện tại</dt>
              <dd>{inventory.quantity}</dd>
            </div>
            <div>
              <dt>Cập nhật lúc</dt>
              <dd>{new Date(inventory.updated_at).toLocaleString("vi-VN")}</dd>
            </div>
          </dl>
          <form
            key={inventory.updated_at + ":" + retry}
            className="seller-shop-form"
            onSubmit={prepare}
          >
            <fieldset disabled={busy || uncertain || !!review}>
              <legend>Nhập hoặc xuất bớt tồn kho</legend>
              <label htmlFor="inventory-direction">Loại điều chỉnh</label>
              <select id="inventory-direction" name="direction">
                <option value="increase">Nhập thêm</option>
                <option value="decrease">Xuất bớt</option>
              </select>
              <label htmlFor="inventory-amount">Số lượng điều chỉnh</label>
              <input
                id="inventory-amount"
                type="number"
                name="amount"
                min={1}
                max={2147483647}
                step={1}
                required
              />
              <button
                className="primary-button"
                disabled={busy || uncertain || !!review}
              >
                Kiểm tra thay đổi
              </button>
            </fieldset>
          </form>
          {review && (
            <div className="seller-inventory-review">
              <h3>Xác nhận điều chỉnh</h3>
              <p>
                Tồn kho đã đọc: <strong>{review.expected}</strong>.{" "}
                {review.delta > 0 ? "Nhập thêm" : "Xuất bớt"}:{" "}
                <strong>{Math.abs(review.delta)}</strong>. Sau điều chỉnh:{" "}
                <strong>{review.expected + review.delta}</strong>.
              </p>
              <button
                className="primary-button"
                disabled={busy || uncertain}
                onClick={() => void save()}
              >
                {busy ? "Đang lưu…" : "Xác nhận điều chỉnh"}
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
        </>
      )}
    </section>
  );
}
