import { proxyCheckoutOptions } from "@/lib/auth-proxy";
export const runtime = "nodejs";
export const GET = (request: Request) => proxyCheckoutOptions(request);
