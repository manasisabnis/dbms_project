"use client";

import Link from "next/link";
import MockBanner from "@/components/MockBanner";
import type { LandmarkResponse } from "@/lib/api";
import { useApi } from "@/lib/useApi";

/** Rows come from the MySQL Landmark_Cases view (cases cited 10+ times). */
export default function LandmarkList() {
  const { data, error, loading } = useApi<LandmarkResponse>("/api/landmark-cases?limit=5");

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="mb-3 font-semibold">🏛 Landmark Cases</h2>
      <div className="mb-3">
        <MockBanner what="landmark cases" />
      </div>
      {loading && <p className="text-sm text-slate-500">Loading…</p>}
      {error && <p className="text-sm text-slate-500">Landmark cases are not available right now.</p>}
      {data && data.results.length === 0 && <p className="text-sm text-slate-500">No landmark cases yet.</p>}
      {data && data.results.length > 0 && (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left text-xs text-slate-500">
              <th className="pb-2 font-medium">Case</th>
              <th className="pb-2 font-medium">Judgment date</th>
              <th className="pb-2 text-right font-medium">Citations</th>
            </tr>
          </thead>
          <tbody>
            {data.results.map((c) => (
              <tr key={c.case_id} className="border-b last:border-0">
                <td className="py-2 pr-3">
                  <Link href={`/cases/${c.case_id}`} className="font-medium text-blue-700 hover:underline">
                    {c.case_name}
                  </Link>
                  <p className="text-xs text-slate-500">{c.case_number ?? `ID ${c.case_id}`}</p>
                </td>
                <td className="py-2 text-slate-600">{c.judgment_date}</td>
                <td className="py-2 text-right font-semibold">{c.citation_count.toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
