from __future__ import annotations

import pandas as pd

from as_report.cleaner import clean_data
from conftest import sample_dataframe


def test_date_and_number_conversion():
    cleaned = clean_data(sample_dataframe())

    assert pd.api.types.is_datetime64_any_dtype(cleaned["접수일"])
    assert pd.api.types.is_numeric_dtype(cleaned["라인 중단 시간 (분)"])
    assert cleaned.loc[0, "접수연도"] == 2025
    assert cleaned.loc[1, "접수반기"] == "H2"
    assert cleaned.loc[0, "기간_연월"] == "2025-01"


def test_missing_value_cleanup_and_derived_columns():
    cleaned = clean_data(sample_dataframe())

    assert pd.isna(cleaned.loc[1, "고객사"])
    assert pd.isna(cleaned.loc[1, "고장원인"])
    assert pd.isna(cleaned.loc[1, "소분류 (고장부품)"])
    assert cleaned.loc[0, "처리상태구분"] == "완료"
    assert cleaned.loc[1, "처리상태구분"] == "미완료"
    assert cleaned.loc[0, "업무유형구분"] == "긴급방문"
    assert cleaned.loc[1, "업무유형구분"] == "원격지원"
    assert cleaned.loc[0, "라인중단_발생여부"] == "발생"
    assert cleaned.loc[1, "라인중단_발생여부"] == "미발생/미입력"