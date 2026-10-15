export default function StatCard({ title, value, hint }: { title: string; value: string | number; hint?: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-3xl font-bold">{value}</p>
      <p className="mt-1 text-sm font-medium text-slate-700">{title}</p>
      {hint && <p className="text-xs text-slate-500">{hint}</p>}
    </div>
  );
}
