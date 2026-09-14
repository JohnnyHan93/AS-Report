from __future__ import annotations

from typing import Any

import pandas as pd

MISSING_TOKENS = {"", "미입력", "미분류", "선택안함", "--", "-", "nan", "none", "null", "na", "n/a", "blank", "<na>"}
NON_INFORMATIVE_TOKENS = {*MISSING_TOKENS, "기타", "미확정", "해당없음", "없음"}


def format_repeat_condition_display(condition_value: str) -> str:
    """
    Convert a repeat condition string to a compact display value.

    Example:
    고객사=HMMME / 대분류=도장기 / 중분류=EVO -> HMMME 도장기 EVO
    """
    values: list[str] = []
    for segment in str(condition_value or "").split("/"):
        text = segment.strip()
        if not text:
            continue
        if "=" in text:
            text = text.split("=", 1)[1].strip()
        if text:
            values.append(text)
    return " ".join(values) if values else "미확인"


def evaluate_repeat_condition_quality(condition_value: str) -> str:
    values = _condition_values(condition_value)
    if not values:
        return "data_quality_issue"
    non_informative_count = sum(1 for value in values if is_non_informative_token(value))
    if non_informative_count == 0:
        return "normal"
    if non_informative_count >= 2 or non_informative_count >= len(values) / 2:
        return "data_quality_issue"
    return "low_confidence"


def format_count(value: Any) -> str:
    try:
        return f"{int(float(value)):,}건"
    except (TypeError, ValueError):
        return "0건"


def format_minutes(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0
    if number.is_integer():
        return f"{int(number):,}분"
    return f"{number:,.1f}분"


def format_percent(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0
    return f"{number:.1f}%"


def _condition_values(condition_value: str) -> list[str]:
    values = []
    for segment in str(condition_value or "").split("/"):
        text = segment.strip()
        if "=" in text:
            text = text.split("=", 1)[1].strip()
        if text:
            values.append(text)
    return values


def _is_missing_token(value: Any) -> bool:
    return is_non_informative_token(value, missing_only=True)


def is_non_informative_token(value: Any, missing_only: bool = False) -> bool:
    if value is None or pd.isna(value):
        return True
    text = str(value).strip()
    lowered = text.lower()
    tokens = MISSING_TOKENS if missing_only else NON_INFORMATIVE_TOKENS
    if lowered in tokens:
        return True
    return not missing_only and lowered.startswith("기타")
