import { proxySellerShop } from "@/lib/auth-proxy";
export const runtime = "nodejs";
export async function DELETE(
  request: Request,
  context: { params: Promise<{ id: string }> },
) {
  return proxySellerShop(request, (await context.params).id);
}
