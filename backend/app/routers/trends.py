"""Person 2's endpoints: everything that reads MongoDB (trends and labels)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from analysis.config import WINDOWS
from backend.app.deps import get_db
from backend.app.schemas import (
    CaseSummary, CaseTrendResponse, CourtLevelCount, DashboardResponse,
    LabelCounts, WindowStats, YearCount,
)
from mongo.pipelines.pipelines import court_level_pipeline, yearly_counts_pipeline

router = APIRouter(tags=["trends"])

def _summary(doc: dict, window: int) -> CaseSummary:
    w = doc["windows"][str(window)]
    return CaseSummary(
        case_id=doc["case_id"],
        case_name=doc["case_name"],
        case_number=doc.get("case_number"),
        total_citations=doc["total_citations"],
        recent=w["recent"],
        previous=w["previous"],
        growth_pct=round(w["growth"] * 100, 1),
        label=doc["labels"][str(window)],
    )


def _top(db, window: int, label: str, sort_field: str, direction: int, limit: int) -> list[CaseSummary]:
    cursor = (
        db["case_window_stats"]
        .find({f"labels.{window}": label}, {"_id": 0})
        .sort(sort_field, direction)
        .limit(limit)
    )
    return [_summary(d, window) for d in cursor]


@router.get("/trends/dashboard", response_model=DashboardResponse)
def dashboard(window: int = 3, limit: int = Query(5, ge=1, le=50), db=Depends(get_db)):
    """Counts per label plus the top lists shown on the home page."""
    if window not in WINDOWS:
        raise HTTPException(status_code=422, detail=f"window must be one of {list(WINDOWS)}")
    stats = db["case_window_stats"]

    counts = {row["_id"]: row["n"] for row in stats.aggregate([
        {"$group": {"_id": f"$labels.{window}", "n": {"$sum": 1}}}
    ])}

    sample = stats.find_one({}, {"as_of": 1, "_id": 0})
    growth = f"windows.{window}.growth"
    most_cited = [_summary(d, window) for d in
                  stats.find({}, {"_id": 0}).sort("total_citations", -1).limit(limit)]

    return DashboardResponse(
        window_years=window,
        as_of=sample["as_of"] if sample else None,
        counts=LabelCounts(**counts),
        emerging=_top(db, window, "emerging", growth, -1, limit),     # biggest rise first
        declining=_top(db, window, "declining", growth, 1, limit),    # biggest drop first
        established=_top(db, window, "established", "total_citations", -1, limit),
        most_cited=most_cited,
    )


@router.get("/cases/{case_id}/citation-trend", response_model=CaseTrendResponse)
def citation_trend(case_id: int, db=Depends(get_db)):
    """Everything the case-details / analysis page needs from MongoDB."""
    doc = db["case_window_stats"].find_one({"case_id": case_id}, {"_id": 0})
    if doc is None:
        raise HTTPException(status_code=404, detail="No citation data for this case")

    events = db["citation_events"]
    yearly = [YearCount(year=r["_id"], count=r["count"]) for r in events.aggregate(yearly_counts_pipeline(case_id))]
    courts = [CourtLevelCount(court_level=r["_id"], count=r["count"]) for r in events.aggregate(court_level_pipeline(case_id))]

    return CaseTrendResponse(
        case_id=doc["case_id"],
        case_name=doc["case_name"],
        case_number=doc.get("case_number"),
        as_of=doc["as_of"],
        total_citations=doc["total_citations"],
        label=doc["label"],
        labels=doc["labels"],
        windows={k: WindowStats(recent=v["recent"], previous=v["previous"], growth_pct=round(v["growth"] * 100, 1))
                 for k, v in doc["windows"].items()},
        yearly=yearly,
        by_court_level=courts,
    )
