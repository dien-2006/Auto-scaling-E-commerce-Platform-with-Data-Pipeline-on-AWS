import { proxyShopping } from "@/lib/auth-proxy";
export const runtime = "nodejs";
export const POST = (request: Request) => proxyShopping(request, "coupon");
