"""MongoDB aggregation pipelines (the "NoSQL way" of doing the analysis).

An aggregation pipeline is a list of stages. Documents flow through the stages
in order, like a factory line:  $match (filter) -> $group (summarise) -> $sort ...
"""
from __future__ import annotations

from datetime import date, datetime, time

from analysis.rolling_window import shift_years


def as_datetime(d: date) -> datetime:
    """MongoDB stores dates as datetimes, so convert a plain date to midnight."""
    return datetime.combine(d, time.min)


def rolling_window_pipeline(as_of: date, years: int) -> list[dict]:
    """Recent vs previous citation counts for EVERY case, computed inside MongoDB."""
    recent_start = as_datetime(shift_years(as_of, -years))
    previous_start = as_datetime(shift_years(as_of, -2 * years))
    end = as_datetime(as_of)
    return [
        # 1. keep only citations inside the two windows
        {"$match": {"citation_date": {"$gt": previous_start, "$lte": end}}},
        # 2. one output row per cited case; add 1 to 'recent' or 'previous' per citation
        {"$group": {
            "_id": "$cited_case_id",
            "recent": {"$sum": {"$cond": [{"$gt": ["$citation_date", recent_start]}, 1, 0]}},
            "previous": {"$sum": {"$cond": [{"$gt": ["$citation_date", recent_start]}, 0, 1]}},
        }},
        # 3. growth = (recent - previous) / max(previous, 1)
        {"$addFields": {"growth": {"$divide": [
            {"$subtract": ["$recent", "$previous"]},
            {"$max": ["$previous", 1]},
        ]}}},
        {"$sort": {"growth": -1}},
    ]


def yearly_counts_pipeline(case_id: int) -> list[dict]:
    """How many times ONE case was cited in each calendar year (for the trend chart)."""
    return [
        {"$match": {"cited_case_id": case_id}},
        {"$group": {"_id": "$year", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]


def court_level_pipeline(case_id: int) -> list[dict]:
    """Which court levels cite ONE case (for the donut chart)."""
    return [
        {"$match": {"cited_case_id": case_id}},
        {"$group": {"_id": "$citing_court_level", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
