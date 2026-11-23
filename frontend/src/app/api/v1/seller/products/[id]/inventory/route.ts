import { proxyInventory } from "@/lib/auth-proxy";
export const runtime = "nodejs";
export async function GET(
  request: Request,
  context: { params: Promise<{ id: string }> },
) {
  return proxyInventory(request, (await context.params).id);
}
