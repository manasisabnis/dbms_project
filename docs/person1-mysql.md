# Person 1: MySQL Schema and Citation Analytics

## Overview

This part of the project covers the relational database schema,
case data preparation, citation extraction, citation matching,
and SQL analytics for the Legal Case Citation Evolution Analyzer.

## Files

- `sql/00_schema.sql`: Creates the MySQL database and relational tables.
- `sql/01_most_cited_cases.sql`: Finds the most-cited cases.
- `sql/02_citation_activity_by_year.sql`: Analyses citation activity by year.
- `sql/03_emerging_declining_precedents.sql`: Analyses changes in precedent citations.
- `sql/04_citations_by_court.sql`: Analyses citations by court.

## Database Setup

Install MySQL and ensure the MySQL server is running.

From the repository root, execute:

    mysql -u root -p < sql/00_schema.sql

Enter your local MySQL password when prompted.

The schema creates these tables:

- `COURT`
- `LEGAL_CASE`
- `JUDGE`
- `CASE_JUDGE`
- `STATUTE`
- `CITATION`

## Analytics Queries

Execute an individual query using:

    mysql -u root -p legal_citation_analyzer < sql/01_most_cited_cases.sql

Replace the SQL filename to run another query.

## Data and Citation Matching

The original dataset and intermediate extraction files are maintained
locally and must not be committed to Git if they are too large or
contain data that should remain outside the repository.

Citation extraction and matching are still subject to validation.
Candidate name matches should be reviewed before being inserted into
`CITATION`; a text match alone does not establish that two records
refer to the same judgment.

## Current Limitation

The analytics queries depend on valid records in `CITATION`.
If the table is empty, citation-based analytics will return no useful
citation results until verified citation relationships are loaded.

## Configuration and Team Workflow

Keep database credentials in local environment variables or a
`.env` file that is excluded from Git. Never commit passwords.

Coordinate schema or query changes with the team before merging them
into the shared branch.
