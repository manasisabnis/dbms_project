"""Integrate a small real-citation sample into MySQL and export Mongo JSONL.

Uses existing extraction/matching outputs only; does not rescan the full dataset.
Only citation candidates with exactly one reporter-identifier match are emitted.
Those edges are explicitly marked as identifier-supported, not manually audited.
"""
from __future__ import annotations

import json
import os
import re
from datetime import date, datetime
from getpass import getpass
from pathlib import Path

import mysql.connector
import pandas as pd

ROOT = Path(__file__).resolve().parents[1] if Path(__file__).resolve().parent.name == "etl" else Path.cwd()
PARQUET_PATH = (
    Path.home()
    / ".cache/huggingface/hub/datasets--KanoonGPT--indian-case-laws/"
      "snapshots/42dd6a97345e9811b3d6219f15c250f1ce2bc5af/"
      "structured/v1/year=2026/indian_case_laws_structured_v1_year=2026.parquet"
)
BATCH_CSV = ROOT / "batch_citation_sections.csv"
CITATIONS_CSV = ROOT / "extracted_citations.csv"
REPORT_CSV = ROOT / "citation_parquet_match_report.csv"
DETAILS_CSV = ROOT / "citation_parquet_match_details.csv"
PROCESSED = ROOT / "data" / "processed"
CASES_OUT = PROCESSED / "cases.jsonl"
EVENTS_OUT = PROCESSED / "citation_events.jsonl"


def normalize_name(value) -> str:
    value = str(value or "").lower().strip()
    value = re.sub(r"\bversus\b|\b(?:v|vs)\.?(?=\s)", " v ", value)
    value = re.sub(r"\b(?:and others|& others|ors\.?)\b", " others ", value)
    value = re.sub(r"\b(?:and another|& another|anr\.?)\b", " another ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def normalize_token(value) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def date_string(value) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, (datetime, date)):
        return value.date().isoformat() if isinstance(value, datetime) else value.isoformat()
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return ""
    return parsed.date().isoformat()


def record_key(name, judgment_date, court_name):
    return (normalize_name(name), date_string(judgment_date), normalize_name(court_name))


def court_level(court_name) -> str:
    value = str(court_name or "").lower()
    if "supreme court" in value:
        return "Supreme Court"
    if "high court" in value:
        return "High Court"
    return "Lower Courts"


def read_source_records():
    batch = pd.read_csv(BATCH_CSV, dtype=str).fillna("")
    if "neutral_citation" not in batch.columns:
        raise ValueError("batch_citation_sections.csv has no neutral_citation column")

    parquet_cols = ["case_title", "neutral_citation", "decision_date", "court_name", "docket_number"]
    frame = pd.read_parquet(PARQUET_PATH, columns=parquet_cols).fillna("")
    frame["_neutral_key"] = frame["neutral_citation"].map(normalize_token)

    source_records = []
    source_by_neutral = {}
    for _, source in batch.iterrows():
        neutral = str(source.get("neutral_citation", "")).strip()
        neutral_key = normalize_token(neutral)
        rows = frame[frame["_neutral_key"] == neutral_key] if neutral_key else frame.iloc[0:0]
        if len(rows) != 1:
            title = source.get("case_title", "")
            # A unique title match is an acceptable fallback only within this 2026 file.
            title_key = normalize_name(title)
            fallback = frame[frame["case_title"].map(normalize_name) == title_key] if title_key else frame.iloc[0:0]
            if len(fallback) != 1:
                raise ValueError(
                    f"Could not uniquely identify source judgment {title!r} / {neutral!r} in the 2026 Parquet file."
                )
            row = fallback.iloc[0]
        else:
            row = rows.iloc[0]

        rec = {
            "case_name": str(row["case_title"]).strip(),
            "judgment_date": date_string(row["decision_date"]),
            "court_name": str(row["court_name"]).strip(),
            "case_number": str(row.get("docket_number", "")).strip() or None,
            "neutral_citation": neutral,
            "role": "source",
        }
        if not rec["case_name"] or not rec["judgment_date"] or not rec["court_name"]:
            raise ValueError(f"Source judgment lacks title/date/court: {rec}")
        key = record_key(rec["case_name"], rec["judgment_date"], rec["court_name"])
        rec["key"] = key
        source_records.append(rec)
        if neutral_key:
            source_by_neutral[neutral_key] = rec
    return source_records, source_by_neutral


def read_unique_targets(citations_df):
    report = pd.read_csv(REPORT_CSV, dtype=str).fillna("")
    details = pd.read_csv(DETAILS_CSV, dtype=str).fillna("")
    report["candidate_row"] = range(1, len(report) + 1)
    counts = pd.to_numeric(report["parquet_identifier_match_records"], errors="coerce").fillna(0)
    singles = report[counts == 1].copy()

    if "candidate_row" not in details.columns:
        raise ValueError("citation_parquet_match_details.csv lacks candidate_row")
    details = details[details["match_type"].astype(str).str.contains("IDENTIFIER", na=False)].copy()
    details = details.drop_duplicates(subset=["candidate_row", "case_title", "decision_date", "court_name"])

    targets_by_row = {}
    for _, row in singles.iterrows():
        candidate_row = int(row["candidate_row"])
        hits = details[pd.to_numeric(details["candidate_row"], errors="coerce") == candidate_row]
        if len(hits) != 1:
            continue
        hit = hits.iloc[0]
        name = str(hit.get("case_title", "")).strip()
        judgment_date = date_string(hit.get("decision_date", ""))
        court_name = str(hit.get("court_name", "")).strip()
        if not name or not judgment_date or not court_name:
            continue
        source_citation = citations_df.iloc[candidate_row - 1]
        rec = {
            "case_name": name,
            "judgment_date": judgment_date,
            "court_name": court_name,
            "case_number": str(hit.get("docket_number", "")).strip() or None,
            "neutral_citation": str(hit.get("neutral_citation", "")).strip(),
            "role": "target",
            "candidate_row": candidate_row,
            "raw_citation_text": str(source_citation.get("raw_citation_text", "")),
            "citation_identifiers": str(source_citation.get("citation_identifiers", "")),
            "match_basis": "unique_reporter_identifier_match; not manually audited",
            "key": record_key(name, judgment_date, court_name),
        }
        targets_by_row[candidate_row] = rec
    return targets_by_row


def ensure_court(cursor, court_cache, court_name):
    key = normalize_name(court_name)
    if key in court_cache:
        return court_cache[key]
    level = court_level(court_name)
    # Existing schema has court_name, location, court_level.
    cursor.execute(
        "INSERT INTO COURT (court_name, location, court_level) VALUES (%s, %s, %s)",
        (court_name, "", level),
    )
    court_id = cursor.lastrowid
    court_cache[key] = court_id
    return court_id


def export_catalog(cursor):
    cursor.execute("""
        SELECT lc.case_id, lc.case_name, lc.case_number, lc.judgment_date, c.court_name
        FROM LEGAL_CASE lc
        LEFT JOIN COURT c ON c.court_id = lc.court_id
        ORDER BY lc.case_id
    """)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    tmp = CASES_OUT.with_suffix(".jsonl.tmp")
    exported = skipped = 0
    with tmp.open("w", encoding="utf-8") as f:
        for row in cursor.fetchall():
            case_id, name, case_number, judgment_date, court_name = row
            d = date_string(judgment_date)
            if not name or not d:
                skipped += 1
                continue
            doc = {
                "case_id": int(case_id),
                "case_name": str(name),
                "case_number": case_number,
                "judgment_date": d,
                "court_name": str(court_name or ""),
            }
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
            exported += 1
    tmp.replace(CASES_OUT)
    return exported, skipped


def main():
    for path in (PARQUET_PATH, BATCH_CSV, CITATIONS_CSV, REPORT_CSV, DETAILS_CSV):
        if not path.exists():
            raise FileNotFoundError(f"Required input not found: {path}")

    citations = pd.read_csv(CITATIONS_CSV, dtype=str).fillna("")
    source_records, source_by_neutral = read_source_records()
    target_by_row = read_unique_targets(citations)

    # Preserve only source records and the target records backed by exactly one identifier match.
    records_by_key = {}
    for rec in source_records:
        records_by_key.setdefault(rec["key"], rec)
    for rec in target_by_row.values():
        records_by_key.setdefault(rec["key"], rec)

    mysql_password = os.getenv("MYSQL_PASSWORD") or getpass("MySQL root password: ")
    connection = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user=os.getenv("MYSQL_USER", "root"),
        password=mysql_password,
        database=os.getenv("MYSQL_DATABASE", "legal_citation_analyzer"),
    )

    case_id_by_key = {}
    inserted_cases = 0
    inserted_courts = 0
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT court_id, court_name FROM COURT")
        court_cache = {}
        for court_id, court_name in cursor.fetchall():
            court_cache.setdefault(normalize_name(court_name), int(court_id))

        # Insert only missing court rows.
        for rec in records_by_key.values():
            ck = normalize_name(rec["court_name"])
            if ck not in court_cache:
                before = len(court_cache)
                ensure_court(cursor, court_cache, rec["court_name"])
                inserted_courts += len(court_cache) - before

        cursor.execute("""
            SELECT lc.case_id, lc.case_name, lc.case_number, lc.judgment_date,
                   lc.court_id, c.court_name
            FROM LEGAL_CASE lc
            LEFT JOIN COURT c ON c.court_id = lc.court_id
        """)
        existing = {}
        for case_id, case_name, case_number, judgment_date, court_id, court_name in cursor.fetchall():
            k = record_key(case_name, judgment_date, court_name or "")
            existing.setdefault(k, int(case_id))

        for key, rec in records_by_key.items():
            if key in existing:
                case_id_by_key[key] = existing[key]
                continue
            court_id = court_cache[normalize_name(rec["court_name"])]
            case_number = rec.get("case_number")
            if case_number:
                case_number = str(case_number)[:255]
            cursor.execute(
                """INSERT INTO LEGAL_CASE (case_name, case_number, judgment_date, court_id)
                   VALUES (%s, %s, %s, %s)""",
                (rec["case_name"], case_number or None, rec["judgment_date"], court_id),
            )
            case_id = int(cursor.lastrowid)
            case_id_by_key[key] = case_id
            inserted_cases += 1
            existing[key] = case_id

        connection.commit()

        # Resolve every source record through the same stable case key.
        source_id_by_neutral = {}
        for neutral_key, rec in source_by_neutral.items():
            source_id_by_neutral[neutral_key] = case_id_by_key[rec["key"]]

        events = []
        seen_pairs = set()
        skipped_edges = 0
        for candidate_row, target in sorted(target_by_row.items()):
            citation = citations.iloc[candidate_row - 1]
            source_neutral = normalize_token(citation.get("source_neutral_citation", ""))
            if source_neutral not in source_id_by_neutral:
                skipped_edges += 1
                continue
            citing_id = source_id_by_neutral[source_neutral]
            cited_id = case_id_by_key[target["key"]]
            if citing_id == cited_id or (citing_id, cited_id) in seen_pairs:
                skipped_edges += 1
                continue

            source_rec = source_by_neutral[source_neutral]
            citation_date = source_rec["judgment_date"]
            events.append({
                "citing_case_id": citing_id,
                "cited_case_id": cited_id,
                "citation_date": citation_date,
                "year": int(citation_date[:4]),
                "citing_court_level": court_level(source_rec["court_name"]),
                "raw_citation_text": target["raw_citation_text"],
                "citation_identifiers": target["citation_identifiers"],
                "match_basis": target["match_basis"],
            })
            seen_pairs.add((citing_id, cited_id))

        exported, skipped_catalog = export_catalog(cursor)
        PROCESSED.mkdir(parents=True, exist_ok=True)
        event_tmp = EVENTS_OUT.with_suffix(".jsonl.tmp")
        with event_tmp.open("w", encoding="utf-8") as f:
            for event in events:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        event_tmp.replace(EVENTS_OUT)
        cursor.close()

        print("\n===== REAL CITATION SAMPLE PREPARED =====")
        print("Source judgments identified:", len(source_records))
        print("Unique identifier-supported target candidates:", len(target_by_row))
        print("New court rows inserted:", inserted_courts)
        print("New LEGAL_CASE rows inserted:", inserted_cases)
        print("Distinct citation events written:", len(events))
        print("Edges skipped (unresolved source, self-edge, or duplicate):", skipped_edges)
        print("Case catalog exported:", exported)
        print("Catalog rows skipped for missing name/date:", skipped_catalog)
        print("Cases JSONL:", CASES_OUT)
        print("Events JSONL:", EVENTS_OUT)
        print("Note: event edges have a unique identifier match but have not been manually audited.")
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    main()
