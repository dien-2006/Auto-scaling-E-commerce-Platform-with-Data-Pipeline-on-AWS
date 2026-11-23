import Image from "next/image";
import { siteBrand } from "@/lib/site-brand";

export function CatalogBanner() {
  return (
    <section className="catalog-banner" aria-labelledby="catalog-banner-title">
      <div className="catalog-banner-art" aria-hidden="true">
        <Image
          src="/images/coco-catalog-banner.png"
          alt=""
          fill
          priority
          sizes="(max-width: 767px) 100vw, 70vw"
          className="object-cover"
        />
      </div>
      <div className="catalog-banner-copy">
        <p>
          {siteBrand.name}
          <span>BEAUTY EDIT</span>
        </p>
        <h1 id="catalog-banner-title">
          Sức khỏe & làm đẹp.
          <br />
          <span>Chăm chút mỗi ngày.</span>
        </h1>
        <p className="catalog-banner-description">
          Khám phá những lựa chọn chăm sóc
          <br className="hidden sm:block" /> và làm đẹp dành riêng cho bạn.
        </p>
      </div>
      <span className="catalog-banner-note">Ảnh minh họa bộ sưu tập</span>
    </section>
  );
}
