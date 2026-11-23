import { proxyProductImages } from "@/lib/auth-proxy";
export const runtime = "nodejs";
export async function POST(
  request: Request,
  context: { params: Promise<{ id: string }> },
) {
  return proxyProductImages(request, (await context.params).id);
}
