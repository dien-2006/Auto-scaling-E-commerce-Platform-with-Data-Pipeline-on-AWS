import type { Category } from "@/lib/catalog-api";

/** Display taxonomy only; database IDs must always come from the categories API. */
export const beautyCategories = [
  {
    key: "ChamSocDaMat",
    slug: "cham-soc-da-mat",
    name: "Chăm sóc da mặt",
    symbol: "◒",
    color: "#e5ede2",
  },
  {
    key: "TrangDiem",
    slug: "trang-diem",
    name: "Trang điểm",
    symbol: "✦",
    color: "#f3e2de",
  },
  {
    key: "DungCuPhuKienLamDep",
    slug: "dung-cu-phu-kien-lam-dep",
    name: "Dụng cụ & phụ kiện làm đẹp",
    symbol: "✳",
    color: "#ece6f1",
  },
  {
    key: "VatTuYTe",
    slug: "vat-tu-y-te",
    name: "Vật tư y tế",
    symbol: "+",
    color: "#e0edf0",
  },
  {
    key: "DungCuMassageTriLieu",
    slug: "dung-cu-massage-tri-lieu",
    name: "Dụng cụ massage & trị liệu",
    symbol: "≈",
    color: "#f1e7d8",
  },
  {
    key: "NuocHoa",
    slug: "nuoc-hoa",
    name: "Nước hoa",
    symbol: "❋",
    color: "#f2e6d9",
  },
] as const;

export const categoryMatchKey = (value: string) =>
  value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/đ/gi, "d")
    .toLowerCase()
    .replace(/[^a-z0-9]/g, "");

export function matchBeautyCategories(tree: Category[]) {
  const flat: Category[] = [];
  const remaining = [...tree];
  while (remaining.length) {
    const item = remaining.pop()!;
    flat.push(item);
    remaining.push(...item.children);
  }
  return beautyCategories.map((display) => {
    const slugMatches = flat.filter((item) =>
      [display.key, display.slug].some(
        (key) => categoryMatchKey(item.category_slug) === categoryMatchKey(key),
      ),
    );
    const matches = slugMatches.length
      ? slugMatches
      : flat.filter(
          (item) =>
            categoryMatchKey(item.category_name) ===
            categoryMatchKey(display.key),
        );
    // Names aren't unique in SQL. Ambiguity must not pick an arbitrary database identity.
    return {
      ...display,
      actual: matches.length === 1 ? matches[0] : undefined,
    };
  });
}

export function formatVnd(value: string): string {
  const [whole, fraction = "00"] = value.split(".");
  return `${new Intl.NumberFormat("vi-VN").format(BigInt(whole))}${Number(fraction) ? `,${fraction.padEnd(2, "0")}` : ""} ₫`;
}
