# Legal Case Citation Evolution Analyzer

DBMS mini-project. Analyses how Indian legal precedents gain or lose influence over time.
MySQL stores structured legal data; MongoDB stores citation events used for rolling-window analysis.

| | Person 1 | Person 2 |
|---|---|---|
| Owns | `etl/`, `sql/`, MySQL routers in `backend/` | `mongo/`, `analysis/`, `tests/`, `backend/app/routers/trends.py`, `frontend/` |

Shared: `contracts/`, `docs/`, `common/`.

## Folder map
```
contracts/   data + API agreements, sample JSON responses (frontend fixtures)
common/      settings shared by all Python code (.env loading, DB connection)
etl/         [Person 1] dataset cleaning + citation extraction
sql/         [Person 1] MySQL schema, queries, views, procedures
mongo/       [Person 2] indexes, import, stats builder, aggregation pipelines, synthetic data
analysis/    [Person 2] rolling-window counting + precedent classifier (pure Python)
backend/     FastAPI app (routers/trends.py = Person 2, other routers = Person 1)
frontend/    [Person 2] Next.js app
tests/       pytest tests
docs/        code walkthrough
data/        local data files (git-ignored)
```

## Setup (Python 3.10+)
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # then edit values
```

## Try it with synthetic data (no MySQL needed)
```bash
docker compose up -d mongo                             # or use a local MongoDB / Atlas
python -m mongo.synthetic.generate_events              # writes data/synthetic/*.jsonl
python -m analysis.demo_local                          # analysis with NO database
python -m mongo.import_data --cases data/synthetic/cases.jsonl \
        --events data/synthetic/citation_events.jsonl --reset
python -m mongo.build_stats
uvicorn backend.app.main:app --reload                  # http://localhost:8000/docs
pytest
```

## Git workflow
- `main` always works. Work on `feature/<topic>` branches, open a pull request, the other person looks, then merge.
- `git pull origin main` every morning. Never commit `.env` or anything in `data/`.
