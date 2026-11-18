import { proxyCart } from "@/lib/auth-proxy";
export const runtime = "nodejs";
export const GET = (request: Request) => proxyCart(request, "cart");
