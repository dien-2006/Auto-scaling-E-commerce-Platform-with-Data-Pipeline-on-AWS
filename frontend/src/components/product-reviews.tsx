"use client";

import { useEffect, useState } from "react";
import { productReviews, type ReviewPage } from "@/lib/shopping-client";

export function ProductReviews({ productId }: { productId: string }) {
  const [data, setData] = useState<ReviewPage | null>(null);
  const [page, setPage] = useState(1);
  const [attempt, setAttempt] = useState(0);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    productReviews(productId, page)
      .then((v) => {
        if (active) setData(v);
      })
      .catch((e) => {
        if (active)
          setError(e instanceof Error ? e.message : "Chưa tải được đánh giá.");
      });
    return () => {
      active = false;
    };
  }, [productId, page, attempt]);
  function load(next: number) {
    setData(null);
    setError("");
    setPage(next);
    setAttempt((v) => v + 1);
  }
  return (
    <section
      className="product-description product-reviews"
      aria-labelledby="product-reviews-title"
    >
      <h2 id="product-reviews-title">Đánh giá sản phẩm</h2>
      <p>Đánh giá từ người mua có đơn hàng đã hoàn thành.</p>
      {error ? (
        <div>
          <p role="alert">{error}</p>
          <button className="secondary-button" onClick={() => load(page)}>
            Thử lại
          </button>
        </div>
      ) : !data ? (
        <p role="status">Đang tải đánh giá…</p>
      ) : (
        <>
          <p>
            {data.total
              ? `${Number(data.average_rating).toFixed(1)}/5 sao · ${data.total} đánh giá`
              : "Chưa có đánh giá nào. Bạn có thể đánh giá từ chi tiết đơn mua sau khi nhận hàng."}
          </p>
          {data.items.map((item) => (
            <article className="review-card" key={item.review_id}>
              <strong>Người mua đã xác minh</strong>
              <span aria-label={`${item.rating} trên 5 sao`}>
                {"★".repeat(item.rating)}
                {"☆".repeat(5 - item.rating)}
              </span>
              <time dateTime={item.created_at}>
                {new Date(item.created_at).toLocaleDateString("vi-VN")}
              </time>
              {item.comment && <p>{item.comment}</p>}
            </article>
          ))}
          {data.total > data.page_size && (
            <nav aria-label="Trang đánh giá" className="checkout-links">
              <button disabled={page === 1} onClick={() => load(page - 1)}>
                Trang trước
              </button>
              <span>
                Trang {page} / {Math.ceil(data.total / data.page_size)}
              </span>
              <button
                disabled={page * data.page_size >= data.total}
                onClick={() => load(page + 1)}
              >
                Trang sau
              </button>
            </nav>
          )}
        </>
      )}
    </section>
  );
}
