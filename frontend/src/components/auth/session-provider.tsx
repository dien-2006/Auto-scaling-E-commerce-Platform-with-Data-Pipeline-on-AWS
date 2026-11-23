"use client";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import { AuthFailure, fetchAccount, mutateAuth } from "@/lib/auth-client";
import type { Account } from "@/lib/auth-contract";
type Session = {
  account: Account | null;
  loading: boolean;
  error: string;
  refresh: () => Promise<Account | null>;
  logout: () => Promise<void>;
};
const SessionContext = createContext<Session | null>(null);
export function SessionProvider({ children }: { children: ReactNode }) {
  const [account, setAccount] = useState<Account | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const generation = useRef(0);
  const router = useRouter();
  const refresh = useCallback(async () => {
    const current = ++generation.current;
    setLoading(true);
    try {
      const user = await fetchAccount();
      if (current === generation.current) {
        setAccount(user);
        setError("");
      }
      return user;
    } catch (failure) {
      if (current === generation.current) {
        setAccount(null);
        setError(
          failure instanceof AuthFailure &&
            ["AUTH_REQUIRED", "INVALID_TOKEN", "TOKEN_EXPIRED"].includes(
              failure.code,
            )
            ? ""
            : failure instanceof Error
              ? failure.message
              : "Chưa thể tải tài khoản.",
        );
      }
      return null;
    } finally {
      if (current === generation.current) setLoading(false);
    }
  }, []);
  useEffect(() => {
    let cancelled = false;
    const current = ++generation.current;
    void fetchAccount()
      .then((user) => {
        if (!cancelled && current === generation.current) {
          setAccount(user);
          setError("");
        }
      })
      .catch((failure) => {
        if (!cancelled && current === generation.current) {
          setAccount(null);
          setError(
            failure instanceof AuthFailure &&
              ["AUTH_REQUIRED", "INVALID_TOKEN", "TOKEN_EXPIRED"].includes(
                failure.code,
              )
              ? ""
              : failure instanceof Error
                ? failure.message
                : "Chưa thể tải tài khoản.",
          );
        }
      })
      .finally(() => {
        if (!cancelled && current === generation.current) setLoading(false);
      });
    const update = () => {
      if (document.visibilityState === "visible") void refresh();
    };
    document.addEventListener("visibilitychange", update);
    const timer = setInterval(() => {
      if (document.visibilityState === "visible") void refresh();
    }, 60000);
    return () => {
      cancelled = true;
      document.removeEventListener("visibilitychange", update);
      clearInterval(timer);
    };
  }, [refresh]);
  async function logout() {
    await mutateAuth("logout");
    ++generation.current;
    setAccount(null);
    setError("");
    setLoading(false);
    router.replace("/");
    router.refresh();
  }
  return (
    <SessionContext.Provider
      value={{ account, loading, error, refresh, logout }}
    >
      {children}
    </SessionContext.Provider>
  );
}
export function useSession() {
  const context = useContext(SessionContext);
  if (!context) throw new Error("SessionProvider required");
  return context;
}
