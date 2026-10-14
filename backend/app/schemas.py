"""Shapes of the JSON the API returns. FastAPI uses these to validate output and
to build the interactive docs at /docs."""
from __future__ import annotations

from pydantic import BaseModel


class CaseSummary(BaseModel):
    case_id: int
    case_name: str
    case_number: str | None = None
    total_citations: int
    recent: int            # citations in the recent window
    previous: int          # citations in the window before it
    growth_pct: float      # +320.0 means +320 %
    label: str


class LabelCounts(BaseModel):
    emerging: int = 0
    declining: int = 0
    established: int = 0
    recent: int = 0
    regular: int = 0


class DashboardResponse(BaseModel):
    window_years: int
    as_of: str | None
    counts: LabelCounts
    emerging: list[CaseSummary]
    declining: list[CaseSummary]
    established: list[CaseSummary]
    most_cited: list[CaseSummary]


class WindowStats(BaseModel):
    recent: int
    previous: int
    growth_pct: float


class YearCount(BaseModel):
    year: int
    count: int


class CourtLevelCount(BaseModel):
    court_level: str
    count: int


class CaseTrendResponse(BaseModel):
    case_id: int
    case_name: str
    case_number: str | None = None
    as_of: str
    total_citations: int
    label: str                         # label for the default 3-year window
    labels: dict[str, str]             # {"1": ..., "3": ..., "5": ...}
    windows: dict[str, WindowStats]    # {"1": ..., "3": ..., "5": ...}
    yearly: list[YearCount]
    by_court_level: list[CourtLevelCount]
