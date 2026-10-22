
import re
from pathlib import Path

text = Path("sample_judgment.txt").read_text(encoding="utf-8")

patterns = [
    # Example: (2024) 12 SCC 660
    r"\(\d{4}\)\s*\d+\s*SCC\s*\d+",

    # Example: 2025 SCC OnLine SC 1291
    r"\b\d{4}\s+SCC\s+OnLine\s+SC\s+\d+\b",

    # Example: [2021] 1 SCR 443
    r"\[\d{4}\]\s*\d+\s*SCR\s*\d+",
]

matches = []

for pattern in patterns:
    matches.extend(
        match.group(0)
        for match in re.finditer(pattern, text, re.IGNORECASE)
    )

# Normalize whitespace and remove duplicates while preserving order.
unique_matches = list(dict.fromkeys(
    re.sub(r"\s+", " ", item).strip()
    for item in matches
))

print("Total raw matches:", len(matches))
print("Unique citation identifiers:", len(unique_matches))

for i, citation in enumerate(unique_matches, start=1):
    print(f"{i}. {citation}")

Path("citation_candidates.txt").write_text(
    "\n".join(unique_matches),
    encoding="utf-8"
)

print("\nSaved to citation_candidates.txt")
