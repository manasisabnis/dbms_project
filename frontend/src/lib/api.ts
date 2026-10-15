// Types mirror backend/app/schemas.py. If the backend changes, change these too.

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export type Label = "emerging" | "declining" | "established" | "recent" | "regular";
export type WindowYears = 1 | 3 | 5;

export interface CaseSummary {
  case_id: number;
  case_name: string;
  case_number: string | null;
  total_citations: number;
  recent: number;
  previous: number;
  growth_pct: number;
  label: Label;
}

export interface DashboardResponse {
  window_years: number;
  as_of: string | null;
  counts: Record<Label, number>;
  emerging: CaseSummary[];
  declining: CaseSummary[];
  established: CaseSummary[];
  most_cited: CaseSummary[];
}

export interface WindowStats {
  recent: number;
  previous: number;
  growth_pct: number;
}

export interface CaseTrendResponse {
  case_id: number;
  case_name: string;
  case_number: string | null;
  as_of: string;
  total_citations: number;
  label: Label;
  labels: Record<string, Label>;
  windows: Record<string, WindowStats>;
  yearly: { year: number; count: number }[];
  by_court_level: { court_level: string; count: number }[];
}

export async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`);
  if (!res.ok) {
    throw new Error(res.status === 404 ? "No citation data found for this case." : `API error (${res.status})`);
  }
  return res.json() as Promise<T>;
}
