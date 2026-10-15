
import csv
import gzip
from pathlib import Path

path = Path("data/processed/cases_final_1970_2026.csv.gz")

expected_columns = [
    "source_record_id",
    "case_name",
    "case_number",
    "cnr_number",
    "neutral_citation",
    "law_report_citation",
    "judgment_date",
    "citation_year",
    "court_name",
    "court_code",
    "bench_name",
    "presiding_judge",
    "decision",
    "source_pdf_s3_url",
]

total = 0
bad_rows = 0
invalid_years = 0
missing_ids = 0
years = set()

with gzip.open(path, "rt", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)

    if reader.fieldnames != expected_columns:
        raise SystemExit(
            f"Header mismatch!\nFound: {reader.fieldnames}"
        )

    for row in reader:
        total += 1

        if None in row or any(row.get(c) is None for c in expected_columns):
            bad_rows += 1
            continue

        source_id = (row.get("source_record_id") or "").strip()
        if not source_id:
            missing_ids += 1

        date = (row.get("judgment_date") or "").strip()
        if len(date) < 4 or not date[:4].isdigit():
            invalid_years += 1
        else:
            year = int(date[:4])
            if not 1970 <= year <= 2026:
                invalid_years += 1
            years.add(year)

print("Header matches expected schema: Yes")
print("Total records:", f"{total:,}")
print("Malformed rows:", bad_rows)
print("Missing source IDs:", missing_ids)
print("Invalid/out-of-range years:", invalid_years)
print("Earliest year:", min(years) if years else None)
print("Latest year:", max(years) if years else None)
print("Number of distinct years:", len(years))
print("File size:", f"{path.stat().st_size / (1024**3):.2f} GiB")
