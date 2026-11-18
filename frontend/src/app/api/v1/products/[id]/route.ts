import { proxyPublicProducts } from "@/lib/auth-proxy";
export const runtime = "nodejs";
export async function GET(
  request: Request,
  context: { params: Promise<{ id: string }> },
) {
  return proxyPublicProducts(request, (await context.params).id);
}
