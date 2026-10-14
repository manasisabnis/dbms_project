"""Generate FAKE cases + citation events with known patterns.

Why: Person 1's real citation data will take a while. This lets you build and
test the rolling-window logic and the UI today. Every case is created with a
planted pattern ("archetype") so we can check the classifier finds it.

Run:  python -m mongo.synthetic.generate_events --cases 2000 --seed 42
Writes (to data/synthetic/):
    cases.jsonl           case catalog (one JSON object per line)
    citation_events.jsonl one citation per line
    ground_truth.json     {case_id: true label} for checking the classifier
"""
from __future__ import annotations

import argparse
import json
import math
import random
from datetime import date, timedelta
from pathlib import Path

LAST_YEAR = 2025  # synthetic data ends on 2025-12-31

PARTIES = [
    "Union of India", "State of Kerala", "State of Karnataka", "State of Tamil Nadu",
    "Ramesh Kumar", "Sunita Devi", "Mohan Lal", "Priya Sharma", "Anil Verma",
    "Meera Nair", "Rajan Pillai", "Fatima Begum", "Suresh Reddy", "Lakshmi Iyer",
    "Municipal Corporation", "National Bank", "Excise Commissioner", "Collector of Customs",
]
COURT_LEVELS = ["Supreme Court", "High Court", "Lower Courts"]
COURT_WEIGHTS = [0.72, 0.22, 0.06]

# archetype -> (how many of 100 cases, range of judgment years)
MIX = {
    "established": (4, (1975, 2012)),
    "emerging":    (3, (1990, 2018)),
    "declining":   (3, (1990, 2014)),
    "recent":      (3, (2023, 2025)),
}
TRUE_LABEL = {
    "established": "established", "emerging": "emerging", "declining": "declining",
    "recent": "recent", "quiet": "regular",
}


def poisson(lam: float, rng: random.Random) -> int:
    """Knuth's algorithm: random count with average `lam` (fine for lam < ~100)."""
    if lam <= 0:
        return 0
    limit, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1


def expected_citations(archetype: str, year: int, judged_year: int, quiet_rate: float) -> float:
    """Average number of citations a case receives in a given year."""
    if archetype == "established":
        return 12.0
    if archetype == "emerging":
        return 1.0 if year <= 2021 else 2.0 + (year - 2021) * 6.0      # 8, 14, 20, 26
    if archetype == "declining":
        return 10.0 if year < 2018 else 30.0 * math.exp(-(year - 2018) / 2.5)
    if archetype == "recent":
        return 5.0 * (year - judged_year + 1)                            # grows each year
    return quiet_rate                                                    # "quiet"


def random_date_in_year(year: int, rng: random.Random) -> date:
    start = date(year, 1, 1)
    return start + timedelta(days=rng.randrange(365))


def generate(n_cases: int = 2000, seed: int = 42):
    rng = random.Random(seed)

    # 1. decide each case's archetype and judgment date
    cases = []
    archetypes = []
    for arch, (per_100, _) in MIX.items():
        archetypes += [arch] * round(n_cases * per_100 / 100)
    archetypes += ["quiet"] * (n_cases - len(archetypes))
    rng.shuffle(archetypes)

    for i, arch in enumerate(archetypes, start=1):
        lo, hi = MIX[arch][1] if arch in MIX else (1960, LAST_YEAR)
        year = rng.randint(lo, hi)
        cases.append({
            "case_id": i,
            "case_name": f"{rng.choice(PARTIES)} v. {rng.choice(PARTIES)}",
            "case_number": f"AIR {year} SC {rng.randint(1, 3000)}",
            "judgment_date": random_date_in_year(year, rng).isoformat(),
            "court_name": "Supreme Court of India",
            "_arch": arch,
            "_year": year,
            "_quiet_rate": rng.uniform(0.2, 1.5),
            "_scale": rng.uniform(0.8, 1.2),
        })

    # 2. index cases by the year they were decided: a citation is made by a
    #    case decided in the same year, and takes that case's judgment date.
    by_year: dict[int, list[dict]] = {}
    for c in cases:
        by_year.setdefault(c["_year"], []).append(c)

    # 3. for every case and every year after it, draw a number of citations
    events = []
    for cited in cases:
        for year in range(cited["_year"], LAST_YEAR + 1):
            lam = expected_citations(cited["_arch"], year, cited["_year"], cited["_quiet_rate"]) * cited["_scale"]
            pool = [c for c in by_year.get(year, []) if c["case_id"] != cited["case_id"]]
            n = min(poisson(lam, rng), len(pool))
            for citing in rng.sample(pool, n):          # without replacement = distinct citing cases
                d = citing["judgment_date"]
                events.append({
                    "citing_case_id": citing["case_id"],
                    "cited_case_id": cited["case_id"],
                    "citation_date": d,
                    "year": int(d[:4]),
                    "citing_court_level": rng.choices(COURT_LEVELS, COURT_WEIGHTS)[0],
                })

    truth = {c["case_id"]: TRUE_LABEL[c["_arch"]] for c in cases}
    public_cases = [{k: v for k, v in c.items() if not k.startswith("_")} for c in cases]
    return public_cases, events, truth


def write_files(out_dir: str, n_cases: int, seed: int):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    cases, events, truth = generate(n_cases, seed)
    with open(out / "cases.jsonl", "w") as f:
        f.writelines(json.dumps(c) + "\n" for c in cases)
    with open(out / "citation_events.jsonl", "w") as f:
        f.writelines(json.dumps(e) + "\n" for e in events)
    with open(out / "ground_truth.json", "w") as f:
        json.dump(truth, f)
    return len(cases), len(events)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="data/synthetic")
    a = ap.parse_args()
    n_c, n_e = write_files(a.out, a.cases, a.seed)
    print(f"Wrote {n_c} cases and {n_e} citation events to {a.out}/")
