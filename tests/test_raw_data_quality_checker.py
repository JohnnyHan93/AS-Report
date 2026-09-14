from __future__ import annotations

import pandas as pd

from as_report.quality import analyze_raw_data_quality, export_manual_review_workbook, write_quality_summary_markdown


def _base_row(**updates):
    row = {
        "*ID": 1,
        "접수일": "2026-01-10",
        "업무유형": "A/S대응(일반 방문)",
        "접수사원": "담당자",
        "접수 내용 (요약)": "기아 화성 R4 로보트 알람 발생",
        "처리내용/진행상황 (요약)": "",
        "고객사": "기아 화성",
        "BOOTH": "B1",
        "LINE": "L1",
        "공정": "도장",
        "로보트 NO": "R4",
        "로보트 기종": "MPX3500",
        "고장원인": "알람",
        "라인 중단 시간 (분)": "10",
        "설치년도": "2020",
        "대분류": "로보트",
        "중분류": "본체",
        "소분류 (고장부품)": "서보모터",
        "유/무상": pd.NA,
        "제조사": pd.NA,
    }
    row.update(updates)
    return row


def test_empty_dataframe_is_blocked():
    result = analyze_raw_data_quality(pd.DataFrame())

    assert result["status"] == "BLOCKED"
    assert result["summary"]["보완 필요 건수"] == 0


def test_missing_received_date_column_is_blocked():
    result = analyze_raw_data_quality(pd.DataFrame([{"고객사": "A"}]))

    assert result["status"] == "BLOCKED"
    assert "접수일" in result["summary"]["blocked_reason"]


def test_conditional_paid_and_manufacturer_fields_apply_only_to_part_repair():
    dataframe = pd.DataFrame(
        [
            _base_row(**{"*ID": 1, "업무유형": "A/S대응(일반 방문)", "유/무상": pd.NA, "제조사": pd.NA}),
            _base_row(**{"*ID": 2, "업무유형": "A/S대응(부품수리/클레임처리)", "유/무상": pd.NA, "제조사": pd.NA}),
        ]
    )

    result = analyze_raw_data_quality(dataframe, start_date="2026-01-01", end_date="2026-12-31")
    flags = result["quality_flags_df"].sort_values("*ID")

    normal_visit = flags.iloc[0]
    part_repair = flags.iloc[1]
    assert "유/무상" in normal_visit["조건부입력_제외필드"]
    assert "제조사" in normal_visit["조건부입력_제외필드"]
    assert "유/무상" in part_repair["보완필요필드"]
    assert "제조사" in part_repair["보완필요필드"]


def test_robot_keyword_auto_guess_and_missing_markers_are_flagged():
    dataframe = pd.DataFrame(
        [
            _base_row(
                고객사="선택안함",
                **{
                    "로보트 NO": pd.NA,
                    "로보트 기종": pd.NA,
                    "접수 내용 (요약)": "기아 광명 R4 로보트 정지 알람",
                    "라인 중단 시간 (분)": pd.NA,
                },
            )
        ]
    )

    result = analyze_raw_data_quality(dataframe, start_date="2026-01-01", end_date="2026-12-31")
    row = result["quality_flags_df"].iloc[0]

    assert row["보완필요여부"] == "Y"
    assert row["고객사_정제"].startswith("추천후보:")
    assert row["로보트대상수_정제"] == "1대"
    assert row["로봇기종_정제"] == "미입력/검토 필요"
    assert "고객사" in row["보완필요필드"]
    assert "로보트 NO" in row["보완필요필드"]
    assert "라인 중단 시간 (분)" in row["보완필요필드"]
    assert "자동추정" in row["보완방법"]


def test_quality_analysis_does_not_mutate_source_dataframe():
    dataframe = pd.DataFrame([_base_row()])
    before = dataframe.copy(deep=True)

    analyze_raw_data_quality(dataframe, start_date="2026-01-01", end_date="2026-12-31")

    pd.testing.assert_frame_equal(dataframe, before)


def test_quality_export_files_are_created(tmp_path):
    dataframe = pd.DataFrame([_base_row(고객사=pd.NA)])
    result = analyze_raw_data_quality(dataframe, start_date="2026-01-01", end_date="2026-12-31")

    excel_path = export_manual_review_workbook(result, tmp_path)
    markdown_path = write_quality_summary_markdown(result, tmp_path)

    assert excel_path.endswith(".xlsx")
    assert markdown_path.endswith(".md")
