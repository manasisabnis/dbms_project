from datetime import date

from analysis import config as cfg
from analysis.classify import classify_case

AS_OF = date(2025, 12, 31)
OLD = date(1990, 1, 1)


def make_stats(prev, recent, trailing=(0, 0, 0, 0), one=(0, 0)):
    growth = (recent - prev) / max(prev, 1)
    return {
        "total": 100,
        "windows": {
            "1": {"previous": one[0], "recent": one[1], "growth": 0},
            "3": {"previous": prev, "recent": recent, "growth": growth},
            "5": {"previous": prev, "recent": recent, "growth": growth},
        },
        "trailing_years": list(trailing),
    }


def test_emerging():
    assert classify_case(make_stats(10, 42), OLD, AS_OF) == cfg.EMERGING


def test_declining():
    assert classify_case(make_stats(52, 13), OLD, AS_OF) == cfg.DECLINING


def test_established_needs_high_and_steady_counts():
    steady = make_stats(100, 100, trailing=(30, 34, 31, 38))
    assert classify_case(steady, OLD, AS_OF) == cfg.ESTABLISHED
    spiky = make_stats(100, 100, trailing=(2, 60, 1, 40))
    assert classify_case(spiky, OLD, AS_OF) == cfg.REGULAR


def test_small_numbers_do_not_count_as_emerging():
    # 1 -> 4 is +300% but far below the volume floor
    assert classify_case(make_stats(1, 4), OLD, AS_OF) == cfg.REGULAR


def test_recent_wins_over_emerging_for_young_cases():
    stats = make_stats(0, 30, one=(5, 20))
    assert classify_case(stats, date(2024, 6, 1), AS_OF) == cfg.RECENT
    # the same numbers on an old case are 'emerging'
    assert classify_case(stats, OLD, AS_OF) == cfg.EMERGING


def test_young_case_that_is_fading_is_not_recent():
    stats = make_stats(0, 4, one=(3, 1))
    assert classify_case(stats, date(2024, 6, 1), AS_OF) == cfg.REGULAR


def test_case_decided_after_as_of_is_ignored():
    assert classify_case(make_stats(10, 42), date(2030, 1, 1), AS_OF) == cfg.REGULAR
