import { proxySellerShop } from "@/lib/auth-proxy";
export const runtime = "nodejs";
export function GET(request: Request) {
  return proxySellerShop(request);
}
export const POST = GET;
export const PATCH = GET;
