from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


def write_quality_summary_markdown(quality_result: dict[str, Any], output_dir: str | Path) -> str:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    markdown_path = output_path / f"raw_data_quality_summary_{timestamp}.md"

    summary = quality_result.get("summary", {})
    field_quality = quality_result.get("field_quality_df", pd.DataFrame())
    quality_flags = quality_result.get("quality_flags_df", pd.DataFrame())
    manual_review = quality_result.get("manual_review_targets_df", pd.DataFrame())

    content = "\n".join(
        [
            "# Raw Data Quality Summary",
            "",
            "## 1. 분석 기준",
            f"- Raw 데이터 파일: {summary.get('Raw 데이터 파일', '')}",
            f"- 접수일 범위: {summary.get('접수일 시작', '')} ~ {summary.get('접수일 종료', '')}",
            f"- 선택 기간 분석 대상 행 수: {summary.get('분석 대상 건수', 0):,}",
            f"- 품질 상태: {quality_result.get('status', '')}",
            "",
            "## 2. 전체 요약",
            f"- 전체 원본 행 수: {summary.get('전체 건수', 0):,}",
            f"- 선택 기간 분석 대상 행 수: {summary.get('분석 대상 건수', 0):,}",
            f"- 보완 필요 행 수: {summary.get('보완 필요 건수', 0):,}",
            f"- 정상 공백/조건부 제외 필드 플래그 수: {summary.get('조건부 제외 건수', 0):,}",
            f"- 우선순위 상: {summary.get('우선순위 상', 0):,}",
            f"- 우선순위 중: {summary.get('우선순위 중', 0):,}",
            f"- 우선순위 하: {summary.get('우선순위 하', 0):,}",
            "",
            "## 보고서 해석 주의",
            "- 보완 필요 행 수는 선택 기간 기준입니다.",
            "- 필드별 보완 건수는 하나의 행에 여러 필드가 포함될 수 있으므로 보완 필요 행 수보다 클 수 있습니다.",
            "- 조건부 제외는 유/무상, 제조사처럼 업무유형에 따라 입력 대상이 아닌 필드를 의미합니다.",
            "",
            "## 3. 필드별 품질 현황",
            _field_quality_markdown(field_quality),
            "",
            "## 4. 업무유형별 품질 현황",
            _count_table_markdown(quality_flags, "업무유형", "보완필요여부"),
            "",
            "## 5. 대상구분별 품질 현황",
            _count_table_markdown(quality_flags, "대상구분_정제", "보완필요여부"),
            "",
            "## 6. 수동 보완 우선 항목",
            _manual_review_markdown(manual_review),
            "",
            "## 7. 주의사항",
            "- 원본 CSV는 수정하지 않았습니다.",
            "- 자동추정 값은 확정값이 아니며 담당자 확인이 필요합니다.",
            "- 그룹웨어 검색은 ID 기준이 아니라 접수일과 접수내용 요약 검색어 중심으로 수행합니다.",
            "- 본 요약은 입력 데이터에서 계산 가능한 품질 후보만 표시합니다.",
            "",
        ]
    )
    markdown_path.write_text(content, encoding="utf-8")
    return str(markdown_path)


def _field_quality_markdown(dataframe: pd.DataFrame) -> str:
    if dataframe.empty:
        return "- 필드별 품질 데이터가 없습니다."
    top = dataframe.sort_values("실제 보완 필요 건수", ascending=False).head(20)
    lines = ["| 필드명 | 전체 공백/미확정 | 조건부 제외 | 실제 보완 필요 | 자동추정 가능 | 수동확인 필요 |", "|---|---:|---:|---:|---:|---:|"]
    for _, row in top.iterrows():
        lines.append(
            f"| {row['필드명']} | {int(row['전체 공백/미확정 건수']):,} | {int(row['조건부 제외 건수']):,} | {int(row['실제 보완 필요 건수']):,} | {int(row['자동추정 가능 건수']):,} | {int(row['수동확인 필요 건수']):,} |"
        )
    return "\n".join(lines)


def _count_table_markdown(dataframe: pd.DataFrame, group_column: str, flag_column: str) -> str:
    if dataframe.empty or group_column not in dataframe.columns or flag_column not in dataframe.columns:
        return "- 집계 데이터가 없습니다."
    grouped = dataframe.groupby(group_column, dropna=False)[flag_column].agg(전체="count", 보완필요=lambda series: int((series == "Y").sum())).reset_index()
    grouped = grouped.sort_values("전체", ascending=False).head(20)
    lines = [f"| {group_column} | 전체 건수 | 보완 필요 건수 |", "|---|---:|---:|"]
    for _, row in grouped.iterrows():
        lines.append(f"| {row[group_column]} | {int(row['전체']):,} | {int(row['보완필요']):,} |")
    return "\n".join(lines)


def _manual_review_markdown(dataframe: pd.DataFrame) -> str:
    if dataframe.empty:
        return "- 수동 보완 대상이 없습니다."
    top = dataframe.head(20)
    lines = ["| 우선순위 | 접수일 | 고객사 | 보완 필요 필드 | 검색어 |", "|---|---|---|---|---|"]
    for _, row in top.iterrows():
        received_at = row.get("접수일", "")
        if hasattr(received_at, "strftime"):
            received_at = received_at.strftime("%Y-%m-%d")
        lines.append(
            f"| {row.get('우선순위', '')} | {received_at} | {row.get('고객사', '')} | {row.get('보완 필요 필드', '')} | {row.get('접수내용 요약 검색어', '')} |"
        )
    return "\n".join(lines)
