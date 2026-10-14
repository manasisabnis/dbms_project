"""Compute rolling-window stats + labels for every cited case and store them.

    python -m mongo.build_stats                 # as_of = newest citation in the data
    python -m mongo.build_stats --as-of 2025-06-30

Reads : citation_events, case_catalog
Writes: case_window_stats  (one document per cited case; replaced on every run; the API reads this)
"""
from __future__ import annotations

import argparse
from datetime import date

from analysis.classify import classify_all_windows
from analysis.config import DEFAULT_WINDOW
from analysis.rolling_window import build_all_stats, to_date


def build_stats(db, as_of: date | None = None) -> int:
    events = list(db["citation_events"].find({}, {"_id": 0, "cited_case_id": 1, "citation_date": 1}))
    if not events:
        return 0
    if as_of is None:
        as_of = max(to_date(e["citation_date"]) for e in events)

    stats = build_all_stats(events, as_of)
    catalog = {c["case_id"]: c for c in db["case_catalog"].find({}, {"_id": 0})}

    docs = []
    for case_id, s in stats.items():
        case = catalog.get(case_id)
        if case is None:                      # cited case missing from the catalog: skip it
            continue
        labels = classify_all_windows(s, to_date(case["judgment_date"]), as_of)
        docs.append({
            "case_id": case_id,
            "case_name": case["case_name"],
            "case_number": case.get("case_number"),
            "judgment_date": case["judgment_date"],
            "as_of": str(as_of),
            "total_citations": s["total"],
            "windows": s["windows"],
            "trailing_years": s["trailing_years"],
            "labels": labels,
            "label": labels[str(DEFAULT_WINDOW)],
        })

    # Full recompute every time: wipe the old stats, then insert the new ones.
    db["case_window_stats"].delete_many({})
    for i in range(0, len(docs), 5000):
        db["case_window_stats"].insert_many(docs[i:i + 5000])
    return len(docs)


if __name__ == "__main__":
    from common.settings import get_db

    ap = argparse.ArgumentParser()
    ap.add_argument("--as-of", default=None, help="YYYY-MM-DD (default: newest citation)")
    a = ap.parse_args()
    n = build_stats(get_db(), date.fromisoformat(a.as_of) if a.as_of else None)
    print(f"Stats written for {n} cases.")
