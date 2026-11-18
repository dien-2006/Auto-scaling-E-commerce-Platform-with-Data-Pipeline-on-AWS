export const shippingCarriers = [
  { code: "GHN", name: "Giao hàng nhanh", wordmark: "GHN" },
  { code: "GHTK", name: "Giao hàng tiết kiệm", wordmark: "GHTK" },
  { code: "VIETTEL_POST", name: "Viettel Post", wordmark: "viettelPost" },
  { code: "JNT_EXPRESS", name: "J&T Express", wordmark: "J&T EXPRESS" },
  { code: "EXPRESS", name: "Hỏa tốc", wordmark: "" },
] as const;
export type CarrierCode = (typeof shippingCarriers)[number]["code"];
export type ShippingDraft = {
  carriers: CarrierCode[];
  feeMode: "PLATFORM" | "CUSTOM";
  customFee: string;
  processingDays: number;
};
export function shippingDraftError(draft: ShippingDraft): string | null {
  if (!draft.carriers.length) return "Chọn ít nhất một phương thức vận chuyển.";
  if (
    new Set(draft.carriers).size !== draft.carriers.length ||
    draft.carriers.some(
      (code) => !shippingCarriers.some((carrier) => carrier.code === code),
    )
  )
    return "Phương thức vận chuyển chưa hợp lệ.";
  if (!["PLATFORM", "CUSTOM"].includes(draft.feeMode))
    return "Chọn cách tính phí vận chuyển hợp lệ.";
  if (
    draft.feeMode === "CUSTOM" &&
    !/^(0|[1-9]\d{0,11})(\.\d{1,2})?$/.test(draft.customFee)
  )
    return "Nhập phí VND không âm, tối đa 12 chữ số và 2 số thập phân.";
  if (
    !Number.isInteger(draft.processingDays) ||
    draft.processingDays < 1 ||
    draft.processingDays > 7
  )
    return "Thời gian xử lý từ 1 đến 7 ngày.";
  return null;
}
