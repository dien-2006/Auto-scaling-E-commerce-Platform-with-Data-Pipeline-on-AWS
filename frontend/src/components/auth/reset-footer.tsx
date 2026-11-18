import Link from "next/link";
import {BrandLogo} from "@/components/layout/brand-logo";
export function ResetFooter(){
  return <footer className="reset-footer"><div className="reset-footer-brand"><BrandLogo/><p>Mua sắm thông minh – Ưu đãi mỗi ngày</p></div><nav aria-label="Thông tin hỗ trợ"><Link href="/#ve-chung-toi"><span aria-hidden="true">ⓘ</span> Giới thiệu COCO</Link><Link href="/#ho-tro"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true"><path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6Z"/><path d="m8 12 3 3 5-6"/></svg> Hỗ trợ tài khoản</Link><Link href="/san-pham">Tiếp tục mua sắm</Link><Link href="/#ho-tro"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true"><path d="M4 14v-3a8 8 0 0 1 16 0v3M4 12H2v7h4v-7ZM20 12h2v7h-4v-7ZM19 19c0 2-2 3-6 3"/></svg> Liên hệ hỗ trợ</Link></nav></footer>;
}
