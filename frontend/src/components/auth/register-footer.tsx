import Link from "next/link";
import { BrandLogo } from "@/components/layout/brand-logo";
import { ShoppingIcon } from "@/components/home/shopping-icon";
export function RegisterFooter() {
  return <footer className="register-footer"><nav className="register-services" aria-label="Thông tin mua sắm">{([
    ["truck","Thông tin giao hàng","Tìm hiểu trước khi mua"],["shield","Mua sắm minh bạch","Thông tin từ gian hàng"],["return","Đổi trả & hỗ trợ","Chính sách đang hoàn thiện"],["support","Chăm sóc khách hàng","Hướng dẫn sử dụng coco"],
  ] as const).map(([icon,title,description])=><Link href="/#ho-tro" key={title}><ShoppingIcon name={icon}/><span><strong>{title}</strong><small>{description}</small></span></Link>)}</nav><div className="register-footer-columns"><div><BrandLogo/><p>Không chỉ mua sắm,<br/>mà còn là trải nghiệm tốt hơn mỗi ngày.</p></div><div><h2>Về COCO</h2><Link href="/#ve-chung-toi">Giới thiệu</Link><Link href="/san-pham">Khám phá sản phẩm</Link><Link href="/#ho-tro">Trung tâm trợ giúp</Link></div><div><h2>Thông tin mua sắm</h2><Link href="/#ho-tro">Giao hàng & đổi trả</Link><Link href="/#ho-tro">Thanh toán COD</Link><Link href="/#ho-tro">Tài khoản & bảo mật</Link></div><div><h2>Tài khoản</h2><Link href="/dang-nhap">Đăng nhập</Link><Link href="/dang-ky" aria-current="page">Đăng ký</Link><Link href="/tai-khoan">Tài khoản của tôi</Link></div></div></footer>;
}
