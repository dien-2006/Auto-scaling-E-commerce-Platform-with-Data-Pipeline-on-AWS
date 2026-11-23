import { beautyCategories } from "@/lib/categories";

type CategoryKey = (typeof beautyCategories)[number]["key"];

/** Original category illustrations; decorative UI assets, not real product images. */
export function CategoryIcon({ category }: { category: CategoryKey }) {
  const artwork = {
    ChamSocDaMat: (
      <>
        <rect x="24" y="29" width="23" height="31" rx="7" fill="#a8d8fc" />
        <path d="M29 28v-9h13v9M33 18v-6h6v6" fill="#558ec7" />
        <rect x="27" y="39" width="17" height="12" rx="3" fill="#fff" />
        <path
          d="M54 24s-8 11-8 15a8 8 0 0 0 16 0c0-4-8-15-8-15Z"
          fill="#f9c8b6"
        />
        <path
          d="M54 31s-3 5-3 8"
          stroke="#fff"
          strokeWidth="2"
          strokeLinecap="round"
        />
      </>
    ),
    TrangDiem: (
      <>
        <rect x="24" y="37" width="17" height="24" rx="3" fill="#7a8bd0" />
        <path d="M27 37V23l11-7v21" fill="#ed947f" />
        <rect x="24" y="44" width="17" height="5" fill="#c4c9ef" />
        <circle cx="53" cy="46" r="14" fill="#f4c9be" />
        <circle cx="53" cy="46" r="9" fill="#f9ded4" />
        <path d="m45 25 2-5 2 5 5 2-5 2-2 5-2-5-5-2 5-2Z" fill="#e6af63" />
      </>
    ),
    DungCuPhuKienLamDep: (
      <>
        <path d="m29 32-6 29h7l5-29" fill="#9cb9da" />
        <path d="M27 33c-7-3-7-13 2-20 7 5 11 14 5 20" fill="#e0b7a4" />
        <path d="M27 33h8l-1 7h-9" fill="#769ac3" />
        <path d="M48 24h9v37h-9z" fill="#e6b7c7" />
        <path d="M46 24h13v9H46z" fill="#bba5ce" />
        <path d="M49 14h7v10h-7z" fill="#7e739c" />
        <ellipse cx="53" cy="14" rx="6" ry="8" fill="#d5c8e5" />
      </>
    ),
    VatTuYTe: (
      <>
        <rect x="17" y="27" width="48" height="33" rx="8" fill="#a8d5ec" />
        <path d="M30 27v-7h21v7" fill="none" stroke="#6e9cbb" strokeWidth="4" />
        <rect x="35" y="33" width="11" height="21" rx="2" fill="#fff" />
        <rect x="30" y="38" width="21" height="11" rx="2" fill="#fff" />
        <path
          d="m58 18 1-4M66 22l4-2M62 12l3-3"
          stroke="#ecb296"
          strokeWidth="2.5"
          strokeLinecap="round"
        />
      </>
    ),
    DungCuMassageTriLieu: (
      <>
        <path
          d="M40 28v32"
          stroke="#8cbda9"
          strokeWidth="7"
          strokeLinecap="round"
        />
        <path
          d="M30 25v10h20V25"
          fill="none"
          stroke="#79aa99"
          strokeWidth="3"
        />
        <rect x="23" y="16" width="34" height="15" rx="7.5" fill="#b0dbc6" />
        <rect x="26" y="18" width="28" height="4" rx="2" fill="#d4eee2" />
        <path
          d="M57 44c-12-5-17 6-10 15 4 6 8 5 12-2 7-12 11-8 11-15-1-5-6-6-13 2Z"
          fill="#efcbb4"
        />
      </>
    ),
    NuocHoa: (
      <>
        <rect x="25" y="31" width="32" height="30" rx="8" fill="#dac9ed" />
        <path d="M34 25h14v7H34z" fill="#b29acb" />
        <rect x="32" y="14" width="18" height="12" rx="3" fill="#7e87b5" />
        <rect x="31" y="41" width="20" height="12" rx="3" fill="#faf8ff" />
        <path d="m41 43 2 3 3 1-3 1-2 3-1-3-3-1 3-1 1-3Z" fill="#d9a65f" />
        <path d="m61 18 1-6 2 6 6 1-6 2-2 5-1-5-5-2 5-1Z" fill="#edbc86" />
      </>
    ),
  };
  return (
    <svg
      viewBox="0 0 82 76"
      width="82"
      height="76"
      aria-hidden="true"
      className="category-art"
    >
      <ellipse cx="41" cy="65" rx="26" ry="4" fill="#6694be" opacity=".12" />
      {artwork[category]}
    </svg>
  );
}
