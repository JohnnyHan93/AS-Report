from __future__ import annotations

from typing import Any

import pandas as pd

from .reporting.display_formatters import evaluate_repeat_condition_quality, format_repeat_condition_display, is_non_informative_token

DOWNTIME_COLUMN = "라인 중단 시간 (분)"
MISSING_LABEL = "미입력"
REPEAT_CRITERIA = [
    ("고객사 + 중분류 + 소분류 (고장부품)", ["고객사", "중분류", "소분류 (고장부품)"]),
    ("고객사 + 대분류 + 중분류 + 소분류 (고장부품)", ["고객사", "대분류", "중분류", "소분류 (고장부품)"]),
    ("고객사 + 로보트 기종 + 중분류 + 소분류 (고장부품)", ["고객사", "로보트 기종", "중분류", "소분류 (고장부품)"]),
    ("고객사 + 대분류 + 중분류", ["고객사", "대분류", "중분류"]),
    ("고객사 + 소분류 (고장부품)", ["고객사", "소분류 (고장부품)"]),
    ("고객사 + 로보트 기종 + 소분류 (고장부품)", ["고객사", "로보트 기종", "소분류 (고장부품)"]),
    ("BOOTH + LINE + 공정 + 대분류", ["BOOTH", "LINE", "공정", "대분류"]),
    ("로보트 기종 + 소분류 (고장부품)", ["로보트 기종", "소분류 (고장부품)"]),
]
REPEAT_COLUMNS = ["반복 기준", "조건값", "조건값_표시", "조건값_품질", "접수 건수", "라인 중단 총 시간", "최초 접수일", "최근 접수일", "관련 ID 목록"]
MAIN_REPEAT_BASE_CRITERION = "고객사 + 중분류 + 소분류 (고장부품)"


def find_repeat_issues(dataframe: pd.DataFrame, min_count: int = 2) -> pd.DataFrame:
    if dataframe.empty:
        return pd.DataFrame(columns=REPEAT_COLUMNS)

    rows: list[dict[str, Any]] = []
    for criterion_name, columns in REPEAT_CRITERIA:
        if not all(column in dataframe.columns for column in columns):
            continue
        working = _repeat_working_frame(dataframe, columns)
        for column in columns:
            working[column] = working[column].map(_display_value)
        working = working.loc[~working[columns].eq(MISSING_LABEL).all(axis=1)].copy()
        if working.empty:
            continue
        downtime = pd.to_numeric(working.get(DOWNTIME_COLUMN, pd.Series(index=working.index, dtype="float")), errors="coerce").fillna(0)
        working["_downtime"] = downtime
        working["_received_at"] = pd.to_datetime(working.get("접수일", pd.Series(index=working.index, dtype="datetime64[ns]")), errors="coerce")
        grouped = working.groupby(columns, dropna=False)
        for key, group in grouped:
            if len(group) < min_count:
                continue
            values = key if isinstance(key, tuple) else (key,)
            condition_value = " / ".join(f"{column}={value}" for column, value in zip(columns, values))
            rows.append(
                {
                    "반복 기준": criterion_name,
                    "조건값": condition_value,
                    "조건값_표시": format_repeat_condition_display(condition_value),
                    "조건값_품질": evaluate_repeat_condition_quality(condition_value),
                    "접수 건수": int(len(group)),
                    "라인 중단 총 시간": float(group["_downtime"].sum()),
                    "최초 접수일": _format_date(group["_received_at"].min()),
                    "최근 접수일": _format_date(group["_received_at"].max()),
                    "관련 ID 목록": _id_list(group),
                }
            )

    if not rows:
        return pd.DataFrame(columns=REPEAT_COLUMNS)
    result = pd.DataFrame(rows, columns=REPEAT_COLUMNS)
    result["_priority"] = result["반복 기준"].map(_criterion_priority)
    result = result.sort_values(["_priority", "접수 건수", "라인 중단 총 시간"], ascending=[True, False, False]).drop(columns=["_priority"])
    return result.reset_index(drop=True)


def filter_main_repeat_issues(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return repeat candidates suitable for the main HTML report."""
    if dataframe.empty:
        return dataframe
    working = dataframe.copy()
    if "반복 기준" not in working.columns or "조건값" not in working.columns:
        return working
    working = working.loc[working["반복 기준"] == MAIN_REPEAT_BASE_CRITERION].copy()
    if working.empty:
        return working
    mask = working["조건값"].map(_has_informative_customer_middle_and_part)
    return working.loc[mask].reset_index(drop=True)


def _repeat_working_frame(dataframe: pd.DataFrame, grouping_columns: list[str]) -> pd.DataFrame:
    optional_columns = [DOWNTIME_COLUMN, "접수일", "*ID"]
    selected_columns = [column for column in [*grouping_columns, *optional_columns] if column in dataframe.columns]
    return dataframe.loc[:, selected_columns].copy()


def _display_value(value: Any) -> str:
    if pd.isna(value) or str(value).strip() == "":
        return MISSING_LABEL
    return str(value).strip()


def _criterion_priority(criterion: str) -> int:
    if criterion == MAIN_REPEAT_BASE_CRITERION:
        return 0
    if "중분류" in criterion and "소분류" in criterion:
        return 1
    return 2


def _has_informative_customer_middle_and_part(condition_value: str) -> bool:
    values = _parse_condition_values(condition_value)
    return (
        _is_informative(values.get("고객사"))
        and _is_informative(values.get("중분류"))
        and _is_informative(values.get("소분류 (고장부품)"))
    )


def _parse_condition_values(condition_value: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for part in str(condition_value).split(" / "):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        parsed[key.strip()] = value.strip()
    return parsed


def _is_informative(value: Any) -> bool:
    return not is_non_informative_token(value)


def _format_date(value: Any) -> str:
    if pd.isna(value):
        return ""
    return pd.Timestamp(value).strftime("%Y-%m-%d")


def _id_list(group: pd.DataFrame) -> str:
    if "*ID" not in group.columns:
        return ""
    values = [str(value) for value in group["*ID"].dropna().tolist()]
    return ", ".join(values[:30])
