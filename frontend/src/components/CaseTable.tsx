import Link from "next/link";
import type { CaseSummary } from "@/lib/api";
import { formatGrowth } from "@/lib/labels";

interface Props {
  title: string;
  cases: CaseSummary[];
  /** which number to highlight in the right-hand column */
  metric: "growth" | "citations";
}

export default function CaseTable({ title, cases, metric }: Props) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="mb-3 font-semibold">{title}</h2>
      {cases.length === 0 ? (
        <p className="text-sm text-slate-500">No cases in this group for this window.</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left text-xs text-slate-500">
              <th className="pb-2 font-medium">Case</th>
              <th className="pb-2 text-right font-medium">{metric === "growth" ? "Change" : "Citations"}</th>
            </tr>
          </thead>
          <tbody>
            {cases.map((c) => (
              <tr key={c.case_id} className="border-b last:border-0">
                <td className="py-2 pr-3">
                  <Link href={`/cases/${c.case_id}`} className="font-medium text-blue-700 hover:underline">
                    {c.case_name}
                  </Link>
                  <p className="text-xs text-slate-500">
                    {c.case_number ?? `ID ${c.case_id}`} · {c.previous} → {c.recent}
                  </p>
                </td>
                <td
                  className={`py-2 text-right font-semibold ${
                    metric === "growth" ? (c.growth_pct >= 0 ? "text-green-600" : "text-red-600") : ""
                  }`}
                >
                  {metric === "growth" ? formatGrowth(c.growth_pct) : c.total_citations.toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
