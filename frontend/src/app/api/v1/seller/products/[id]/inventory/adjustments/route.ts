import { proxyInventory } from "@/lib/auth-proxy";
export const runtime = "nodejs";
export async function POST(
  request: Request,
  context: { params: Promise<{ id: string }> },
) {
  return proxyInventory(request, (await context.params).id, true);
}
