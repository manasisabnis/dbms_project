# ETL and Data Validation

Run commands from the repository root with the project virtual environment
activated:

    source .venv/bin/activate

The large source datasets and intermediate CSV files are intentionally not
stored in Git. Place the required files under data/processed or configure
the relevant script paths before running a script.

## Scripts

- prepare_final_dataset.py
  Combines the configured CSV inputs into
  data/processed/cases_final_1970_2026.csv.gz.
  Requires the input CSVs listed in the script.

- verify_final_dataset.py
  Checks the prepared compressed dataset. Run after preparation.

- audit_clean_csv.py
  Audits data/processed/cases_clean.csv. Requires that file to exist.

- extract_citations_batch.py
  Extracts citation candidates from the configured judgment archive.
  Requires the source archive and its configured path.

- extract_citation_candidates.py
  A small exploratory script that currently expects sample_judgment.txt
  in the working directory.

- import_recent_cases.py
  Imports the configured recent-cases CSV into MySQL. Review the target
  database and CSV before running it.

- match_citations_to_mysql.py
  Reads extracted_citations.csv and writes citation_match_report.csv.
  It does not insert citation rows into MySQL.

## MySQL configuration

The case importer and citation matcher currently contain connection
settings in their source code. Review those settings before running
them, and never commit passwords or other credentials.

## Citation validation

A normalized case-name match is a candidate, not proof that two records
refer to the same judgment. Review citation identifiers, case details,
and source context before accepting a relationship.

Do not populate CITATION from unreviewed matches. Keep unmatched and
ambiguous candidates in the report for manual review.

## Current repository limitation

The repository's data directories contain only .gitkeep placeholders.
The actual datasets must be supplied locally before the ETL scripts can
be run end to end. Do not commit large source datasets or intermediate
files.
