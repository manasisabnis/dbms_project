import { USE_MOCKS } from "@/lib/api";

/** Shown only in mock mode, so nobody mistakes sample data for real data. */
export default function MockBanner({ what }: { what: string }) {
  if (!USE_MOCKS) return null;
  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-2 text-xs text-amber-800">
      Sample data: {what} come from placeholder files until the MySQL API is connected.
    </div>
  );
}
