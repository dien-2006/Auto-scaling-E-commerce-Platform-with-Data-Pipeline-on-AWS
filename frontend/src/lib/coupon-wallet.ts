export type SavedCoupon = {code:string; expires_at:string};
type WalletStorage = Pick<Storage,"getItem"|"setItem">;
function key(userId:string) {
  if (!/^[1-9]\d{0,18}$/.test(userId)) throw new Error("Invalid account");
  return `coco.coupons.v1:${userId}`;
}
export function readCoupons(storage:WalletStorage,userId:string,now=Date.now()):SavedCoupon[] {
  const raw=storage.getItem(key(userId));
  if(!raw)return [];
  let rows:unknown;try {rows=JSON.parse(raw);} catch{return [];}
  if(!Array.isArray(rows))return [];
  const seen=new Set<string>();
  return rows.slice(0,100).filter((v):v is SavedCoupon=>{
    if(!v || typeof v.code!=="string" || !v.code.trim() || v.code.length>50 || typeof v.expires_at!=="string" || !Number.isFinite(Date.parse(v.expires_at)) || Date.parse(v.expires_at)<=now || seen.has(v.code))return false;
    seen.add(v.code);return true;
  }).map(v=>({code:v.code,expires_at:v.expires_at}));
}
export function saveCoupon(storage:WalletStorage,userId:string,coupon:SavedCoupon):SavedCoupon[] {
  const rows=readCoupons(storage,userId);
  if (!coupon.code.trim() || coupon.code.length>50 || !Number.isFinite(Date.parse(coupon.expires_at)) || Date.parse(coupon.expires_at)<=Date.now())throw new Error("Mã đã hết hạn hoặc không hợp lệ.");
  if(!rows.some(row=>row.code===coupon.code)) {
    if(rows.length>=100)throw new Error("Bạn đã lưu đủ 100 mã trên trình duyệt này.");
    rows.push(coupon);
  }
  storage.setItem(key(userId),JSON.stringify(rows));return rows;
}
