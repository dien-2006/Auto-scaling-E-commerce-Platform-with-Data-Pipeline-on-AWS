import Link from "next/link";
import { beautyCategories } from "@/lib/categories";
import { CategoryIcon } from "@/components/category-icon";
import { ShoppingIcon } from "@/components/home/shopping-icon";

/** Original decorative shopping artwork; never a catalog photo or live offer. */
function ShoppingArtwork() {
  return <svg className="coco-shopping-art" viewBox="0 0 440 350" fill="none" aria-hidden="true">
    <defs>
      <linearGradient id="bag-blue" x1="200" y1="95" x2="360" y2="320" gradientUnits="userSpaceOnUse"><stop stopColor="#f7fdff" /><stop offset=".48" stopColor="#87d7f9" /><stop offset="1" stopColor="#34a7df" /></linearGradient>
      <linearGradient id="gift-blue" x1="300" y1="220" x2="400" y2="330" gradientUnits="userSpaceOnUse"><stop stopColor="#bdecff" /><stop offset="1" stopColor="#2899d5" /></linearGradient>
      <linearGradient id="handle-blue" x1="225" y1="35" x2="310" y2="140" gradientUnits="userSpaceOnUse"><stop stopColor="#f4fdff" /><stop offset=".45" stopColor="#2093cf" /><stop offset="1" stopColor="#a2e6ff" /></linearGradient>
    </defs>
    <ellipse cx="267" cy="321" rx="154" ry="16" fill="#328ec0" opacity=".13" />
    <circle cx="272" cy="166" r="135" fill="white" opacity=".16" />
    <path d="M233 122V82c0-63 76-63 76 0v40" stroke="#2188bd" strokeWidth="15" />
    <path d="M229 119V82c0-63 76-63 76 0v37" stroke="url(#handle-blue)" strokeWidth="12" />
    <path d="m196 115 139-9 37 201-192 8 16-200Z" fill="url(#bag-blue)" stroke="#d9f5ff" strokeWidth="2" />
    <path d="m335 106 27 25 21 173-11 3-37-201Z" fill="#43b3e8" />
    <circle cx="228" cy="134" r="5" fill="#319bce" /><circle cx="308" cy="129" r="5" fill="#319bce" />
    <path d="m238 188 17 3 11 49h47l13-37h-67" stroke="white" strokeWidth="7" strokeLinecap="round" strokeLinejoin="round" />
    <circle cx="273" cy="254" r="5" fill="white" /><circle cx="308" cy="254" r="5" fill="white" />
    <path d="M116 231v-25c0-39 49-39 49 0v25" stroke="#66bee7" strokeWidth="9" />
    <path d="m99 223 81-8 21 106-111 4 9-102Z" fill="#d9f5ff" stroke="#effbff" strokeWidth="2" />
    <text x="113" y="284" fill="#2485b9" fontSize="23" fontWeight="800" fontFamily="Arial, sans-serif">coco</text>
    <rect x="303" y="257" width="91" height="66" rx="7" fill="url(#gift-blue)" />
    <rect x="297" y="246" width="103" height="20" rx="5" fill="#d0f2ff" />
    <path d="M344 248v75" stroke="#2998d4" strokeWidth="15" />
    <path d="M345 247c-53-4-46-43-20-27 13 8 20 27 20 27Zm0 0c46-5 49-43 23-28-13 7-23 28-23 28Z" fill="#9cdef9" stroke="#effbff" strokeWidth="3" />
    <path d="m365 42 5 14 15 5-15 6-5 15-6-15-15-6 15-5 6-14ZM145 94l4 11 12 5-12 4-4 12-5-12-11-4 11-5 5-11Z" fill="#fff3b8" />
    <circle cx="389" cy="177" r="4" fill="white" /><circle cx="160" cy="156" r="3" fill="white" /><path d="M111 134v12m-6-6h12" stroke="white" strokeWidth="2" />
  </svg>;
}

export function CampaignBanners() {
  return <div className="home-discovery">
    <nav id="danh-muc" className="home-category-menu" aria-label="Danh mục sản phẩm">
      <h2><span aria-hidden="true">☰</span> Danh mục sản phẩm</h2>
      <ul>{beautyCategories.map((category) => <li key={category.key}><Link href={`/san-pham?danh-muc=${category.slug}`}><CategoryIcon category={category.key} /><span>{category.name}</span><span className="category-chevron" aria-hidden="true">›</span></Link></li>)}</ul>
      <Link className="home-category-all" href="/san-pham">Tất cả sản phẩm <span aria-hidden="true">→</span></Link>
    </nav>
    <div className="home-discovery-content">
      <section className="coco-campaign-grid" aria-label="Khám phá cùng coco">
        <div className="coco-main-campaign">
          <div className="coco-campaign-copy"><span className="coco-campaign-logo">coco<span aria-hidden="true">ˊ</span></span><h1>Mua sắm thả ga.<br />Chăm chút mỗi ngày.</h1><p>Sức khỏe & làm đẹp, theo cách của bạn.</p><Link className="coco-campaign-cta" href="/san-pham">Khám phá ngay <span aria-hidden="true">→</span></Link></div>
          <ShoppingArtwork />
        </div>
        <div className="coco-side-campaigns">
          <Link href="/san-pham?danh-muc=cham-soc-da-mat" className="coco-side-campaign"><ShoppingIcon name="sparkle" /><span><strong>Chăm sóc da</strong><small>Nâng niu mỗi ngày</small></span><span aria-hidden="true">›</span></Link>
          <Link href="/san-pham?danh-muc=nuoc-hoa" className="coco-side-campaign"><ShoppingIcon name="gift" /><span><strong>Dấu hương riêng</strong><small>Khám phá nước hoa</small></span><span aria-hidden="true">›</span></Link>
        </div>
      </section>
      <nav className="home-shortcuts" aria-label="Khám phá mua sắm">
        {([
          ["ticket", "Mã giảm giá", "/#uu-dai"], ["truck", "Giao hàng", "/#ho-tro"], ["bolt", "Deal sốc", "/#flash-sale"], ["star", "Bán chạy", "/#ban-chay"], ["gift", "Ưu đãi thành viên", "/#uu-dai"],
        ] as const).map(([icon, label, href]) => <Link key={label} href={href}><span className={`shortcut-icon shortcut-${icon}`}><ShoppingIcon name={icon} /></span><span>{label}</span></Link>)}
      </nav>
    </div>
  </div>;
}
