import { proxyCheckoutOptions } from "@/lib/auth-proxy";
export const runtime = "nodejs";
export const POST = (request: Request) => proxyCheckoutOptions(request, true);
