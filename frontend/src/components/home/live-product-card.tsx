"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { NavigationHint } from "@/components/navigation-hint";
import type { PublicProduct } from "@/lib/catalog-api";
import { formatVnd } from "@/lib/categories";

export function LiveProductCard({ product }: { product: PublicProduct }) {
  const [imageFailed, setImageFailed] = useState(false);
  return (
    <article className="product-card">
      <Link href={`/san-pham/${product.product_id}`} aria-label={product.product_name} className="relative flex aspect-square items-center justify-center bg-[#f1f3ed]">
        {product.primary_image_url && !imageFailed ? (
          <Image
            unoptimized
            src={product.primary_image_url}
            alt={product.product_name}
            fill
            sizes="(max-width: 767px) 50vw, 25vw"
            className="object-contain p-4"
            onError={() => setImageFailed(true)}
          />
        ) : (
          <div className="text-center text-muted">
            <svg
              aria-hidden="true"
              viewBox="0 0 80 72"
              width="80"
              height="72"
              className="mx-auto"
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
              <path
                d="M28 65h24"
                stroke="#c5daeb"
                strokeWidth="2"
                strokeLinecap="round"
              />
            </svg>
            <p className="mt-2 text-xs">Chưa có hình ảnh</p>
          </div>
        )}
      </Link>
      <div className="p-4">
        <Link
          href={`/gian-hang/${encodeURIComponent(product.shop.shop_slug)}`}
          className="text-xs text-muted hover:text-brand"
        >
          {product.shop.shop_name}
          <NavigationHint />
        </Link>
        <h3 className="mt-2 min-h-12 text-sm leading-6 font-semibold">
          <Link
            href={`/san-pham/${product.product_id}`}
            className="hover:text-brand"
          >
            {product.product_name}
            <NavigationHint />
          </Link>
        </h3>
        <p className="mt-3 text-lg font-semibold text-brand">
          {formatVnd(product.price)}
        </p>
        <p
          className={`mt-2 text-xs ${product.in_stock ? "text-brand" : "text-muted"}`}
        >
          {product.in_stock ? "Còn hàng" : "Tạm hết hàng"}
        </p>

      </div>
    </article>
  );
}
