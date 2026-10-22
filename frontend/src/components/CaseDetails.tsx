"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { AnalysisTab, CitedByTab, FullTextTab, JudgesTab, OverviewTab, StatutesTab } from "@/components/CaseTabs";
import LabelBadge from "@/components/LabelBadge";
import MockBanner from "@/components/MockBanner";
import type { CaseDetail, CaseTrendResponse, CitedByResponse } from "@/lib/api";
import { useApi } from "@/lib/useApi";

const TABS = ["Overview", "Citation Analysis", "Cited By", "Judges", "Statutes", "Full Text"] as const;
type Tab = (typeof TABS)[number];

export default function CaseDetails() {
  const { id } = useParams<{ id: string }>();
  const [tab, setTab] = useState<Tab>("Overview");

  const trend = useApi<CaseTrendResponse>(`/api/cases/${id}/citation-trend`); // MongoDB
  const detail = useApi<CaseDetail>(`/api/cases/${id}`); //                      MySQL
  const citedBy = useApi<CitedByResponse>(
    `/api/cases/${id}/citations?page=1&page_size=1`
  );

  const visibleTabs = TABS.filter((t) => {
    if (t === "Overview" || t === "Citation Analysis") return true;

    if (t === "Cited By") {
      return (citedBy.data?.total ?? 0) > 0;
    }

    const d = detail.data;
    if (!d) return false;

    if (t === "Judges") {
      return Boolean(
        (Array.isArray(d.judges) && d.judges.length > 0) ||
        d.coram_members_text?.trim()
      );
    }

    if (t === "Statutes") {
      return Boolean(d.statutes?.length);
    }

    if (t === "Full Text") {
      return Boolean(
        d.pdf_url || d.source_pdf_s3_url || d.source_json_s3_url
      );
    }

    return false;
  });

  // Both failed: nothing to show for this id.
  if (trend.error && detail.error) {
    return (
      <div className="space-y-3">
        <Link href="/" className="text-sm text-blue-700 hover:underline">← Back to dashboard</Link>
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          Could not load case {id}. {detail.error}
        </div>
      </div>
    );
  }

  const name = trend.data?.case_name ?? detail.data?.case_name ?? `Case ${id}`;
  const number = trend.data?.case_number ?? detail.data?.case_number;

  return (
    <div className="space-y-6">
      <Link href="/" className="text-sm text-blue-700 hover:underline">← Back to dashboard</Link>

      <header>
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-bold">{name}</h1>
          {trend.data && <LabelBadge label={trend.data.label} />}
        </div>
        <p className="mt-1 text-sm text-slate-600">{number ?? `Case ID ${id}`}</p>
      </header>

      <MockBanner what="case information, judges, statutes and cited-by lists" />

      <nav className="flex flex-wrap gap-2 border-b border-slate-200">
        {visibleTabs.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`-mb-px border-b-2 px-3 py-2 text-sm ${
              tab === t ? "border-blue-600 font-medium text-blue-700" : "border-transparent text-slate-600 hover:text-slate-900"
            }`}
          >
            {t}
          </button>
        ))}
      </nav>

      {tab === "Overview" && <OverviewTab detail={detail} trend={trend} />}
      {tab === "Citation Analysis" && <AnalysisTab trend={trend} />}
      {tab === "Cited By" && <CitedByTab caseId={id} />}
      {tab === "Judges" && <JudgesTab detail={detail} />}
      {tab === "Statutes" && <StatutesTab detail={detail} />}
      {tab === "Full Text" && <FullTextTab detail={detail} />}
    </div>
  );
}
