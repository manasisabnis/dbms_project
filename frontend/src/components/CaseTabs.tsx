"use client";

import Link from "next/link";
import { useState } from "react";
import { CourtDonut, CumulativeLine, YearlyBars } from "@/components/Charts";
import LabelBadge from "@/components/LabelBadge";
import StatCard from "@/components/StatCard";
import WindowToggle from "@/components/WindowToggle";
import type { CaseDetail, CaseTrendResponse, CitedByResponse, WindowYears } from "@/lib/api";
import { LABEL_EXPLANATION, LABEL_TEXT, formatGrowth } from "@/lib/labels";
import { useApi, type ApiState } from "@/lib/useApi";

const BOX = "rounded-xl border border-slate-200 bg-white p-5 shadow-sm";

function Notice({ text }: { text: string }) {
  return <div className={`${BOX} text-sm text-slate-600`}>{text}</div>;
}

function Row({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <tr className="border-b last:border-0">
      <th className="w-40 py-2 pr-4 text-left text-sm font-medium text-slate-500">{label}</th>
      <td className="py-2 text-sm">{value || "-"}</td>
    </tr>
  );
}

/** Wraps the three states every detail tab has: loading, error, data. */
function Loaded<T>({ state, children }: { state: ApiState<T>; children: (data: T) => React.ReactNode }) {
  if (state.error) return <Notice text={state.error} />;
  if (state.loading || !state.data) return <p className="text-slate-500">Loading…</p>;
  return <>{children(state.data)}</>;
}

export function OverviewTab({ detail, trend }: { detail: ApiState<CaseDetail>; trend: ApiState<CaseTrendResponse> }) {
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <div className={`${BOX} lg:col-span-2`}>
        <h3 className="mb-3 font-semibold">Case information</h3>
        <Loaded state={detail}>
          {(d) => (
            <table className="w-full">
              <tbody>
                <Row label="Case name" value={trend.data?.case_name ?? d.case_name} />
                <Row label="Case number" value={d.case_number} />
                <Row label="Judgment date" value={d.judgment_date} />
                <Row label="Court" value={d.court_name} />
                <Row label="Case type" value={d.case_type ?? "Not available in the current dataset"} />
                <Row label="Decision" value={d.decision ?? "Not available in the current dataset"} />
                <Row label="Judges" value={Array.isArray(d.judges) ? (d.judges.length ? `${d.judges.length} on the bench` : "No judges recorded") : "Not available in the current dataset"} />
              </tbody>
            </table>
          )}
        </Loaded>
      </div>

      <div className="space-y-4">
        {trend.data ? (
          <>
            <div className="grid grid-cols-2 gap-3">
              <StatCard title="Total citations" value={trend.data.total_citations.toLocaleString()} />
              <StatCard title="Status" value={LABEL_TEXT[trend.data.label]} hint="3-year window" />
            </div>
            <div className={BOX}>
              <h3 className="mb-1 font-semibold">Precedent status</h3>
              <p className="text-sm text-slate-600">{LABEL_EXPLANATION[trend.data.label]}</p>
            </div>
          </>
        ) : (
          <Notice text={trend.loading ? "Loading citation statistics…" : "No citation statistics for this case yet."} />
        )}
      </div>
    </div>
  );
}

export function AnalysisTab({ trend }: { trend: ApiState<CaseTrendResponse> }) {
  const [windowYears, setWindowYears] = useState<WindowYears>(3);

  return (
    <Loaded state={trend}>
      {(t) => {
        const w = t.windows[String(windowYears)];
        const label = t.labels[String(windowYears)];
        return (
          <div className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-sm text-slate-600">
                Status over this window: <LabelBadge label={label} /> · data as of {t.as_of}
              </div>
              <WindowToggle value={windowYears} onChange={setWindowYears} />
            </div>
            <section className="grid grid-cols-2 gap-4 md:grid-cols-4">
              <StatCard title="Total citations" value={t.total_citations.toLocaleString()} />
              <StatCard title={`Last ${windowYears} yr`} value={w.recent} hint="recent window" />
              <StatCard title={`Previous ${windowYears} yr`} value={w.previous} hint="window before it" />
              <StatCard title="Change" value={formatGrowth(w.growth_pct)} hint="recent vs previous" />
            </section>
            <section className="grid gap-4 lg:grid-cols-2">
              <CumulativeLine yearly={t.yearly} />
              <YearlyBars yearly={t.yearly} />
            </section>
            <section className="grid gap-4 lg:grid-cols-2">
              <CourtDonut data={t.by_court_level} />
            </section>
          </div>
        );
      }}
    </Loaded>
  );
}

const CITED_PAGE_SIZE = 10;

export function CitedByTab({ caseId }: { caseId: string }) {
  const [page, setPage] = useState(1);
  const state = useApi<CitedByResponse>(`/api/cases/${caseId}/citations?page=${page}&page_size=${CITED_PAGE_SIZE}`);
  const lastPage = state.data ? Math.max(1, Math.ceil(state.data.total / CITED_PAGE_SIZE)) : 1;

  return (
    <Loaded state={state}>
      {(d) => (
        <div className="space-y-3">
          <p className="text-sm text-slate-500">
            Cited by {d.total} {d.total === 1 ? "case" : "cases"}
          </p>
          {d.results.length === 0 ? (
            <Notice text="No other case cites this judgment yet." />
          ) : (
            d.results.map((c) => (
              <div key={`${c.citing_case_id}-${c.judgment_date}`} className={BOX}>
                <Link href={`/cases/${c.citing_case_id}`} className="font-medium text-blue-700 hover:underline">
                  {c.case_name}
                </Link>
                <p className="text-xs text-slate-500">
                  {c.case_number ?? `ID ${c.citing_case_id}`} · {c.judgment_date}
                  {c.page_number ? ` · page ${c.page_number}` : ""}
                </p>
                {c.context_text && <p className="mt-2 text-sm text-slate-700">&ldquo;{c.context_text}&rdquo;</p>}
              </div>
            ))
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
      )}
    </Loaded>
  );
}

export function JudgesTab({ detail }: { detail: ApiState<CaseDetail> }) {
  return (
    <Loaded state={detail}>
      {(d) => {
        const judges = Array.isArray(d.judges) && d.judges.length
          ? d.judges
          : (d.coram_members_text ?? "")
              .split(";")
              .map((name) => name.trim())
              .filter(Boolean);

        return judges.length === 0 ? (
          <Notice text="No judges recorded for this case." />
        ) : (
          <div className={BOX}>
            <h3 className="font-semibold">
              Bench: {d.bench_name ?? `${judges.length} judges`}
            </h3>
            <ul className="mt-3 list-disc pl-5">
              {judges.map((name, index) => (
                <li key={`${name}-${index}`} className="py-1">
                  {name}
                </li>
              ))}
            </ul>
          </div>
        );
      }}
    </Loaded>
  );
}

export function StatutesTab({ detail }: { detail: ApiState<CaseDetail> }) {
  return (
    <Loaded state={detail}>
      {(d) =>
<<<<<<< Updated upstream
        !d.statutes?.length ? (
          <Notice text="Statute details are not available in the current dataset." />
=======
        (d.statutes ?? []).length === 0 ? (
          <Notice text="No statutes recorded for this case." />
>>>>>>> Stashed changes
        ) : (
          <div className={BOX}>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-xs text-slate-500">
                  <th className="pb-2 font-medium">Act</th>
                  <th className="pb-2 font-medium">Section</th>
                  <th className="pb-2 font-medium">Description</th>
                  <th className="pb-2 font-medium">Enacted</th>
                </tr>
              </thead>
              <tbody>
                {(d.statutes ?? []).map((s) => (
                  <tr key={s.statute_id} className="border-b last:border-0">
                    <td className="py-2 font-medium">{s.act_name}</td>
                    <td className="py-2 text-slate-600">{s.section ?? "-"}</td>
                    <td className="py-2 text-slate-600">{s.description ?? "-"}</td>
                    <td className="py-2 text-slate-600">{s.enactment_year ?? "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      }
    </Loaded>
  );
}

export function FullTextTab({ detail }: { detail: ApiState<CaseDetail> }) {
  return (
    <Loaded state={detail}>
      {(d) =>
        d.pdf_url ? (
          <div className={BOX}>
            <p className="mb-3 text-sm text-slate-600">The full judgment is hosted as a PDF.</p>
            <a href={d.pdf_url} target="_blank" rel="noreferrer" className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
              Open judgment PDF
            </a>
          </div>
        ) : (
          <Notice text="No PDF link is available for this case." />
        )
      }
    </Loaded>
  );
}
