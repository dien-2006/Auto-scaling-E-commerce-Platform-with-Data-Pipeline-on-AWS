"use client";
import Image from "next/image";
import { useState } from "react";

export function ShopAvatar({
  src,
  name,
}: {
  src: string | null;
  name: string;
}) {
  const [failed, setFailed] = useState(false);
  return (
    <div className="shop-avatar">
      {src && !failed ? (
        <Image
          src={src}
          alt={`Logo ${name}`}
          fill
          unoptimized
          sizes="72px"
          className="object-contain p-2"
          onError={() => setFailed(true)}
        />
      ) : (
        <span aria-hidden="true">
          {[...name.trim()][0]?.toLocaleUpperCase("vi") || "S"}
        </span>
      )}
    </div>
  );
}
