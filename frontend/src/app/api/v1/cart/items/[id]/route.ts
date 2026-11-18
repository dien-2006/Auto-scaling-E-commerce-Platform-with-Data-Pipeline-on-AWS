import { proxyCart } from "@/lib/auth-proxy";
export const runtime = "nodejs";
async function handle(
  request: Request,
  context: { params: Promise<{ id: string }> },
) {
  return proxyCart(request, "item", (await context.params).id);
}
export { handle as PATCH, handle as DELETE };
