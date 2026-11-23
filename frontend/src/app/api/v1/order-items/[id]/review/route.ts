import { proxyShopping } from "@/lib/auth-proxy";
export const runtime = "nodejs";
type Context = { params: Promise<{ id: string }> };
export async function GET(request: Request, context: Context) {
  return proxyShopping(request, "review", (await context.params).id);
}
export async function POST(request: Request, context: Context) {
  return proxyShopping(request, "review", (await context.params).id);
}
