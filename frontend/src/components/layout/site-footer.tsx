import Link from "next/link";
import { beautyCategories } from "@/lib/categories";
import { BrandLogo } from "@/components/layout/brand-logo";
import { ShoppingIcon } from "@/components/home/shopping-icon";
export function SiteFooter() {
  return <footer id="ve-chung-toi" className="coco-footer">
    <div className="shell"><nav className="coco-service-strip" aria-label="Thông tin mua sắm">
      {([ ["truck", "Thông tin giao hàng", "Tìm hiểu trước khi mua"], ["shield", "Mua sắm minh bạch", "Thông tin từ gian hàng"], ["return", "Đổi trả & hoàn tiền", "Chính sách đang hoàn thiện"], ["support", "Hỗ trợ khách hàng", "Giải đáp cách sử dụng"] ] as const).map(([icon,title,description]) => <Link href="/#ho-tro" key={title}><ShoppingIcon name={icon} /><span><strong>{title}</strong><small>{description}</small></span></Link>)}
    </nav><div className="coco-footer-grid">
      <div className="coco-footer-brand"><BrandLogo /><p>Sàn thương mại điện tử<br />Sức khỏe & Làm đẹp</p><small>Chăm chút từng ngày, theo cách của bạn.</small></div>
      <div><h2>Mua sắm cùng coco</h2><Link href="/#danh-muc">Danh mục sản phẩm</Link><Link href="/#flash-sale">Deal sốc hôm nay</Link><Link href="/#ban-chay">Sản phẩm bán chạy</Link><Link href="/#uu-dai">Ưu đãi thành viên</Link></div>
      <div><h2>Khám phá danh mục</h2>{beautyCategories.map(category => <Link key={category.key} href={`/san-pham?danh-muc=${category.slug}`}>{category.name}</Link>)}</div>
      <section id="ho-tro" className="coco-footer-support"><h2>Hỗ trợ khách hàng</h2><details><summary>Cách tìm và xem sản phẩm</summary><p>Tìm theo tên ở thanh tìm kiếm hoặc chọn một trong sáu danh mục. Bấm vào sản phẩm để xem chi tiết và tên gian hàng để xem shop.</p></details><details><summary>Giao hàng, thanh toán & đổi trả</summary><p>Bạn có thể đặt hàng COD mô phỏng từ giỏ sau khi chọn địa chỉ. Chưa tích hợp vận chuyển hoặc thanh toán tiền thật; chính sách đổi trả đang hoàn thiện.</p></details><details><summary>Tài khoản & bảo mật</summary><p>Bạn có thể đăng ký, đăng nhập và đăng xuất bằng tài khoản coco. Khu vực người bán đang được phát triển; xem sản phẩm công khai không cần đăng nhập.</p></details><p className="coco-project-note">Nền tảng thương mại điện tử tự động mở rộng trên AWS.</p></section>
    </div><div className="coco-footer-bottom">coco · Sức khỏe & làm đẹp mỗi ngày <Link href="/san-pham">Khám phá sản phẩm →</Link></div></div>
  </footer>;
}
