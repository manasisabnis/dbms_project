
import csv
from collections import Counter
from pathlib import Path

path = Path("data/processed/cases_clean.csv")

if not path.exists():
    print(f"File not found: {path}")
    raise SystemExit(1)

year_counts = Counter()
seen_ids = set()
duplicate_ids = 0
missing_ids = 0
invalid_dates = 0
total = 0

with path.open("r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)
    print("Columns:", reader.fieldnames)

    for row in reader:
        total += 1

        source_id = (row.get("source_record_id") or "").strip()

        if not source_id:
            missing_ids += 1
        elif source_id in seen_ids:
            duplicate_ids += 1
        else:
            seen_ids.add(source_id)

        date = (row.get("judgment_date") or "").strip()

        if len(date) >= 4 and date[:4].isdigit():
            year_counts[date[:4]] += 1
        else:
            invalid_dates += 1

print("\nTotal records:", total)
print("Records by judgment year:")
for year, count in sorted(year_counts.items()):
    print(f"  {year}: {count}")

print("\nUnique source IDs:", len(seen_ids))
print("Duplicate IDs:", duplicate_ids)
print("Missing IDs:", missing_ids)
print("Invalid or missing dates:", invalid_dates)
