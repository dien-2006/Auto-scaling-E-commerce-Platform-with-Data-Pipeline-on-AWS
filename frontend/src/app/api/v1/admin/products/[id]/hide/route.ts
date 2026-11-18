import { proxyAdminProducts } from "@/lib/auth-proxy";
export const runtime = "nodejs";
export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  return proxyAdminProducts(request, (await params).id);
}
