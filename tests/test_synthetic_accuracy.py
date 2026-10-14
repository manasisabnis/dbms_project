"""Sanity check: the classifier should rediscover the patterns we planted.

Uses the full 2000-case dataset (in memory, no database) because the planted
"declining" pattern needs enough cases per year to cite from.
"""
from analysis.classify import classify_case
from analysis.rolling_window import build_all_stats, latest_date, to_date
from mongo.synthetic.generate_events import generate


def test_classifier_recovers_planted_patterns():
    cases, events, truth = generate(n_cases=2000, seed=42)
    catalog = {c["case_id"]: c for c in cases}
    as_of = latest_date(events)
    stats = build_all_stats(events, as_of)

    for label in ("emerging", "declining", "established", "recent"):
        ids = [cid for cid, t in truth.items() if t == label and cid in stats]
        hits = sum(classify_case(stats[c], to_date(catalog[c]["judgment_date"]), as_of) == label for c in ids)
        assert hits / len(ids) >= 0.85, f"{label}: only {hits}/{len(ids)} recovered"
