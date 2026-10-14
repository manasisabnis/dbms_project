"""Create the MongoDB indexes. Safe to run many times.

    python -m mongo.init_indexes

An index is like a book's index: Mongo can jump straight to the matching
documents instead of reading the whole collection.
"""
from __future__ import annotations

from pymongo import ASCENDING, DESCENDING


def create_indexes(db) -> None:
    ev = db["citation_events"]
    ev.create_index([("cited_case_id", ASCENDING), ("citation_date", ASCENDING)])  # per-case trends
    ev.create_index([("citing_case_id", ASCENDING)])                               # "who does this case cite"
    ev.create_index([("year", ASCENDING)])                                         # year-wise charts

    db["case_catalog"].create_index([("case_id", ASCENDING)], unique=True)

    st = db["case_window_stats"]
    st.create_index([("case_id", ASCENDING)], unique=True)
    st.create_index([("total_citations", DESCENDING)])                             # most cited
    for w in ("1", "3", "5"):
        st.create_index([(f"labels.{w}", ASCENDING), (f"windows.{w}.growth", DESCENDING)])


if __name__ == "__main__":
    from common.settings import get_db

    create_indexes(get_db())
    print("Indexes created.")
