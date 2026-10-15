
import re
import pandas as pd
import mysql.connector
from getpass import getpass
from pathlib import Path

INPUT = Path("extracted_citations.csv")
OUTPUT = Path("citation_match_report.csv")

if not INPUT.exists():
    raise FileNotFoundError(f"Input file not found: {INPUT}")

citations = pd.read_csv(INPUT, dtype=str).fillna("")

def normalize(value):
    value = str(value).lower().strip()

    # Standardize case-name separators.
    value = re.sub(r"\bversus\b|\b(?:v|vs)\.?(?=\s)", " v ", value)

    # Standardize common party-name abbreviations.
    value = re.sub(r"\b(?:and others|& others|ors\.?)\b", " others ", value)
    value = re.sub(r"\b(?:and another|& another|anr\.?)\b", " another ", value)

    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()

def case_name_part(raw):
    raw = str(raw)
    raw = re.split(
        r"\[\s*\d{4}\s*\]|\(\s*\d{4}\s*\)|"
        r"\b\d{4}\s+SCC\b|\b\d{4}\s+INSC\b|"
        r"\bAIR\s+\d{4}\b|\bSLP\s*\(",
        raw,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    return raw.strip(" ,;:-")

print("Connecting to MySQL database: legal_citation_analyzer")
password = getpass("MySQL root password: ")

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password=password,
    database="legal_citation_analyzer",
)

try:
    cursor = connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT case_id, case_name, case_number, judgment_date
        FROM LEGAL_CASE
    """)
    cases = pd.DataFrame(cursor.fetchall())
    cursor.close()
finally:
    connection.close()

# Index cases by standardized name.
case_name_index = {}
for _, case in cases.iterrows():
    name = normalize(case["case_name"])
    if name:
        case_name_index.setdefault(name, []).append(case)

results = []

for _, citation in citations.iterrows():
    raw = str(citation.get("raw_citation_text", ""))
    candidate_name = case_name_part(raw)
    normalized_name = normalize(candidate_name)

    matches = case_name_index.get(normalized_name, [])

    matched_id = ""
    matched_name = ""
    status = "UNMATCHED"
    reason = "No exact normalized case-name match"

    if len(matches) == 1:
        matched_id = int(matches[0]["case_id"])
        matched_name = str(matches[0]["case_name"])
        status = "EXACT_NORMALIZED_NAME"
        reason = "Unique match after standardizing case-name wording"
    elif len(matches) > 1:
        status = "AMBIGUOUS_NAME"
        reason = "Multiple database cases share the normalized name"

    results.append({
        "source_case_title": citation.get("source_case_title", ""),
        "source_neutral_citation": citation.get("source_neutral_citation", ""),
        "raw_citation_text": raw,
        "citation_identifiers": citation.get("citation_identifiers", ""),
        "candidate_case_name": candidate_name,
        "matched_case_id": matched_id,
        "matched_case_name": matched_name,
        "match_status": status,
        "match_reason": reason,
    })

report = pd.DataFrame(results)
report.to_csv(OUTPUT, index=False)

print("\n========== MATCHING SUMMARY ==========")
print("Citation entries checked:", len(report))
print("\nMatch statuses:")
print(report["match_status"].value_counts().to_string())
print("\nReport saved to:", OUTPUT.resolve())
print("No database rows were inserted or modified.")
