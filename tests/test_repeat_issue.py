from __future__ import annotations

import pandas as pd

from as_report.repeat_issue import filter_main_repeat_issues, find_repeat_issues


def test_find_repeat_issues_extracts_repeated_combinations():
    source = pd.DataFrame(
        [
            {
                "*ID": 1,
                "접수일": pd.Timestamp("2025-01-01"),
                "고객사": "A",
                "대분류": "Robot",
                "중분류": "Motor",
                "소분류 (고장부품)": "Reducer",
                "로보트 기종": "M1",
                "BOOTH": "B1",
                "LINE": "L1",
                "공정": "Weld",
                "라인 중단 시간 (분)": 10,
            },
            {
                "*ID": 2,
                "접수일": pd.Timestamp("2025-01-03"),
                "고객사": "A",
                "대분류": "Robot",
                "중분류": "Motor",
                "소분류 (고장부품)": "Reducer",
                "로보트 기종": "M1",
                "BOOTH": "B1",
                "LINE": "L1",
                "공정": "Weld",
                "라인 중단 시간 (분)": 20,
            },
            {
                "*ID": 3,
                "접수일": pd.Timestamp("2025-02-01"),
                "고객사": "B",
                "대분류": "Vision",
                "중분류": "Camera",
                "소분류 (고장부품)": "Lens",
                "로보트 기종": "M2",
                "BOOTH": "B2",
                "LINE": "L2",
                "공정": "Inspect",
                "라인 중단 시간 (분)": 5,
            },
        ]
    )

    result = find_repeat_issues(source)

    assert not result.empty
    row = result.loc[result["반복 기준"] == "고객사 + 대분류 + 중분류"].iloc[0]
    assert row["조건값"] == "고객사=A / 대분류=Robot / 중분류=Motor"
    assert row["접수 건수"] == 2
    assert row["라인 중단 총 시간"] == 30.0
    assert row["관련 ID 목록"] == "1, 2"


def test_find_repeat_issues_excludes_single_items():
    source = pd.DataFrame(
        [
            {
                "*ID": 1,
                "접수일": pd.Timestamp("2025-01-01"),
                "고객사": "A",
                "대분류": "Robot",
                "중분류": "Motor",
                "소분류 (고장부품)": "Reducer",
                "로보트 기종": "M1",
                "BOOTH": "B1",
                "LINE": "L1",
                "공정": "Weld",
                "라인 중단 시간 (분)": 10,
            }
        ]
    )

    result = find_repeat_issues(source)

    assert result.empty


def test_main_repeat_issues_prioritizes_customer_middle_part() -> None:
    source = pd.DataFrame(
        [
            {
                "*ID": 1,
                "접수일": pd.Timestamp("2026-01-01"),
                "고객사": "A",
                "대분류": "Robot",
                "중분류": "Motor",
                "소분류 (고장부품)": "Reducer",
                "로보트 기종": "M1",
                "라인 중단 시간 (분)": 10,
            },
            {
                "*ID": 2,
                "접수일": pd.Timestamp("2026-01-02"),
                "고객사": "A",
                "대분류": "Robot",
                "중분류": "Motor",
                "소분류 (고장부품)": "Reducer",
                "로보트 기종": "M2",
                "라인 중단 시간 (분)": 0,
            },
        ]
    )

    result = filter_main_repeat_issues(find_repeat_issues(source))

    assert not result.empty
    assert result.iloc[0]["반복 기준"] == "고객사 + 중분류 + 소분류 (고장부품)"
    assert result.iloc[0]["조건값"] == "고객사=A / 중분류=Motor / 소분류 (고장부품)=Reducer"


def test_main_repeat_issues_excludes_non_informative_middle_or_part() -> None:
    source = pd.DataFrame(
        [
            {
                "*ID": 1,
                "접수일": pd.Timestamp("2026-01-01"),
                "고객사": "A",
                "대분류": "Robot",
                "중분류": "기타",
                "소분류 (고장부품)": "Reducer",
                "라인 중단 시간 (분)": 10,
            },
            {
                "*ID": 2,
                "접수일": pd.Timestamp("2026-01-02"),
                "고객사": "A",
                "대분류": "Robot",
                "중분류": "기타",
                "소분류 (고장부품)": "Reducer",
                "라인 중단 시간 (분)": 0,
            },
            {
                "*ID": 3,
                "접수일": pd.Timestamp("2026-01-03"),
                "고객사": "B",
                "대분류": "Robot",
                "중분류": "Motor",
                "소분류 (고장부품)": "미입력",
                "라인 중단 시간 (분)": 0,
            },
            {
                "*ID": 4,
                "접수일": pd.Timestamp("2026-01-04"),
                "고객사": "B",
                "대분류": "Robot",
                "중분류": "Motor",
                "소분류 (고장부품)": "미입력",
                "라인 중단 시간 (분)": 0,
            },
        ]
    )

    result = filter_main_repeat_issues(find_repeat_issues(source))

    assert result.empty


def test_main_repeat_issues_excludes_non_informative_customer_but_excel_candidate_remains() -> None:
    source = pd.DataFrame(
        [
            {
                "*ID": 1,
                "접수일": pd.Timestamp("2026-01-01"),
                "고객사": "미입력",
                "대분류": "Robot",
                "중분류": "Motor",
                "소분류 (고장부품)": "Reducer",
                "라인 중단 시간 (분)": 10,
            },
            {
                "*ID": 2,
                "접수일": pd.Timestamp("2026-01-02"),
                "고객사": "미입력",
                "대분류": "Robot",
                "중분류": "Motor",
                "소분류 (고장부품)": "Reducer",
                "라인 중단 시간 (분)": 5,
            },
        ]
    )

    all_candidates = find_repeat_issues(source)
    main_candidates = filter_main_repeat_issues(all_candidates)

    assert not all_candidates.empty
    assert all_candidates.iloc[0]["조건값_품질"] in {"low_confidence", "data_quality_issue"}
    assert main_candidates.empty


def test_find_repeat_issues_displays_missing_values_when_partially_missing():
    source = pd.DataFrame(
        [
            {
                "*ID": 1,
                "접수일": pd.Timestamp("2025-01-01"),
                "고객사": "A",
                "대분류": "Robot",
                "중분류": pd.NA,
                "소분류 (고장부품)": "Reducer",
                "로보트 기종": pd.NA,
                "BOOTH": "B1",
                "LINE": "L1",
                "공정": "Weld",
                "라인 중단 시간 (분)": 10,
            },
            {
                "*ID": 2,
                "접수일": pd.Timestamp("2025-01-02"),
                "고객사": "A",
                "대분류": "Robot",
                "중분류": pd.NA,
                "소분류 (고장부품)": "Reducer",
                "로보트 기종": pd.NA,
                "BOOTH": "B1",
                "LINE": "L1",
                "공정": "Weld",
                "라인 중단 시간 (분)": 0,
            },
        ]
    )

    result = find_repeat_issues(source)
    row = result.loc[result["반복 기준"] == "고객사 + 대분류 + 중분류"].iloc[0]

    assert "중분류=미입력" in row["조건값"]


def test_find_repeat_issues_excludes_all_missing_combinations():
    source = pd.DataFrame(
        [
            {
                "*ID": 1,
                "접수일": pd.Timestamp("2025-01-01"),
                "고객사": pd.NA,
                "대분류": pd.NA,
                "중분류": pd.NA,
                "소분류 (고장부품)": pd.NA,
                "로보트 기종": pd.NA,
                "BOOTH": pd.NA,
                "LINE": pd.NA,
                "공정": pd.NA,
                "라인 중단 시간 (분)": 0,
            },
            {
                "*ID": 2,
                "접수일": pd.Timestamp("2025-01-02"),
                "고객사": pd.NA,
                "대분류": pd.NA,
                "중분류": pd.NA,
                "소분류 (고장부품)": pd.NA,
                "로보트 기종": pd.NA,
                "BOOTH": pd.NA,
                "LINE": pd.NA,
                "공정": pd.NA,
                "라인 중단 시간 (분)": 0,
            },
        ]
    )

    result = find_repeat_issues(source)

    assert result.empty
