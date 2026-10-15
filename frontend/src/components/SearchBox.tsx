"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

// TEMPORARY: jumps to a case by its numeric ID. When Person 1's /api/cases?q=
// endpoint exists, replace this with a real name/number search page.
export default function SearchBox() {
  const router = useRouter();
  const [text, setText] = useState("");
  const [message, setMessage] = useState("");

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const id = Number(text.trim());
    if (Number.isInteger(id) && id > 0) {
      router.push(`/cases/${id}`);
    } else {
      setMessage("Search by name arrives with the cases API. For now, enter a case ID (a number).");
    }
  }

  return (
    <form onSubmit={submit} className="w-full max-w-xl">
      <div className="flex gap-2">
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Enter a case ID, e.g. 1530"
          className="flex-1 rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm outline-none focus:border-blue-500"
        />
        <button className="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-blue-700">Search</button>
      </div>
      {message && <p className="mt-2 text-xs text-amber-700">{message}</p>}
    </form>
  );
}
