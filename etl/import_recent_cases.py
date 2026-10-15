import pandas as pd
import mysql.connector
from getpass import getpass
CSV_PATH = "data/processed/cases_recent_2024_2026_unique.csv"

df = pd.read_csv(CSV_PATH).fillna("")
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password=getpass("MySQL root password: "),
    database="legal_citation_analyzer"
)
cursor = conn.cursor()

added = 0
skipped = 0

try:
    for _, row in df.iterrows():
        cursor.execute(
            "SELECT case_id FROM LEGAL_CASE WHERE case_number = %s",
            (str(row["case_number"]),)
        )
        if cursor.fetchone():
            skipped += 1
            continue

        court_name = str(row["court_name"]).strip()
        cursor.execute(
            "SELECT court_id FROM COURT WHERE court_name = %s",
            (court_name,)
        )
        court = cursor.fetchone()

        if court:
            court_id = court[0]
        else:
            cursor.execute(
                "INSERT INTO COURT (court_name, location, court_level) "
                "VALUES (%s, %s, %s)",
                (court_name, "India", "Supreme Court" if "Supreme Court" in court_name else "High Court")
            )
            court_id = cursor.lastrowid

        judgment_date = str(row["judgment_date"]).strip() or None
        decision = str(row["decision"]).strip() or None

        cursor.execute(
            """
            INSERT INTO LEGAL_CASE
                (case_name, case_number, judgment_date, court_id, decision)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                str(row["case_name"]).strip(),
                str(row["case_number"]).strip(),
                judgment_date,
                court_id,
                decision
            )
        )
        added += 1

    conn.commit()
    print("Recent cases added:", added)
    print("Existing case numbers skipped:", skipped)
    print("Import completed.")

except Exception:
    conn.rollback()
    raise

finally:
    cursor.close()
    conn.close()
