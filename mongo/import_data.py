"""Import case catalog and citation events from JSONL into MongoDB."""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pymongo import ReplaceOne


BATCH = 1000


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def parse_date(value):
    return datetime.fromisoformat(value[:10])


def import_cases(db, path, reset=False) -> int:
    collection = db["case_catalog"]

    if reset:
        collection.delete_many({})

    processed = 0
    for case in read_jsonl(path):
        case["judgment_date"] = parse_date(case["judgment_date"])
        collection.replace_one(
            {"case_id": case["case_id"]},
            case,
            upsert=True,
        )
        processed += 1

    return processed


def import_events(db, path, reset=False) -> int:
    collection = db["citation_events"]

    if reset:
        collection.delete_many({})

    processed = 0
    for event in read_jsonl(path):
        event["citation_date"] = parse_date(event["citation_date"])
        event["citing_case_id"] = int(event["citing_case_id"])
        event["cited_case_id"] = int(event["cited_case_id"])

        pair = {
            "citing_case_id": event["citing_case_id"],
            "cited_case_id": event["cited_case_id"],
        }
        collection.replace_one(pair, event, upsert=True)
        processed += 1

    return processed


if __name__ == "__main__":
    from common.settings import get_db
    from mongo.init_indexes import create_indexes

    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", required=True)
    parser.add_argument("--events")
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    db = get_db()
    create_indexes(db)

    print("Cases processed:", import_cases(db, args.cases, args.reset))

    if args.events:
        print(
            "Events imported:",
            import_events(db, args.events, args.reset),
        )
    else:
        print("Citation events unchanged (no --events supplied).")
