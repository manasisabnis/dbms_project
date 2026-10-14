"""Run the whole analysis on the synthetic files, with NO database.

    python -m mongo.synthetic.generate_events
    python -m analysis.demo_local

Prints label counts, the top emerging/declining cases, and how often the
classifier agrees with the pattern we planted (the "ground truth").
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from analysis import config as cfg
from analysis.classify import classify_case
from analysis.rolling_window import build_all_stats, latest_date, to_date


def read_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def main(folder: str = "data/synthetic", window: int = cfg.DEFAULT_WINDOW):
    folder = Path(folder)
    events = read_jsonl(folder / "citation_events.jsonl")
    cases = {c["case_id"]: c for c in read_jsonl(folder / "cases.jsonl")}
    truth = {int(k): v for k, v in json.load(open(folder / "ground_truth.json")).items()}

    as_of = latest_date(events)
    stats = build_all_stats(events, as_of)
    labels = {
        cid: classify_case(s, to_date(cases[cid]["judgment_date"]), as_of, window)
        for cid, s in stats.items()
    }

    print(f"as_of = {as_of}   window = {window} years   cited cases = {len(stats)}\n")
    print("Label counts:", dict(Counter(labels.values())), "\n")

    for name, reverse in (("emerging", True), ("declining", False)):
        picks = [cid for cid, lab in labels.items() if lab == name]
        picks.sort(key=lambda c: stats[c]["windows"][str(window)]["growth"], reverse=reverse)
        print(f"Top {name}:")
        for cid in picks[:5]:
            w = stats[cid]["windows"][str(window)]
            print(f"  case {cid:>5}  previous={w['previous']:>3}  recent={w['recent']:>3}  growth={w['growth']:+.0%}")
        print()

    # compare with planted patterns (never-cited cases are 'regular' by definition)
    agree = Counter()
    total = Counter()
    for cid, true in truth.items():
        guess = labels.get(cid, cfg.REGULAR)
        total[true] += 1
        agree[true] += guess == true
    print("Agreement with planted patterns:")
    for lab in cfg.ALL_LABELS:
        if total[lab]:
            print(f"  {lab:<12} {agree[lab]:>4}/{total[lab]:<4} = {agree[lab] / total[lab]:.0%}")


if __name__ == "__main__":
    main()
