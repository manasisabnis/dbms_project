import type { Label } from "@/lib/api";

// The API says "established"; the UI says "Influential".
export const LABEL_TEXT: Record<Label, string> = {
  emerging: "Emerging",
  declining: "Declining",
  established: "Influential",
  recent: "Recent",
  regular: "Regular",
};

export const LABEL_STYLE: Record<Label, string> = {
  emerging: "bg-green-100 text-green-800",
  declining: "bg-red-100 text-red-800",
  established: "bg-amber-100 text-amber-800",
  recent: "bg-blue-100 text-blue-800",
  regular: "bg-slate-100 text-slate-700",
};

export const LABEL_EXPLANATION: Record<Label, string> = {
  emerging: "Citations are rising sharply compared with the previous period.",
  declining: "Citations have dropped sharply compared with the previous period.",
  established: "Consistently high citation activity year after year.",
  recent: "A recently decided case that is already being cited.",
  regular: "Cited at a modest, stable level. No strong trend.",
};

export function formatGrowth(pct: number): string {
  return `${pct > 0 ? "+" : ""}${Math.round(pct)}%`;
}
