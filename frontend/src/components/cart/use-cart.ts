"use client";
import { useCallback, useEffect, useState } from "react";
import { fetchCart } from "@/lib/cart-client";
import type { CartData } from "@/lib/cart-contract";

export function useCart() {
  const [cart, setCart] = useState<CartData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [version, setVersion] = useState(0);
  const reload = useCallback(() => {
    setLoading(true);
    setVersion((value) => value + 1);
  }, []);
  useEffect(() => {
    let active = true;
    void fetchCart().then(
      (data) => {
        if (active) {
          setCart(data);
          setError("");
          setLoading(false);
        }
      },
      (failure) => {
        if (active) {
          setCart(null);
          setError(
            failure instanceof Error
              ? failure.message
              : "Không tải được giỏ hàng.",
          );
          setLoading(false);
        }
      },
    );
    window.addEventListener("coco:cart-changed", reload);
    return () => {
      active = false;
      window.removeEventListener("coco:cart-changed", reload);
    };
  }, [reload, version]);
  return { cart, loading, error, reload };
}
