"use client";

import { useTransition } from "react";
import { useRouter } from "next/navigation";

export function CatalogRetry() {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  return (
    <button
      type="button"
      className="primary-button mt-5 disabled:opacity-60"
      disabled={pending}
      onClick={() => startTransition(() => router.refresh())}
    >
      {pending ? "Đang tải lại…" : "Thử lại"}
    </button>
  );
}

export function CatalogFailure() {
  return (
    <div role="alert" className="catalog-message">
      <span className="text-3xl text-brand" aria-hidden="true">
        ↻
      </span>
      <h3 className="mt-3 text-lg font-semibold">Chưa thể tải sản phẩm</h3>
      <p className="mt-2 text-sm text-muted">Vui lòng thử lại sau giây lát.</p>
      <CatalogRetry />
    </div>
  );
}

export function CatalogSkeleton() {
  return (
    <div role="status" aria-live="polite" className="py-8">
      <span className="sr-only">Đang tải danh mục và sản phẩm…</span>
      <div aria-hidden="true" className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {[1, 2, 3, 4].map((index) => (
          <div
            key={index}
            className="h-72 rounded-2xl bg-ink/5 motion-safe:animate-pulse"
          />
        ))}
      </div>
    </div>
  );
}
