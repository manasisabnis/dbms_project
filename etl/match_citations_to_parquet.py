from pathlib import Path
import re
import pandas as pd
import pyarrow.parquet as pq

ROOT = (
    Path.home()
    / ".cache/huggingface/hub/datasets--KanoonGPT--indian-case-laws/"
      "snapshots/42dd6a97345e9811b3d6219f15c250f1ce2bc5af/"
      "structured/v1"
)
INPUT = Path("extracted_citations.csv")
SUMMARY_OUT = Path("citation_parquet_match_report.csv")
DETAILS_OUT = Path("citation_parquet_match_details.csv")

BATCH_SIZE = 50000
MAX_NAME_SAMPLES = 10
MAX_IDENTIFIER_SAMPLES = 100

REPORTER_PATTERNS = [
    re.compile(
        r"(?:\[\s*)?(?:19|20)\d{2}(?:\s*\])?\s*"
        r"(?:\(?\s*\d{1,3}\s*\)?\s*)?"
        r"(?:SCC\s*OnLine\s*[A-Z.]+\s*\d+|"
        r"INSC\s*\d+|SCC\s*\d+|SCR\s*\d+|S\.C\.R\.\s*\d+)",
        re.I,
    ),
    re.compile(r"\bAIR\s+(?:19|20)\d{2}\s+[A-Z.]+\s+\d+", re.I),
]


def normalize_name(value):
    value = str(value or "").lower().strip()
    value = re.sub(
        r"\bversus\b|\b(?:v|vs)\.?(?=\s)", " v ", value
    )
    value = re.sub(
        r"\b(?:and others|& others|ors\.?)\b", " others ", value
    )
    value = re.sub(
        r"\b(?:and another|& another|anr\.?)\b", " another ", value
    )
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def normalize_name_series(values):
    values = values.fillna("").astype(str).str.lower()
    values = values.str.replace(
        r"\bversus\b|\b(?:v|vs)\.?(?=\s)", " v ", regex=True
    )
    values = values.str.replace(
        r"\b(?:and others|& others|ors\.?)\b",
        " others ", regex=True
    )
    values = values.str.replace(
        r"\b(?:and another|& another|anr\.?)\b",
        " another ", regex=True
    )
    values = values.str.replace(r"[^a-z0-9]+", " ", regex=True)
    values = values.str.replace(r"\s+", " ", regex=True).str.strip()
    return values


def normalize_identifier(value):
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def case_name_part(raw):
    raw = str(raw or "")
    raw = re.split(
        r"\[\s*\d{4}\s*\]|\(\s*\d{4}\s*\)|"
        r"\b\d{4}\s+SCC\b|\b\d{4}\s+INSC\b|"
        r"\bAIR\s+\d{4}\b|\bSLP\s*\(",
        raw,
        maxsplit=1,
        flags=re.I,
    )[0]
    return raw.strip(" ,;:-")


def extract_identifier_keys(raw, existing_identifiers=""):
    values = []
    raw = str(raw or "")

    for pattern in REPORTER_PATTERNS:
        values.extend(m.group(0) for m in pattern.finditer(raw))

    # Also retain the identifiers already recognized by the extractor.
    if existing_identifiers:
        values.extend(
            part.strip()
            for part in str(existing_identifiers).split("|")
            if part.strip()
        )

    return sorted({
        normalize_identifier(value)
        for value in values
        if normalize_identifier(value)
    })


if not INPUT.exists():
    raise FileNotFoundError(f"Missing input file: {INPUT.resolve()}")
if not ROOT.exists():
    raise FileNotFoundError(f"Parquet dataset directory not found: {ROOT}")

citations = pd.read_csv(INPUT, dtype=str).fillna("")
if "raw_citation_text" not in citations.columns:
    raise ValueError("Input lacks raw_citation_text column")

candidates = []
key_to_candidates = {}
name_to_candidates = {}

for idx, citation in citations.iterrows():
    candidate_name = case_name_part(citation["raw_citation_text"])
    normalized_name = normalize_name(candidate_name)
    keys = extract_identifier_keys(
        citation["raw_citation_text"],
        citation.get("citation_identifiers", ""),
    )

    candidate = {
        "source_case_title": citation.get("source_case_title", ""),
        "source_neutral_citation": citation.get(
            "source_neutral_citation", ""
        ),
        "raw_citation_text": citation["raw_citation_text"],
        "citation_identifiers": citation.get("citation_identifiers", ""),
        "candidate_case_name": candidate_name,
        "normalized_candidate_name": normalized_name,
        "identifier_keys": keys,
    }
    candidates.append(candidate)

    if normalized_name:
        name_to_candidates.setdefault(normalized_name, set()).add(idx)

    for key in keys:
        key_to_candidates.setdefault(key, set()).add(idx)

all_keys = sorted(key_to_candidates, key=len, reverse=True)
if all_keys:
    identifier_pattern = re.compile(
        "|".join(re.escape(key) for key in all_keys)
    )
else:
    identifier_pattern = None

identifier_counts = [0] * len(candidates)
name_counts = [0] * len(candidates)
identifier_samples = [0] * len(candidates)
name_samples = [0] * len(candidates)
details = []

files = sorted(ROOT.rglob("*.parquet"))
if not files:
    raise FileNotFoundError(f"No Parquet files found under {ROOT}")

total_rows = 0
files_scanned = 0

print("Citation candidates:", len(candidates))
print("Distinct identifier keys:", len(all_keys))
print("Parquet files to scan:", len(files))
print("Starting read-only scan...", flush=True)

wanted = [
    "id", "case_title", "neutral_citation", "law_report_citation",
    "decision_date", "court_name", "docket_number", "cnr_number",
]

for file_num, path in enumerate(files, start=1):
    parquet = pq.ParquetFile(path)
    available = set(parquet.schema.names)
    columns = [column for column in wanted if column in available]

    if "case_title" not in columns:
        continue

    files_scanned += 1
    file_rows = 0

    for batch in parquet.iter_batches(
        batch_size=BATCH_SIZE, columns=columns
    ):
        df = batch.to_pandas()
        n = len(df)
        file_rows += n
        total_rows += n

        normalized_names = normalize_name_series(df["case_title"])
        name_mask = normalized_names.isin(name_to_candidates)

        citation_blob = pd.Series("", index=df.index, dtype="object")
        for column in ("neutral_citation", "law_report_citation"):
            if column in df.columns:
                values = (
                    df[column].fillna("").astype(str).str.lower()
                    .str.replace(r"[^a-z0-9]+", "", regex=True)
                )
                citation_blob = citation_blob + " " + values

        if identifier_pattern:
            id_mask = citation_blob.str.contains(
                identifier_pattern, na=False
            )
        else:
            id_mask = pd.Series(False, index=df.index)

        relevant_positions = (
            name_mask | id_mask
        ).to_numpy().nonzero()[0]

        for pos in relevant_positions:
            row = df.iloc[pos]
            matched_name = normalize_name(row.get("case_title", ""))
            name_hits = name_to_candidates.get(matched_name, set())

            blob = citation_blob.iloc[pos]
            found_keys = (
                {key for key in all_keys if key in blob}
                if id_mask.iloc[pos] else set()
            )

            identifier_hits = set()
            for key in found_keys:
                identifier_hits.update(key_to_candidates.get(key, set()))

            hit_candidates = name_hits | identifier_hits

            for candidate_idx in hit_candidates:
                name_hit = candidate_idx in name_hits
                id_hit = candidate_idx in identifier_hits

                if name_hit:
                    name_counts[candidate_idx] += 1
                if id_hit:
                    identifier_counts[candidate_idx] += 1

                save_detail = False
                if id_hit and (
                    identifier_samples[candidate_idx]
                    < MAX_IDENTIFIER_SAMPLES
                ):
                    identifier_samples[candidate_idx] += 1
                    save_detail = True
                elif name_hit and (
                    name_samples[candidate_idx] < MAX_NAME_SAMPLES
                ):
                    name_samples[candidate_idx] += 1
                    save_detail = True

                if save_detail:
                    details.append({
                        "candidate_row": candidate_idx + 1,
                        "match_type": (
                            "IDENTIFIER_AND_EXACT_NAME"
                            if id_hit and name_hit
                            else "IDENTIFIER_MATCH"
                            if id_hit
                            else "EXACT_NORMALIZED_NAME"
                        ),
                        "matched_identifier_keys": " | ".join(
                            sorted(
                                key for key in found_keys
                                if candidate_idx in
                                key_to_candidates.get(key, set())
                            )
                        ),
                        "parquet_file": str(path),
                        **{
                            col: row.get(col, "")
                            for col in wanted
                            if col in df.columns
                        },
                    })

    print(
        f"[{file_num}/{len(files)}] {path.parent.name}: "
        f"{file_rows:,} rows scanned",
        flush=True,
    )

summary_rows = []
for idx, candidate in enumerate(candidates):
    id_count = identifier_counts[idx]
    name_count = name_counts[idx]

    if id_count:
        status = (
            "IDENTIFIER_MATCH_FOUND_REVIEW"
            if id_count == 1
            else "IDENTIFIER_MATCH_MULTIPLE_RECORDS_REVIEW"
        )
    elif name_count:
        status = "EXACT_NAME_ONLY_REVIEW"
    else:
        status = "UNMATCHED_IN_PARQUET"

    summary_rows.append({
        "source_case_title": candidate["source_case_title"],
        "source_neutral_citation": candidate["source_neutral_citation"],
        "raw_citation_text": candidate["raw_citation_text"],
        "citation_identifiers": candidate["citation_identifiers"],
        "candidate_case_name": candidate["candidate_case_name"],
        "identifier_keys": " | ".join(candidate["identifier_keys"]),
        "parquet_identifier_match_records": id_count,
        "parquet_exact_name_match_records": name_count,
        "match_status": status,
    })

pd.DataFrame(summary_rows).to_csv(SUMMARY_OUT, index=False)
pd.DataFrame(details).to_csv(DETAILS_OUT, index=False)

report = pd.DataFrame(summary_rows)
print("\n========== PARQUET MATCHING SUMMARY ==========")
print("Parquet files scanned:", files_scanned)
print("Rows scanned:", f"{total_rows:,}")
print("Citation candidates:", len(report))
print("\nMatch statuses:")
print(report["match_status"].value_counts().to_string())
print("\nSummary report:", SUMMARY_OUT.resolve())
print("Match details:", DETAILS_OUT.resolve())
print("No MySQL or MongoDB records were changed.")
