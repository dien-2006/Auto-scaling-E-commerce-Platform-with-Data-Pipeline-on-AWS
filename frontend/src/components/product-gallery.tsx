"use client";
import Image from "next/image";
import { useRef, useState } from "react";
import type { ProductImage } from "@/lib/catalog-api";

export function ProductGallery({
  name,
  images,
  primaryUrl,
}: {
  name: string;
  images: ProductImage[];
  primaryUrl: string | null;
}) {
  const sorted = [...images].sort(
    (a, b) =>
      Number(b.is_primary) - Number(a.is_primary) ||
      a.sort_order - b.sort_order ||
      (BigInt(a.product_image_id) < BigInt(b.product_image_id) ? -1 : 1),
  );
  const urls = [
    ...new Set([
      ...sorted.flatMap((image) => (image.url ? [image.url] : [])),
      ...(primaryUrl ? [primaryUrl] : []),
    ]),
  ];
  const [index, setIndex] = useState(0);
  const [failed, setFailed] = useState<Set<string>>(() => new Set());
  const buttons = useRef<(HTMLButtonElement | null)[]>([]);
  const current = urls[index];
  const markFailed = (url: string) =>
    setFailed((previous) => new Set([...previous, url]));
  const select = (next: number, focus = false) => {
    const target = (next + urls.length) % urls.length;
    setIndex(target);
    if (focus) buttons.current[target]?.focus();
  };
  return (
    <div
      className="product-gallery"
      onKeyDown={(event) => {
        if (!urls.length) return;
        const next =
          event.key === "ArrowRight"
            ? index + 1
            : event.key === "ArrowLeft"
              ? index - 1
              : event.key === "Home"
                ? 0
                : event.key === "End"
                  ? urls.length - 1
                  : null;
        if (next !== null) {
          event.preventDefault();
          select(next, true);
        }
      }}
    >
      <div className="gallery-main">
        {current && !failed.has(current) ? (
          <Image
            key={current}
            src={current}
            alt={`${name} — ảnh ${index + 1}`}
            fill
            unoptimized
            priority
            className="object-contain p-6"
            sizes="(max-width: 767px) 100vw, 50vw"
            onError={() => markFailed(current)}
          />
        ) : (
          <div className="gallery-placeholder">
            <svg
              viewBox="0 0 80 72"
              width="90"
              height="82"
              fill="none"
              aria-hidden="true"
            >
              <rect
                x="11"
                y="10"
                width="58"
                height="50"
                rx="12"
                fill="#e5f2fc"
                stroke="#a4c5df"
                strokeWidth="1.5"
              />
              <circle cx="31" cy="27" r="6" fill="#c2dbed" />
              <path d="m18 51 15-15 10 9 10-13 10 19" fill="#c2dbed" />
            </svg>
            <p>
              {current ? "Ảnh chưa tải được" : "Ảnh sản phẩm đang cập nhật"}
            </p>
          </div>
        )}
      </div>
      {urls.length > 0 && (
        <>
          <div
            className="gallery-thumbnails"
            role="group"
            aria-label="Chọn ảnh sản phẩm"
          >
            {urls.map((url, position) => (
              <button
                key={url}
                type="button"
                ref={(element) => {
                  buttons.current[position] = element;
                }}
                onClick={() => select(position)}
                aria-label={`Xem ảnh ${position + 1}`}
                aria-pressed={position === index}
              >
                {failed.has(url) ? (
                  <span aria-hidden="true">{position + 1}</span>
                ) : (
                  <Image
                    src={url}
                    alt=""
                    fill
                    unoptimized
                    className="object-contain p-1"
                    sizes="64px"
                    onError={() => markFailed(url)}
                  />
                )}
              </button>
            ))}
          </div>
          <p role="status" className="gallery-caption">
            Ảnh {index + 1} / {urls.length} · Dùng phím ← → để chuyển ảnh
          </p>
        </>
      )}
    </div>
  );
}
