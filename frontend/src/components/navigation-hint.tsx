"use client";
import { useLinkStatus } from "next/link";

/** Link-level feedback avoids streaming the resource route before its 404 check. */
export function NavigationHint() {
  const { pending } = useLinkStatus();
  return pending ? (
    <span role="status" className="ml-2 text-xs font-normal text-muted">
      Đang mở…
    </span>
  ) : null;
}
