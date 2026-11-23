"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import {
  createReview,
  myReview,
  type ProductReview,
} from "@/lib/shopping-client";

export function ReviewForm({ itemId, name }: { itemId: string; name: string }) {
  const [saved, setSaved] = useState<ProductReview | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const guard = useRef(false);
  useEffect(() => {
    let active = true;
    myReview(itemId)
      .then((value) => {
        if (active) {
          setSaved(value);
          setLoaded(true);
        }
      })
      .catch((e) => {
        if (active)
          setError(e instanceof Error ? e.message : "Chưa đọc được đánh giá.");
      });
    return () => {
      active = false;
    };
  }, [itemId, attempt]);
  async function submit(e: FormEvent) {
    e.preventDefault();
    if (guard.current || !loaded || saved) return;
    guard.current = true;
    setBusy(true);
    setError("");
    try {
      setSaved(await createReview(itemId, rating, comment));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Chưa xác nhận được đánh giá.");
      setLoaded(false);
    } finally {
      guard.current = false;
      setBusy(false);
    }
  }
  function reload() {
    setError("");
    setLoaded(false);
    setAttempt((v) => v + 1);
  }
  return (
    <div className="buyer-review-form">
      {saved ? (
        <>
          <strong>Đánh giá của bạn: {saved.rating}/5 sao</strong>
          {saved.comment && <p>{saved.comment}</p>}
        </>
      ) : (
        <form onSubmit={submit} aria-label={`Đánh giá ${name}`}>
          <h3>Đánh giá sản phẩm đã mua</h3>
          {error && <p role="alert">{error}</p>}
          {!loaded ? (
            <>
              <p role="status">
                {error
                  ? "Cần kiểm tra lại đánh giá trước khi gửi."
                  : "Đang kiểm tra đánh giá…"}
              </p>
              {error && (
                <button
                  type="button"
                  className="secondary-button"
                  onClick={reload}
                >
                  Tải lại đánh giá
                </button>
              )}
            </>
          ) : (
            <fieldset disabled={busy}>
              <label htmlFor={`rating-${itemId}`}>Số sao</label>
              <select
                id={`rating-${itemId}`}
                value={rating}
                onChange={(e) => setRating(Number(e.target.value))}
              >
                {[5, 4, 3, 2, 1].map((v) => (
                  <option key={v} value={v}>
                    {v} sao
                  </option>
                ))}
              </select>
              <label htmlFor={`comment-${itemId}`}>
                Nhận xét (không bắt buộc)
              </label>
              <textarea
                id={`comment-${itemId}`}
                value={comment}
                maxLength={2000}
                rows={3}
                onChange={(e) => setComment(e.target.value)}
              />
              <small>
                {comment.length}/2.000 ký tự · Mỗi dòng hàng được đánh giá một
                lần.
              </small>
              <button className="primary-button" type="submit">
                {busy ? "Đang gửi…" : "Gửi đánh giá"}
              </button>
            </fieldset>
          )}
        </form>
      )}
    </div>
  );
}
