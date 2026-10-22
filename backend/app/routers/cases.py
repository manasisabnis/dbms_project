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
