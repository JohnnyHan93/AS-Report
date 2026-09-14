from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from .period import PeriodRange, filter_by_period

DOWNTIME_COLUMN = "라인 중단 시간 (분)"
COMPARISON_ITEMS = [
    "총 접수 건수",
    "처리완료 건수",
    "미완료 건수",
    "긴급방문 건수",
    "원격지원 건수",
    "라인 중단 발생 건수",
    "라인 중단 시간(입력 건 기준)",
]


def build_comparison_periods(period_range: PeriodRange) -> dict[str, PeriodRange | None]:
    if period_range.period == "year":
        year = period_range.start_date.year
        return {
            "전년 동기": PeriodRange("year", date(year - 1, 1, 1), date(year - 1, 12, 31), str(year - 1), str(year - 1)),
            "직전 기간": None,
        }

    if period_range.period == "half":
        year = period_range.start_date.year
        half = "H1" if period_range.start_date.month == 1 else "H2"
        previous_year_period = _half_range(year - 1, half)
        previous_period = _half_range(year - 1, "H2") if half == "H1" else _half_range(year, "H1")
        return {"전년 동기": previous_year_period, "직전 기간": previous_period}

    if period_range.period == "quarter":
        year = period_range.start_date.year
        quarter = _quarter_from_month(period_range.start_date.month)
        previous_year_period = _quarter_range(year - 1, quarter)
        previous_quarter = _previous_quarter(year, quarter)
        return {"전년 동기": previous_year_period, "직전 기간": _quarter_range(*previous_quarter)}

    return {"전년 동기": None, "직전 기간": None}


def analyze_comparison(clean_df: pd.DataFrame, current_df: pd.DataFrame, period_range: PeriodRange, source_period_data: pd.DataFrame | None = None) -> pd.DataFrame:
    source_actual_min_date, source_actual_max_date = _actual_date_range(source_period_data if source_period_data is not None else current_df)
    filtered_actual_min_date, filtered_actual_max_date = _actual_date_range(current_df)
    effective_end_date = source_actual_max_date if source_actual_max_date and source_actual_max_date < period_range.end_date else period_range.end_date
    is_partial_period = bool(source_actual_max_date and source_actual_max_date < period_range.end_date)
    comparison_mode = "YTD" if period_range.period == "year" and is_partial_period else "Full Period"
    periods = _effective_comparison_periods(period_range, effective_end_date, comparison_mode)
    if periods["전년 동기"] is None and periods["직전 기간"] is None:
        return pd.DataFrame(columns=_comparison_columns())

    effective_current = _filter_between(clean_df, period_range.start_date, effective_end_date) if is_partial_period else current_df
    current = _comparison_kpi(effective_current)
    previous_year = _comparison_kpi(filter_by_period(clean_df, periods["전년 동기"])) if periods["전년 동기"] else None
    previous_period = _comparison_kpi(filter_by_period(clean_df, periods["직전 기간"])) if periods["직전 기간"] else None
    metadata = {
        "비교 방식": comparison_mode,
        "선택 기간": f"{period_range.start_date.isoformat()} ~ {period_range.end_date.isoformat()}",
        "실제 데이터 존재 기간": _actual_period_text(source_actual_min_date, source_actual_max_date),
        "필터 데이터 존재 기간": _actual_period_text(filtered_actual_min_date, filtered_actual_max_date),
        "비교 기준 기간": _comparison_period_text(periods["전년 동기"]),
        "비교 주의": _ytd_note(period_range, source_actual_max_date, periods["전년 동기"]) if comparison_mode == "YTD" else "",
    }

    rows: list[dict[str, Any]] = []
    for item in COMPARISON_ITEMS:
        current_value = current[item]
        previous_year_value = previous_year[item] if previous_year else None
        previous_period_value = previous_period[item] if previous_period else None
        year_delta, year_rate = _delta(current_value, previous_year_value)
        period_delta, period_rate = _delta(current_value, previous_period_value)
        rows.append(
            {
                "항목": item,
                "현재 기간 값": current_value,
                "전년 동기 값": _display_value(previous_year_value),
                "전년 동기 대비 증감": _display_value(year_delta),
                "전년 동기 대비 증감률": year_rate,
                "직전 기간 값": _display_value(previous_period_value),
                "직전 기간 대비 증감": _display_value(period_delta),
                "직전 기간 대비 증감률": period_rate,
                **metadata,
            }
        )
    return pd.DataFrame(rows, columns=_comparison_columns())


def _comparison_columns() -> list[str]:
    return [
        "항목",
        "현재 기간 값",
        "전년 동기 값",
        "전년 동기 대비 증감",
        "전년 동기 대비 증감률",
        "직전 기간 값",
        "직전 기간 대비 증감",
        "직전 기간 대비 증감률",
        "비교 방식",
        "선택 기간",
        "실제 데이터 존재 기간",
        "필터 데이터 존재 기간",
        "비교 기준 기간",
        "비교 주의",
    ]


def _effective_comparison_periods(period_range: PeriodRange, effective_end_date: date, comparison_mode: str) -> dict[str, PeriodRange | None]:
    if period_range.period == "year" and comparison_mode == "YTD":
        start = _shift_year(period_range.start_date, -1)
        end = _shift_year(effective_end_date, -1)
        return {
            "전년 동기": PeriodRange("year", start, end, f"{start.year} YTD", f"{start.isoformat()}_{end.isoformat()}"),
            "직전 기간": None,
        }
    return build_comparison_periods(period_range)


def _comparison_kpi(dataframe: pd.DataFrame) -> dict[str, float | int]:
    total = int(len(dataframe))
    status = dataframe.get("처리상태구분", pd.Series(index=dataframe.index, dtype="object"))
    work_type = dataframe.get("업무유형구분", pd.Series(index=dataframe.index, dtype="object")).fillna("기타")
    downtime = pd.to_numeric(dataframe.get(DOWNTIME_COLUMN, pd.Series(index=dataframe.index, dtype="float")), errors="coerce")
    return {
        "총 접수 건수": total,
        "처리완료 건수": int((status == "완료").sum()),
        "미완료 건수": int(total - (status == "완료").sum()),
        "긴급방문 건수": int((work_type == "긴급방문").sum()),
        "원격지원 건수": int((work_type == "원격지원").sum()),
        "라인 중단 발생 건수": int((downtime.fillna(0) > 0).sum()),
        "라인 중단 시간(입력 건 기준)": float(downtime.dropna().sum()) if downtime.notna().any() else 0.0,
    }


def _delta(current: float | int, previous: float | int | None) -> tuple[float | int | None, str]:
    if previous is None:
        return None, "-"
    delta = current - previous
    if previous == 0:
        return delta, "-"
    return delta, f"{(delta / previous * 100):.1f}%"


def _display_value(value: float | int | None) -> float | int | str:
    return "-" if value is None else value


def _actual_date_range(dataframe: pd.DataFrame) -> tuple[date | None, date | None]:
    if dataframe.empty or "접수일" not in dataframe.columns:
        return None, None
    received_at = pd.to_datetime(dataframe["접수일"], errors="coerce").dropna()
    if received_at.empty:
        return None, None
    return received_at.min().date(), received_at.max().date()


def _filter_between(dataframe: pd.DataFrame, start_date: date, end_date: date) -> pd.DataFrame:
    if dataframe.empty or "접수일" not in dataframe.columns:
        return dataframe.copy()
    received_at = pd.to_datetime(dataframe["접수일"], errors="coerce")
    mask = received_at.between(pd.Timestamp(start_date), pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1), inclusive="both")
    return dataframe.loc[mask].copy()


def _actual_period_text(start_date: date | None, end_date: date | None) -> str:
    if not start_date or not end_date:
        return "데이터 없음"
    return f"{start_date.isoformat()} ~ {end_date.isoformat()}"


def _comparison_period_text(period_range: PeriodRange | None) -> str:
    if period_range is None:
        return "-"
    return f"{period_range.start_date.isoformat()} ~ {period_range.end_date.isoformat()}"


def _ytd_note(period_range: PeriodRange, actual_end_date: date | None, previous_period: PeriodRange | None) -> str:
    if actual_end_date is None or previous_period is None:
        return ""
    return (
        f"{period_range.start_date.year}년 데이터가 {actual_end_date.month}월 {actual_end_date.day}일까지 입력되어, "
        f"전년 동일 기간({previous_period.start_date.isoformat()}~{previous_period.end_date.isoformat()})과 비교했습니다."
    )


def _shift_year(value: date, years: int) -> date:
    try:
        return value.replace(year=value.year + years)
    except ValueError:
        return value.replace(year=value.year + years, day=28)


def _half_range(year: int, half: str) -> PeriodRange:
    if half == "H1":
        return PeriodRange("half", date(year, 1, 1), date(year, 6, 30), f"{year} H1", f"{year}_H1")
    return PeriodRange("half", date(year, 7, 1), date(year, 12, 31), f"{year} H2", f"{year}_H2")


def _quarter_range(year: int, quarter: str) -> PeriodRange:
    ranges = {
        "Q1": (date(year, 1, 1), date(year, 3, 31)),
        "Q2": (date(year, 4, 1), date(year, 6, 30)),
        "Q3": (date(year, 7, 1), date(year, 9, 30)),
        "Q4": (date(year, 10, 1), date(year, 12, 31)),
    }
    start_date, end_date = ranges[quarter]
    return PeriodRange("quarter", start_date, end_date, f"{year} {quarter}", f"{year}_{quarter}")


def _quarter_from_month(month: int) -> str:
    return f"Q{((month - 1) // 3) + 1}"


def _previous_quarter(year: int, quarter: str) -> tuple[int, str]:
    number = int(quarter[1])
    if number == 1:
        return year - 1, "Q4"
    return year, f"Q{number - 1}"
