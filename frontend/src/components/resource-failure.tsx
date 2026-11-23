import { CatalogRetry } from "@/components/home/catalog-feedback";

export function ResourceFailure({ kind }: { kind: "sản phẩm" | "gian hàng" }) {
  return (
    <section className="shell py-12">
      <div role="alert" className="catalog-message">
        <h1 className="text-2xl font-semibold text-brand">
          Chưa thể tải {kind}
        </h1>
        <p className="mt-3 text-sm text-muted">
          Vui lòng thử lại sau giây lát.
        </p>
        <CatalogRetry />
      </div>
    </section>
  );
}
