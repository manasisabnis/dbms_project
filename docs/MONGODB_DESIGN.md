# MongoDB design (NoSQL part of the project)

## 1. Why a second database?
MySQL stores the stable legal facts (courts, cases, judges, statutes). Citations, however, behave like a
**stream of dated events** that keeps growing and that we mostly read as "how many in the last N years?".
MongoDB suits this because:
- each citation is one small self-contained document, and fields can be added without altering a table;
- time-window counting is a natural fit for aggregation pipelines;
- precomputed results can be stored next to the raw events as ordinary documents.

| Question | Answered by |
|---|---|
| Who decided this case, which judges, which statutes? | MySQL |
| Which cases cite this one (with page and context)? | MySQL (`Citation`) |
| How many citations per year? Is it emerging or declining? | MongoDB |

## 2. Collections
Database: `legal_citations` (name set by `MONGO_DB` in `.env`).

### `citation_events`: one document per "case A cites case B"
```json
{ "citing_case_id": 310, "cited_case_id": 205, "citation_date": ISODate("2021-08-20"),
  "year": 2021, "citing_court_level": "Supreme Court" }
```
`citation_date` is the judgment date of the citing case. `year` is stored separately to make year-wise grouping cheap.

### `case_catalog`: basic case facts needed by the analysis
```json
{ "case_id": 205, "case_name": "...", "case_number": "AIR 1973 SC 1461",
  "judgment_date": ISODate("1973-04-24"), "court_name": "Supreme Court of India" }
```

### `case_window_stats`: computed results, one document per cited case
```json
{ "case_id": 205, "case_name": "...", "case_number": "...", "judgment_date": ISODate("..."),
  "as_of": "2025-12-19", "total_citations": 701,
  "windows": { "1": {"recent": 28, "previous": 20, "growth": 0.4},
               "3": {"recent": 67, "previous": 40, "growth": 0.675},
               "5": {"recent": 91, "previous": 75, "growth": 0.2133} },
  "trailing_years": [30, 34, 31, 38],
  "labels": { "1": "regular", "3": "established", "5": "established" },
  "label": "established" }
```
`growth = (recent - previous) / max(previous, 1)`. `label` is the label for the default 3-year window.
This collection is rebuilt by `python -m mongo.build_stats`, so the API answers in milliseconds instead of
recounting every event on each request.

## 3. Indexes (`mongo/init_indexes.py`)
| Collection | Index | Speeds up |
|---|---|---|
| citation_events | `(cited_case_id, citation_date)` | all citations of one case, optionally within a date range |
| citation_events | `(citing_case_id)` | what a case cites |
| citation_events | `(year)` | year-wise charts |
| case_catalog | `(case_id)` unique | lookup; prevents duplicates |
| case_window_stats | `(case_id)` unique | case page |
| case_window_stats | `(total_citations desc)` | most-cited list |
| case_window_stats | `(labels.W, windows.W.growth desc)` for W in 1, 3, 5 | emerging / declining lists per window |

## 4. Aggregation pipelines (`mongo/pipelines/pipelines.py`)
**Rolling window for every case** (3-year window, as_of = 2025-12-31):
```js
db.citation_events.aggregate([
  { $match: { citation_date: { $gt: ISODate("2019-12-31"), $lte: ISODate("2025-12-31") } } },
  { $group: {
      _id: "$cited_case_id",
      recent:   { $sum: { $cond: [ { $gt: ["$citation_date", ISODate("2022-12-31")] }, 1, 0 ] } },
      previous: { $sum: { $cond: [ { $gt: ["$citation_date", ISODate("2022-12-31")] }, 0, 1 ] } } } },
  { $addFields: { growth: { $divide: [ { $subtract: ["$recent", "$previous"] }, { $max: ["$previous", 1] } ] } } },
  { $sort: { growth: -1 } }
])
```
Stage by stage: `$match` keeps only the two windows; `$group` makes one row per cited case and adds 1 to `recent`
or `previous` depending on the date; `$addFields` computes the growth ratio; `$sort` ranks cases.
A test (`tests/test_pipeline_matches_python.py`) proves this gives exactly the same numbers as the Python function.

**Citations of one case per year** (feeds the bar and line charts):
```js
db.citation_events.aggregate([
  { $match: { cited_case_id: 205 } },
  { $group: { _id: "$year", count: { $sum: 1 } } },
  { $sort: { _id: 1 } } ])
```

**Citations of one case by court level** (feeds the donut chart): same shape, grouped by `$citing_court_level`.

## 5. Example queries for the report (run in mongosh and paste your output)
```js
// 1. Top 10 emerging cases (3-year window)
db.case_window_stats.find({ "labels.3": "emerging" }, { case_name: 1, "windows.3": 1 })
  .sort({ "windows.3.growth": -1 }).limit(10)

// 2. How many cases carry each label?
db.case_window_stats.aggregate([ { $group: { _id: "$labels.3", cases: { $sum: 1 } } } ])

// 3. Citations of case 205 between two dates
db.citation_events.find({ cited_case_id: 205,
  citation_date: { $gte: ISODate("2015-01-01"), $lt: ISODate("2020-01-01") } }).count()

// 4. Most cited cases overall
db.case_window_stats.find({}, { case_name: 1, total_citations: 1 }).sort({ total_citations: -1 }).limit(10)

// 5. Which court levels cite the most?
db.citation_events.aggregate([ { $group: { _id: "$citing_court_level", n: { $sum: 1 } } }, { $sort: { n: -1 } } ])

// 6. Show how an index is used (look for IXSCAN in the output)
db.citation_events.find({ cited_case_id: 205 }).explain("executionStats")
```
Screenshot or paste the real output under each query before submitting.

## 6. Design decisions to explain in the viva
- **Events vs counters:** we store each citation event and compute windows on demand, so any window length can be added later.
- **Precompute vs on-the-fly:** `case_window_stats` is rebuilt in a batch job for speed. The cost is that it can go stale until the job is re-run.
- **IDs:** `case_id` matches MySQL's `Legal_Case.case_id`, so the two databases can be joined in the backend.
- **Dates as real dates:** stored as BSON dates so range queries and window boundaries work correctly.
- **Window boundaries:** open on the left, closed on the right, so a citation is never counted in two windows.

## 7. Limitations
- Counts only include citations where both cases are in our database, so absolute numbers are lower than reality.
- Citations are extracted from judgment text by pattern matching, so some are missed or mismatched.
- The labelling thresholds in `analysis/config.py` are tuned by hand, not learned.
- `build_stats` recomputes everything each run (it is not incremental).
