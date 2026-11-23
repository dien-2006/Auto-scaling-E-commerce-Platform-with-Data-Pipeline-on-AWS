import Link from "next/link";
import { matchBeautyCategories } from "@/lib/categories";
import {
  getCategories,
  getProducts,
  type PublicProduct,
} from "@/lib/catalog-api";
import { CatalogFailure } from "@/components/home/catalog-feedback";
import { LiveProductCard } from "@/components/home/live-product-card";

export async function HomeCatalog({
  selected,
  query,
}: {
  selected: string;
  query: string;
}) {
  const result = await getCategories();
  if (!result.ok) return <CatalogFailure />;
  const mapped = matchBeautyCategories(result.data);
  const chosen = selected
    ? mapped.filter((item) => item.slug === selected)
    : mapped;
  const responses = await Promise.all(
    chosen
      .filter((item) => item.actual)
      .map((item) => getProducts(item.actual!.category_id, query)),
  );
  const failed = responses.some((response) => !response.ok);
  const unique = new Map<string, PublicProduct>();
  // Interleave categories instead of letting the first category fill the whole homepage.
  for (let index = 0; index < 12; index++)
    for (const response of responses)
      if (response.ok && response.data.items[index]) {
        const product = response.data.items[index];
        unique.set(product.product_id, product);
      }
  const products = [...unique.values()].slice(0, 12);
  return (
    <>
      <section
        id="san-pham"
        className="home-live-catalog scroll-mt-5"
        aria-labelledby="products-title"
      >
        <div className="section-heading border-b border-brand/15 pb-5">
          <div>
            <p className="eyebrow">DỮ LIỆU TỪ CÁC GIAN HÀNG</p>
            <h2 id="products-title">
              {selected
                ? (mapped.find((item) => item.slug === selected)?.name ??
                  "Danh mục không tồn tại")
                : "Gợi ý khám phá hôm nay"}
            </h2>
          </div>
          {(selected || query) && (
            <Link href="/#san-pham" className="text-sm text-brand">
              Xóa tìm kiếm và bộ lọc ×
            </Link>
          )}
        </div>
        {query && (
          <p className="mt-4 text-sm text-muted">Kết quả cho “{query}”</p>
        )}
        {failed ? (
          <CatalogFailure />
        ) : products.length ? (
          <>
            <p role="status" className="mt-5 text-xs text-muted">
              Hiển thị {products.length} sản phẩm mới cập nhật
            </p>
            <div className="mt-5 grid grid-cols-2 gap-3 sm:gap-5 md:grid-cols-3 xl:grid-cols-4">
              {products.map((product) => (
                <LiveProductCard key={product.product_id} product={product} />
              ))}
            </div>
          </>
        ) : (
          <div className="catalog-message">
            <span aria-hidden="true" className="text-4xl text-brand">
              ✧
            </span>
            <h3 className="mt-4 text-xl font-semibold">
              {query || selected
                ? "Chưa tìm thấy sản phẩm phù hợp"
                : "Sản phẩm đang được cập nhật"}
            </h3>
            <p className="mx-auto mt-3 max-w-md text-sm leading-7 text-muted">
              {query || selected
                ? "Bạn có thể thử từ khóa khác hoặc xem tất cả danh mục."
                : "Hãy quay lại để khám phá những lựa chọn mới từ các gian hàng."}
            </p>
            {(query || selected) && (
              <Link href="/#san-pham" className="primary-button mt-5">
                Xem tất cả danh mục ↗
              </Link>
            )}
          </div>
        )}
      </section>
    </>
  );
}
