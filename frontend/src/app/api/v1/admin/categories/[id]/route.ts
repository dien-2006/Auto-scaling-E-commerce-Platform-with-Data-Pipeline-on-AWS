import { proxyAdminCategories } from "@/lib/auth-proxy";
export const runtime = "nodejs";
export async function PATCH(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  return proxyAdminCategories(request, (await params).id);
}
