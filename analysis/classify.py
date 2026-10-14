"""Turn a case's window statistics into one label.

Rules are checked in this order and the first match wins:
    1. recent       young case already being cited, not fading
    2. emerging     lots of citations now AND big increase vs before
    3. declining    lots of citations before AND big drop now
    4. established  high, steady citations every year lately
    5. regular      everything else
"""
from __future__ import annotations

from datetime import date
from statistics import mean, pstdev

from analysis import config as cfg


def classify_case(stats: dict, judgment_date: date, as_of: date, window: int = cfg.DEFAULT_WINDOW) -> str:
    age_years = (as_of - judgment_date).days / 365.25
    if age_years < 0:                       # decided after the as_of date: ignore
        return cfg.REGULAR

    w = stats["windows"][str(window)]
    one_year = stats["windows"]["1"]
    three_year = stats["windows"]["3"]
    volume_floor = cfg.MIN_VOLUME_PER_YEAR * window

    # 1. Recent
    if (
        age_years < cfg.RECENT_MAX_AGE_YEARS
        and three_year["recent"] >= cfg.RECENT_MIN_CITATIONS
        and one_year["recent"] >= one_year["previous"]
    ):
        return cfg.RECENT

    # 2. Emerging
    if w["recent"] >= volume_floor and w["growth"] >= cfg.EMERGING_MIN_GROWTH:
        return cfg.EMERGING

    # 3. Declining
    if w["previous"] >= volume_floor and w["growth"] <= cfg.DECLINING_MAX_GROWTH:
        return cfg.DECLINING

    # 4. Established
    yearly = stats["trailing_years"]
    avg = mean(yearly)
    if avg >= cfg.ESTABLISHED_MIN_MEAN and pstdev(yearly) / avg <= cfg.ESTABLISHED_MAX_CV:
        return cfg.ESTABLISHED

    return cfg.REGULAR


def classify_all_windows(stats: dict, judgment_date: date, as_of: date) -> dict[str, str]:
    """{'1': label, '3': label, '5': label} so the UI toggle needs no recomputation."""
    return {str(w): classify_case(stats, judgment_date, as_of, w) for w in cfg.WINDOWS}
