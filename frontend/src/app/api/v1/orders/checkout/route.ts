import { proxyCheckout } from "@/lib/auth-proxy";
export const runtime = "nodejs";
export const POST = (request: Request) => proxyCheckout(request);
