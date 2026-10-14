from datetime import date

from analysis.rolling_window import (
    compute_case_stats, shift_years, trailing_year_counts, window_counts,
)

AS_OF = date(2025, 12, 31)


def test_shift_years_handles_leap_day():
    assert shift_years(date(2024, 2, 29), -1) == date(2023, 2, 28)
    assert shift_years(date(2025, 6, 1), -3) == date(2022, 6, 1)


def test_window_counts_splits_recent_and_previous():
    dates = [date(2025, 3, 1), date(2025, 6, 1),      # recent 1y window
             date(2024, 3, 1)]                        # previous 1y window
    r = window_counts(dates, AS_OF, years=1)
    assert (r["recent"], r["previous"]) == (2, 1)
    assert r["growth"] == 1.0                         # (2-1)/1


def test_boundary_is_open_left_closed_right():
    # exactly one year before as_of belongs to the PREVIOUS window, not recent
    r = window_counts([date(2024, 12, 31)], AS_OF, years=1)
    assert (r["recent"], r["previous"]) == (0, 1)
    # as_of itself is counted as recent
    r = window_counts([AS_OF], AS_OF, years=1)
    assert (r["recent"], r["previous"]) == (1, 0)


def test_growth_when_no_previous_citations_does_not_divide_by_zero():
    r = window_counts([date(2025, 1, 1)] * 5, AS_OF, years=1)
    assert r["previous"] == 0 and r["growth"] == 5.0


def test_trailing_year_counts_are_oldest_first():
    dates = [date(2022, 6, 1)] * 1 + [date(2023, 6, 1)] * 2 + [date(2024, 6, 1)] * 3 + [date(2025, 6, 1)] * 4
    assert trailing_year_counts(dates, AS_OF, n_years=4) == [1, 2, 3, 4]


def test_compute_case_stats_has_all_windows():
    s = compute_case_stats([date(2025, 1, 1)], AS_OF)
    assert set(s["windows"]) == {"1", "3", "5"}
    assert s["total"] == 1 and len(s["trailing_years"]) == 4
