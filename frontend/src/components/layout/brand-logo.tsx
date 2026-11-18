import Image from "next/image";
import Link from "next/link";
import { siteBrand } from "@/lib/site-brand";
export function BrandLogo() {
  return (
    <Link
      href="/"
      className="header-logo"
      aria-label={`${siteBrand.name} — Trang chủ`}
    >
      <Image
        className="coco-brand-image"
        src="/images/coco-logo-transparent.png"
        alt={siteBrand.name}
        width={2193}
        height={717}
        priority
      />
    </Link>
  );
}
