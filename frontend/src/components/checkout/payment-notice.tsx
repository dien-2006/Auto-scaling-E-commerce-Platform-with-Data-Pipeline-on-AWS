"use client";
import { useEffect, useState } from "react";
import {
  fetchCheckoutOptions,
  type CheckoutOptions,
} from "@/lib/checkout-options-client";
export function PaymentNotice({
  orderId,
  method,
  status,
}: {
  orderId: string;
  method: string;
  status?: string | null;
}) {
  const [options, setOptions] = useState<CheckoutOptions | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    if (method === "BANK_TRANSFER")
      void fetchCheckoutOptions()
        .then((v) => {
          if (active) setOptions(v);
        })
        .catch(() => {
          if (active)
            setError(
              "Chưa đọc được thông tin nhận chuyển khoản. Vui lòng tải lại trang.",
            );
        });
    return () => {
      active = false;
    };
  }, [method]);
  if (method === "COD") return null;
  return (
    <section className="payment-notice">
      <h3>
        {status === "SUCCESS"
          ? "Đã xác nhận thanh toán"
          : status === "FAILED" || status === "REFUNDED"
            ? "Thanh toán đã dừng"
            : "Chờ xác nhận thanh toán"}
      </h3>
      {method === "BANK_TRANSFER" && status === "PENDING" && (
        <>
          {error && <p role="alert">{error}</p>}
          {options?.bank ? (
            <>
              <p>Ngân hàng: {options.bank.name}</p>
              <p>Số tài khoản: {options.bank.account_number}</p>
              <p>Người nhận: {options.bank.account_holder}</p>
              <p>
                Nội dung: <strong>COCO{orderId}</strong>
              </p>
              <small>
                Thông tin nhận tiền hiện tại của COCO. Chuyển khoản không tự
                đánh dấu đơn đã thanh toán.
              </small>
            </>
          ) : (
            !error && (
              <p>
                {options
                  ? "Chưa có thông tin nhận chuyển khoản. Vui lòng liên hệ COCO."
                  : "Đang tải thông tin chuyển khoản…"}
              </p>
            )
          )}
        </>
      )}
    </section>
  );
}
