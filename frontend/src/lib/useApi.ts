"use client";

import { useEffect, useState } from "react";
import { fetchJson } from "@/lib/api";

export type ApiState<T> = { data?: T; error?: string; loading: boolean };

type Result<T> = { path: string; data?: T; error?: string };

/**
 * Fetch `path` from the API. Re-fetches whenever `path` changes.
 * Pass null to skip fetching (used by tabs that load only when opened).
 */
export function useApi<T>(path: string | null): ApiState<T> {
  const [result, setResult] = useState<Result<T> | null>(null);

  useEffect(() => {
    if (path === null) return;
    let cancelled = false; // ignore answers that arrive after the path changed
    fetchJson<T>(path)
      .then((data) => !cancelled && setResult({ path, data }))
      .catch((e: Error) => !cancelled && setResult({ path, error: e.message || "Could not reach the API" }));
    return () => {
      cancelled = true;
    };
  }, [path]);

  if (path === null) return { loading: false };
  const current = result?.path === path ? result : null;
  return { data: current?.data, error: current?.error, loading: current === null };
}
