import { AuthFailure } from "@/lib/auth-client";
import {
  addressFrom,
  type AddressInput,
  type ShippingAddress,
} from "@/lib/address-contract";

async function request(path: string, init?: RequestInit): Promise<unknown> {
  try {
    const response = await fetch(`/api/v1/${path}`, {
      ...init,
      credentials: "same-origin",
      cache: "no-store",
      signal: AbortSignal.timeout(20000),
    });
    if (response.status === 204) return null;
    const payload = await response.json();
    if (!response.ok)
      throw new AuthFailure(payload?.error?.code ?? "UNAVAILABLE");
    return payload;
  } catch (error) {
    if (error instanceof AuthFailure) throw error;
    throw new AuthFailure("UNAVAILABLE");
  }
}
export async function listAddresses(): Promise<ShippingAddress[]> {
  const payload = (await request("addresses")) as {
    data?: { items?: unknown };
  };
  if (!Array.isArray(payload?.data?.items))
    throw new AuthFailure("UNAVAILABLE");
  const rows = payload.data.items.map(addressFrom);
  if (rows.some((row) => row === null)) throw new AuthFailure("UNAVAILABLE");
  return rows as ShippingAddress[];
}
export async function saveAddress(
  method: "POST" | "PATCH" | "DELETE",
  id?: string,
  data?: Partial<AddressInput>,
) {
  if (id !== undefined && !/^[1-9]\d{0,18}$/.test(id))
    throw new AuthFailure("VALIDATION_ERROR");
  const csrf = (await request("auth/csrf")) as {
    data?: { csrf_token?: unknown };
  };
  if (typeof csrf?.data?.csrf_token !== "string")
    throw new AuthFailure("UNAVAILABLE");
  const payload = await request(`addresses${id ? `/${id}` : ""}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": csrf.data.csrf_token,
    },
    ...(data ? { body: JSON.stringify(data) } : {}),
  });
  if (
    method !== "DELETE" &&
    !addressFrom((payload as { data?: unknown })?.data)
  )
    throw new AuthFailure("UNAVAILABLE");
}
