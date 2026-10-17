"""Export the existing MySQL case catalog to the agreed MongoDB JSONL contract."""
import json
import os
from datetime import date, datetime
from pathlib import Path
from getpass import getpass

import mysql.connector

from etl.config import OUTPUT_DIR

OUTPUT = OUTPUT_DIR / "data" / "processed" / "cases.jsonl"


def main():
    conn = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD") or getpass("MySQL password: "),
        database=os.getenv("MYSQL_DATABASE", "legal_citation_analyzer"),
    )
    cur = conn.cursor(buffered=False)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temp = OUTPUT.with_suffix(".jsonl.tmp")

    exported = skipped = 0
    try:
        cur.execute("""
            SELECT c.case_id, c.case_name, c.case_number,
                   c.judgment_date, co.court_name
            FROM LEGAL_CASE c
            LEFT JOIN COURT co ON co.court_id = c.court_id
            ORDER BY c.case_id
        """)

        with temp.open("w", encoding="utf-8") as out:
            while True:
                rows = cur.fetchmany(1000)
                if not rows:
                    break

                for case_id, name, number, judgment_date, court in rows:
                    if judgment_date is None or not name:
                        skipped += 1
                        continue

                    if isinstance(judgment_date, (date, datetime)):
                        date_text = judgment_date.strftime("%Y-%m-%d")
                    else:
                        date_text = str(judgment_date)[:10]

                    record = {
                        "case_id": int(case_id),
                        "case_name": name,
                        "case_number": number,
                        "judgment_date": date_text,
                        "court_name": court or "Unknown Court",
                    }
                    out.write(json.dumps(record, ensure_ascii=False) + "\n")
                    exported += 1

        temp.replace(OUTPUT)
        print(f"Exported cases: {exported:,}")
        print(f"Skipped rows missing required fields: {skipped:,}")
        print(f"Output: {OUTPUT}")
        print("Existing MySQL rows were not modified.")
    except Exception:
        temp.unlink(missing_ok=True)
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
