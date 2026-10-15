import { Suspense } from "react";
import CaseDetails from "@/components/CaseDetails";

// The route's [id] is read inside CaseDetails (a client component).
// This version of Next.js requires such reads to sit inside <Suspense>.
export default function CasePage() {
  return (
    <Suspense fallback={<p className="text-slate-500">Loading…</p>}>
      <CaseDetails />
    </Suspense>
  );
}
