"use client";

import { useState } from "react";
import CaseTable from "@/components/CaseTable";
import LandmarkList from "@/components/LandmarkList";
import SearchBox from "@/components/SearchBox";
import StatCard from "@/components/StatCard";
import WindowToggle from "@/components/WindowToggle";
import type { DashboardResponse, WindowYears } from "@/lib/api";
import { useApi } from "@/lib/useApi";

export default function Dashboard() {
  const [windowYears, setWindowYears] = useState<WindowYears>(3);
  const { data, error, loading } = useApi<DashboardResponse>(`/api/trends/dashboard?window=${windowYears}&limit=5`);

  return (
    <div className="space-y-8">
      <section>
        <h1 className="text-3xl font-bold">Explore how legal precedents gain or lose influence</h1>
        <p className="mt-2 text-slate-600">Citation activity of Indian cases, analysed over rolling time windows.</p>
        <div className="mt-5">
          <SearchBox />
        </div>
      </section>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl font-semibold">Citation trends</h2>
        <WindowToggle value={windowYears} onChange={setWindowYears} />
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          Could not load data: {error}. Is the backend running on port 8000?
        </div>
      )}
      {loading && !error && <p className="text-slate-500">Loading…</p>}

      {data && (
        <>
          <section className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <StatCard title="Emerging cases" value={data.counts.emerging ?? 0} hint={`${windowYears}-year window`} />
            <StatCard title="Influential cases" value={data.counts.established ?? 0} />
            <StatCard title="Declining cases" value={data.counts.declining ?? 0} />
            <StatCard title="Recent cases" value={data.counts.recent ?? 0} hint={data.as_of ? `as of ${data.as_of}` : undefined} />
          </section>

          <section className="grid gap-4 lg:grid-cols-3">
            <CaseTable title="🔥 Emerging Cases" cases={data.emerging} metric="growth" />
            <CaseTable title="⭐ Most Cited Cases" cases={data.most_cited} metric="citations" />
            <CaseTable title="📉 Declining Cases" cases={data.declining} metric="growth" />
          </section>
        </>
      )}

      <LandmarkList />
    </div>
  );
}
