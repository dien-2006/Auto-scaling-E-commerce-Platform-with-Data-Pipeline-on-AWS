import { proxyAuth } from "@/lib/auth-proxy";
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
async function handle(
  request: Request,
  context: { params: Promise<{ endpoint: string }> },
) {
  return proxyAuth(request, (await context.params).endpoint);
}
export { handle as GET, handle as POST };
