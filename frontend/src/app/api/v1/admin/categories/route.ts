import { proxyAdminCategories } from "@/lib/auth-proxy";
export const runtime = "nodejs";
export async function GET(request: Request) {
  return proxyAdminCategories(request);
}
export async function POST(request: Request) {
  return proxyAdminCategories(request);
}
