from __future__ import annotations

import pandas as pd

from as_report.comparison import analyze_comparison, build_comparison_periods
from as_report.period import PeriodSelection, build_period_range, filter_by_period


def _comparison_source() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "접수일": pd.Timestamp("2024-10-05"),
                "처리상태구분": "완료",
                "업무유형구분": "긴급방문",
                "라인 중단 시간 (분)": 10,
                "고객사": "A",
                "대분류": "Robot",
            },
            {
                "접수일": pd.Timestamp("2025-07-05"),
                "처리상태구분": "미완료",
                "업무유형구분": "원격지원",
                "라인 중단 시간 (분)": 0,
                "고객사": "A",
                "대분류": "Robot",
            },
            {
                "접수일": pd.Timestamp("2025-10-05"),
                "처리상태구분": "완료",
                "업무유형구분": "긴급방문",
                "라인 중단 시간 (분)": 30,
                "고객사": "A",
                "대분류": "Robot",
            },
            {
                "접수일": pd.Timestamp("2025-11-05"),
                "처리상태구분": "완료",
                "업무유형구분": "원격지원",
                "라인 중단 시간 (분)": 0,
                "고객사": pd.NA,
                "대분류": pd.NA,
            },
        ]
    )


def test_comparison_periods_for_year_half_and_quarter():
    year = build_comparison_periods(build_period_range(PeriodSelection(period="year", year=2025)))
    half = build_comparison_periods(build_period_range(PeriodSelection(period="half", year=2025, half="H1")))
    quarter = build_comparison_periods(build_period_range(PeriodSelection(period="quarter", year=2025, quarter="Q4")))

    assert year["전년 동기"].start_date.isoformat() == "2024-01-01"
    assert year["직전 기간"] is None
    assert half["직전 기간"].label == "2024 H2"
    assert quarter["전년 동기"].label == "2024 Q4"
    assert quarter["직전 기간"].label == "2025 Q3"


def test_analyze_comparison_calculates_current_previous_and_rates():
    source = _comparison_source()
    period_range = build_period_range(PeriodSelection(period="quarter", year=2025, quarter="Q4"))
    current = filter_by_period(source, period_range)

    result = analyze_comparison(source, current, period_range)
    total = result.loc[result["항목"] == "총 접수 건수"].iloc[0]
    downtime = result.loc[result["항목"] == "라인 중단 시간(입력 건 기준)"].iloc[0]

    assert total["현재 기간 값"] == 2
    assert total["전년 동기 값"] == 1
    assert total["전년 동기 대비 증감"] == 1
    assert total["전년 동기 대비 증감률"] == "100.0%"
    assert total["직전 기간 값"] == 1
    assert downtime["현재 기간 값"] == 30.0
    assert "고객사 미입력 건수" not in set(result["항목"])
    assert "대분류 미입력 건수" not in set(result["항목"])


def test_comparison_rate_is_dash_when_previous_value_is_zero():
    source = pd.DataFrame(
        [
            {
                "접수일": pd.Timestamp("2025-10-01"),
                "처리상태구분": "완료",
                "업무유형구분": "긴급방문",
                "라인 중단 시간 (분)": 0,
                "고객사": "A",
                "대분류": "Robot",
            }
        ]
    )
    period_range = build_period_range(PeriodSelection(period="quarter", year=2025, quarter="Q4"))

    result = analyze_comparison(source, filter_by_period(source, period_range), period_range)
    total = result.loc[result["항목"] == "총 접수 건수"].iloc[0]

    assert total["전년 동기 값"] == 0
    assert total["전년 동기 대비 증감률"] == "-"


def test_year_comparison_uses_raw_period_for_ytd_basis_not_filtered_current():
    source = pd.DataFrame(
        [
            {
                "접수일": pd.Timestamp("2024-01-05"),
                "처리상태구분": "완료",
                "업무유형구분": "긴급방문",
                "라인 중단 시간 (분)": 5,
                "고객사": "A",
                "대분류": "Robot",
            },
            {
                "접수일": pd.Timestamp("2025-01-05"),
                "처리상태구분": "완료",
                "업무유형구분": "긴급방문",
                "라인 중단 시간 (분)": 10,
                "고객사": "A",
                "대분류": "Robot",
            },
            {
                "접수일": pd.Timestamp("2025-12-31"),
                "처리상태구분": "완료",
                "업무유형구분": "원격지원",
                "라인 중단 시간 (분)": 0,
                "고객사": "B",
                "대분류": "Robot",
            },
        ]
    )
    period_range = build_period_range(PeriodSelection(period="year", year=2025))
    filtered_source = source.loc[source["고객사"] == "A"].copy()
    current = filter_by_period(filtered_source, period_range)
    source_period = filter_by_period(source, period_range)

    result = analyze_comparison(filtered_source, current, period_range, source_period_data=source_period)
    total = result.loc[result["항목"] == "총 접수 건수"].iloc[0]

    assert total["비교 방식"] == "Full Period"
    assert total["현재 기간 값"] == 1
    assert total["전년 동기 값"] == 1
    assert total["실제 데이터 존재 기간"] == "2025-01-05 ~ 2025-12-31"
    assert total["필터 데이터 존재 기간"] == "2025-01-05 ~ 2025-01-05"


def test_year_comparison_warns_ytd_when_raw_period_is_partial():
    source = pd.DataFrame(
        [
            {
                "접수일": pd.Timestamp("2025-01-05"),
                "처리상태구분": "완료",
                "업무유형구분": "긴급방문",
                "라인 중단 시간 (분)": 5,
                "고객사": "A",
                "대분류": "Robot",
            },
            {
                "접수일": pd.Timestamp("2026-06-20"),
                "처리상태구분": "완료",
                "업무유형구분": "긴급방문",
                "라인 중단 시간 (분)": 10,
                "고객사": "A",
                "대분류": "Robot",
            },
        ]
    )
    period_range = build_period_range(PeriodSelection(period="year", year=2026))
    current = filter_by_period(source, period_range)

    result = analyze_comparison(source, current, period_range, source_period_data=current)
    total = result.loc[result["항목"] == "총 접수 건수"].iloc[0]

    assert total["비교 방식"] == "YTD"
    assert total["비교 주의"] == "2026년 데이터가 6월 20일까지 입력되어, 전년 동일 기간(2025-01-01~2025-06-20)과 비교했습니다."
