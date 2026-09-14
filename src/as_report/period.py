from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd
from dateutil.parser import parse

DATE_COLUMN = "접수일"


@dataclass(frozen=True)
class PeriodSelection:
    period: str
    year: int | None = None
    half: str | None = None
    quarter: str | None = None
    start: str | None = None
    end: str | None = None


@dataclass(frozen=True)
class PeriodRange:
    period: str
    start_date: date
    end_date: date
    label: str
    filename_label: str


class PeriodError(ValueError):
    """Raised when period arguments are invalid."""


def build_period_range(selection: PeriodSelection) -> PeriodRange:
    period = selection.period.lower()
    if period == "year":
        if selection.year is None:
            raise PeriodError("연간 리포트에는 --year 값이 필요합니다.")
        return PeriodRange("year", date(selection.year, 1, 1), date(selection.year, 12, 31), str(selection.year), str(selection.year))

    if period == "half":
        if selection.year is None or not selection.half:
            raise PeriodError("반기 리포트에는 --year와 --half 값이 필요합니다.")
        half = selection.half.upper()
        if half == "H1":
            return PeriodRange("half", date(selection.year, 1, 1), date(selection.year, 6, 30), f"{selection.year} H1", f"{selection.year}_H1")
        if half == "H2":
            return PeriodRange("half", date(selection.year, 7, 1), date(selection.year, 12, 31), f"{selection.year} H2", f"{selection.year}_H2")
        raise PeriodError("--half 값은 H1 또는 H2만 사용할 수 있습니다.")

    if period == "quarter":
        if selection.year is None or not selection.quarter:
            raise PeriodError("분기 리포트에는 --year와 --quarter 값이 필요합니다.")
        quarter = selection.quarter.upper()
        ranges = {
            "Q1": (date(selection.year, 1, 1), date(selection.year, 3, 31)),
            "Q2": (date(selection.year, 4, 1), date(selection.year, 6, 30)),
            "Q3": (date(selection.year, 7, 1), date(selection.year, 9, 30)),
            "Q4": (date(selection.year, 10, 1), date(selection.year, 12, 31)),
        }
        if quarter not in ranges:
            raise PeriodError("--quarter 값은 Q1, Q2, Q3, Q4만 사용할 수 있습니다.")
        start_date, end_date = ranges[quarter]
        return PeriodRange("quarter", start_date, end_date, f"{selection.year} {quarter}", f"{selection.year}_{quarter}")

    if period == "custom":
        if not selection.start or not selection.end:
            raise PeriodError("사용자 지정 기간에는 --start와 --end 값이 필요합니다.")
        start_date = parse(selection.start).date()
        end_date = parse(selection.end).date()
        if start_date > end_date:
            raise PeriodError("시작일은 종료일보다 늦을 수 없습니다.")
        filename_label = f"{start_date.isoformat()}_{end_date.isoformat()}"
        label = f"{start_date.isoformat()} ~ {end_date.isoformat()}"
        return PeriodRange("custom", start_date, end_date, label, filename_label)

    raise PeriodError("--period 값은 year, half, quarter, custom 중 하나여야 합니다.")


def filter_by_period(dataframe: pd.DataFrame, period_range: PeriodRange) -> pd.DataFrame:
    if DATE_COLUMN not in dataframe.columns:
        raise PeriodError("기간 필터 기준 컬럼인 '접수일'이 없습니다.")

    received_at = pd.to_datetime(dataframe[DATE_COLUMN], errors="coerce")
    start = pd.Timestamp(period_range.start_date)
    end = pd.Timestamp(period_range.end_date) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
    mask = received_at.between(start, end, inclusive="both")
    return dataframe.loc[mask].copy()