import { proxyAdminUsers } from "@/lib/auth-proxy";
export const runtime = "nodejs";
export async function PATCH(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  return proxyAdminUsers(request, (await params).id);
}
