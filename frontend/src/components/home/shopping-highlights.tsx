"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { useSession } from "@/components/auth/session-provider";
import { readCoupons, saveCoupon } from "@/lib/coupon-wallet";
import Image from "next/image";
import { ShoppingIcon } from "@/components/home/shopping-icon";

type Deal = {
  product_id: string;
  product_name: string;
  price: string;
  primary_image_url: string | null;
  original_price: string;
  sale_price: string;
  discount_percent: string;
  coupon_code: string | null;
  ends_at: string | null;
};

type FeaturedProduct = Pick<Deal, "product_id" | "product_name" | "price" | "primary_image_url">;

export function ShoppingHighlights() {
  const {account} = useSession();
  const [wallet,setWallet] = useState<{userId:string; codes:string[]}>({userId:"",codes:[]});
  const [walletNotice,setWalletNotice] = useState("");
  const [walletError,setWalletError] = useState("");
  useEffect(()=>{
    let active=true;
    Promise.resolve().then(()=>{
      if(!account)return;
      try {const rows=readCoupons(localStorage,account.user_id);if(active)setWallet({userId:account.user_id,codes:rows.map(row=>row.code)});}catch{if(active)setWalletError("Không đọc được mã đã lưu trên trình duyệt.");}
    });
    return()=>{active=false;};
  },[account]);
  function keepCoupon(code:string,expires_at:string) {
    if(!account)return;
    setWalletNotice("");setWalletError("");
    try {const rows=saveCoupon(localStorage,account.user_id,{code,expires_at});setWallet({userId:account.user_id,codes:rows.map(row=>row.code)});setWalletNotice(`Đã lưu mã ${code}.`);}
    catch(e){setWalletError(e instanceof Error?e.message:"Không lưu được mã.");}
  }
  const [featured, setFeatured] = useState<FeaturedProduct[]>([]);
  const [ranked, setRanked] = useState(false);
  const [featuredState, setFeaturedState] = useState("loading");
  useEffect(() => {
    let active = true;
    fetch("/api/products/bestsellers").then(async response => {
      if (!response.ok) throw new Error("Unavailable");
      const data = await response.json();
      if (!Array.isArray(data.items) || typeof data.ranked !== "boolean") throw new Error("Invalid response");
      if (active) { setFeatured(data.items); setRanked(data.ranked); setFeaturedState("ready"); }
    }).catch(() => { if (active) setFeaturedState("error"); });
    return () => { active = false; };
  }, []);
  const rail = useRef<HTMLDivElement>(null);
  const [now, setNow] = useState(0);
  useEffect(() => {
    const tick = setInterval(() => setNow(Date.now()), 1000);
  return () => clearInterval(tick);
  }, []);
  const [deals, setDeals] = useState<Deal[]>([]);
  const [failed, setFailed] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDeals() {
      try {
        const response = await fetch("/api/deals/today");

        if (!response.ok) {
          throw new Error("Không thể tải Deal");
        }

        const data = await response.json();
        if (!Array.isArray(data.items)) throw new Error("Invalid response");
        setDeals(data.items);
      } catch {
        setFailed(true);
      } finally {
        setLoading(false);
      }
    }

    loadDeals();
  }, []);

    const activeDeals = deals.filter(p => Number(p.discount_percent) > 0 && Number(p.discount_percent) < 30 && (!p.ends_at || !now || Date.parse(p.ends_at) > now));
  const offers = activeDeals.filter((deal, index, list) => deal.coupon_code && list.findIndex(item => item.coupon_code === deal.coupon_code) === index).slice(0, 6);
  const deadlines = activeDeals.flatMap(p => p.ends_at ? [Date.parse(p.ends_at)] : []).filter(Number.isFinite);
  const nearestEnd = deadlines.length ? Math.min(...deadlines) : null;


  return (
    <div className="shopping-highlights coco-highlight-sections">

      <section
        id="flash-sale"
        className="coco-deal-section"
        aria-labelledby="flash-sale-title"
      >
        <div className="coco-deal-heading">
          <h2 id="flash-sale-title">
            <ShoppingIcon name="bolt" />
            <span><b>FLASH</b> SALE</span>
          </h2>

          {nearestEnd && <div className="deal-header-clock" aria-label="Ưu đãi kết thúc gần nhất">
            <small>Kết thúc gần nhất</small>
            <time dateTime={new Date(nearestEnd).toISOString()}>{now ? formatRemaining(nearestEnd - now) : "…"}</time>
          </div>}
        </div>

        <div className="deal-controls">
          <button type="button" onClick={() => rail.current?.scrollBy({left: -600, behavior: "smooth"})}>← Xem trước</button>
          <button type="button" onClick={() => rail.current?.scrollBy({left: 600, behavior: "smooth"})}>Xem tiếp →</button>
        </div>
        {failed ? (<p role="alert">Không thể tải Deal. Vui lòng tải lại trang để thử lại.</p>) : loading ? (
          <p>Đang tải sản phẩm...</p>
        ) : activeDeals.length > 0 ? (
          <div ref={rail} className="coco-deal-products" tabIndex={0} aria-label="Danh sách Deal, cuộn ngang để xem tiếp">
            {activeDeals.map((product) => (
              <Link
                key={product.product_id}
                href={`/san-pham/${product.product_id}`}
                className="coco-deal-product"
              >
                {product.primary_image_url ? <Image src={product.primary_image_url} alt={product.product_name} width={220} height={220} unoptimized /> : <span>Chưa có ảnh</span>}
                <h3 title={product.product_name}>{product.product_name}</h3>

                {product.coupon_code && Number(product.discount_percent) > 0 && <span className="deal-discount">-{product.discount_percent}%</span>}
                {product.coupon_code ? <>
                  <del>{Number(product.original_price).toLocaleString("vi-VN")}đ</del>
                  <strong>{Number(product.sale_price).toLocaleString("vi-VN")}đ</strong>
                  <span className="deal-code-strip">Mã: {product.coupon_code}</span>
                </> : <strong>{Number(product.price).toLocaleString("vi-VN")}đ</strong>}
              </Link>
            ))}
          </div>
        ) : (
          <div className="coco-deal-empty">
            <ShoppingIcon name="ticket" />
            <div>
              <h3>Chờ đón những ưu đãi mới</h3>
              <p>Hiện chưa có sản phẩm giảm giá phù hợp.</p>
            </div>
            <Link href="/san-pham" className="coco-outline-link">
              Khám phá sản phẩm →
            </Link>
          </div>
        )}
      </section>

      <section id="ban-chay" className="home-featured-section" aria-labelledby="best-sellers-title">
        <div className="coco-deal-heading">
          <h2 id="best-sellers-title"><ShoppingIcon name="star" />{ranked ? "Sản phẩm bán chạy" : "Khám phá sản phẩm"}</h2>
          <Link href="/san-pham?sort=newest" className="coco-outline-link">Xem tất cả →</Link>
        </div>
        {featuredState === "loading" ? <p>Đang tải sản phẩm…</p> : featuredState === "error" ? <p role="alert">Không thể tải sản phẩm. Vui lòng tải lại trang.</p> : featured.length === 0 ? <p>Chưa có sản phẩm để hiển thị.</p> : <>
          <div className="home-featured-products">
            {featured.map(product => <Link className="home-featured-card" href={`/san-pham/${product.product_id}`} key={product.product_id}>
              {product.primary_image_url ? <Image src={product.primary_image_url} alt={product.product_name} width={220} height={220} unoptimized /> : <span className="home-featured-placeholder">Chưa có ảnh</span>}
              <h3 title={product.product_name}>{product.product_name}</h3>
              <strong>{Number(product.price).toLocaleString("vi-VN")}đ</strong>
            </Link>)}
          </div>
        </>}
      </section>

      <section id="uu-dai" className="home-offers-section" aria-labelledby="offers-title">
        <h2 id="offers-title"><ShoppingIcon name="gift" />Ưu đãi dành cho bạn</h2>
        {walletNotice && <p role="status">{walletNotice}</p>}
        {walletError && <p role="alert">{walletError}</p>}
        {loading ? <p>Đang tải ưu đãi…</p> : failed ? <p role="alert">Không thể tải ưu đãi. Vui lòng tải lại trang.</p> : offers.length === 0 ? <p>Chưa có ưu đãi còn hiệu lực.</p> :
          <div className="home-offer-cards">
            {offers.map(offer => <article className="home-offer-card" key={offer.coupon_code}>
              <strong>Giảm {offer.discount_percent}%</strong>
              <code>{offer.coupon_code}</code>
              {account && offer.coupon_code && offer.ends_at ? <button className="coupon-save-button" type="button" disabled={wallet.userId===account.user_id && wallet.codes.includes(offer.coupon_code)} onClick={()=>keepCoupon(offer.coupon_code!,offer.ends_at!)}>{wallet.userId===account.user_id && wallet.codes.includes(offer.coupon_code)?"Đã lưu":"Lưu mã"}</button> : <Link href="/dang-nhap?returnTo=%2F%23uu-dai">Đăng nhập để lưu</Link>}
              {offer.ends_at && <time dateTime={offer.ends_at}>HSD: {new Date(offer.ends_at).toLocaleDateString("vi-VN", { timeZone: "Asia/Ho_Chi_Minh" })}</time>}
              <Link href={`/san-pham/${offer.product_id}`}>Xem sản phẩm →</Link>
            </article>)}
          </div>}
      </section>
    </div>
  );
}
function formatRemaining(ms: number): string {
  const seconds = Math.max(0, Math.floor(ms / 1000));
  const days = Math.floor(seconds / 86400);
  const clock = [Math.floor(seconds / 3600) % 24, Math.floor(seconds / 60) % 60, seconds % 60].map(v => String(v).padStart(2, "0")).join(":");
  return `${days ? `${days} ngày ` : ""}${clock}`;
}
