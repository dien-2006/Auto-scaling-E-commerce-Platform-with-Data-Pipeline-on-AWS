type IconName = "ticket" | "truck" | "bolt" | "star" | "gift" | "shield" | "return" | "support" | "sparkle";
export function ShoppingIcon({ name }: { name: IconName }) {
  const paths = {
    ticket: <><path d="M3 5h18v5a2 2 0 0 0 0 4v5H3v-5a2 2 0 0 0 0-4V5Z" /><path d="m9 16 6-8M9 8h.01M15 16h.01" /></>,
    truck: <><path d="M2 5h12v12H2V5Zm12 5h4l4 4v3h-8" /><circle cx="6" cy="18" r="2" /><circle cx="18" cy="18" r="2" /></>,
    bolt: <path d="m14 2-11 12h8l-1 8 11-12h-8l1-8Z" />,
    star: <path d="m12 2 3 6 7 1-5 5 1 8-6-4-6 4 1-8-5-5 7-1 3-6Z" />,
    gift: <><path d="M4 11h16v10H4V11ZM2 7h20v4H2V7Zm10 0v14" /><path d="M12 7C3 7 4 0 8 2c3 1 4 5 4 5Zm0 0c9 0 8-7 4-5-3 1-4 5-4 5Z" /></>,
    shield: <><path d="m12 2 9 4v6c0 6-9 10-9 10S3 18 3 12V6l9-4Z" /><path d="m8 12 3 3 5-6" /></>,
    return: <><path d="M3 11a9 9 0 0 1 16-6l2 3M21 3v5h-5M21 13A9 9 0 0 1 5 19l-2-3M3 21v-5h5" /></>,
    support: <><path d="M3 14V11a9 9 0 0 1 18 0v7c0 3-4 4-7 4M3 11h3v8H3v-8Zm15 0h3v8h-3v-8Z" /></>,
    sparkle: <><path d="m12 2 3 7 7 3-7 3-3 7-3-7-7-3 7-3 3-7ZM20 2v4m-2-2h4" /></>,
  };
  return <svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>;
}
