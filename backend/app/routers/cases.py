"""Read-only endpoints for relational legal-case records."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.mysql_db import get_mysql_connection

router = APIRouter(tags=["cases"])


@router.get("/cases")
def search_cases(
    q: Optional[str] = Query(default=None, max_length=200),
    limit: int = Query(default=20, ge=1, le=100),
    connection=Depends(get_mysql_connection),
):
    """List recent cases or search by case name/number."""
    try:
        cursor = connection.cursor(dictionary=True)
        if q and q.strip():
            term = f"%{q.strip()}%"
            cursor.execute(
                """
                SELECT c.case_id, c.case_name, c.case_number,
                       c.judgment_date, c.case_type, c.decision,
                       court.court_name
                FROM LEGAL_CASE AS c
                LEFT JOIN COURT AS court ON court.court_id = c.court_id
                WHERE c.case_name LIKE %s OR c.case_number LIKE %s
                ORDER BY c.judgment_date DESC, c.case_id DESC
                LIMIT %s
                """,
                (term, term, limit),
            )
        else:
            cursor.execute(
                """
                SELECT c.case_id, c.case_name, c.case_number,
                       c.judgment_date, c.case_type, c.decision,
                       court.court_name
                FROM LEGAL_CASE AS c
                LEFT JOIN COURT AS court ON court.court_id = c.court_id
                ORDER BY c.judgment_date DESC, c.case_id DESC
                LIMIT %s
                """,
                (limit,),
            )
        rows = cursor.fetchall()
        return {"count": len(rows), "cases": rows}
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail="Unable to retrieve legal cases."
        ) from exc
    finally:
        if "cursor" in locals():
            cursor.close()
        connection.close()


@router.get("/cases/{case_id}")
def get_case(case_id: int, connection=Depends(get_mysql_connection)):
    """Retrieve one case and its court details."""
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT c.case_id, c.case_name, c.case_number,
                   c.judgment_date, c.case_type, c.decision,
                   court.court_name, court.location, court.court_level
            FROM LEGAL_CASE AS c
            LEFT JOIN COURT AS court ON court.court_id = c.court_id
            WHERE c.case_id = %s
            """,
            (case_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Case not found.")
        return row
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail="Unable to retrieve the case."
        ) from exc
    finally:
        if "cursor" in locals():
            cursor.close()
        connection.close()
