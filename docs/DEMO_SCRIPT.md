# Demo script (fill in the [brackets] once real data is loaded)

Total time: about 8 minutes.

## Before the demo
- [ ] MongoDB running; real data imported; `python -m mongo.build_stats` run
- [ ] MySQL running; data loaded
- [ ] Backend: `uvicorn backend.app.main:app --reload` (from the repo root, venv active)
- [ ] Frontend: `NEXT_PUBLIC_USE_MOCKS=false` in `frontend/.env.local`, then `npm run dev`
- [ ] Browser open on http://localhost:3000; Grammarly-type extensions off
- [ ] Pick 3 cases beforehand: one emerging [name, id], one declining [name, id], one influential [name, id]

## Flow
1. **Problem (30 s).** "Legal precedents gain and lose influence. We measure that from how often courts cite them."
2. **Dashboard (1.5 min).** Point at the four counts, then the three lists. Switch **1 / 3 / 5 years** and show the numbers change.
   Say: "These labels come from rolling windows computed in MongoDB."
3. **Search (1 min).** Search for [case name]. Show the result table (from MySQL).
4. **Case page, Overview (1 min).** Open [emerging case]. Show case information (MySQL) and the status badge (MongoDB).
5. **Citation Analysis tab (1.5 min).** Walk through the line chart, year-wise bars and court donut.
   Toggle the window and show recent vs previous counts and the % change.
6. **Cited By, Judges, Statutes tabs (1 min).** Click through briefly.
7. **Landmark cases (30 s).** Back on the dashboard, point at the landmark list (a MySQL view).
8. **Behind the scenes (1.5 min).** Show one document in `case_window_stats` (mongosh or Compass), the aggregation pipeline,
   and one MySQL query or view. Say which database answered which part of the page.
9. **Close (30 s).** Limitations (see `docs/MONGODB_DESIGN.md` section 7) and one possible extension.

## Screenshots for the report
- [ ] Dashboard (3-year window)
- [ ] Dashboard (1-year window)
- [ ] Search results
- [ ] Case page: Overview, Citation Analysis, Cited By
- [ ] mongosh output for the six example queries
- [ ] MySQL queries and the `Landmark_Cases` view output
- [ ] FastAPI `/docs` page

## Likely questions
- Why two databases? (see MongoDB design, section 1)
- How is "emerging" decided? (growth ≥ +100 % with enough citations; thresholds in `analysis/config.py`)
- What if a case has no citations? (it simply has no stats; the page says so)
- How do you know the MongoDB pipeline is right? (a test compares it with the Python implementation)
- What are the weaknesses? (extraction misses citations; thresholds are hand-tuned)
