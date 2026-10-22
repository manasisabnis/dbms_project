"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useState } from "react";
import MockBanner from "@/components/MockBanner";
import SearchBox from "@/components/SearchBox";
import type { CaseSearchResponse } from "@/lib/api";
import { useApi } from "@/lib/useApi";

const PAGE_SIZE = 10;

function ResultsList({ q }: { q: string }) {
  const [page, setPage] = useState(1);
  const { data, error, loading } = useApi<CaseSearchResponse>(
    `/api/cases?q=${encodeURIComponent(q)}&page=${page}&page_size=${PAGE_SIZE}`,
  );

  if (error) return <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">{error}</div>;
  if (loading || !data) return <p className="text-slate-500">Searching…</p>;

  const lastPage = Math.max(1, Math.ceil(data.total / PAGE_SIZE));

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-500">
        Found {data.total} {data.total === 1 ? "result" : "results"}
      </p>

      {data.results.length === 0 ? (
        <div className="rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-600">
          No cases match &ldquo;{q}&rdquo;. Try part of the case name or its case number.
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-slate-50 text-left text-xs text-slate-500">
                <th className="p-3 font-medium">Case</th>
                <th className="p-3 font-medium">Court</th>
                <th className="p-3 font-medium">Judgment date</th>
                <th className="p-3 text-right font-medium">Citations</th>
              </tr>
            </thead>
            <tbody>
              {data.results.map((c) => (
                <tr key={c.case_id} className="border-b last:border-0">
                  <td className="p-3">
                    <Link href={`/cases/${c.case_id}`} className="font-medium text-blue-700 hover:underline">
                      {c.case_name}
                    </Link>
                    <p className="text-xs text-slate-500">{c.case_number ?? `ID ${c.case_id}`}</p>
                  </td>
                  <td className="p-3 text-slate-600">{c.court_name ?? "-"}</td>
                  <td className="p-3 text-slate-600">{c.judgment_date}</td>
                  <td className="p-3 text-right font-semibold">{c.total_citations.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {lastPage > 1 && (
        <div className="flex items-center gap-3 text-sm">
          <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="rounded border px-3 py-1 disabled:opacity-40">
            Previous
          </button>
          <span>
            Page {page} of {lastPage}
          </span>
          <button disabled={page >= lastPage} onClick={() => setPage(page + 1)} className="rounded border px-3 py-1 disabled:opacity-40">
            Next
          </button>
        </div>
      )}
    </div>
  );
}

export default function SearchResults() {
  const q = useSearchParams().get("q")?.trim() ?? "";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="mb-3 text-2xl font-bold">{q ? <>Search results for &ldquo;{q}&rdquo;</> : "Search cases"}</h1>
        <SearchBox key={q} initial={q} />
      </div>
      <MockBanner what="search results" />
      {q ? <ResultsList key={q} q={q} /> : <p className="text-slate-500">Type a case name or number above.</p>}
    </div>
  );
}
