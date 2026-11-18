import { proxySellerProducts } from "@/lib/auth-proxy";
export const runtime = "nodejs";
export async function GET(request: Request) {
  return proxySellerProducts(request);
}
export const POST = GET;
