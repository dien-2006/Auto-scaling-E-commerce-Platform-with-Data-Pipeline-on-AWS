"use client";

import Link from "next/link";
import { CommerceRestriction } from "@/components/auth/commerce-restriction";
import { useEffect, useState } from "react";
import { useSession } from "@/components/auth/session-provider";
import { OrderAction } from "@/components/orders/order-action";
import { PaymentNotice } from "@/components/checkout/payment-notice";
import { ReviewForm } from "@/components/orders/review-form";
import {
  paymentLabels,
  orderStatuses,
  type CheckoutOrder,
} from "@/lib/checkout-contract";
import { formatVnd } from "@/lib/categories";
import { fetchOrder, fetchOrders, type OrderPage } from "@/lib/orders-client";

const date = (value: string) =>
  new Intl.DateTimeFormat("vi-VN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
export function BuyerOrders({ page = 1, id }: { page?: number; id?: string }) {
  const { account, loading, error, refresh } = useSession();
  if (account?.user_role === "ADMIN") return <CommerceRestriction />;
  const target = `/tai-khoan/don-hang${id ? `/${id}` : page > 1 ? `?page=${page}` : ""}`;
  return (
    <main className="shell buyer-orders-page">
      <nav aria-label="Đường dẫn" className="buyer-order-breadcrumb">
        <Link href="/">Trang chủ</Link>
        <span>/</span>
        <Link href="/tai-khoan">Tài khoản</Link>
        <span>/</span>
        <Link href="/tai-khoan/don-hang">Đơn mua</Link>
        {id && (
          <>
            <span>/</span>
            <span>#{id}</span>
          </>
        )}
      </nav>
      <header className="buyer-orders-heading">
        <div>
          <p>COCO · ĐƠN MUA</p>
          <h1>{id ? "Chi tiết đơn hàng" : "Đơn hàng của tôi"}</h1>
          <span>Theo dõi từng đơn shop, lưu giữ thông tin mua hàng.</span>
        </div>
        <Link className="secondary-button" href="/san-pham">
          Tiếp tục mua sắm →
        </Link>
      </header>
      {loading && !account ? (
        <p role="status" className="order-panel">
          Đang kiểm tra phiên đăng nhập…
        </p>
      ) : !account ? (
        <section className="order-panel buyer-order-empty">
          <h2>Đăng nhập để xem đơn mua</h2>
          <p role={error ? "alert" : undefined}>
            {error || "Lịch sử mua hàng chỉ hiển thị cho chủ tài khoản."}
          </p>
          <Link
            className="primary-button"
            href={`/dang-nhap?returnTo=${encodeURIComponent(target)}`}
          >
            Đăng nhập
          </Link>
          <button className="account-retry" onClick={() => void refresh()}>
            Kiểm tra lại phiên
          </button>
        </section>
      ) : (
        <OrderContent
          key={`${account.user_id}:${id ?? page}`}
          page={page}
          id={id}
        />
      )}
    </main>
  );
}

function OrderContent({ page, id }: { page: number; id?: string }) {
  const [result, setResult] = useState<{
    list?: OrderPage;
    order?: CheckoutOrder;
  } | null>(null);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    (id
      ? fetchOrder(id, controller.signal).then((order) => ({ order }))
      : fetchOrders(page, controller.signal).then((list) => ({ list }))
    )
      .then((value) => {
        if (!controller.signal.aborted) setResult(value);
      })
      .catch((e: unknown) => {
        if (!controller.signal.aborted)
          setError(e instanceof Error ? e.message : "Không tải được đơn hàng.");
      });
    return () => controller.abort();
  }, [page, id, retry]);
  function reload() {
    setResult(null);
    setError("");
    setRetry((value) => value + 1);
  }
  if (error)
    return (
      <section className="order-panel buyer-order-empty">
        <h2>Chưa thể hiển thị đơn hàng</h2>
        <p role="alert">{error}</p>
        <button className="primary-button" onClick={reload}>
          Thử lại
        </button>
        <Link href="/tai-khoan/don-hang">Về danh sách đơn mua</Link>
      </section>
    );
  if (!result)
    return (
      <p className="order-panel" role="status">
        Đang tải đơn hàng…
      </p>
    );
  return (
    <>
      <div className="buyer-orders-toolbar">
        <span>
          {result.list
            ? `${result.list.total} đơn hàng`
            : `Đơn #${result.order?.order_id}`}
        </span>
        <button className="secondary-button" onClick={reload}>
          Cập nhật trạng thái
        </button>
      </div>
      {result.order ? (
        <OrderDetail order={result.order} onReload={reload} />
      ) : (
        result.list && <OrderHistory data={result.list} />
      )}
    </>
  );
}

function OrderHistory({ data }: { data: OrderPage }) {
  const pages = Math.ceil(data.total / data.page_size);
  return (
    <>
      {!data.items.length ? (
        <section className="order-panel buyer-order-empty">
          <h2>
            {data.total
              ? "Trang này chưa có đơn hàng"
              : "Bạn chưa có đơn hàng nào"}
          </h2>
          <p>
            {data.total
              ? "Quay lại trang trước để xem các đơn đã mua."
              : "Các đơn được đặt thành công sẽ xuất hiện tại đây."}
          </p>
          <Link
            href={data.total ? "/tai-khoan/don-hang" : "/san-pham"}
            className="primary-button"
          >
            {data.total ? "Về trang đầu" : "Khám phá sản phẩm"}
          </Link>
        </section>
      ) : (
        <div className="buyer-orders-list">
          {data.items.map((order) => (
            <article
              className="order-panel buyer-order-card"
              key={order.order_id}
            >
              <header>
                <div>
                  <Link href={`/tai-khoan/don-hang/${order.order_id}`}>
                    <h2>Đơn #{order.order_id}</h2>
                  </Link>
                  <time dateTime={order.created_at}>
                    {date(order.created_at)}
                  </time>
                </div>
                <span className="buyer-order-cod">
                  {paymentLabels[order.payment_method]}
                </span>
              </header>
              <ul className="buyer-shop-summaries">
                {order.shop_orders.map((shop) => (
                  <li key={shop.shop_order_id}>
                    <div>
                      <strong>{shop.shop_name}</strong>
                      <small>Đơn shop #{shop.shop_order_id}</small>
                    </div>
                    <span
                      className={`buyer-order-status status-${shop.order_status.toLowerCase()}`}
                    >
                      {orderStatuses[shop.order_status]}
                    </span>
                    <strong>{formatVnd(shop.subtotal)}</strong>
                  </li>
                ))}
              </ul>
              <footer>
                <p>
                  Tổng giá trị đơn{" "}
                  <strong>{formatVnd(order.total_amount)}</strong>
                </p>
                <Link
                  href={`/tai-khoan/don-hang/${order.order_id}`}
                  className="primary-button"
                >
                  Xem chi tiết →
                </Link>
              </footer>
            </article>
          ))}
        </div>
      )}
      {data.total > 0 && (
        <nav
          aria-label="Phân trang đơn hàng"
          className="buyer-order-pagination"
        >
          {data.page > 1 && (
            <Link
              className="secondary-button"
              href={`/tai-khoan/don-hang?page=${data.page - 1}`}
            >
              ← Trang trước
            </Link>
          )}
          <span aria-current="page">
            Trang {data.page}
            {data.page <= pages ? ` / ${pages}` : ""}
          </span>
          {data.page < pages && (
            <Link
              className="secondary-button"
              href={`/tai-khoan/don-hang?page=${data.page + 1}`}
            >
              Trang sau →
            </Link>
          )}
        </nav>
      )}
    </>
  );
}

function OrderDetail({
  order,
  onReload,
}: {
  order: CheckoutOrder;
  onReload: () => void;
}) {
  return (
    <div className="buyer-order-detail-grid">
      <div className="buyer-orders-list">
        <section className="order-panel">
          <h2>Thông tin nhận hàng</h2>
          <p>
            <strong>{order.recipient_name}</strong> · {order.phone}
          </p>
          <p className="buyer-order-address">{order.shipping_address}</p>
          <small>Địa chỉ được lưu tại thời điểm đặt hàng.</small>
        </section>
        {order.shop_orders.map((shop) => (
          <section
            className="order-panel buyer-order-card"
            key={shop.shop_order_id}
          >
            <header>
              <div>
                <h2>{shop.shop_name}</h2>
                <small>Đơn shop #{shop.shop_order_id}</small>
              </div>
              <span
                className={`buyer-order-status status-${shop.order_status.toLowerCase()}`}
              >
                {orderStatuses[shop.order_status]}
              </span>
            </header>
            <ul className="buyer-order-lines">
              {shop.items.map((item) => (
                <li key={item.order_item_id}>
                  <div>
                    <strong>{item.product_name}</strong>
                    <small>
                      {formatVnd(item.unit_price)} × {item.quantity}
                    </small>
                    {shop.order_status === "COMPLETED" && (
                      <ReviewForm
                        itemId={item.order_item_id}
                        name={item.product_name}
                      />
                    )}
                  </div>
                  <strong>{formatVnd(item.line_total)}</strong>
                </li>
              ))}
            </ul>
            <footer>
              <p>
                Giá trị đơn shop <strong>{formatVnd(shop.subtotal)}</strong>
              </p>
            </footer>
            <OrderAction
              key={shop.order_status}
              order={{
                order_id: order.order_id,
                shop_order_id: shop.shop_order_id,
                order_status: shop.order_status,
              }}
              buyer
              onReload={onReload}
            />
          </section>
        ))}
      </div>
      <aside className="order-panel buyer-order-summary">
        <h2>Tóm tắt đơn hàng</h2>
        <dl>
          <div>
            <dt>Mã đơn</dt>
            <dd>#{order.order_id}</dd>
          </div>
          <div>
            <dt>Ngày đặt</dt>
            <dd>
              <time dateTime={order.created_at}>{date(order.created_at)}</time>
            </dd>
          </div>
          <div>
            <dt>Thanh toán</dt>
            <dd>{paymentLabels[order.payment_method]}</dd>
          </div>
          <div>
            <dt>Số shop</dt>
            <dd>{order.shop_orders.length}</dd>
          </div>
        </dl>
        <PaymentNotice
          orderId={order.order_id}
          method={order.payment_method}
          status={order.payment_status}
        />
        <p className="buyer-order-total">
          Tổng giá trị đơn<strong>{formatVnd(order.total_amount)}</strong>
        </p>
        {order.discount_amount && (
          <p>Giảm giá: {formatVnd(order.discount_amount)}</p>
        )}
        {order.shipping_discount_amount && (
          <p>Đã giảm cước: {formatVnd(order.shipping_discount_amount)}</p>
        )}
        {order.shipping_fee && (
          <p>Phí vận chuyển: {formatVnd(order.shipping_fee)}</p>
        )}
        <p>
          Trạng thái được theo dõi riêng theo từng shop. Tổng giá trị là số tiền
          đã ghi nhận khi đặt, kể cả khi đơn shop được hủy sau đó.
        </p>
        <Link className="secondary-button" href="/tai-khoan/don-hang">
          ← Lịch sử đơn hàng
        </Link>
      </aside>
    </div>
  );
}
