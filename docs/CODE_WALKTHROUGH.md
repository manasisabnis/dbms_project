# Code walkthrough (Person 2's code)

Read in this order. Each section gives the HIGH-LEVEL idea (what and why) and the
LOW-LEVEL detail (how, line by line in spirit), plus something to try.

The data flow in one picture:

```
generate_events.py ──► cases.jsonl + citation_events.jsonl
                              │  import_data.py
                              ▼
                   MongoDB: case_catalog, citation_events
                              │  build_stats.py  (uses analysis/ code)
                              ▼
                   MongoDB: case_window_stats  (counts + labels per case)
                              │  FastAPI routers/trends.py
                              ▼
                        JSON  ──►  Next.js pages
```

---
## 1. `analysis/config.py`
**High level:** every threshold in one place. Changing "what counts as emerging" never needs a logic edit.
**Low level:** plain constants. `MIN_VOLUME_PER_YEAR = 3` means a 3-year window needs 9 citations
before a percentage change is trusted. Label strings are what MongoDB and the API store.
**Try:** set `EMERGING_MIN_GROWTH = 3.0`, run `python -m analysis.demo_local`, watch the emerging count drop.

## 2. `analysis/rolling_window.py`
**High level:** for a case's list of citation dates, count citations in the recent window and the window before it.
```
as_of - 2y        as_of - 1y          as_of
   |---- previous ----|----- recent -----|        (shown for a 1-year window)
```
**Low level:**
- `shift_years(d, n)` moves a date by whole years; Feb 29 falls back to Feb 28 so it never crashes.
- `count_between(dates, start_exclusive, end_inclusive)` counts `start < d <= end`. Open on the left,
  closed on the right, so a citation on a boundary day belongs to exactly one window.
- `window_counts(dates, as_of, years)` builds the two ranges and returns
  `recent`, `previous`, `growth = (recent - previous) / max(previous, 1)`. The `max(..., 1)` is the guard
  against dividing by zero when a case had no earlier citations.
- `trailing_year_counts` slices the last N years into one-year pieces, **oldest first** (used to judge steadiness).
- `compute_case_stats` runs 1, 3 and 5-year windows plus the trailing counts for one case.
- `build_all_stats` first groups all events by `cited_case_id` (a dict of lists), then calls
  `compute_case_stats` for each case.
**Try:** call `window_counts([date(2025,3,1)], date(2025,12,31), 1)` in a Python shell and change the dates.

## 3. `analysis/classify.py`
**High level:** one label per case using rules checked in a fixed order (first match wins).
**Low level:** `classify_case` computes the case's age, picks the chosen window's numbers, then:
1. **recent**: age < 3 years, at least 3 citations in the last 3 years, and the last year is not
   quieter than the year before.
2. **emerging**: recent count above the volume floor AND growth ≥ +100 %.
3. **declining**: previous count above the floor AND growth ≤ −50 %.
4. **established**: average of the last 4 yearly counts ≥ 8 AND `pstdev / mean ≤ 0.5`
   (the coefficient of variation: small means steady).
5. otherwise **regular**.
Order matters: a brand-new case with 30 citations would also look "emerging", so `recent` is tested first.
`classify_all_windows` returns a label for 1, 3 and 5 years so the UI toggle needs no extra computation.
**Try:** `tests/test_classify.py` shows each rule with hand-made numbers. Break a rule and see which test fails.

## 4. `mongo/synthetic/generate_events.py`
**High level:** invents 2,000 cases and ~100k citations with planted patterns (emerging, declining,
established, recent, plus quiet filler) so we can test everything before real data exists.
**Low level:**
- Each case gets an archetype and a judgment date.
- `expected_citations(archetype, year, ...)` gives the average citations that case gets in a year
  (e.g. emerging: 1/yr until 2021, then 8, 14, 20, 26).
- `poisson(lam)` (Knuth's algorithm) turns an average into a random whole number.
- A citation is made by another case decided in the same year, and takes that case's judgment date.
  Sampling is *without replacement*, so a pair (citing, cited) never repeats.
- A fixed seed makes the output repeatable.
- `ground_truth.json` records the planted label so the demo can score the classifier.
**Try:** `python -m analysis.demo_local` ends with "Agreement with planted patterns".

## 5. `mongo/import_data.py`, `mongo/init_indexes.py`
**High level:** load JSONL into MongoDB and make queries fast.
**Low level:** dates arrive as strings; `parse_date` converts them to `datetime` because MongoDB can only
compare real dates. `insert_many` runs in batches of 5,000. Indexes: `(cited_case_id, citation_date)` makes
"all citations of case X in a date range" fast; `year` serves the year-wise chart; a unique index on `case_id`
prevents duplicates.

## 6. `mongo/pipelines/pipelines.py` (the NoSQL showpiece)
**High level:** the same window counting, done *inside* MongoDB.
**Low level of `rolling_window_pipeline`:**
1. `$match`: keep citations dated after `as_of - 2y` and up to `as_of`.
2. `$group` by `cited_case_id`: for each citation add 1 to `recent` if its date is after `as_of - 1y`, otherwise to `previous`.
   (`$cond` is MongoDB's if/else.)
3. `$addFields`: compute `growth` with `$divide`, `$subtract` and `$max`.
4. `$sort` by growth.
`tests/test_pipeline_matches_python.py` proves this gives exactly the same numbers as `window_counts`.
`yearly_counts_pipeline` and `court_level_pipeline` feed the two charts on the case page.

## 7. `mongo/build_stats.py`
**High level:** the batch job that fills `case_window_stats`.
**Low level:** read every event's `cited_case_id` and date; choose `as_of` (newest citation, or `--as-of`);
`build_all_stats`; look up each case's judgment date in `case_catalog`; `classify_all_windows`;
delete old stats and insert the new documents. Precomputing means the API answers in milliseconds
instead of recomputing 100k events on each request.

## 8. `backend/app/*`
**High level:** a small web API on top of `case_window_stats`.
**Low level:**
- `main.py` creates the FastAPI app, allows the Next.js dev server through CORS, mounts routers under `/api`.
- `deps.py` provides `get_db`; FastAPI injects it with `Depends`. Tests replace it with a fake DB.
- `schemas.py` defines the response shapes (pydantic); FastAPI validates output and writes `/docs` from them.
- `routers/trends.py`:
  - `dashboard`: `$group` to count cases per label; for emerging, `find({"labels.3": "emerging"}).sort("windows.3.growth", -1)`
    gives the biggest risers; declining sorts ascending (biggest drops first).
  - `citation_trend`: one `find_one` for the stats plus the two pipelines for the charts; 404 if the case is unknown.

## 9. `tests/`
Run `pytest`. `conftest.py` builds a small fake MongoDB (mongomock) so tests need no server.
- `test_rolling_window.py`: boundaries, leap day, divide-by-zero.
- `test_classify.py`: one test per rule and for rule order.
- `test_pipeline_matches_python.py`: Mongo and Python agree for every case and window.
- `test_synthetic_accuracy.py`: classifier finds ≥ 85 % of the planted patterns.
- `test_api.py`: endpoints return the right shape and ordering.

## Known simplifications (be ready to explain these)
- Synthetic labels are easy; real data will need threshold tuning.
- Some young "recent" cases that fade within a year fall through to `emerging`; real data may show more such cases.
- `build_stats` replaces the whole collection (simple, but not incremental).
- The tests use mongomock, which mimics MongoDB; run once against a real MongoDB too.
