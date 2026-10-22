"""Extract a small real citation sample from several judgment years.

Run from repository root as:
    python -m etl.extract_citations_multiyear

This script reads only selected metadata columns from the local Parquet files,
then downloads the archives for a small sample of PDFs. It writes the same
batch_citation_sections.csv and extracted_citations.csv filenames used by the
existing matching pipeline, adding source judgment date/court fields needed to
build correctly dated citation events.
"""
from __future__ import annotations

import io
import os
import tarfile
from collections import defaultdict
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
import requests
import pymupdf

from etl.extract_citations_batch import (
    extract_citation_section,
    find_pdf_member,
    get_pdf_member_name,
    parse_citation_entries,
)

ROOT = Path(__file__).resolve().parents[1]
PARQUET_ROOT = (
    Path.home()
    / ".cache/huggingface/hub/datasets--KanoonGPT--indian-case-laws/"
      "snapshots/42dd6a97345e9811b3d6219f15c250f1ce2bc5af/"
      "structured/v1"
)
YEARS = [int(v.strip()) for v in os.getenv("EXTRACTION_YEARS", "2018,2019,2020,2021,2022,2023,2024,2025,2026").split(",") if v.strip()]
PER_YEAR = int(os.getenv("EXTRACTION_PER_YEAR", "10"))
OUTPUT_SUFFIX = os.getenv("EXTRACTION_SUFFIX", "")
BATCH_CSV = ROOT / f"batch_citation_sections{OUTPUT_SUFFIX}.csv"
CITATIONS_CSV = ROOT / f"extracted_citations{OUTPUT_SUFFIX}.csv"

COLUMNS = [
    "id", "case_title", "neutral_citation", "source_pdf_s3_url",
    "source_relative_path", "decision_date", "court_name", "docket_number",
]


def text(value) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def date_text(value) -> str:
    value = text(value)
    if not value:
        return ""
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return ""
    return parsed.date().isoformat()


def sample_year(path: Path, year: int, count: int) -> list[dict]:
    parquet = pq.ParquetFile(path)
    available = set(parquet.schema.names)
    cols = [col for col in COLUMNS if col in available]
    required = {"case_title", "source_pdf_s3_url", "decision_date"}
    if not required.issubset(set(cols)):
        raise ValueError(f"{path} missing required columns {sorted(required - set(cols))}")

    chosen: list[dict] = []
    seen_ids: set[str] = set()
    # Stream batches so a 1M+ row year's Parquet file isn't loaded all at once.
    for batch in parquet.iter_batches(batch_size=50_000, columns=cols):
        frame = batch.to_pandas()
        for _, row in frame.iterrows():
            title = text(row.get("case_title"))
            url = text(row.get("source_pdf_s3_url"))
            decision_date = date_text(row.get("decision_date"))
            if not title or not url or "#member=" not in url or not decision_date:
                continue
            # Use the actual judgment year, not just the Parquet partition label.
            if not decision_date.startswith(f"{year}-"):
                continue
            source_id = text(row.get("id"))
            dedupe_key = source_id or url
            if dedupe_key in seen_ids:
                continue
            seen_ids.add(dedupe_key)
            chosen.append({
                "source_parquet_id": source_id,
                "source_year_partition": year,
                "case_title": title,
                "neutral_citation": text(row.get("neutral_citation")),
                "source_pdf_s3_url": url,
                "source_relative_path": text(row.get("source_relative_path")),
                "decision_date": decision_date,
                "court_name": text(row.get("court_name")),
                "docket_number": text(row.get("docket_number")),
            })
            if len(chosen) >= count:
                return chosen
    return chosen


def main() -> None:
    if not PARQUET_ROOT.exists():
        raise FileNotFoundError(f"Dataset root not found: {PARQUET_ROOT}")

    selected: list[dict] = []
    print(f"Selecting up to {PER_YEAR} judgments per year: {YEARS}")
    for year in YEARS:
        path = PARQUET_ROOT / f"year={year}" / f"indian_case_laws_structured_v1_year={year}.parquet"
        if not path.exists():
            print(f"[WARN] No local Parquet file for {year}: {path}")
            continue
        rows = sample_year(path, year, PER_YEAR)
        selected.extend(rows)
        print(f"year={year}: selected {len(rows)} judgments")
        for rec in rows:
            print(f"  {rec['decision_date']} | {rec['case_title'][:90]}")

    if not selected:
        raise RuntimeError("No source judgments selected; no outputs were changed.")

    # Group by archive so each archive is downloaded only once, then released.
    by_archive: dict[str, list[dict]] = defaultdict(list)
    for rec in selected:
        archive_url = rec["source_pdf_s3_url"].split("#member=", 1)[0]
        by_archive[archive_url].append(rec)

    session = requests.Session()
    section_results: list[dict] = []
    citation_results: list[dict] = []

    for archive_num, (archive_url, records) in enumerate(by_archive.items(), start=1):
        print(f"\nArchive {archive_num}/{len(by_archive)}: {len(records)} selected PDF(s)")
        try:
            response = session.get(archive_url, timeout=180)
            response.raise_for_status()
            archive_bytes = response.content
        except Exception as exc:
            for rec in records:
                section_results.append({
                    **rec,
                    "pdf_bytes": 0,
                    "pdf_text_characters": 0,
                    "extraction_status": f"ERROR: archive download: {type(exc).__name__}: {exc}",
                    "case_law_cited_section": "",
                    "source_pdf_member": get_pdf_member_name(rec["source_pdf_s3_url"]),
                })
            pd.DataFrame(section_results).to_csv(BATCH_CSV, index=False)
            pd.DataFrame(citation_results).to_csv(CITATIONS_CSV, index=False)
            continue

        with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:*") as archive:
            for rec in records:
                member_name = get_pdf_member_name(rec["source_pdf_s3_url"])
                status = ""
                section = ""
                pdf_bytes = 0
                text_length = 0
                try:
                    member = find_pdf_member(archive, member_name)
                    extracted = archive.extractfile(member)
                    if extracted is None:
                        raise FileNotFoundError(member_name)
                    pdf = extracted.read()
                    pdf_bytes = len(pdf)
                    with pymupdf.open(stream=pdf, filetype="pdf") as document:
                        judgment_text = "\n".join(page.get_text() for page in document)
                    text_length = len(judgment_text)
                    section, status = extract_citation_section(judgment_text)
                    print(f"{rec['decision_date']} | {rec['case_title'][:65]} | {status} | section chars={len(section)}")
                    if status == "SECTION_EXTRACTED":
                        for entry_number, entry in enumerate(parse_citation_entries(section), start=1):
                            citation_results.append({
                                "source_case_title": rec["case_title"],
                                "source_neutral_citation": rec["neutral_citation"],
                                "source_judgment_date": rec["decision_date"],
                                "source_court_name": rec["court_name"],
                                "source_case_number": rec["docket_number"],
                                "source_parquet_id": rec["source_parquet_id"],
                                "source_year": int(rec["decision_date"][:4]),
                                "source_pdf_member": member_name,
                                "entry_number": entry_number,
                                **entry,
                            })
                except Exception as exc:
                    status = f"ERROR: {type(exc).__name__}: {exc}"
                    print(f"{rec['case_title'][:65]} | {status}")

                section_results.append({
                    **rec,
                    "source_pdf_member": member_name,
                    "pdf_bytes": pdf_bytes,
                    "pdf_text_characters": text_length,
                    "extraction_status": status,
                    "case_law_cited_section": section,
                })
                # Preserve progress after every judgment.
                pd.DataFrame(section_results).to_csv(BATCH_CSV, index=False)
                pd.DataFrame(citation_results).to_csv(CITATIONS_CSV, index=False)

        del archive_bytes

    sections = pd.DataFrame(section_results)
    citations = pd.DataFrame(citation_results)
    print("\n========== MULTI-YEAR EXTRACTION SUMMARY ==========")
    print("Judgments attempted:", len(sections))
    if not sections.empty:
        print("\nJudgments by source year:")
        print(sections.assign(source_year=sections["decision_date"].str[:4]).groupby(["source_year", "extraction_status"]).size().to_string())
    print("Citation entries extracted:", len(citations))
    if not citations.empty:
        print("Citation entries by source year:")
        print(citations.groupby("source_year").size().to_string())
    print("Sections file:", BATCH_CSV)
    print("Citations file:", CITATIONS_CSV)
    print("Note: extracted entries are candidates, not verified citation edges.")


if __name__ == "__main__":
    main()
