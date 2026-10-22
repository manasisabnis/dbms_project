
import csv
import gzip
from pathlib import Path

INPUT_FILES = [
    Path("data/processed/cases_clean.csv"),
    Path("data/processed/cases_2023_2026.csv"),
    Path("data/processed/cases_2025_2026.csv"),
]

OUTPUT = Path("data/processed/cases_final_1970_2026.csv.gz")
MIN_YEAR = 1970
MAX_YEAR = 2026

COLUMNS = [
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

if OUTPUT.exists():
    raise SystemExit(
        f"Output already exists: {OUTPUT}\n"
        "Inspect it before deciding whether to rerun."
    )

for path in INPUT_FILES:
    if not path.exists():
        raise SystemExit(f"Input file not found: {path}")

total_read = 0
total_kept = 0
excluded = 0
year_counts = {}

try:
    with gzip.open(
        OUTPUT, "wt", encoding="utf-8", newline=""
    ) as out:
        writer = csv.DictWriter(out, fieldnames=COLUMNS)
        writer.writeheader()

        for path in INPUT_FILES:
            print(f"Processing {path.name}...", flush=True)

            with path.open(
                "r", encoding="utf-8", newline=""
            ) as source:
                reader = csv.DictReader(source)

                missing = set(COLUMNS) - set(reader.fieldnames or [])
                if missing:
                    raise ValueError(
                        f"{path.name} is missing required columns: "
                        f"{sorted(missing)}"
                    )

                for row in reader:
                    total_read += 1
                    date = (row.get("judgment_date") or "").strip()

                    if len(date) < 4 or not date[:4].isdigit():
                        excluded += 1
                        continue

                    year = int(date[:4])

                    if MIN_YEAR <= year <= MAX_YEAR:
                        writer.writerow({
                            col: row.get(col, "")
                            for col in COLUMNS
                        })
                        total_kept += 1
                        year_counts[year] = year_counts.get(year, 0) + 1
                    else:
                        excluded += 1

            print(
                f"Finished {path.name}. "
                f"Records retained so far: {total_kept:,}",
                flush=True,
            )

except Exception:
    if OUTPUT.exists():
        OUTPUT.unlink()
    raise

print("\nFINAL DATASET SUMMARY")
print("Records read:", f"{total_read:,}")
print("Records retained:", f"{total_kept:,}")
print("Records excluded:", f"{excluded:,}")
print("Output:", OUTPUT)
print("\nRecords by year:")
for year in sorted(year_counts):
    print(f"{year}: {year_counts[year]:,}")
print(
    "\nCompressed size:",
    f"{OUTPUT.stat().st_size / (1024**3):.2f} GiB",
)
