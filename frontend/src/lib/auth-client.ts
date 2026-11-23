import { accountFrom, authMessages, type Account } from "@/lib/auth-contract";
export class AuthFailure extends Error {
  constructor(public code: string) {
    super(authMessages[code] ?? "Không thể kết nối dịch vụ. Vui lòng thử lại.");
  }
}
async function call(endpoint: string, init?: RequestInit): Promise<unknown> {
  try {
    const response = await fetch(`/api/v1/auth/${endpoint}`, {
      ...init,
      credentials: "same-origin",
      cache: "no-store",
      signal: AbortSignal.timeout(20000),
    });
    if (response.status === 204) return null;
    const payload = await response.json().catch(() => null);
    if (!response.ok)
      throw new AuthFailure(
        typeof payload?.error?.code === "string"
          ? payload.error.code
          : response.status === 429 ? "RATE_LIMITED" : response.status >= 500 ? "SERVER_ERROR" : "UNAVAILABLE",
      );
    return payload;
  } catch (error) {
    if (error instanceof AuthFailure) throw error;
    throw new AuthFailure(error instanceof DOMException && ["TimeoutError", "AbortError"].includes(error.name) ? "REQUEST_TIMEOUT" : error instanceof TypeError ? "NETWORK_ERROR" : "UNAVAILABLE");
  }
}
export async function fetchAccount(): Promise<Account> {
  const payload = (await call("me")) as { data?: unknown };
  const account = accountFrom(payload?.data);
  if (!account) throw new AuthFailure("UNAVAILABLE");
  return account;
}
export async function mutateAuth(
  endpoint: "login" | "register" | "logout" | "otp-login",
  data?: Record<string, string>,
) {
  const csrf = (await call("csrf")) as { data?: { csrf_token?: unknown } };
  if (typeof csrf?.data?.csrf_token !== "string")
    throw new AuthFailure("UNAVAILABLE");
  const payload = await call(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": csrf.data.csrf_token,
    },
    ...(data ? { body: JSON.stringify(data) } : {}),
  });
  if (
    endpoint !== "logout" &&
    !accountFrom((payload as { data?: unknown })?.data)
  )
    throw new AuthFailure("UNAVAILABLE");
}
