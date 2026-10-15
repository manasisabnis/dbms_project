"use client";

import {
  Bar, BarChart, CartesianGrid, Cell, Line, LineChart, Pie, PieChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis, Legend,
} from "recharts";

type YearCount = { year: number; count: number };

/** The API only returns years that had citations. Fill the gaps with 0 and add a running total. */
export function fillYears(yearly: YearCount[]) {
  if (yearly.length === 0) return [];
  const byYear = new Map(yearly.map((y) => [y.year, y.count]));
  const first = Math.min(...yearly.map((y) => y.year));
  const last = Math.max(...yearly.map((y) => y.year));
  let running = 0;
  const rows = [];
  for (let year = first; year <= last; year++) {
    const count = byYear.get(year) ?? 0;
    running += count;
    rows.push({ year, count, cumulative: running });
  }
  return rows;
}

const CARD = "rounded-xl border border-slate-200 bg-white p-5 shadow-sm";

export function CumulativeLine({ yearly }: { yearly: YearCount[] }) {
  const data = fillYears(yearly);
  return (
    <div className={CARD}>
      <h3 className="mb-3 text-sm font-semibold">Citation Trend Over Time (running total)</h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Line type="monotone" dataKey="cumulative" name="Total citations" stroke="#2563eb" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function YearlyBars({ yearly }: { yearly: YearCount[] }) {
  const data = fillYears(yearly);
  return (
    <div className={CARD}>
      <h3 className="mb-3 text-sm font-semibold">Year-wise Citations</h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Bar dataKey="count" name="Citations" fill="#3b82f6" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

const COLORS = ["#2563eb", "#16a34a", "#f59e0b", "#9333ea"];

export function CourtDonut({ data }: { data: { court_level: string; count: number }[] }) {
  return (
    <div className={CARD}>
      <h3 className="mb-3 text-sm font-semibold">Citations by Court Level</h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} dataKey="count" nameKey="court_level" innerRadius={55} outerRadius={90}>
              {data.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
