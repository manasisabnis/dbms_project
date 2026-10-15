"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

// A number goes straight to that case. Anything else is a name / case-number search.
export default function SearchBox({ initial = "" }: { initial?: string }) {
  const router = useRouter();
  const [text, setText] = useState(initial);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const value = text.trim();
    if (!value) return;
    if (/^\d+$/.test(value)) router.push(`/cases/${value}`);
    else router.push(`/search?q=${encodeURIComponent(value)}`);
  }

  return (
    <form onSubmit={submit} className="w-full max-w-xl">
      <div className="flex gap-2">
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Search a case name or number (or type a case ID)"
          className="flex-1 rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm outline-none focus:border-blue-500"
        />
        <button className="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-blue-700">Search</button>
      </div>
    </form>
  );
}
