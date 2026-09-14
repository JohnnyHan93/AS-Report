from __future__ import annotations

from as_report.analyzer import analyze
from as_report.cleaner import clean_data
from as_report.period import PeriodSelection, build_period_range, filter_by_period
from conftest import sample_dataframe


def test_kpi_and_downtime_calculation():
    cleaned = clean_data(sample_dataframe())
    period_range = build_period_range(PeriodSelection(period="year", year=2025))
    period_data = filter_by_period(cleaned, period_range)

    analysis = analyze(cleaned, period_data)

    assert analysis["kpi"]["총 접수 건수"] == 2
    assert analysis["kpi"]["처리완료 건수"] == 1
    assert analysis["kpi"]["미완료 건수"] == 1
    assert analysis["kpi"]["라인 중단 총 시간"] == 30
    assert analysis["quality"]["고객사 미입력 건수"] == 1


def test_open_issues_and_downtime_top_lists():
    cleaned = clean_data(sample_dataframe())
    period_range = build_period_range(PeriodSelection(period="year", year=2025))
    period_data = filter_by_period(cleaned, period_range)

    analysis = analyze(cleaned, period_data)

    assert list(analysis["tables"]["진행중/미완료 이슈 목록"]["*ID"]) == [2]
    assert list(analysis["tables"]["라인 중단 시간 TOP 20 이슈 목록"]["*ID"]) == [1]


def test_empty_period_kpis_are_zero():
    cleaned = clean_data(sample_dataframe())
    period_range = build_period_range(PeriodSelection(period="custom", start="2023-01-01", end="2023-12-31"))
    period_data = filter_by_period(cleaned, period_range)

    analysis = analyze(cleaned, period_data)

    assert analysis["kpi"]["총 접수 건수"] == 0
    assert analysis["kpi"]["처리완료율"] == 0