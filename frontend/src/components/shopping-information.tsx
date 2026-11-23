import Link from "next/link";
import { ShoppingIcon } from "@/components/home/shopping-icon";
export function ShoppingInformation() {
 return <aside className="product-service-info" aria-label="Thông tin mua sắm">{([
 ["shield","Thông tin từ gian hàng","Xem tên shop và mô tả trước khi lựa chọn."],
 ["truck","Giao hàng & thanh toán","Dự kiến hỗ trợ COD mô phỏng khi mở đặt hàng."],
 ["return","Đổi trả & hỗ trợ","Chính sách đang được hoàn thiện."],
 ] as const).map(([icon,title,description])=><Link href="/#ho-tro" key={title}><ShoppingIcon name={icon}/><span><strong>{title}</strong><small>{description}</small></span></Link>)}</aside>;
}
