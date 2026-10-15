# Legal Case Citation Evolution Analyzer

A database system that shows how Indian legal precedents **gain or lose influence over time**.
It counts how often each case is cited in rolling time windows (1, 3 and 5 years) and labels
cases as **emerging**, **declining**, **established (influential)**, **recent** or **regular**.

**Team:** M.B. Divyadharshini (PES2UG24CS252) and Manasi Sabnis (PES2UG24CS261), Section E.
**Dataset:** KanoonGPT/indian-case-laws (Hugging Face), judgments 1950 to 2026. We use the Supreme Court cases only.

| Layer | Technology | What it stores / does |
|---|---|---|
| SQL database | MySQL | Courts, cases, judges, statutes, case-to-case citations |
| NoSQL database | MongoDB | One document per citation event + precomputed rolling-window stats |
| Backend | Python FastAPI | JSON API on port 8000 |
| Frontend | Next.js (TypeScript, Tailwind, Recharts) | Dashboard and analysis pages on port 3000 |

---

## 1. Where we are

| Part | Owner | Status |
|---|---|---|
| ER diagram, relational schema, DDL (MySQL) | both | Done (in the project report) |
| Rolling-window counting + classifier (`analysis/`) | Divyadharshini | Done, tested |
| MongoDB import, indexes, aggregation pipelines (`mongo/`) | Divyadharshini | Done, tested on synthetic data |
| API: `/api/trends/dashboard`, `/api/cases/{id}/citation-trend` | Divyadharshini | Done |
| Frontend: dashboard page | Divyadharshini | Done, shows live data |
| Frontend: case analysis page with charts | Divyadharshini | Built, still to be checked on real data |
| Dataset cleaning, citation extraction | Manasi | **To do (this blocks real data)** |
| MySQL load, queries, views, procedures | Manasi | **To do** |
| API: cases, case details, citations, landmark cases | Manasi | **To do** |
| Search and case-details pages | Divyadharshini | Waiting for Manasi's API |
| Integration, tuning, demo, report | both | To do |

Right now everything runs on **synthetic (fake) data** so we could build in parallel.
The real data replaces it as soon as Manasi's files are ready (see section 5).

---

## 2. How the pieces fit together

```
Hugging Face dataset
      |  (Manasi: clean + extract citations)
      v
cases.jsonl + citation_events.jsonl          <- the two files that connect our halves
      |                         |
      | load                    | import_data.py
      v                         v
   MySQL                    MongoDB (citation_events, case_catalog)
 (case info, judges,             |  build_stats.py  (rolling windows + labels)
  statutes, citations)           v
      |                    MongoDB (case_window_stats)
      |                          |
      +-----------+--------------+
                  v
           FastAPI backend  (port 8000)
                  |
                  v
           Next.js frontend (port 3000)
```

- **MySQL answers:** "Tell me about this case" (name, court, judges, statutes, who cites it).
- **MongoDB answers:** "How is this case's citation count changing over time?"

---

## 3. Folder map

```
contracts/    Agreements between us: file formats, API shapes, sample JSON   (shared)
common/       Settings shared by all Python code (.env, DB connection)       (shared)
etl/          Dataset cleaning + citation extraction scripts                 (Manasi)
sql/          MySQL schema, load script, queries, views, procedures          (Manasi)
mongo/        Indexes, import, stats builder, aggregation pipelines,
              synthetic data generator                                       (Divyadharshini)
analysis/     Rolling-window counting and the classifier (pure Python)       (Divyadharshini)
backend/      FastAPI app; routers/trends.py is Divyadharshini's,
              other routers are Manasi's                                     (both)
frontend/     Next.js app                                                    (Divyadharshini)
tests/        pytest tests                                                   (Divyadharshini)
docs/         CODE_WALKTHROUGH.md explains Divyadharshini's code             (shared)
data/         Local data files. NOT in Git (too big). Share files by Drive/USB.
```

Rule of thumb: **only edit files in your own folders.** That avoids merge conflicts.
Shared files (`contracts/`, `backend/app/main.py`, `requirements.txt`, this README): tell the other person before changing them.

---

## 4. Set up on your computer

You need: **Git, Python 3.10+, Node.js (LTS), MongoDB** (Docker or a local install, or a free Atlas cluster).
Manasi also needs **MySQL**.

```bash
git clone https://github.com/manasisabnis/dbms_project.git
cd dbms_project

python -m venv .venv
source .venv/Scripts/activate          # Windows Git Bash. Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env                   # then edit .env (never commit it)
```

Always check your terminal prompt shows `(.venv)` and the right folder before running Python commands.

### Try everything with synthetic data (no real dataset needed)

```bash
docker compose up -d mongo                         # or start your own MongoDB
python -m mongo.synthetic.generate_events          # makes data/synthetic/*.jsonl
python -m analysis.demo_local                      # analysis with no database
python -m mongo.import_data --cases data/synthetic/cases.jsonl --events data/synthetic/citation_events.jsonl --reset
python -m mongo.build_stats
uvicorn backend.app.main:app --reload              # API: http://127.0.0.1:8000/docs
```

In a second terminal:

```bash
cd frontend
npm install
npm run dev                                        # site: http://localhost:3000
```

Run the tests any time with `pytest` (they use a fake MongoDB, so no server is needed).

---

## 5. The integration plan (read this one, Manasi)

The two halves meet at **two files**. Manasi produces them; Divyadharshini loads them into MongoDB.

### 5.1 The two files (JSON Lines: one JSON object per line)

Full rules are in `contracts/data_contract.md`. Short version:

**`cases.jsonl`**
```json
{"case_id": 205, "case_name": "Kesavananda Bharati v. State of Kerala", "case_number": "AIR 1973 SC 1461", "judgment_date": "1973-04-24", "court_name": "Supreme Court of India"}
```

**`citation_events.jsonl`** ("case 310 cites case 205")
```json
{"citing_case_id": 310, "cited_case_id": 205, "citation_date": "2021-08-20", "year": 2021, "citing_court_level": "Supreme Court"}
```

Rules that matter:
1. `case_id` must be **the same number as in MySQL** (`Legal_Case.case_id`). Easiest way: create the ids once during cleaning, load MySQL from the same cleaned data, and write the files from MySQL or from the same dataframe.
2. `citation_date` is the **judgment date of the citing case** (the newer case).
3. Both ids must exist in `cases.jsonl`. No self-citations. No duplicate (citing, cited) pairs.
4. `citing_court_level` is one of `"Supreme Court"`, `"High Court"`, `"Lower Courts"`.
5. Dates are `YYYY-MM-DD`.

Tip: the MySQL `Citation` table already has `citing_case_id`, `cited_case_id` and `citation_date`. Joining it with `Legal_Case` and `Court` gives you everything in `citation_events.jsonl`.

### 5.2 Hand-over steps

1. **Manasi** writes the files into `data/processed/` and shares them (Drive/USB; `data/` is not in Git).
   Start with a **small slice** (3,000 to 5,000 Supreme Court cases) so we can test quickly. Scale up later.
2. **Divyadharshini** loads them:
   ```bash
   python -m mongo.import_data --cases data/processed/cases.jsonl --events data/processed/citation_events.jsonl --reset
   python -m mongo.build_stats
   ```
3. Check the label counts on the dashboard look sensible. If almost everything is "regular" or "emerging",
   tune the numbers in `analysis/config.py` (they are explained in `docs/CODE_WALKTHROUGH.md`).
4. **Manasi** adds her routers (section 6) and merges them. **Divyadharshini** switches the search and case-details
   pages from placeholders to the real endpoints.
5. **Together:** run the end-to-end test below.

### 5.3 End-to-end test (do this together)

- [ ] Type a case name in search, then see a result list from MySQL
- [ ] Click a case, then see court, judges, statutes (MySQL) and trend charts (MongoDB) on one page
- [ ] "Cited by" list matches the citation count
- [ ] Switching 1 / 3 / 5 years changes the numbers and the labels
- [ ] Dashboard lists (emerging, declining, most cited) show real case names
- [ ] A case with no citations shows a friendly message, not a crash

---

## 6. Manasi's tasks (Person 1)

Do them in this order. Task 2 is the hardest and blocks everything else, so start it early.

### Task 1: Prepare the dataset (`etl/`)
- [ ] Download the dataset; keep only Supreme Court rows (check the exact court name in the data). Use a small slice first.
- [ ] Clean case names, dates, case numbers; remove duplicate judgments.
- [ ] Give every case a unique integer `case_id`.
- [ ] Normalise judge names (they are messy, e.g. "MR. JUSTICE S. KUMAR").
- Done when: a clean file/table with `case_id, case_name, case_number, judgment_date, court, decision, judges`.

### Task 2: Extract citations (`etl/`)
- [ ] Download the judgment PDFs (the dataset links to them) and convert them to text.
- [ ] Find citations with patterns such as `AIR 1973 SC 1461` and `(1978) 1 SCC 248`.
- [ ] Match each citation string to a `case_id` in your cleaned cases. Keep only matches where both cases exist.
- [ ] Record `citing_case_id`, `cited_case_id`, `citation_date`, `context_text`, `page_number`.
- Done when: you can print "case A cites case B" for a few real, known examples.
- Heads up: older judgments may be scanned images and need OCR. Expect fewer citations for old years.

### Task 3: MySQL (`sql/`)
- [ ] Put the DDL from our report into `sql/schema.sql` (Court, Legal_Case, Judge, Case_Judge, Statute, Citation, indexes, `Landmark_Cases` view). Add `established_year` to Court if we want it.
- [ ] Write a load script that inserts the cleaned data.
- [ ] Queries in `sql/queries.sql`: most cited cases, cases citing a given case, citation counts per year, cases in a date range, cases with several judges, cases referring to a statute.
- [ ] Course extras: a stored procedure (e.g. `get_trend(case_id, window_years)`), a trigger, more views.
- Done when: `Landmark_Cases` returns rows and the queries run on real data.

### Task 4: Backend endpoints (`backend/app/routers/`)
Create `backend/app/routers/cases.py` and register it in `backend/app/main.py`:
```python
from backend.app.routers import cases
app.include_router(cases.router, prefix="/api")
```
Endpoints to build (add MySQL connection settings to `common/settings.py` and `.env.example`):

| Method | Path | Returns |
|---|---|---|
| GET | `/api/cases?q=...&page=1` | Search results: case_id, case_name, case_number, court, judgment_date, total_citations |
| GET | `/api/cases/{case_id}` | Case info: court, judges, decision, statutes |
| GET | `/api/cases/{case_id}/citations` | "Cited by" list from the `Citation` table |
| GET | `/api/landmark-cases` | Rows from the `Landmark_Cases` view |

**Before coding each endpoint:** write the exact JSON shape into `contracts/api_contract.md` and a sample file in
`contracts/sample_responses/`, then tell Divyadharshini. She builds the page from the sample while you build the endpoint.
Look at `backend/app/routers/trends.py` and `backend/app/schemas.py` for a working example.
Do **not** use `/api/cases/{id}/citation-trend`; that one is already taken by the MongoDB router.

---

## 7. Divyadharshini's tasks (Person 2)

- [ ] Open `/cases/1530` and check the three charts render (line, bars, court donut)
- [ ] Build the **search results page** (`/search?q=`) once `/api/cases?q=` exists
- [ ] Build the **case details page** (overview, judges, statutes, cited by) using Manasi's endpoints
- [ ] Add "landmark cases" to the dashboard from `/api/landmark-cases`
- [ ] Load real data, check label counts, tune `analysis/config.py`
- [ ] Document the MongoDB design and queries (collections, indexes, aggregation pipelines) for the report
- [ ] Loading, empty and error states on every page; basic mobile layout
- [ ] Demo script and screenshots for the report

---

## 8. API reference

Interactive docs while the backend runs: http://127.0.0.1:8000/docs

| Method | Path | Owner | Status |
|---|---|---|---|
| GET | `/api/health` | Divyadharshini | Done |
| GET | `/api/trends/dashboard?window=3&limit=5` | Divyadharshini | Done |
| GET | `/api/cases/{id}/citation-trend` | Divyadharshini | Done |
| GET | `/api/cases?q=` | Manasi | To do |
| GET | `/api/cases/{id}` | Manasi | To do |
| GET | `/api/cases/{id}/citations` | Manasi | To do |
| GET | `/api/landmark-cases` | Manasi | To do |

Sample responses for the finished endpoints are in `contracts/sample_responses/`.

---

## 9. Git workflow

- `main` always works. Never commit directly to it after the first setup.
- One branch per piece of work: `feature/<topic>` (e.g. `feature/etl-citations`, `feature/search-page`).
- Small commits with clear messages (`feat: ...`, `fix: ...`, `docs: ...`).
- Open a pull request on GitHub, let the other person look, then merge.
- Every morning: `git checkout main && git pull origin main`, then `git checkout feature/<topic> && git merge main`.
- Never commit `.env`, anything in `data/`, `node_modules/` or `.next/`.
- Before `git add .`, run `git status` and read the list.

Always work in **one folder per project** and check the terminal prompt shows the repo folder and the right branch.

---

## 10. Troubleshooting

| Problem | Fix |
|---|---|
| `No module named 'pymongo'` | Python is not using the venv. Run `source .venv/Scripts/activate` from the repo root, then start uvicorn again. |
| Dashboard says "NetworkError" | Backend is down, MongoDB is down, or CORS. Open http://127.0.0.1:8000/api/trends/dashboard?window=3 and check what it says. |
| API returns Internal Server Error | Look at the uvicorn terminal. Usually MongoDB is not running. |
| Frontend starts on port 3001 | Something still uses 3000. Stop the old `npm run dev` (or `cmd //c "netstat -ano \| findstr :3000"` then `taskkill /PID <id> /F`). |
| `git push` says "No configured push destination" | You are in a folder that is not the cloned repo. `cd` into the repo folder. |
| Empty folders missing on GitHub | Git ignores empty folders. Put a `.gitkeep` file in them. |
| Hydration warning mentioning `data-gr-...` | Grammarly extension. Harmless; `suppressHydrationWarning` is already set on `<body>`. |
| Tests fail on `import` | Run `pytest` from the repo root with the venv active. |

---

## 11. More documentation

- `contracts/data_contract.md`: exact file formats and MongoDB collections
- `contracts/api_contract.md`: API agreements
- `docs/CODE_WALKTHROUGH.md`: line-by-line explanation of the analysis, MongoDB and API code
