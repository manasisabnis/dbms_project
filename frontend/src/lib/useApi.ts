"use client";

import { useEffect, useState } from "react";
import { fetchJson } from "@/lib/api";

type Result<T> = { path: string; data?: T; error?: string };

/** Fetch `path` from the API. Re-fetches whenever `path` changes. */
export function useApi<T>(path: string) {
  const [result, setResult] = useState<Result<T> | null>(null);

  useEffect(() => {
    let cancelled = false; // ignore answers that arrive after the path changed
    fetchJson<T>(path)
      .then((data) => !cancelled && setResult({ path, data }))
      .catch((e: Error) => !cancelled && setResult({ path, error: e.message || "Could not reach the API" }));
    return () => {
      cancelled = true;
    };
  }, [path]);

  const current = result?.path === path ? result : null;
  return { data: current?.data, error: current?.error, loading: current === null };
}
