"use client";
import Link from "next/link";
import { paymentLabels } from "@/lib/checkout-contract";
import { useEffect, useState } from "react";
import { useSession } from "@/components/auth/session-provider";
import { OrderAction } from "@/components/orders/order-action";
import { orderStatuses } from "@/lib/checkout-contract";
import { formatVnd } from "@/lib/categories";
import {
  fetchSellerOrder,
  fetchSellerOrders,
  SellerOrderFailure,
  type SellerOrderDetail,
  type SellerOrderPage,
} from "@/lib/seller-orders-client";

export function SellerOrders({ id }: { id?: string }) {
  const { account, loading, error, refresh } = useSession();
  const shop = account?.owned_shop;
  const target = `/kenh-nguoi-ban/don-hang${id ? `/${id}` : ""}`;
  return (
    <main className="shell seller-page">
      <nav className="seller-breadcrumb" aria-label="Đường dẫn">
        <Link href="/">Trang chủ</Link>
        <span>/</span>
        <Link href="/kenh-nguoi-ban">Kênh người bán</Link>
        <span>/</span>
        <Link href="/kenh-nguoi-ban/don-hang">Đơn bán</Link>
        <Link href="/tai-khoan/don-hang">Đơn mua của tôi</Link>
        {id && <span>/ #{id}</span>}
      </nav>
      <header className="seller-heading">
        <div>
          <h1>{id ? "Chi tiết đơn bán" : "Đơn hàng của gian hàng"}</h1>
          <p>Thông tin và trạng thái riêng cho từng đơn shop.</p>
        </div>
        <Link className="seller-outline-button" href="/kenh-nguoi-ban">
          Về gian hàng
        </Link>
      </header>
      {loading && !account ? (
        <p role="status" className="seller-card">
          Đang kiểm tra phiên đăng nhập…
        </p>
      ) : !account ? (
        <section className="seller-card">
          <p role={error ? "alert" : undefined}>
            {error || "Đăng nhập bằng tài khoản sở hữu gian hàng."}
          </p>
          <Link
            className="primary-button"
            href={`/dang-nhap?returnTo=${encodeURIComponent(target)}`}
          >
            Đăng nhập
          </Link>
          <button className="secondary-button" onClick={() => void refresh()}>
            Kiểm tra lại phiên
          </button>
        </section>
      ) : !shop || !["APPROVED", "LOCKED"].includes(shop.shop_status) ? (
        <section className="seller-card">
          <p>Gian hàng chưa được phép xử lý đơn.</p>
          <Link href="/kenh-nguoi-ban">Xem trạng thái gian hàng</Link>
        </section>
      ) : (
        <>
          {shop.shop_status === "LOCKED" && (
            <p className="seller-storage-notice">
              Gian hàng đang bị khóa. Bạn vẫn có thể xử lý các đơn đã đặt.
            </p>
          )}
          <Content
            key={`${account.user_id}:${shop.shop_id}:${id ?? "list"}`}
            shopId={shop.shop_id}
            id={id}
          />
        </>
      )}
    </main>
  );
}
function Content({ shopId, id }: { shopId: string; id?: string }) {
  const { refresh } = useSession();
  const [page, setPage] = useState(1),
    [status, setStatus] = useState(""),
    [retry, setRetry] = useState(0),
    [result, setResult] = useState<{
      list?: SellerOrderPage;
      detail?: SellerOrderDetail;
    } | null>(null),
    [error, setError] = useState("");
  useEffect(() => {
    const c = new AbortController();
    (id
      ? fetchSellerOrder(id, shopId, c.signal).then((detail) => ({ detail }))
      : fetchSellerOrders(shopId, page, status, c.signal).then((list) => ({
          list,
        }))
    )
      .then((value) => {
        if (!c.signal.aborted) setResult(value);
      })
      .catch((e: unknown) => {
        if (!c.signal.aborted) {
          setResult(null);
          setError(e instanceof Error ? e.message : "Chưa tải được đơn hàng.");
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
          )
            void refresh();
        }
      });
    return () => c.abort();
  }, [id, shopId, page, status, retry, refresh]);
  function reload() {
    setResult(null);
    setError("");
    setRetry((v) => v + 1);
  }
  return (
    <div className="seller-orders">
      <div className="buyer-orders-toolbar">
        {!id && (
          <label>
            Lọc trạng thái
            <select
              aria-label="Lọc trạng thái"
              value={status}
              onChange={(e) => {
                setResult(null);
                setError("");
                setStatus(e.target.value);
                setPage(1);
              }}
            >
              {<option value="">Tất cả</option>}
              {Object.entries(orderStatuses).map(([key, label]) => (
                <option key={key} value={key}>
                  {label}
                </option>
              ))}
            </select>
          </label>
        )}
        <button className="secondary-button" onClick={reload}>
          Tải lại đơn
        </button>
      </div>
      {error ? (
        <section className="seller-card">
          <p role="alert">{error}</p>
          <button className="primary-button" onClick={reload}>
            Thử lại
          </button>
        </section>
      ) : !result ? (
        <p role="status" className="seller-card">
          Đang tải đơn hàng…
        </p>
      ) : result.detail ? (
        <Detail order={result.detail} onReload={reload} />
      ) : (
        result.list && (
          <>
            <p>
              {result.list.total} đơn shop · Trang {page}
            </p>
            {!result.list.items.length ? (
              <section className="seller-card">
                <h2>Chưa có đơn hàng trong trang này</h2>
                <p>Thử chọn trạng thái khác hoặc quay về trang trước.</p>
              </section>
            ) : (
              <ul className="seller-order-list">
                {result.list.items.map((order) => (
                  <li key={order.shop_order_id} className="seller-card">
                    <div>
                      <Link
                        href={`/kenh-nguoi-ban/don-hang/${order.shop_order_id}`}
                      >
                        Đơn shop #{order.shop_order_id}
                      </Link>
                      <p>
                        {new Date(order.created_at).toLocaleString("vi-VN")}
                      </p>
                    </div>
                    <span
                      className={`buyer-order-status status-${order.order_status.toLowerCase()}`}
                    >
                      {orderStatuses[order.order_status]}
                    </span>
                    <strong>{formatVnd(order.subtotal)}</strong>
                    <Link
                      className="secondary-button"
                      href={`/kenh-nguoi-ban/don-hang/${order.shop_order_id}`}
                    >
                      Xem đơn
                    </Link>
                  </li>
                ))}
              </ul>
            )}
            <nav
              aria-label="Phân trang đơn bán"
              className="buyer-order-pagination"
            >
              <button
                className="secondary-button"
                disabled={page === 1}
                onClick={() => {
                  setResult(null);
                  setPage((v) => v - 1);
                }}
              >
                Trang trước
              </button>
              <span>Trang {page}</span>
              <button
                className="secondary-button"
                disabled={page * 24 >= result.list.total}
                onClick={() => {
                  setResult(null);
                  setPage((v) => v + 1);
                }}
              >
                Trang sau
              </button>
            </nav>
          </>
        )
      )}
    </div>
  );
}
function Detail({
  order,
  onReload,
}: {
  order: SellerOrderDetail;
  onReload: () => void;
}) {
  return (
    <div className="buyer-orders-list">
      <section className="seller-card">
        <header className="seller-heading">
          <div>
            <h2>Đơn shop #{order.shop_order_id}</h2>
            <p>
              Mã đơn mua #{order.order_id} ·{" "}
              {new Date(order.created_at).toLocaleString("vi-VN")}
            </p>
          </div>
          <span
            className={`buyer-order-status status-${order.order_status.toLowerCase()}`}
          >
            {orderStatuses[order.order_status]}
          </span>
        </header>
        <p>Cập nhật: {new Date(order.updated_at).toLocaleString("vi-VN")}</p>
        <OrderAction
          key={order.order_status}
          order={order}
          onReload={onReload}
        />
      </section>
      <section className="seller-card">
        <h2>Người mua và giao hàng</h2>
        {order.buyer_name && <p>Người mua: <strong>{order.buyer_name}</strong></p>}
        <p>
          Người nhận: <strong>{order.recipient_name}</strong> · {order.phone}
        </p>
        <p className="buyer-order-address">{order.shipping_address}</p>
        <p>
          {paymentLabels[order.payment_method]} · Chưa tích hợp hãng vận chuyển.
        </p>
      </section>
      <section className="seller-card">
        <h2>Sản phẩm trong đơn shop</h2>
        <ul className="buyer-order-lines">
          {order.items.map((item) => (
            <li key={item.order_item_id}>
              <div>
                <strong>{item.product_name}</strong>
                <small>
                  {formatVnd(item.unit_price)} × {item.quantity}
                </small>
              </div>
              <strong>{formatVnd(item.line_total)}</strong>
            </li>
          ))}
        </ul>
        <p>
          Giá trị đơn shop <strong>{formatVnd(order.subtotal)}</strong>
        </p>
      </section>
      <Link className="secondary-button" href="/kenh-nguoi-ban/don-hang">
        Về danh sách đơn bán
      </Link>
    </div>
  );
}
