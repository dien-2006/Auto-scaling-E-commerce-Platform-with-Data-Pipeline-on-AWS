import { proxyProductImages } from "@/lib/auth-proxy";
export const runtime = "nodejs";
type Context = { params: Promise<{ id: string; resource: string }> };
async function handle(request: Request, context: Context) {
  const { id, resource } = await context.params;
  return proxyProductImages(request, id, resource);
}
export const POST = handle;
export const PATCH = handle;
export const DELETE = handle;
