from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from .raw_data_quality_rules import (
    BASE_REVIEW_FIELDS,
    CONDITIONAL_FIELDS,
    DATE_COLUMN,
    DETAIL_REQUIRED_MARKERS,
    DOWNTIME_COLUMN,
    ERROR_MARKERS,
    ID_COLUMN,
    MANUAL_REVIEW_COLUMNS,
    MISSING_MARKERS,
    PART_REPAIR_WORK_TYPE,
    QUALITY_COLUMNS,
    TARGET_TYPES,
    TRACE_COLUMNS,
)


def analyze_raw_data_quality(
    df: pd.DataFrame,
    source_path: str | Path | None = None,
    start_date: str | pd.Timestamp | None = None,
    end_date: str | pd.Timestamp | None = None,
) -> dict[str, Any]:
    source_name = Path(source_path).name if source_path else ""
    empty_result = _empty_result(source_name, start_date, end_date)

    if df.empty:
        empty_result["summary"]["blocked_reason"] = "데이터가 0건입니다."
        return empty_result
    if DATE_COLUMN not in df.columns:
        empty_result["summary"]["blocked_reason"] = f"{DATE_COLUMN} 컬럼이 없습니다."
        return empty_result

    working = df.copy(deep=True)
    received_at = pd.to_datetime(working[DATE_COLUMN], errors="coerce")
    if received_at.notna().mean() < 0.5:
        empty_result["summary"]["blocked_reason"] = f"{DATE_COLUMN} 파싱 실패가 과반입니다."
        return empty_result

    mask = received_at.notna()
    if start_date is not None:
        mask &= received_at >= pd.Timestamp(start_date)
    if end_date is not None:
        mask &= received_at <= pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
    working = working.loc[mask].copy()
    working[DATE_COLUMN] = received_at.loc[mask]

    if working.empty:
        empty_result["summary"]["blocked_reason"] = "선택 기간에 해당하는 데이터가 0건입니다."
        return empty_result

    quality_rows = [_build_quality_row(row) for _, row in working.iterrows()]
    quality_frame = pd.DataFrame(quality_rows, index=working.index)
    quality_flags_df = pd.concat([working.reset_index(drop=True), quality_frame.reset_index(drop=True)], axis=1)
    manual_review_targets_df = _manual_review_targets(quality_flags_df)
    conditional_field_df = _conditional_field_frame(quality_flags_df)
    field_quality_df = _field_quality_frame(quality_flags_df)
    summary = _summary(
        source_name=source_name,
        source_path=str(source_path) if source_path else "",
        start_date=start_date,
        end_date=end_date,
        source_count=len(df),
        analyzed_count=len(quality_flags_df),
        quality_flags_df=quality_flags_df,
        manual_review_targets_df=manual_review_targets_df,
        conditional_field_df=conditional_field_df,
        field_quality_df=field_quality_df,
    )
    status = "WARNING" if summary["보완 필요 건수"] or summary["조건부 제외 건수"] or summary["오류값 건수"] else "PASS"
    return {
        "status": status,
        "summary": summary,
        "quality_flags_df": quality_flags_df,
        "manual_review_targets_df": manual_review_targets_df,
        "field_quality_df": field_quality_df,
        "conditional_field_df": conditional_field_df,
    }


def _empty_result(source_name: str, start_date: Any, end_date: Any) -> dict[str, Any]:
    summary = {
        "Raw 데이터 파일": source_name,
        "접수일 시작": _date_text(start_date),
        "접수일 종료": _date_text(end_date),
        "전체 건수": 0,
        "분석 대상 건수": 0,
        "보완 필요 건수": 0,
        "우선순위 상": 0,
        "우선순위 중": 0,
        "우선순위 하": 0,
        "조건부 제외 건수": 0,
        "오류값 건수": 0,
        "blocked_reason": "",
    }
    return {
        "status": "BLOCKED",
        "summary": summary,
        "quality_flags_df": pd.DataFrame(columns=QUALITY_COLUMNS),
        "manual_review_targets_df": pd.DataFrame(columns=MANUAL_REVIEW_COLUMNS),
        "field_quality_df": pd.DataFrame(),
        "conditional_field_df": pd.DataFrame(),
    }


def _build_quality_row(row: pd.Series) -> dict[str, Any]:
    text = _row_text(row)
    target_type = _classify_target(row, text)
    excluded_fields = _conditional_excluded_fields(row)
    missing_fields, reasons, auto_fields = _review_fields(row, target_type, text, excluded_fields)
    priority = _priority(missing_fields, target_type, text)
    method = _completion_method(missing_fields, auto_fields)

    return {
        "대상구분_정제": target_type,
        "고객사_정제": _cleaned_customer(row, text),
        "위치상태_정제": _location_status(row),
        "로보트대상수_정제": _robot_target_count(row, text, target_type),
        "로봇기종_정제": _robot_model_status(row, target_type),
        "분류상태_정제": _category_status(row),
        "조건부입력_제외필드": ", ".join(excluded_fields),
        "보완필요필드": ", ".join(missing_fields),
        "보완방법": method,
        "보완난이도": _difficulty(priority),
        "보완필요여부": "Y" if missing_fields else "N",
        "보완우선순위": priority if missing_fields else "-",
        "보완메모": "; ".join(reasons) if reasons else "보완 필요 항목 없음",
        "추천검색방법": _search_method(row, text),
        "접수내용_요약검색어": _keywords(text),
    }


def _review_fields(row: pd.Series, target_type: str, text: str, excluded_fields: list[str]) -> tuple[list[str], list[str], list[str]]:
    fields: list[str] = []
    reasons: list[str] = []
    auto_fields: list[str] = []

    for field in BASE_REVIEW_FIELDS:
        if field in excluded_fields:
            continue
        if field == DOWNTIME_COLUMN and not _line_impact_text(text):
            continue
        if field in {"로보트 NO", "로보트 기종"} and target_type not in {"단일로보트", "다중로보트"}:
            continue
        if _needs_review(row.get(field)):
            fields.append(field)
            reasons.append(f"{field} 보완 필요")
            if _auto_guess_possible(field, text):
                auto_fields.append(field)

    for field in CONDITIONAL_FIELDS:
        if field in excluded_fields:
            continue
        if _needs_review(row.get(field)):
            fields.append(field)
            reasons.append(f"{PART_REPAIR_WORK_TYPE} 조건에서 {field} 보완 필요")

    return fields, reasons, auto_fields


def _conditional_excluded_fields(row: pd.Series) -> list[str]:
    work_type = _text(row.get("업무유형"))
    if work_type == PART_REPAIR_WORK_TYPE:
        return []
    return [field for field in CONDITIONAL_FIELDS if _is_blank(row.get(field))]


def _field_quality_frame(quality_flags_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    fields = [*BASE_REVIEW_FIELDS, *CONDITIONAL_FIELDS]
    for field in fields:
        if field not in quality_flags_df.columns:
            continue
        missing_count = int(quality_flags_df[field].map(_needs_review).sum())
        excluded_count = int(quality_flags_df["조건부입력_제외필드"].map(lambda value: _list_contains(value, field)).sum())
        required_count = int(quality_flags_df["보완필요필드"].map(lambda value: _list_contains(value, field)).sum())
        auto_values = quality_flags_df.loc[quality_flags_df["보완방법"].str.contains("자동추정", na=False), "보완필요필드"]
        auto_count = sum(1 for value in auto_values if _list_contains(value, field))
        rows.append(
            {
                "필드명": field,
                "전체 공백/미확정 건수": missing_count,
                "조건부 제외 건수": excluded_count,
                "실제 보완 필요 건수": required_count,
                "자동추정 가능 건수": auto_count,
                "수동확인 필요 건수": max(required_count - auto_count, 0),
            }
        )
    return pd.DataFrame(rows)


def _manual_review_targets(quality_flags_df: pd.DataFrame) -> pd.DataFrame:
    targets = quality_flags_df.loc[quality_flags_df["보완필요여부"] == "Y"].copy()
    if targets.empty:
        return pd.DataFrame(columns=MANUAL_REVIEW_COLUMNS)
    result = pd.DataFrame(
        {
            "추천 검색방법": targets["추천검색방법"],
            DATE_COLUMN: targets[DATE_COLUMN],
            "고객사": targets.get("고객사", ""),
            "업무유형": targets.get("업무유형", ""),
            "접수사원": targets.get("접수사원", ""),
            ID_COLUMN: targets.get(ID_COLUMN, ""),
            "보완 필요 필드": targets["보완필요필드"],
            "보완 판단 사유": targets["보완메모"],
            "우선순위": targets["보완우선순위"],
            "접수내용 요약 검색어": targets["접수내용_요약검색어"],
            "참고용 원본ID": targets.get(ID_COLUMN, ""),
        }
    )
    order = {"상": 0, "중": 1, "하": 2, "-": 3}
    result["_order"] = result["우선순위"].map(order).fillna(9)
    result = result.sort_values(["_order", DATE_COLUMN], ascending=[True, False]).drop(columns=["_order"])
    return result.reset_index(drop=True)


def _conditional_field_frame(quality_flags_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in quality_flags_df.iterrows():
        excluded = _split_list(row.get("조건부입력_제외필드"))
        for field in excluded:
            rows.append(
                {
                    ID_COLUMN: row.get(ID_COLUMN, ""),
                    DATE_COLUMN: row.get(DATE_COLUMN, ""),
                    "업무유형": row.get("업무유형", ""),
                    "제외 필드": field,
                    "제외 사유": f"{PART_REPAIR_WORK_TYPE} 외 업무유형의 정상 공백",
                }
            )
    return pd.DataFrame(rows)


def _summary(
    source_name: str,
    source_path: str,
    start_date: Any,
    end_date: Any,
    source_count: int,
    analyzed_count: int,
    quality_flags_df: pd.DataFrame,
    manual_review_targets_df: pd.DataFrame,
    conditional_field_df: pd.DataFrame,
    field_quality_df: pd.DataFrame,
) -> dict[str, Any]:
    priority_counts = quality_flags_df["보완우선순위"].value_counts()
    error_count = int(quality_flags_df.map(lambda value: _text(value) in ERROR_MARKERS).sum().sum())
    return {
        "Raw 데이터 파일": source_name,
        "Raw 데이터 경로": source_path,
        "접수일 시작": _date_text(start_date),
        "접수일 종료": _date_text(end_date),
        "전체 건수": int(source_count),
        "분석 대상 건수": int(analyzed_count),
        "보완 필요 건수": int(len(manual_review_targets_df)),
        "우선순위 상": int(priority_counts.get("상", 0)),
        "우선순위 중": int(priority_counts.get("중", 0)),
        "우선순위 하": int(priority_counts.get("하", 0)),
        "조건부 제외 건수": int(len(conditional_field_df)),
        "오류값 건수": error_count,
        "필드별 품질 항목 수": int(len(field_quality_df)),
    }


def _classify_target(row: pd.Series, text: str) -> str:
    work_type = _text(row.get("업무유형"))
    robot_count = _robot_token_count(_text(row.get("로보트 NO")) or text)
    category_text = " ".join(_text(row.get(column)) for column in ["대분류", "중분류", "소분류 (고장부품)"])

    if "VOC" in work_type.upper() or "고객문의" in text:
        return "고객문의_VOC"
    if "교육" in text or "테스트" in text:
        return "기타_교육_테스트_미확정"
    if "부품수리" in work_type or "클레임" in work_type or "설치" in work_type or "개선" in work_type:
        return "부품수리_클레임_설치_시운전_개선"
    if _line_impact_text(text) and robot_count == 0:
        return "라인전체"
    if robot_count >= 2:
        return "다중로보트"
    if robot_count == 1:
        return "단일로보트"
    if any(keyword in f"{text} {category_text}" for keyword in ["시스템", "PLC", "HMI", "네트워크", "Profinet", "Ethernet", "주변장비"]):
        return "시스템_현장기기_주변장치"
    return "미확정"


def _cleaned_customer(row: pd.Series, text: str) -> str:
    value = row.get("고객사")
    if not _needs_review(value):
        return _text(value)
    guessed = _guess_customer(text)
    return guessed if guessed else "미입력"


def _guess_customer(text: str) -> str:
    keywords = {
        "기아": "기아",
        "현대": "현대",
        "HMGMA": "HMGMA",
        "HMMME": "HMMME",
        "KaGA": "KaGA",
        "대성": "대성피엔티",
        "아이아": "아이아",
    }
    for keyword, customer in keywords.items():
        if keyword.lower() in text.lower():
            return f"추천후보:{customer}"
    return ""


def _location_status(row: pd.Series) -> str:
    fields = ["BOOTH", "LINE", "공정"]
    filled = [not _needs_review(row.get(field)) for field in fields]
    if all(filled):
        return "입력값 존재"
    if any(filled):
        return "일부 입력"
    return "미입력/해당없음"


def _robot_target_count(row: pd.Series, text: str, target_type: str) -> str:
    if target_type == "라인전체":
        return "라인전체"
    count = _robot_token_count(_text(row.get("로보트 NO")) or text)
    if count == 0:
        return "미입력/검토 필요"
    if count == 1:
        return "1대"
    return "2대이상"


def _robot_model_status(row: pd.Series, target_type: str) -> str:
    value = row.get("로보트 기종")
    if target_type not in {"단일로보트", "다중로보트"} and _needs_review(value):
        return "해당없음"
    if _needs_review(value):
        return "미입력/검토 필요"
    return _text(value)


def _category_status(row: pd.Series) -> str:
    fields = ["대분류", "중분류", "소분류 (고장부품)"]
    filled = [not _needs_review(row.get(field)) for field in fields]
    if all(filled):
        return "대중소분류 완료"
    if any(filled):
        return "일부 누락"
    return "미분류"


def _completion_method(fields: list[str], auto_fields: list[str]) -> str:
    if not fields:
        return "해당없음"
    if auto_fields:
        return "자동추정+수동확인필요"
    return "수동확인필요"


def _priority(fields: list[str], target_type: str, text: str) -> str:
    if not fields:
        return "-"
    high_fields = {"고객사", "BOOTH", "LINE", "공정", "로보트 NO", "로보트 기종", DOWNTIME_COLUMN, "대분류", "중분류", "소분류 (고장부품)"}
    if any(field in high_fields for field in fields):
        return "상"
    if target_type in {"미확정", "라인전체"} or _line_impact_text(text):
        return "중"
    return "하"


def _difficulty(priority: str) -> str:
    return {"상": "높음", "중": "중간", "하": "낮음", "-": "낮음"}.get(priority, "중간")


def _search_method(row: pd.Series, text: str) -> str:
    date_text = _date_text(row.get(DATE_COLUMN))
    customer = _text(row.get("고객사")) or "고객사 미입력"
    work_type = _text(row.get("업무유형")) or "업무유형 미입력"
    keywords = _keywords(text)
    if keywords:
        return f"접수일+접수내용 요약 검색어: {date_text} / {keywords}"
    return f"접수일+고객사+업무유형: {date_text} / {customer} / {work_type}"


def _keywords(text: str) -> str:
    tokens = re.findall(r"[A-Za-z0-9가-힣]{2,}", text)
    stop_words = {"접수", "요청", "확인", "진행", "처리", "발생", "문의", "지원", "내용"}
    counter = Counter(token for token in tokens if token not in stop_words)
    return ", ".join(token for token, _ in counter.most_common(8))


def _auto_guess_possible(field: str, text: str) -> bool:
    if field == "고객사" and _guess_customer(text):
        return True
    if field in {"로보트 NO", "로보트 기종"} and _robot_token_count(text):
        return True
    if field in {"BOOTH", "LINE", "공정"} and any(keyword in text for keyword in ["1라인", "2라인", "L1", "L2", "공정", "부스"]):
        return True
    return False


def _needs_review(value: Any) -> bool:
    text = _text(value)
    return pd.isna(value) or text in MISSING_MARKERS or text in DETAIL_REQUIRED_MARKERS


def _is_blank(value: Any) -> bool:
    text = _text(value)
    return pd.isna(value) or text == "" or text in {"선택안함", "nan", "None", "NaN", "<NA>"}


def _row_text(row: pd.Series) -> str:
    fields = ["업무유형", "접수 내용 (요약)", "접수 내용 (자세히)", "처리내용/진행상황 (요약)", "대분류", "중분류", "소분류 (고장부품)", "로보트 NO", "로보트 기종"]
    return " ".join(_text(row.get(field)) for field in fields if _text(row.get(field)))


def _line_impact_text(text: str) -> bool:
    return any(keyword in text for keyword in ["라인", "중단", "정지", "생산", "가동", "전체"])


def _robot_token_count(text: str) -> int:
    tokens = re.findall(r"\b[A-Z가-힣]*[RLCBP]\s*\d+\b", text.upper())
    return len(set(token.replace(" ", "") for token in tokens))


def _split_list(value: Any) -> list[str]:
    text = _text(value)
    return [item.strip() for item in text.split(",") if item.strip()]


def _list_contains(value: Any, field: str) -> bool:
    return field in _split_list(value)


def _text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def _date_text(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    try:
        return pd.Timestamp(value).strftime("%Y-%m-%d")
    except Exception:
        return str(value)
