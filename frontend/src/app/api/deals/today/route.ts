export const runtime = "nodejs";
export async function GET() {
  try {
    const base = process.env.INTERNAL_API_URL;
    if (!base) throw new Error("Missing API configuration");
    const response = await fetch(`${base}/api/v1/deals/today`, { cache: "no-store", signal: AbortSignal.timeout(5000) });
    if (!response.ok) throw new Error("Unavailable");
    return Response.json(await response.json(), { headers: { "Cache-Control": "no-store" } });
  } catch {
    return Response.json({ error: { code: "DEPENDENCY_UNAVAILABLE" } }, { status: 503 });
  }
}
