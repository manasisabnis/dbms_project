// Types mirror backend/app/schemas.py (Mongo endpoints) and contracts/api_contract.md (MySQL endpoints).
// If the backend changes, change these too.

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

/**
 * MOCK MODE: until Manasi's MySQL endpoints exist, the search / case-details / cited-by /
 * landmark requests are answered from files in /public/mock (copies of contracts/sample_responses).
 * The MongoDB endpoints (dashboard, citation-trend) are ALWAYS real.
 * When her API is ready, create frontend/.env.local containing:  NEXT_PUBLIC_USE_MOCKS=false
 */
export const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS !== "false";

export type Label = "emerging" | "declining" | "established" | "recent" | "regular";
export type WindowYears = 1 | 3 | 5;

// ---------- MongoDB-backed (Person 2) ----------
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

// ---------- MySQL-backed (Person 1): PROPOSED shapes, see contracts/api_contract.md ----------
export interface CaseSearchResult {
  case_id: number;
  case_name: string;
  case_number: string | null;
  court_name: string | null;
  judgment_date: string;
  total_citations: number;
}
export interface CaseSearchResponse {
  query: string;
  page: number;
  page_size: number;
  total: number;
  results: CaseSearchResult[];
}

export interface Judge {
  judge_id: number;
  name: string;
  designation: string | null;
  role_in_case: string | null;
}
export interface Statute {
  statute_id: number;
  act_name: string;
  section: string | null;
  description: string | null;
  enactment_year: number | null;
}
export interface CaseDetail {
  case_id: number;
  case_name: string;
  case_number: string | null;
  judgment_date: string;
  court_name: string | null;
  court_level: string | null;
  case_type: string | null;
  decision: string | null;
  pdf_url: string | null;
  judges: Judge[];
  statutes: Statute[];
}

export interface CitedByItem {
  citing_case_id: number;
  case_name: string;
  case_number: string | null;
  judgment_date: string;
  context_text: string | null;
  page_number: number | null;
}
export interface CitedByResponse {
  case_id: number;
  total: number;
  page: number;
  page_size: number;
  results: CitedByItem[];
}

export interface LandmarkCase {
  case_id: number;
  case_name: string;
  case_number: string | null;
  judgment_date: string;
  citation_count: number;
}
export interface LandmarkResponse {
  results: LandmarkCase[];
}

// ---------- fetching ----------
async function loadMock(file: string): Promise<unknown> {
  const res = await fetch(`/mock/${file}`);
  if (!res.ok) throw new Error(`Missing mock file ${file}`);
  return res.json();
}

/** Returns a promise if this path should be answered by a mock file, otherwise null. */
function mockRequest(path: string): Promise<unknown> | null {
  const [pathname, query = ""] = path.split("?");

  if (pathname === "/api/cases") {
    const q = (new URLSearchParams(query).get("q") ?? "").trim().toLowerCase();
    return loadMock("cases_search.json").then((raw) => {
      const data = raw as CaseSearchResponse;
      const results = data.results.filter(
        (r) => !q || r.case_name.toLowerCase().includes(q) || (r.case_number ?? "").toLowerCase().includes(q),
      );
      return { ...data, query: q, total: results.length, results };
    });
  }

  const citations = pathname.match(/^\/api\/cases\/(\d+)\/citations$/);
  if (citations) {
    return loadMock("case_citations.json").then((raw) => ({ ...(raw as CitedByResponse), case_id: Number(citations[1]) }));
  }

  const detail = pathname.match(/^\/api\/cases\/(\d+)$/);
  if (detail) {
    return loadMock("case_detail.json").then((raw) => ({ ...(raw as CaseDetail), case_id: Number(detail[1]) }));
  }

  if (pathname === "/api/landmark-cases") return loadMock("landmark_cases.json");

  return null; // e.g. /api/trends/dashboard and /api/cases/{id}/citation-trend are real
}

export async function fetchJson<T>(path: string): Promise<T> {
  const mock = USE_MOCKS ? mockRequest(path) : null;
  if (mock) return (await mock) as T;

  const res = await fetch(`${API_URL}${path}`);
  if (!res.ok) {
    throw new Error(res.status === 404 ? "No data found for this request." : `API error (${res.status})`);
  }
  return res.json() as Promise<T>;
}
