import { CategoryNavigation } from "@/components/category-navigation";
import { AddToCart } from "@/components/cart/add-to-cart";
import { ShoppingInformation } from "@/components/shopping-information";
import type { Metadata } from "next";
import Link from "next/link";
import { cache, Suspense } from "react";
import { notFound } from "next/navigation";
import { getProductDetail, getProductPage } from "@/lib/catalog-api";
import { formatVnd } from "@/lib/categories";
import { ProductGallery } from "@/components/product-gallery";
import { ProductReviews } from "@/components/product-reviews";
import { LiveProductCard } from "@/components/home/live-product-card";
import {
  CatalogFailure,
  CatalogSkeleton,
} from "@/components/home/catalog-feedback";
import { NavigationHint } from "@/components/navigation-hint";
import { ResourceFailure } from "@/components/resource-failure";

export const dynamic = "force-dynamic";
// The existing dynamic path now uses the exact BIGINT product ID instead of preview slugs.
const loadProduct = cache(getProductDetail);
export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const result = await loadProduct(slug);
  return {
    title: result.ok
      ? result.data.product_name
      : result.notFound
        ? "Không tìm thấy sản phẩm"
        : "Sản phẩm",
  };
}
async function RelatedProducts({
  categoryId,
  productId,
}: {
  categoryId: string;
  productId: string;
}) {
  const result = await getProductPage({ categoryId, pageSize: 5 });
  if (!result.ok) return <CatalogFailure />;
  const products = result.data.items
    .filter((product) => product.product_id !== productId)
    .slice(0, 4);
  return products.length ? (
    <div className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
      {products.map((product) => (
        <LiveProductCard key={product.product_id} product={product} />
      ))}
    </div>
  ) : (
    <p className="mt-5 text-sm text-muted">
      Chưa có sản phẩm khác trong danh mục này.
    </p>
  );
}
export default async function ProductPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const result = await loadProduct(slug);
  if (!result.ok) {
    if (result.notFound) notFound();
    return <ResourceFailure kind="sản phẩm" />;
  }
  const product = result.data;
  return (
    <div className="shell storefront-page">
      <div className="storefront-sidebar">
        <CategoryNavigation />
      </div>
      <div className="storefront-content">
        <nav aria-label="Đường dẫn" className="resource-breadcrumb">
          <Link href="/">Trang chủ</Link>
          <span>/</span>
          <Link href="/san-pham">Sản phẩm</Link>
          <span>/</span>
          <span>{product.product_name}</span>
        </nav>
        <div className="product-detail-grid">
          <ProductGallery
            key={product.product_id}
            name={product.product_name}
            images={product.images}
            primaryUrl={product.primary_image_url}
          />
          <section
            className="product-detail-summary"
            aria-labelledby="product-title"
          >
            <p className="eyebrow">COCO · CHĂM CHÚT MỖI NGÀY</p>
            <h1 id="product-title">{product.product_name}</h1>
            <Link
              href={`/gian-hang/${encodeURIComponent(product.shop.shop_slug)}`}
              className="product-shop-link"
            >
              Gian hàng: {product.shop.shop_name} ↗<NavigationHint />
            </Link>
            <div className="product-detail-price">
              {formatVnd(product.price)}
              <span>Giá bán từ gian hàng</span>
            </div>
            <dl className="product-details-specs">
              <div>
                <dt>Mã SKU</dt>
                <dd>{product.sku}</dd>
              </div>
              <div>
                <dt>Tình trạng</dt>
                <dd className={product.in_stock ? "text-brand" : "text-muted"}>
                  {product.in_stock ? "Còn hàng" : "Tạm hết hàng"}
                </dd>
              </div>
              <div>
                <dt>Tồn kho hiện tại</dt>
                <dd>
                  {new Intl.NumberFormat("vi-VN").format(
                    product.available_quantity,
                  )}{" "}
                  sản phẩm
                </dd>
              </div>
            </dl>
            <AddToCart
              productId={product.product_id}
              shopId={product.shop.shop_id}
              availableQuantity={product.available_quantity}
            />
            <Link
              href={`/gian-hang/${encodeURIComponent(product.shop.shop_slug)}`}
              className="primary-button mt-6"
            >
              Xem gian hàng ↗<NavigationHint />
            </Link>
          </section>
          <ShoppingInformation />
        </div>
        <section className="product-description">
          <h2>Mô tả sản phẩm</h2>
          <p>
            {product.description?.trim() ||
              "Gian hàng chưa cung cấp mô tả cho sản phẩm này."}
          </p>
        </section>
        <ProductReviews
          key={product.product_id}
          productId={product.product_id}
        />
        <section className="mt-10">
          <div className="section-heading">
            <h2>Cùng danh mục, thêm lựa chọn</h2>
            <Link href="/san-pham" className="text-sm text-brand">
              Khám phá sản phẩm ↗
            </Link>
          </div>
          <Suspense fallback={<CatalogSkeleton />}>
            <RelatedProducts
              categoryId={product.category_id}
              productId={product.product_id}
            />
          </Suspense>
        </section>
      </div>
    </div>
  );
}
