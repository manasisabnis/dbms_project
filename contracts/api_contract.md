# API contract

Base URL (dev): `http://localhost:8000`   Interactive docs: `/docs`

## Person 2 (MongoDB-backed, already implemented)
| Method | Path | Returns |
|---|---|---|
| GET | `/api/health` | `{"status":"ok"}` |
| GET | `/api/trends/dashboard?window=3&limit=5` | label counts + emerging / declining / established / most_cited lists. `window` is 1, 3 or 5. See `sample_responses/dashboard.json` |
| GET | `/api/cases/{case_id}/citation-trend` | window stats, labels, yearly counts, court-level split for one case. 404 if the case has no citation data. See `sample_responses/case_trend.json` |

## Person 1 (MySQL-backed, to be agreed and added)
| Method | Path | Notes |
|---|---|---|
| GET | `/api/cases?q=&page=` | search results: case_id, case_name, case_number, court, judgment_date, total_citations |
| GET | `/api/cases/{case_id}` | case info: court, judges, statutes, decision |
| GET | `/api/cases/{case_id}/citations` | "Cited by" list from the MySQL `Citation` table |
| GET | `/api/landmark-cases` | rows from the `Landmark_Cases` view |

Person 1: please add the exact JSON shape of each endpoint here (and a sample file in
`sample_responses/`) BEFORE building the frontend pages that use them.
