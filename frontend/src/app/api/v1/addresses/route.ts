import { proxyAddresses } from "@/lib/auth-proxy";
export const runtime = "nodejs";
export const GET = (request: Request) => proxyAddresses(request);
export const POST = (request: Request) => proxyAddresses(request);
