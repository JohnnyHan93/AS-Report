from __future__ import annotations

import pandas as pd

from as_report.master import build_master_analysis_result, export_master_analysis_outputs, match_as_to_robot_master, validate_failure_part_categories


def _robot_master() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "*ID": "M1",
                "설치연도(Installation year)": "2025",
                "고객사(Customer)": "A",
                "위치(Location)": "화성",
                "공장(plant)": "1공장",
                "BOOTH": "상도",
                "LINE": "1 Line",
                "ZONE": "1 ZONE",
                "Robot No": "R1",
                "공정-대분류 (major category)": "도장",
                "공정-중분류 (middle category)": "상도",
                "컨트롤러(Controller)": "YRC1000",
            },
            {
                "*ID": "M2",
                "설치연도(Installation year)": "2024",
                "고객사(Customer)": "A",
                "위치(Location)": "화성",
                "공장(plant)": "1공장",
                "BOOTH": "상도",
                "LINE": "2 Line",
                "ZONE": "1 ZONE",
                "Robot No": "R2",
                "공정-대분류 (major category)": "도장",
                "공정-중분류 (middle category)": "상도",
                "컨트롤러(Controller)": "YRC1000",
            },
        ]
    )


def _failure_master() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"*ID": "P1", "제조사": "Maker", "품명": "OS카드", "중분류": "컨트롤러", "대분류": "로보트", "검색용": "OS카드"},
            {"*ID": "P2", "제조사": "Maker", "품명": "EVO", "중분류": "EVO", "대분류": "도장기", "검색용": "EVO"},
        ]
    )


def test_robot_matching_levels() -> None:
    as_df = pd.DataFrame(
        [
            {"접수일": "2026-01-01", "고객사": "A", "BOOTH": "상도", "LINE": "1 Line", "로보트 NO": "R1"},
            {"접수일": "2026-01-02", "고객사": "A", "BOOTH": "하도", "LINE": "9 Line", "로보트 NO": "R2"},
            {"접수일": "2026-01-03", "고객사": "A", "BOOTH": "상도", "LINE": "1 Line", "로보트 NO": ""},
            {"접수일": "2026-01-04", "고객사": "B", "BOOTH": "상도", "LINE": "1 Line", "로보트 NO": "R1"},
        ]
    )

    result = match_as_to_robot_master(as_df, _robot_master())

    assert result.loc[0, "match_level"] == "exact_robot"
    assert result.loc[1, "match_level"] == "customer_robot"
    assert result.loc[2, "match_level"] == "location_only"
    assert result.loc[3, "match_level"] == "unmatched"


def test_failure_part_category_validation_cases() -> None:
    as_df = pd.DataFrame(
        [
            {"접수일": "2026-01-01", "고객사": "A", "대분류": "로보트", "중분류": "컨트롤러", "소분류 (고장부품)": "OS카드"},
            {"접수일": "2026-01-02", "고객사": "A", "대분류": "", "중분류": "", "소분류 (고장부품)": "EVO"},
            {"접수일": "2026-01-03", "고객사": "A", "대분류": "로보트", "중분류": "컨트롤러", "소분류 (고장부품)": ""},
            {"접수일": "2026-01-04", "고객사": "A", "대분류": "도장기", "중분류": "컨트롤러", "소분류 (고장부품)": "OS카드"},
        ]
    )

    result = validate_failure_part_categories(as_df, _failure_master())

    assert result.loc[0, "category_validity"] == "valid"
    assert result.loc[0, "recommendation_confidence"] == "high"
    assert result.loc[1, "category_validity"] == "valid"
    assert result.loc[1, "recommendation_confidence"] == "medium"
    assert result.loc[2, "category_validity"] == "missing_category"
    assert result.loc[3, "category_validity"] == "invalid_combination"


def test_master_analysis_builds_rate_outputs() -> None:
    as_df = pd.DataFrame(
        [
            {"접수일": "2026-01-01", "고객사": "A", "BOOTH": "상도", "LINE": "1 Line", "로보트 NO": "R1", "대분류": "로보트", "중분류": "컨트롤러", "소분류 (고장부품)": "OS카드"},
            {"접수일": "2026-01-02", "고객사": "A", "BOOTH": "상도", "LINE": "2 Line", "로보트 NO": "R2", "대분류": "", "중분류": "", "소분류 (고장부품)": ""},
        ]
    )

    result = build_master_analysis_result(as_df, _robot_master(), _failure_master())

    assert result["summary"]["고장성 AS 행 수"] == 1
    assert result["customer_as_rate_df"].loc[0, "설치 로봇 수"] == 2
    assert result["customer_as_rate_df"].loc[0, "고장성 AS 접수 건수"] == 1


def test_master_exporter_creates_expected_files(tmp_path) -> None:
    as_df = pd.DataFrame(
        [
            {"접수일": "2026-01-01", "고객사": "A", "BOOTH": "상도", "LINE": "1 Line", "로보트 NO": "R1", "대분류": "로보트", "중분류": "컨트롤러", "소분류 (고장부품)": "OS카드"},
        ]
    )
    result = build_master_analysis_result(as_df, _robot_master(), _failure_master())

    paths = export_master_analysis_outputs(result, tmp_path, timestamp="20260619_120000")

    assert paths["as_robot_match_preview"].exists()
    assert paths["unmatched_as_issues"].exists()
    assert paths["customer_as_rate_summary"].exists()
    assert paths["failure_part_trend"].exists()
