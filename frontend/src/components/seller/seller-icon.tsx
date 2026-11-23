export function SellerIcon({
  name,
}: {
  name:
    | "shop"
    | "message"
    | "email"
    | "phone"
    | "users"
    | "account"
    | "adduser"
    | "truck"
    | "growth"
    | "shield"
    | "support"
    | "bell"
    | "search"
    | "check"
    | "box"
    | "calendar"
    | "info"
    | "bolt"
    | "arrow-left"
    | "arrow-right";
}) {
  const paths = {
    check: <path d="m5 12 4 4 10-10" />,
    box: (
      <>
        <path d="m12 2 10 5-10 5L2 7l10-5ZM2 7v10l10 5 10-5V7M12 12v10M7 4.5l10 5" />
      </>
    ),
    calendar: (
      <>
        <rect x="3" y="5" width="18" height="17" rx="2" />
        <path d="M7 2v6M17 2v6M3 11h18M7 15h3M7 18h7" />
      </>
    ),
    info: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 10v7M12 6v.1" />
      </>
    ),
    bolt: (
      <path
        d="m13 1-9 13h7l-1 9 10-14h-8l1-8Z"
        fill="#ffd53a"
        stroke="#ffb81d"
      />
    ),
    "arrow-left": <path d="m10 5-7 7 7 7M3 12h18" />,
    "arrow-right": <path d="m14 5 7 7-7 7M21 12H3" />,
    account: (
      <>
        <circle cx="12" cy="12" r="10" />
        <circle cx="12" cy="8" r="3" />
        <path d="M5 20v-2a7 7 0 0 1 14 0v2" />
      </>
    ),
    adduser: (
      <>
        <circle cx="9" cy="7" r="4" />
        <path d="M1 22v-3a8 8 0 0 1 16 0v3M20 6v8M16 10h8" />
      </>
    ),
    shop: (
      <>
        <path d="M3 10h18l-2-6H5l-2 6Zm2 0v10h14V10M9 20v-6h6v6" />
        <path d="M3 10a3 3 0 0 0 6 0 3 3 0 0 0 6 0 3 3 0 0 0 6 0" />
      </>
    ),
    message: (
      <>
        <path d="M5 3h14a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-8l-5 3v-3H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z" />
        <path d="M7 7h10M7 11h10M7 15h6" />
      </>
    ),
    email: (
      <>
        <rect x="3" y="5" width="18" height="14" rx="2" />
        <path d="m3 6 9 7 9-7" />
      </>
    ),
    phone: (
      <path d="m6 3 4 5-3 3c2 3 3 4 6 6l3-3 5 4c-1 4-3 5-7 3C7 18 3 14 2 8c-1-3 1-5 4-5Z" />
    ),
    users: (
      <>
        <circle cx="12" cy="7" r="4" />
        <path d="M5 21v-3a7 7 0 0 1 14 0v3M3 5a3 3 0 0 0 0 6M21 5a3 3 0 0 1 0 6M1 20v-3a5 5 0 0 1 3-4M23 20v-3a5 5 0 0 0-3-4" />
      </>
    ),
    truck: (
      <>
        <path d="M2 4h12v13H2V4Zm12 5h5l3 4v4h-8M2 17h3M10 17h7" />
        <circle cx="7.5" cy="18" r="2.5" />
        <circle cx="19.5" cy="18" r="2.5" />
      </>
    ),
    growth: (
      <>
        <path d="M3 21v-5M9 21V9M15 21v-9M21 21V3M3 10l6-5 6 3 6-6M16 2h5v5" />
      </>
    ),
    shield: (
      <>
        <path d="m12 2 9 4v6c0 5-5 9-9 11-4-2-9-6-9-11V6l9-4Z" />
        <path d="m7 12 3 3 7-7" />
      </>
    ),
    support: (
      <>
        <path d="m2 9 4-5 5 2 3-1 8 5-4 8-5 4-9-8M7 8l4-3 5 3-3 3-3-1M6 15l4 4M10 14l5 5M14 13l4 4" />
      </>
    ),
    bell: (
      <>
        <path d="M5 17h14l-2-4V9A5 5 0 0 0 7 9v4l-2 4ZM10 21h4M12 2v2" />
      </>
    ),
    search: (
      <>
        <circle cx="10" cy="10" r="7" />
        <path d="m15 15 7 7" />
      </>
    ),
  };
  return (
    <svg
      viewBox="0 0 24 24"
      width="28"
      height="28"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name]}
    </svg>
  );
}
