"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { fetchJson } from "@/lib/api";

type CaseSearchResult = {
  case_id: number;
  case_name: string;
  case_number: string | null;
  judgment_date: string | null;
  court_name: string | null;
};

type CaseSearchResponse = {
  count: number;
  cases: CaseSearchResult[];
};

export default function SearchBox() {
  const router = useRouter();

  const [text, setText] = useState("");
  const [results, setResults] = useState<CaseSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();

    const query = text.trim();
    setError("");
    setResults([]);
    setSearched(false);

    if (!query) {
      setError("Enter a case name, case number, or case ID.");
      return;
    }

    // Preserve direct navigation by numeric case ID.
    if (/^\d+$/.test(query)) {
      router.push(`/cases/${query}`);
      return;
    }

    setLoading(true);

    try {
      const data = await fetchJson<CaseSearchResponse>(
        `/api/cases?q=${encodeURIComponent(query)}&limit=10`
      );

      setResults(data.cases ?? []);
      setSearched(true);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to search cases. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="w-full max-w-2xl">
      <form onSubmit={submit} className="w-full">
        <div className="flex gap-2">
          <input
            value={text}
            onChange={(e) => {
              setText(e.target.value);
              setResults([]);
              setSearched(false);
              setError("");
            }}
            placeholder="Search by case name or case number..."
            aria-label="Search cases by name, number, or case ID"
            className="min-w-0 flex-1 rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          />

          <button
            type="submit"
            disabled={loading}
            className="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "Searching..." : "Search"}
          </button>
        </div>
      </form>

      {error && (
        <p role="alert" className="mt-3 text-sm text-red-600">
          {error}
        </p>
      )}

      {searched && results.length === 0 && !error && (
        <p className="mt-3 text-sm text-slate-600">
          No matching cases found. Try a different name or case number.
        </p>
      )}

      {results.length > 0 && (
        <div
          className="mt-4 overflow-hidden rounded-lg border border-slate-200 bg-white"
          aria-label="Case search results"
        >
          <p className="border-b border-slate-200 px-4 py-2 text-xs text-slate-500">
            Found {results.length} matching case
            {results.length === 1 ? "" : "s"}. Select one to view its trends.
          </p>

          <ul className="divide-y divide-slate-100">
            {results.map((item) => (
              <li key={item.case_id}>
                <button
                  type="button"
                  onClick={() => router.push(`/cases/${item.case_id}`)}
                  className="w-full px-4 py-3 text-left hover:bg-slate-50 focus:bg-slate-50 focus:outline-none"
                >
                  <span className="block text-sm font-medium text-slate-900">
                    {item.case_name}
                  </span>

                  <span className="mt-1 block text-xs text-slate-600">
                    Case ID: {item.case_id}
                    {item.case_number
                      ? ` · ${item.case_number}`
                      : ""}
                  </span>

                  {(item.court_name || item.judgment_date) && (
                    <span className="mt-1 block text-xs text-slate-500">
                      {[item.court_name, item.judgment_date?.slice(0, 10)]
                        .filter(Boolean)
                        .join(" · ")}
                    </span>
                  )}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
