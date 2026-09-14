from __future__ import annotations

from typing import Any

import pandas as pd

MISSING_LABEL = "미입력"
CLAIM_WORK_TYPE_TOKEN = "부품수리/클레임처리"

ISSUE_PREVIEW_COLUMNS = [
    ("접수일", "접수일"),
    ("고객사", "고객사"),
    ("BOOTH", "BOOTH"),
    ("LINE", "LINE"),
    ("공정", "공정"),
    ("ZONE", "ZONE"),
    ("로보트 NO", "로보트 NO"),
    ("업무유형", "업무유형"),
    ("대분류", "대분류"),
    ("중분류", "중분류"),
    ("소분류 (고장부품)", "소분류 (고장부품)"),
    ("접수 내용 (요약)", "접수내용"),
    ("처리내용/진행상황 (요약)", "조치이력"),
]


def build_quality_feedback_candidates(dataframe: pd.DataFrame) -> dict[str, Any]:
    """Build AS27 review-candidate outputs from existing report-period data."""
    claim_rows = _claim_rows(dataframe)
    missing_field_candidates = _missing_field_candidates(claim_rows)
    claim_candidates = _claim_manufacturer_candidates(claim_rows)
    part_candidates = _part_category_candidates(dataframe)
    issue_preview = _issue_preview(claim_rows, missing_field_candidates, part_candidates)
    type_summary = _candidate_type_summary(claim_rows, missing_field_candidates, part_candidates)
    summary = _summary_frame(claim_rows, missing_field_candidates, part_candidates, issue_preview)
    return {
        "quality_feedback_summary": summary,
        "quality_feedback_by_candidate_type": type_summary,
        "quality_feedback_claim_candidates": claim_candidates,
        "quality_feedback_missing_field_candidates": missing_field_candidates,
        "quality_feedback_part_category_candidates": part_candidates,
        "quality_feedback_issue_preview": issue_preview,
        "quality_feedback_note": "입력값 기준으로 추가 확인이 필요한 후보를 모은 참고 섹션입니다. 표시 항목은 확정 판단이 아닙니다.",
    }


def _claim_rows(dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataframe.empty or "업무유형" not in dataframe.columns:
        return dataframe.iloc[0:0].copy()
    work_type = dataframe["업무유형"].fillna("").astype(str)
    return dataframe.loc[work_type.str.contains(CLAIM_WORK_TYPE_TOKEN, regex=False, na=False)].copy()


def _claim_manufacturer_candidates(dataframe: pd.DataFrame) -> pd.DataFrame:
    columns = ["제조사", "유/무상", "대분류", "중분류", "소분류 (고장부품)"]
    output_columns = columns + ["접수 건수", "입력 상태", "검토 메모"]
    if dataframe.empty:
        return pd.DataFrame(columns=output_columns)
    working = pd.DataFrame({column: _display_series(dataframe, column) for column in columns})
    result = working.groupby(columns, dropna=False).size().reset_index(name="접수 건수")
    result["입력 상태"] = result.apply(_claim_input_status, axis=1)
    result["검토 메모"] = "업무유형 입력값 기준 검토 후보"
    return result.sort_values(["접수 건수", "제조사"], ascending=[False, True]).reset_index(drop=True)


def _missing_field_candidates(dataframe: pd.DataFrame) -> pd.DataFrame:
    output_columns = [
        "접수일",
        "고객사",
        "BOOTH",
        "LINE",
        "공정",
        "ZONE",
        "로보트 NO",
        "업무유형",
        "유/무상",
        "제조사",
        "미입력 항목",
        "검토 메모",
    ]
    if dataframe.empty:
        return pd.DataFrame(columns=output_columns)
    rows = []
    for _, record in dataframe.iterrows():
        missing_fields = []
        for column in ["유/무상", "제조사"]:
            if _display_value(record.get(column)) == MISSING_LABEL:
                missing_fields.append(column)
        if not missing_fields:
            continue
        row = {column: _display_value(record.get(column)) for column in output_columns if column not in {"미입력 항목", "검토 메모"}}
        row["미입력 항목"] = ", ".join(missing_fields)
        row["검토 메모"] = "Raw 보완 또는 추가 확인 후보"
        rows.append(row)
    return pd.DataFrame(rows, columns=output_columns)


def _part_category_candidates(dataframe: pd.DataFrame) -> pd.DataFrame:
    columns = ["대분류", "중분류", "소분류 (고장부품)"]
    output_columns = columns + ["접수 건수", "검토 메모"]
    if dataframe.empty:
        return pd.DataFrame(columns=output_columns)
    working = pd.DataFrame({column: _display_series(dataframe, column) for column in columns})
    result = working.groupby(columns, dropna=False).size().reset_index(name="접수 건수")
    result = result.sort_values("접수 건수", ascending=False).head(20).reset_index(drop=True)
    result["검토 메모"] = "부품/분류별 접수 현황 검토 후보"
    return result.loc[:, output_columns]


def _issue_preview(claim_rows: pd.DataFrame, missing_rows: pd.DataFrame, part_candidates: pd.DataFrame) -> pd.DataFrame:
    output_columns = [label for _, label in ISSUE_PREVIEW_COLUMNS] + ["검토 후보 유형"]
    if claim_rows.empty:
        return pd.DataFrame(columns=output_columns)

    missing_index = set(missing_rows.index.tolist()) if not missing_rows.empty else set()
    top_parts = set()
    if not part_candidates.empty:
        for _, row in part_candidates.head(5).iterrows():
            top_parts.add((row.get("대분류"), row.get("중분류"), row.get("소분류 (고장부품)")))

    rows = []
    for index, record in claim_rows.head(50).iterrows():
        candidate_types = ["클레임/제조사 입력 검토"]
        if index in missing_index or any(_display_value(record.get(column)) == MISSING_LABEL for column in ["유/무상", "제조사"]):
            candidate_types.append("유/무상/제조사 미입력 검토")
        part_key = tuple(_display_value(record.get(column)) for column in ["대분류", "중분류", "소분류 (고장부품)"])
        if part_key in top_parts:
            candidate_types.append("부품/분류별 접수 검토")
        row = {label: _display_value(record.get(source)) for source, label in ISSUE_PREVIEW_COLUMNS}
        row["검토 후보 유형"] = " / ".join(candidate_types)
        rows.append(row)
    return pd.DataFrame(rows, columns=output_columns)


def _candidate_type_summary(claim_rows: pd.DataFrame, missing_rows: pd.DataFrame, part_candidates: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {"검토 후보 유형": "클레임/제조사 입력 검토", "관련 건수": int(len(claim_rows)), "비고": "업무유형 입력값 기준"},
        {"검토 후보 유형": "유/무상/제조사 미입력 검토", "관련 건수": int(len(missing_rows)), "비고": "Raw 보완 또는 추가 확인 후보"},
        {"검토 후보 유형": "부품/분류별 접수 검토", "관련 건수": int(part_candidates["접수 건수"].sum()) if "접수 건수" in part_candidates.columns else 0, "비고": "상위 분류 입력값 기준"},
    ]
    return pd.DataFrame(rows)


def _summary_frame(claim_rows: pd.DataFrame, missing_rows: pd.DataFrame, part_candidates: pd.DataFrame, issue_preview: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {"항목": "클레임/제조사 입력 검토 후보", "값": int(len(claim_rows)), "비고": "업무유형 입력값 기준"},
        {"항목": "유/무상/제조사 미입력 검토 후보", "값": int(len(missing_rows)), "비고": "Raw 보완 또는 추가 확인 후보"},
        {"항목": "부품/분류별 접수 검토 후보", "값": int(len(part_candidates)), "비고": "상위 분류 조합 기준"},
        {"항목": "이슈 preview 행 수", "값": int(len(issue_preview)), "비고": "상세 확인용"},
    ]
    return pd.DataFrame(rows)


def _claim_input_status(row: pd.Series) -> str:
    missing = [column for column in ["제조사", "유/무상"] if _display_value(row.get(column)) == MISSING_LABEL]
    return "입력 확인 필요: " + ", ".join(missing) if missing else "입력값 있음"


def _display_series(dataframe: pd.DataFrame, column: str) -> pd.Series:
    if column not in dataframe.columns:
        return pd.Series(MISSING_LABEL, index=dataframe.index, dtype="object")
    return dataframe[column].map(_display_value)


def _display_value(value: Any) -> str:
    if value is None or pd.isna(value):
        return MISSING_LABEL
    text = str(value).strip()
    if text in {"", "선택안함", "--", "#NAME?", "nan", "None", "NaN", "<NA>"}:
        return MISSING_LABEL
    return text
