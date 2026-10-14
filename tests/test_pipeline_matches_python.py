"""The MongoDB aggregation pipeline and the pure-Python function must agree."""
from datetime import date

from analysis.rolling_window import group_dates_by_case, window_counts
from mongo.pipelines.pipelines import rolling_window_pipeline

AS_OF = date(2025, 12, 31)


def test_pipeline_equals_python_for_every_case(db):
    events = list(db["citation_events"].find({}, {"_id": 0}))
    dates_by_case = group_dates_by_case(events)

    for years in (1, 3, 5):
        from_mongo = {r["_id"]: r for r in db["citation_events"].aggregate(rolling_window_pipeline(AS_OF, years))}
        for case_id, dates in dates_by_case.items():
            expected = window_counts(dates, AS_OF, years)
            if expected["recent"] + expected["previous"] == 0:
                assert case_id not in from_mongo        # outside both windows -> not in output
                continue
            got = from_mongo[case_id]
            assert got["recent"] == expected["recent"]
            assert got["previous"] == expected["previous"]
            assert round(got["growth"], 4) == expected["growth"]
