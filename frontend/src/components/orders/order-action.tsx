"use client";
import { useEffect, useRef, useState } from "react";
import { useSession } from "@/components/auth/session-provider";
import { orderStatuses } from "@/lib/checkout-contract";
import {
  changeShopOrder,
  SellerOrderFailure,
  type OrderStatus,
} from "@/lib/seller-orders-client";

export function OrderAction({
  order,
  buyer = false,
  onReload,
}: {
  order: { order_id: string; shop_order_id: string; order_status: string };
  buyer?: boolean;
  onReload: () => void;
}) {
  const { refresh } = useSession();
  const [target, setTarget] = useState<OrderStatus | null>(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const submitting = useRef(false),
    controller = useRef<AbortController | null>(null),
    mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      controller.current?.abort();
    };
  }, []);
  const choices: OrderStatus[] = buyer
    ? order.order_status === "PENDING"
      ? ["CANCELLED"]
      : []
    : ((
        {
          PENDING: ["CONFIRMED", "CANCELLED"],
          CONFIRMED: ["SHIPPING", "CANCELLED"],
          SHIPPING: ["COMPLETED"],
          COMPLETED: [],
          CANCELLED: [],
        } as Record<string, OrderStatus[]>
      )[order.order_status] ?? []);
  async function save() {
    if (!target || submitting.current || error) return;
    submitting.current = true;
    setBusy(true);
    const c = new AbortController();
    controller.current = c;
    try {
      await changeShopOrder(order, target, c.signal, buyer);
      if (mounted.current) onReload();
    } catch (e) {
      if (!mounted.current) return;
      setTarget(null);
      setError(
        e instanceof Error
          ? e.message
          : "Chưa xác minh được kết quả. Hãy tải lại đơn.",
      );
      if (
        e instanceof SellerOrderFailure &&
        [
          "AUTH_REQUIRED",
          "TOKEN_EXPIRED",
          "INVALID_TOKEN",
          "USER_LOCKED",
          "FORBIDDEN",
          "SHOP_NOT_APPROVED",
        ].includes(e.code)
      ) {
        onReload();
        void refresh();
      }
    } finally {
      submitting.current = false;
      if (mounted.current) setBusy(false);
    }
  }
  if (!choices.length) return null;
  return (
    <div className="order-actions">
      {error ? (
        <>
          <p role="alert">{error}</p>
          <p>
            Kết quả có thể đã được lưu. Tải lại đơn và kiểm tra trước khi thao
            tác tiếp.
          </p>
          <button className="secondary-button" onClick={onReload}>
            Tải lại đơn
          </button>
        </>
      ) : target ? (
        <>
          <p role="status">
            Xác nhận chuyển từ{" "}
            <strong>{orderStatuses[order.order_status]}</strong> sang{" "}
            <strong>{orderStatuses[target]}</strong>?
          </p>
          {target === "CANCELLED" && (
            <p>
              Chỉ hủy đơn của shop này. Số lượng sản phẩm sẽ được hoàn tồn;
              không có thanh toán trực tuyến cần hoàn tiền.
            </p>
          )}
          <button
            className="primary-button"
            disabled={busy}
            onClick={() => void save()}
          >
            {busy ? "Đang lưu…" : "Xác nhận thay đổi"}
          </button>
          <button
            className="secondary-button"
            disabled={busy}
            onClick={() => setTarget(null)}
          >
            Quay lại
          </button>
        </>
      ) : (
        choices.map((status) => (
          <button
            key={status}
            className="secondary-button"
            onClick={() => setTarget(status)}
          >
            {status === "CANCELLED"
              ? "Hủy đơn shop"
              : status === "CONFIRMED"
                ? "Xác nhận đơn"
                : status === "SHIPPING"
                  ? "Bắt đầu giao hàng"
                  : "Hoàn tất đơn"}
          </button>
        ))
      )}
    </div>
  );
}
