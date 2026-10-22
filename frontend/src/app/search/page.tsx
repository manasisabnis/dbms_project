import { Suspense } from "react";
import SearchResults from "@/components/SearchResults";

// useSearchParams must sit inside <Suspense> in this version of Next.js.
export default function SearchPage() {
  return (
    <Suspense fallback={<p className="text-slate-500">Loading…</p>}>
      <SearchResults />
    </Suspense>
  );
}
