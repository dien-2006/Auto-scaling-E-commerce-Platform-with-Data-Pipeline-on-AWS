import type { Metadata } from "next";
import type { ReactNode } from "react";
import localFont from "next/font/local";
import { SiteFooter } from "@/components/layout/site-footer";
import { SiteHeader } from "@/components/layout/site-header";
import "./globals.css";
import { siteBrand } from "@/lib/site-brand";
import { SessionProvider } from "@/components/auth/session-provider";
import { SiteFrame } from "@/components/layout/site-frame";

const notoSans = localFont({
  src: "./fonts/NotoSans-Variable.ttf",
  variable: "--font-noto-sans",
  display: "swap",
  weight: "100 900",
});

export const metadata: Metadata = {
  icons: { icon: "/images/coco-logo-transparent.png?v=2" },
  title: {
    default: `${siteBrand.name} | Chăm chút từng ngày`,
    template: `%s | ${siteBrand.name}`,
  },
  description:
    "Nền tảng thương mại điện tử đa người bán. Khám phá sản phẩm và kết nối với những gian hàng yêu thích.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="vi" className={notoSans.variable}>
      <body className="flex min-h-dvh flex-col antialiased">
        <a className="skip-link" href="#noi-dung-chinh">
          Đến nội dung chính
        </a>
        <SessionProvider>
          <SiteFrame header={<SiteHeader />} footer={<SiteFooter />}>
            <main
              id="noi-dung-chinh"
              tabIndex={-1}
              className="flex-1 outline-none"
            >
              {children}
            </main>
          </SiteFrame>
        </SessionProvider>
      </body>
    </html>
  );
}
