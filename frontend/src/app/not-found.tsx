import Link from "next/link";

export default function NotFound() {
  return (
    <section className="mx-auto max-w-xl px-5 py-24 text-center">
      <p className="text-sm font-semibold tracking-widest text-brand">404</p>
      <h1 className="mt-4 text-3xl font-semibold">Không tìm thấy trang</h1>
      <p className="mt-4 leading-7 text-muted">Đường dẫn có thể đã thay đổi. Bạn có thể trở về trang chủ để tiếp tục khám phá.</p>
      <Link href="/" className="mt-7 inline-block rounded-full bg-brand px-6 py-3 text-sm font-semibold text-white">Về trang chủ</Link>
    </section>
  );
}
