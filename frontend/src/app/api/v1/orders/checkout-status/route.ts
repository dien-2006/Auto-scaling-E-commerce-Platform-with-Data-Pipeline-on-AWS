import { proxyCheckout } from "@/lib/auth-proxy";
export const runtime = "nodejs";
export const GET = (request: Request) => proxyCheckout(request, true);
