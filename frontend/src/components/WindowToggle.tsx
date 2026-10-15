import type { WindowYears } from "@/lib/api";

const OPTIONS: WindowYears[] = [1, 3, 5];

export default function WindowToggle({ value, onChange }: { value: WindowYears; onChange: (w: WindowYears) => void }) {
  return (
    <div className="inline-flex rounded-lg border border-slate-200 bg-white p-1 text-sm">
      {OPTIONS.map((w) => (
        <button
          key={w}
          onClick={() => onChange(w)}
          className={`rounded-md px-3 py-1.5 ${value === w ? "bg-blue-600 text-white" : "text-slate-600 hover:bg-slate-100"}`}
        >
          {w} {w === 1 ? "Year" : "Years"}
        </button>
      ))}
    </div>
  );
}
