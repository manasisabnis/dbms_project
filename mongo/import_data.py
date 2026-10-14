"""Load cases + citation events from JSONL files into MongoDB.

    python -m mongo.import_data --cases data/synthetic/cases.jsonl \
                                --events data/synthetic/citation_events.jsonl --reset

Works for the synthetic files AND for Person 1's real files, as long as they
follow contracts/data_contract.md.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime

BATCH = 5000


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def parse_date(value: str) -> datetime:
    return datetime.fromisoformat(value[:10])           # 'YYYY-MM-DD' -> datetime at midnight


def _insert_in_batches(collection, docs) -> int:
    batch, total = [], 0
    for doc in docs:
        batch.append(doc)
        if len(batch) >= BATCH:
            collection.insert_many(batch)
            total += len(batch)
            batch = []
    if batch:
        collection.insert_many(batch)
        total += len(batch)
    return total


def import_cases(db, path, reset=False) -> int:
    if reset:
        db["case_catalog"].delete_many({})
    docs = ({**c, "judgment_date": parse_date(c["judgment_date"])} for c in read_jsonl(path))
    return _insert_in_batches(db["case_catalog"], docs)


def import_events(db, path, reset=False) -> int:
    if reset:
        db["citation_events"].delete_many({})
    docs = ({**e, "citation_date": parse_date(e["citation_date"])} for e in read_jsonl(path))
    return _insert_in_batches(db["citation_events"], docs)


if __name__ == "__main__":
    from common.settings import get_db
    from mongo.init_indexes import create_indexes

    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", required=True)
    ap.add_argument("--events", required=True)
    ap.add_argument("--reset", action="store_true", help="empty the collections first")
    a = ap.parse_args()

    db = get_db()
    create_indexes(db)
    print("cases imported: ", import_cases(db, a.cases, a.reset))
    print("events imported:", import_events(db, a.events, a.reset))
