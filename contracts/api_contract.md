# API contract

Base URL (dev): `http://localhost:8000`   Interactive docs: `/docs`
Every sample response is in `contracts/sample_responses/`. The frontend mock mode serves copies of them
from `frontend/public/mock/` (keep the two in sync if a shape changes).

## Person 2: MongoDB-backed (implemented)
| Method | Path | Returns |
|---|---|---|
| GET | `/api/health` | `{"status":"ok"}` |
| GET | `/api/trends/dashboard?window=3&limit=5` | label counts + emerging / declining / established / most_cited lists. `window` is 1, 3 or 5. Sample: `dashboard.json` |
| GET | `/api/cases/{case_id}/citation-trend` | window stats, labels, yearly counts, court-level split. 404 if the case has no citation data. Sample: `case_trend.json` |

## Person 1: MySQL-backed (PROPOSED shapes: Manasi, please confirm or change them)
The frontend is already built against these shapes. If you change a field name, update the sample file
and tell Divyadharshini.

| Method | Path | Query params | Sample file |
|---|---|---|---|
| GET | `/api/cases` | `q` (name or case number, partial match), `page` (from 1), `page_size` | `cases_search.json` |
| GET | `/api/cases/{case_id}` | none | `case_detail.json` |
| GET | `/api/cases/{case_id}/citations` | `page`, `page_size` | `case_citations.json` |
| GET | `/api/landmark-cases` | `limit` | `landmark_cases.json` |

### `GET /api/cases?q=&page=&page_size=`
`{ query, page, page_size, total, results: [ {case_id, case_name, case_number, court_name, judgment_date, total_citations} ] }`
`total_citations` = number of rows in `Citation` where `cited_case_id = case_id`.

### `GET /api/cases/{case_id}`
`{ case_id, case_name, case_number, judgment_date, court_name, court_level, case_type, decision, pdf_url,
   judges: [ {judge_id, name, designation, role_in_case} ],
   statutes: [ {statute_id, act_name, section, description, enactment_year} ] }`
Judges come from `Case_Judge` joined with `Judge`. `pdf_url` can be null. Return 404 for an unknown id.

### `GET /api/cases/{case_id}/citations?page=&page_size=`
"Cited by": cases that cite this one.
`{ case_id, total, page, page_size, results: [ {citing_case_id, case_name, case_number, judgment_date, context_text, page_number} ] }`
`case_name`, `case_number` and `judgment_date` are those of the CITING case. `context_text` and `page_number` may be null.

### `GET /api/landmark-cases?limit=`
Rows of the `Landmark_Cases` view, most cited first.
`{ results: [ {case_id, case_name, case_number, judgment_date, citation_count} ] }`

## Rules
- Dates are `YYYY-MM-DD` strings. Missing values are `null`, never an empty string.
- Errors: 404 for unknown ids, 422 for bad parameters, JSON body `{"detail": "..."}` (FastAPI default).
- Add new routers in `backend/app/routers/` and register them in `backend/app/main.py`.
- Do not reuse `/api/cases/{id}/citation-trend` (MongoDB router owns it).
