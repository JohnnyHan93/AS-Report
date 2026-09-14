from __future__ import annotations

from as_report.cleaner import clean_data
from as_report.period import PeriodSelection, build_period_range, filter_by_period
from conftest import sample_dataframe


def test_year_filter_uses_received_date():
    cleaned = clean_data(sample_dataframe())
    period_range = build_period_range(PeriodSelection(period="year", year=2025))

    result = filter_by_period(cleaned, period_range)

    assert list(result["*ID"]) == [1, 2]


def test_half_and_quarter_filter():
    cleaned = clean_data(sample_dataframe())
    half = build_period_range(PeriodSelection(period="half", year=2025, half="H2"))
    quarter = build_period_range(PeriodSelection(period="quarter", year=2025, quarter="Q1"))

    assert list(filter_by_period(cleaned, half)["*ID"]) == [2]
    assert list(filter_by_period(cleaned, quarter)["*ID"]) == [1]


def test_custom_empty_period_returns_empty_dataframe():
    cleaned = clean_data(sample_dataframe())
    period_range = build_period_range(PeriodSelection(period="custom", start="2023-01-01", end="2023-12-31"))

    result = filter_by_period(cleaned, period_range)

    assert result.empty