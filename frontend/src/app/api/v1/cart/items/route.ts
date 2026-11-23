import { proxyCart } from "@/lib/auth-proxy";
export const runtime = "nodejs";
export const POST = (request: Request) => proxyCart(request, "items");
