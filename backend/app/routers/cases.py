"""Read-only endpoints for legal cases stored in MongoDB."""
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.deps import get_db

router = APIRouter(tags=["cases"])

CASE_FIELDS = {
    "_id": 0,
    "case_id": 1,
    "case_name": 1,
    "case_number": 1,
    "judgment_date": 1,
    "court_name": 1,
    "case_type": 1,
    "decision": 1,
    "location": 1,
    "court_level": 1,
    "cnr_number": 1,
    "neutral_citation": 1,
    "law_report_citation": 1,
    "source_pdf_s3_url": 1,
}


@router.get("/cases")
def search_cases(
    q: Optional[str] = Query(default=None, max_length=200),
    limit: int = Query(default=20, ge=1, le=100),
    db=Depends(get_db),
):
    """List recent cases or search by case name or number."""
    try:
        query = {}

        if q and q.strip():
            term = re.escape(q.strip())
            query = {
                "$or": [
                    {"case_name": {"$regex": term, "$options": "i"}},
                    {"case_number": {"$regex": term, "$options": "i"}},
                ]
            }

        rows = list(
            db["case_catalog"]
            .find(query, CASE_FIELDS)
            .sort([("judgment_date", -1), ("case_id", -1)])
            .limit(limit)
        )

        return {"count": len(rows), "cases": rows}

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve legal cases.",
        ) from exc


@router.get("/cases/{case_id}")
def get_case(case_id: int, db=Depends(get_db)):
    """Retrieve one case from the MongoDB case catalogue."""
    try:
        row = db["case_catalog"].find_one(
            {"case_id": case_id},
            CASE_FIELDS,
        )

        if row is None:
            raise HTTPException(status_code=404, detail="Case not found.")

        return row

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve the case.",
        ) from exc


@router.get("/landmark-cases")
def landmark_cases(
    limit: int = Query(default=5, ge=1, le=50),
    db=Depends(get_db),
):
    """Return most-cited cases from MongoDB citation statistics."""
    try:
        docs = list(
            db["case_window_stats"]
            .find(
                {"total_citations": {"$gt": 0}},
                {
                    "_id": 0,
                    "case_id": 1,
                    "case_name": 1,
                    "case_number": 1,
                    "judgment_date": 1,
                    "total_citations": 1,
                },
            )
            .sort([("total_citations", -1), ("case_id", 1)])
            .limit(limit)
        )

        results = []
        for doc in docs:
            date = doc.get("judgment_date")
            if hasattr(date, "isoformat"):
                date = date.isoformat()[:10]
            elif date:
                date = str(date)[:10]

            results.append({
                "case_id": doc["case_id"],
                "case_name": doc["case_name"],
                "case_number": doc.get("case_number"),
                "judgment_date": date or "",
                "citation_count": int(doc.get("total_citations", 0)),
            })

        return {"results": results}
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve landmark cases.",
        ) from exc

