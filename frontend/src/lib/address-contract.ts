export type ShippingAddress = {
  address_id: string;
  recipient_name: string;
  phone: string;
  address_line: string;
  ward: string | null;
  district: string | null;
  city: string;
  is_default: boolean;
  created_at: string;
};
export type AddressInput = Omit<ShippingAddress, "address_id" | "created_at">;
export function addressFrom(value: unknown): ShippingAddress | null {
  if (typeof value !== "object" || value === null) return null;
  const row = value as Record<string, unknown>;
  if (
    typeof row.address_id !== "string" ||
    !/^[1-9]\d{0,18}$/.test(row.address_id) ||
    BigInt(row.address_id) > BigInt("9223372036854775807") ||
    ["recipient_name", "phone", "address_line", "city", "created_at"].some(
      (key) => typeof row[key] !== "string",
    ) ||
    ["ward", "district"].some(
      (key) => row[key] !== null && typeof row[key] !== "string",
    ) ||
    typeof row.is_default !== "boolean" ||
    !Number.isFinite(Date.parse(row.created_at as string))
  )
    return null;
  return {
    address_id: row.address_id,
    recipient_name: row.recipient_name as string,
    phone: row.phone as string,
    address_line: row.address_line as string,
    ward: row.ward as string | null,
    district: row.district as string | null,
    city: row.city as string,
    is_default: row.is_default,
    created_at: row.created_at as string,
  };
}
