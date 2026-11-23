import { proxyAdminUsers } from "@/lib/auth-proxy";
export const runtime = "nodejs";
export async function GET(request: Request) {
  return proxyAdminUsers(request);
}
