"""Rolling-window citation counting (pure Python, no database needed).

Window idea, for a window of `years` ending at `as_of`:

    previous window            recent window
  (as_of-2y, as_of-1y]       (as_of-1y, as_of]        <- shown for years=1

Both windows are "open on the left, closed on the right" so no citation is
ever counted twice.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from typing import Iterable

from analysis.config import TRAILING_YEARS, WINDOWS


def to_date(value) -> date:
    """Accept a date, datetime or 'YYYY-MM-DD' string and return a date."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def shift_years(d: date, years: int) -> date:
    """Move a date by whole years (Feb 29 falls back to Feb 28)."""
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        return d.replace(year=d.year + years, day=28)


def count_between(dates: list[date], start_exclusive: date, end_inclusive: date) -> int:
    return sum(1 for d in dates if start_exclusive < d <= end_inclusive)


def window_counts(dates: list[date], as_of: date, years: int) -> dict:
    """Citations in the recent window vs the window just before it."""
    recent_start = shift_years(as_of, -years)
    previous_start = shift_years(as_of, -2 * years)
    recent = count_between(dates, recent_start, as_of)
    previous = count_between(dates, previous_start, recent_start)
    # max(previous, 1) avoids dividing by zero when a case had no earlier citations.
    growth = (recent - previous) / max(previous, 1)
    return {"recent": recent, "previous": previous, "growth": round(growth, 4)}


def trailing_year_counts(dates: list[date], as_of: date, n_years: int = TRAILING_YEARS) -> list[int]:
    """Citations in each of the last n one-year slices, oldest first."""
    counts = []
    for k in range(n_years, 0, -1):
        end = shift_years(as_of, -(k - 1))
        start = shift_years(as_of, -k)
        counts.append(count_between(dates, start, end))
    return counts


def compute_case_stats(dates: list[date], as_of: date) -> dict:
    """Everything the classifier and the UI need for ONE case."""
    return {
        "total": sum(1 for d in dates if d <= as_of),
        # keys are strings because MongoDB document keys must be strings
        "windows": {str(w): window_counts(dates, as_of, w) for w in WINDOWS},
        "trailing_years": trailing_year_counts(dates, as_of),
    }


def group_dates_by_case(events: Iterable[dict]) -> dict[int, list[date]]:
    """{cited_case_id: [citation dates...]} from a stream of citation events."""
    grouped: dict[int, list[date]] = defaultdict(list)
    for e in events:
        grouped[e["cited_case_id"]].append(to_date(e["citation_date"]))
    return grouped


def latest_date(events: Iterable[dict]) -> date:
    return max(to_date(e["citation_date"]) for e in events)


def build_all_stats(events: Iterable[dict], as_of: date) -> dict[int, dict]:
    """Stats for every cited case. Cases never cited simply don't appear."""
    return {
        case_id: compute_case_stats(dates, as_of)
        for case_id, dates in group_dates_by_case(events).items()
    }
