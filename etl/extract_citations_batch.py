import io
import re
import tarfile
import requests
import pandas as pd
import pymupdf

from pathlib import Path
from urllib.parse import unquote

PARQUET_PATH = (
    Path.home()
    / ".cache/huggingface/hub/datasets--KanoonGPT--indian-case-laws/"
      "snapshots/42dd6a97345e9811b3d6219f15c250f1ce2bc5af/"
      "structured/v1/year=2026/"
      "indian_case_laws_structured_v1_year=2026.parquet"
)

BATCH_SIZE = 10

SECTIONS_OUTPUT = Path("batch_citation_sections.csv")
CITATIONS_OUTPUT = Path("extracted_citations.csv")

# Common headings that end the citation list in the judgment report.
END_HEADING = re.compile(
    r"^\s*(?:"
    r"List\s+of\s+Acts|"
    r"List\s+of\s+Keywords|"
    r"Books\s+and\s+Periodicals\s+cited|"
    r"Books?\s+Cited|"
    r"Acts?\s+Cited|"
    r"Cases?\s+Referred\s+To|"
    r"Subject\s+Index|"
    r"Case\s+Arising\s+From|"
    r"Appearances\s+for\s+Parties|"
    r"Judgment\s*/\s*Order\s+of\s+the\s+Supreme\s+Court"
    r")\b",
    re.IGNORECASE,
)

# Recognize reporter citations and common case-number identifiers.
IDENTIFIER_PATTERN = re.compile(
    r"\b(?:"
    r"\d{4}\s+SCC\s+OnLine\s+[A-Za-z]+\s+\d+|"
    r"\d{4}\s+SCC\s+OnLine\s+\w+\s+\d+|"
    r"\d{4}\s+INSC\s+\d+|"
    r"\d{4}\s+SCC\s+\d+|"
    r"\d{4}\s+SCR\s+\d+|"
    r"\d{4}\s+S\.C\.R\.\s+\d+|"
    r"AIR\s+\d{4}\s+[A-Z]+\s+\d+|"
    r"SLP\s*\([^)]*\)\s*No\.?\s*[\w/-]+|"
    r"(?:Civil|Criminal)\s+Appeal\s+No\.?\s*[\w/-]+"
    r")\b",
    re.IGNORECASE,
)


def get_pdf_member_name(pdf_url):
    """Read the requested archive member from the URL fragment."""
    if "#member=" not in pdf_url:
        raise ValueError("PDF URL has no #member= filename")

    return unquote(pdf_url.split("#member=", 1)[1].strip())


def find_pdf_member(archive, requested_name):
    """Find a PDF despite archive paths or an optional _EN suffix."""
    members = [m for m in archive.getmembers() if m.isfile()]
    requested_base = Path(requested_name).name

    candidates = [
        requested_base,
        Path(requested_base).stem + "_EN.pdf",
    ]

    # Try exact basename first, then case-insensitive matching.
    by_basename = {}
    for member in members:
        by_basename.setdefault(Path(member.name).name.lower(), member)

    for candidate in candidates:
        member = by_basename.get(candidate.lower())
        if member is not None and member.name.lower().endswith(".pdf"):
            return member

    raise FileNotFoundError(
        f"PDF not found: {requested_name}. "
        f"Archive contains {len(members)} files."
    )


def clean_report_noise(section):
    """Remove common report page headers without altering citation wording."""
    cleaned = []

    for line in section.splitlines():
        value = line.strip()

        if not value:
            continue

        # Page numbers and standard Supreme Court Reports running headers.
        if re.fullmatch(r"\d{1,4}(?:\x08)?", value):
            continue
        if re.fullmatch(r"\[\d{4}\]\s+\d+\s+S\.C\.R\.", value, re.I):
            continue
        if value.lower() == "supreme court reports":
            continue

        cleaned.append(value)

    return " ".join(cleaned)


def extract_citation_section(text):
    """Extract the citation list and explicitly flag uncertain boundaries."""
    start_match = re.search(r"Case\s+Law\s+Cited", text, re.IGNORECASE)

    if not start_match:
        return "", "NO_CASE_LAW_CITED_HEADING"

    start = start_match.end()
    remaining = text[start:]

    # Check each line for a known section heading.
    boundary = None
    for match in re.finditer(r"(?m)^[ \t]*\S[^\n]*$", remaining):
        line = match.group(0).strip()
        if END_HEADING.match(line):
            boundary = match.start()
            break

    if boundary is None:
        # Do not silently pretend that an unknown boundary is correct.
        section = remaining.strip()
        status = "SECTION_EXTRACTED_BOUNDARY_UNCERTAIN"
    else:
        section = remaining[:boundary].strip()
        status = "SECTION_EXTRACTED"

    return clean_report_noise(section), status


def parse_citation_entries(section):
    """
    Split on semicolons, retaining the raw text.
    This creates candidates, not verified database relationships.
    """
    entries = []

    for raw in section.split(";"):
        raw = re.sub(r"\s+", " ", raw).strip(" \t\r\n;")

        if not raw:
            continue

        identifiers = IDENTIFIER_PATTERN.findall(raw)

        entries.append({
            "raw_citation_text": raw,
            "citation_identifiers": " | ".join(identifiers),
            "identifier_count": len(identifiers),
            "mapping_status": (
                "PENDING_REVIEW" if identifiers
                else "NO_IDENTIFIER_PENDING_REVIEW"
            ),
        })

    return entries


def main():
    if not PARQUET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {PARQUET_PATH}")

    df = pd.read_parquet(PARQUET_PATH)

    required = [
        "case_title",
        "neutral_citation",
        "source_pdf_s3_url",
    ]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing dataset columns: {missing}")

    rows = df[
        df["source_pdf_s3_url"].notna()
        & df["case_title"].notna()
        & df["case_title"].astype(str).str.strip().ne("")
    ].head(BATCH_SIZE)

    session = requests.Session()

    # Cache each archive's bytes so shared archives download only once.
    archive_cache = {}
    section_results = []
    citation_results = []

    for index, (_, row) in enumerate(rows.iterrows(), start=1):
        title = str(row["case_title"])
        neutral = str(row["neutral_citation"])
        pdf_url = str(row["source_pdf_s3_url"])
        relative_path = str(row.get("source_relative_path", ""))

        print(f"\n[{index}/{len(rows)}] {title}")

        base_result = {
            "case_title": title,
            "neutral_citation": neutral,
            "source_relative_path": relative_path,
            "source_pdf_s3_url": pdf_url,
            "pdf_bytes": 0,
            "pdf_text_characters": 0,
            "extraction_status": "",
            "case_law_cited_section": "",
        }

        try:
            archive_url = pdf_url.split("#member=", 1)[0]
            member_name = get_pdf_member_name(pdf_url)

            if archive_url not in archive_cache:
                response = session.get(archive_url, timeout=180)
                response.raise_for_status()
                archive_cache[archive_url] = response.content
                print(
                    "Downloaded archive:",
                    len(response.content),
                    "bytes",
                )

            archive_bytes = archive_cache[archive_url]

            with tarfile.open(
                fileobj=io.BytesIO(archive_bytes), mode="r:*"
            ) as archive:
                target = find_pdf_member(archive, member_name)
                pdf_file = archive.extractfile(target)

                if pdf_file is None:
                    raise FileNotFoundError(target.name)

                pdf_bytes = pdf_file.read()

            with pymupdf.open(
                stream=pdf_bytes, filetype="pdf"
            ) as document:
                text = "\n".join(page.get_text() for page in document)

            section, status = extract_citation_section(text)

            base_result.update({
                "pdf_bytes": len(pdf_bytes),
                "pdf_text_characters": len(text),
                "extraction_status": status,
                "case_law_cited_section": section,
            })

            print(
                status,
                "| section characters:",
                len(section),
            )

            if status.startswith("SECTION_EXTRACTED"):
                for entry_number, entry in enumerate(
                    parse_citation_entries(section), start=1
                ):
                    citation_results.append({
                        "source_case_title": title,
                        "source_neutral_citation": neutral,
                        "source_pdf_member": member_name,
                        "entry_number": entry_number,
                        **entry,
                    })

        except Exception as error:
            base_result["extraction_status"] = (
                f"ERROR: {type(error).__name__}: {error}"
            )
            print(base_result["extraction_status"])

        section_results.append(base_result)

        # Save progress after each judgment, so completed work is retained.
        pd.DataFrame(section_results).to_csv(
            SECTIONS_OUTPUT, index=False
        )
        pd.DataFrame(citation_results).to_csv(
            CITATIONS_OUTPUT, index=False
        )

    print("\n========== FINAL SUMMARY ==========")
    print("Judgments attempted:", len(section_results))
    print("\nExtraction statuses:")
    print(
        pd.Series(
            [r["extraction_status"] for r in section_results]
        ).value_counts().to_string()
    )
    print("\nCitation entries extracted:", len(citation_results))
    print("Unique archive downloads:", len(archive_cache))
    print("Sections file:", SECTIONS_OUTPUT.resolve())
    print("Citations file:", CITATIONS_OUTPUT.resolve())

    if citation_results:
        citation_df = pd.DataFrame(citation_results)
        print("\nMapping-status summary:")
        print(citation_df["mapping_status"].value_counts().to_string())


if __name__ == "__main__":
    main()
