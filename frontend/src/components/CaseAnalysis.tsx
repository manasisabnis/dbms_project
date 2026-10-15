"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { CourtDonut, CumulativeLine, YearlyBars } from "@/components/Charts";
import LabelBadge from "@/components/LabelBadge";
import StatCard from "@/components/StatCard";
import WindowToggle from "@/components/WindowToggle";
import type { CaseTrendResponse, WindowYears } from "@/lib/api";
import { formatGrowth } from "@/lib/labels";
import { useApi } from "@/lib/useApi";

export default function CaseAnalysis() {
  const { id } = useParams<{ id: string }>();
  const [windowYears, setWindowYears] = useState<WindowYears>(3);
  const { data, error, loading } = useApi<CaseTrendResponse>(`/api/cases/${id}/citation-trend`);

  if (error) {
    return (
      <div className="space-y-3">
        <Link href="/" className="text-sm text-blue-700 hover:underline">← Back to dashboard</Link>
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">{error}</div>
      </div>
    );
  }
  if (loading || !data) return <p className="text-slate-500">Loading…</p>;

  const w = data.windows[String(windowYears)];
  const label = data.labels[String(windowYears)];

  return (
    <div className="space-y-6">
      <Link href="/" className="text-sm text-blue-700 hover:underline">← Back to dashboard</Link>

      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">{data.case_name}</h1>
            <LabelBadge label={label} />
          </div>
          <p className="mt-1 text-sm text-slate-600">
            {data.case_number ?? `Case ID ${data.case_id}`} · data as of {data.as_of}
          </p>
        </div>
        <WindowToggle value={windowYears} onChange={setWindowYears} />
      </header>

      <section className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard title="Total citations" value={data.total_citations.toLocaleString()} />
        <StatCard title={`Last ${windowYears} yr`} value={w.recent} hint="recent window" />
        <StatCard title={`Previous ${windowYears} yr`} value={w.previous} hint="window before it" />
        <StatCard title="Change" value={formatGrowth(w.growth_pct)} hint="recent vs previous" />
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <CumulativeLine yearly={data.yearly} />
        <YearlyBars yearly={data.yearly} />
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <CourtDonut data={data.by_court_level} />
      </section>
    </div>
  );
}
