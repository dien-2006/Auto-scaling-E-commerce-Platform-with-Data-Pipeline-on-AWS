import { proxyShopping } from "@/lib/auth-proxy";
export const runtime = "nodejs";
export async function GET(
  request: Request,
  context: { params: Promise<{ id: string }> },
) {
  return proxyShopping(request, "public-reviews", (await context.params).id);
}
