import { proxySellerOrders } from "@/lib/auth-proxy";
export const runtime = "nodejs";
export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  return proxySellerOrders(request, (await params).id);
}
