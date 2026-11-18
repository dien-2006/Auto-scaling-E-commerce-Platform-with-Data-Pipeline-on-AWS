import { proxyPublicProducts } from "@/lib/auth-proxy";
export const runtime = "nodejs";
export function GET(request: Request) {
  return proxyPublicProducts(request);
}
