"use client";

import Link from "next/link";

export default function ErrorPage({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <section role="alert" className="mx-auto max-w-xl px-5 py-24 text-center">
      <h1 className="text-3xl font-semibold">Chưa thể tải nội dung</h1>
      <p className="mt-4 leading-7 text-muted">Vui lòng thử lại sau giây lát.</p>
      <div className="mt-7 flex flex-wrap justify-center gap-4">
        <button type="button" onClick={reset} className="rounded-full bg-brand px-6 py-3 text-sm font-semibold text-white">Thử lại</button>
        <Link href="/" className="rounded-full border border-ink/20 px-6 py-3 text-sm font-semibold">Về trang chủ</Link>
      </div>
    </section>
  );
}
