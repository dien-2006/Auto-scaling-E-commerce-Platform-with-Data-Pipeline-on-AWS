import { proxySellerProducts } from "@/lib/auth-proxy";
export const runtime = "nodejs";
type Context = { params: Promise<{ id: string }> };
export async function GET(request: Request, context: Context) {
  return proxySellerProducts(request, (await context.params).id);
}
export const PATCH = GET;
export const DELETE = GET;
