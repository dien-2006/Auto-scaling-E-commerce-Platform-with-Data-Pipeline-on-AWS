import { proxyCancelOrder } from "@/lib/auth-proxy";
export const runtime = "nodejs";
export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string; shopOrderId: string }> },
) {
  const { id, shopOrderId } = await params;
  return proxyCancelOrder(request, id, shopOrderId);
}
