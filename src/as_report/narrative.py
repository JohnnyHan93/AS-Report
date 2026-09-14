from __future__ import annotations

from typing import Any

import pandas as pd

from .reporting.display_formatters import evaluate_repeat_condition_quality, format_repeat_condition_display
from .repeat_issue import filter_main_repeat_issues


def build_narrative(analysis: dict[str, Any], period_label: str, start_date: str, end_date: str) -> list[str]:
    kpi = analysis["kpi"]
    tables = analysis["tables"]

    if kpi["총 접수 건수"] == 0:
        return ["분석 대상 기간에 접수된 이슈가 없습니다."]

    lines = [
        f"총 A/S 접수는 {kpi['총 접수 건수']}건이며, 처리완료는 {kpi['처리완료 건수']}건입니다.",
    ]

    comparison_line = _comparison_line(analysis.get("comparison"))
    if comparison_line:
        lines.append(comparison_line)

    monthly_top = _top_label(tables.get("월별 접수 건수"), "기간_연월", "접수 건수")
    if monthly_top:
        lines.append(f"월별 접수는 {monthly_top[0]}에 {monthly_top[1]}건으로 가장 많았습니다.")

    top_customer = _top_label(tables.get("고객사별 접수 건수 TOP 20"), "고객사", "접수 건수")
    if top_customer:
        lines.append(f"고객사별 접수 건수가 가장 많은 곳은 {top_customer[0]}으로 {top_customer[1]}건입니다.")

    top_work_type = _top_label(tables.get("업무유형구분별 접수 건수"), "업무유형구분", "접수 건수")
    if top_work_type:
        lines.append(f"업무유형 기준으로는 {top_work_type[0]}이 {top_work_type[1]}건으로 가장 많았습니다.")

    repeat_line = _repeat_issue_line(analysis.get("repeat_issues"))
    if repeat_line:
        lines.append(repeat_line)

    lines.append("라인 중단 시간은 입력된 건 기준의 참고값이며, 미입력 건은 0분으로 간주하지 않았습니다.")

    return lines[:7]


def build_quality_notes(quality: dict[str, Any]) -> list[str]:
    notes = [
        "고객사 분석은 고객사명이 입력된 건을 기준으로 산출하였으며, 고객사 미입력 건은 미분류 항목으로 별도 집계했습니다.",
        "라인 중단 시간 분석은 입력된 건 기준의 참고값이며, 미입력 건은 0분으로 간주하지 않았습니다.",
    ]
    if quality.get("대분류 미입력 건수", 0) or quality.get("중분류 미입력 건수", 0) or quality.get("소분류 미입력 건수", 0):
        notes.append("대분류/중분류/소분류 미입력 건이 있을 경우 장비군 분석 결과 해석에 주의가 필요합니다.")
    return notes


def _top_label(dataframe: pd.DataFrame | None, label_column: str, value_column: str) -> tuple[str, int] | None:
    if dataframe is None or dataframe.empty or label_column not in dataframe.columns or value_column not in dataframe.columns:
        return None
    row = dataframe.sort_values(value_column, ascending=False).iloc[0]
    label = str(row[label_column])
    if label == "미분류":
        return None
    return label, int(row[value_column])


def _comparison_line(dataframe: pd.DataFrame | None) -> str | None:
    if dataframe is None or dataframe.empty or "항목" not in dataframe.columns:
        return None
    row = dataframe.loc[dataframe["항목"] == "총 접수 건수"]
    if row.empty:
        return None
    record = row.iloc[0]
    previous_year_delta = record.get("전년 동기 대비 증감", "-")
    previous_year_rate = record.get("전년 동기 대비 증감률", "-")
    previous_period_delta = record.get("직전 기간 대비 증감", "-")
    previous_period_rate = record.get("직전 기간 대비 증감률", "-")
    comparison_mode = record.get("비교 방식", "")

    parts = []
    if previous_year_delta != "-":
        label = "전년 동일 기간(YTD) 대비" if comparison_mode == "YTD" else "전년 동기 대비"
        parts.append(f"{label} {previous_year_delta:+g}건({previous_year_rate})")
    if previous_period_delta != "-":
        parts.append(f"직전 기간 대비 {previous_period_delta:+g}건({previous_period_rate})")
    if not parts:
        return None
    return "총 접수 건수는 " + ", ".join(parts) + " 변동했습니다."


def _repeat_issue_line(dataframe: pd.DataFrame | None) -> str | None:
    if dataframe is None or dataframe.empty:
        return None
    required = {"반복 기준", "조건값", "접수 건수"}
    if not required.issubset(dataframe.columns):
        return None
    working = filter_main_repeat_issues(dataframe)
    if working.empty:
        return "반복 이슈 후보는 동일 고객사 중분류/소분류 조합 기준으로 산출했으며, 메인 표에 표시할 정보성 후보가 없습니다."
    if "조건값_표시" not in working.columns:
        working["조건값_표시"] = working["조건값"].map(format_repeat_condition_display)
    if "조건값_품질" not in working.columns:
        working["조건값_품질"] = working["조건값"].map(evaluate_repeat_condition_quality)
    meaningful = working.loc[working["조건값_품질"].isin(["normal", "low_confidence"])].copy()
    if meaningful.empty:
        return f"반복 이슈 후보는 동일 고객사 중분류/소분류 조합 기준 총 {len(working)}건이며, 원인 확정이 아닌 검토 후보입니다."
    row = meaningful.iloc[0]
    if row["조건값_품질"] == "low_confidence":
        return f"반복 이슈 후보는 동일 고객사 중분류/소분류 조합 기준 총 {len(working)}건이며, 주요 후보는 {row['조건값_표시']} 기준 {int(row['접수 건수'])}건입니다."
    return f"반복 이슈 후보는 동일 고객사 중분류/소분류 조합 기준 총 {len(working)}건이며, 주요 후보는 {row['조건값_표시']} 기준 {int(row['접수 건수'])}건입니다."
