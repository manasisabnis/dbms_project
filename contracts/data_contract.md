# Data contract (agreed between Person 1 and Person 2)

Person 1's ETL must produce two JSONL files (one JSON object per line).
Person 2's code loads them into MongoDB. Change this file only by agreement.

## `cases.jsonl`  ->  MongoDB `case_catalog`
| field | type | notes |
|---|---|---|
| case_id | int | SAME id as `Legal_Case.case_id` in MySQL |
| case_name | string | |
| case_number | string or null | e.g. "AIR 1973 SC 1461" |
| judgment_date | "YYYY-MM-DD" | |
| court_name | string | |

## `citation_events.jsonl`  ->  MongoDB `citation_events`
One line per "case A cites case B".
| field | type | notes |
|---|---|---|
| citing_case_id | int | the newer case that contains the citation |
| cited_case_id | int | the precedent being cited |
| citation_date | "YYYY-MM-DD" | = judgment date of the citing case |
| year | int | = year of `citation_date` |
| citing_court_level | string | "Supreme Court", "High Court" or "Lower Courts" |

Rules: both ids must exist in `cases.jsonl`; `citing_case_id != cited_case_id`;
no duplicate (citing, cited) pairs.

## `case_window_stats` (computed by Person 2, never imported)
One document per cited case, rebuilt by `python -m mongo.build_stats`:
`case_id, case_name, case_number, judgment_date, as_of, total_citations,
windows{"1","3","5"}{recent,previous,growth}, trailing_years[4],
labels{"1","3","5"}, label`.

## Labels
`emerging`, `declining`, `established` (UI text: "Influential"), `recent`, `regular`.
