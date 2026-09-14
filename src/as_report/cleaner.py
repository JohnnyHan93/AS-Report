from __future__ import annotations

import pandas as pd

DATE_COLUMNS = ("접수일", "등록일", "수정일")
DOWNTIME_COLUMN = "라인 중단 시간 (분)"
MISSING_MARKERS = ("", "선택안함", "--", "#NAME?", "nan", "None", "NaN")
MARKER_COUNT_KEYS = {
    "선택안함": "선택안함 정리 건수",
    "--": "-- 정리 건수",
    "#NAME?": "#NAME? 정리 건수",
}


def clean_data(dataframe: pd.DataFrame) -> pd.DataFrame:
    cleaned = dataframe.copy()
    cleaned.columns = [str(column).strip() for column in cleaned.columns]

    for column in cleaned.select_dtypes(include=["object", "string"]).columns:
        cleaned[column] = cleaned[column].map(_strip_if_text)

    cleaning_counts = _count_cleaning_markers(cleaned)
    cleaned = cleaned.replace(list(MISSING_MARKERS), pd.NA)

    for column in DATE_COLUMNS:
        if column in cleaned.columns:
            cleaned[column] = pd.to_datetime(cleaned[column], errors="coerce")

    if DOWNTIME_COLUMN in cleaned.columns:
        cleaned[DOWNTIME_COLUMN] = pd.to_numeric(cleaned[DOWNTIME_COLUMN], errors="coerce")

    _add_derived_columns(cleaned)
    cleaned.attrs["cleaning_counts"] = cleaning_counts
    return cleaned


def _strip_if_text(value: object) -> object:
    if isinstance(value, str):
        return value.strip()
    return value


def _count_cleaning_markers(dataframe: pd.DataFrame) -> dict[str, int]:
    counts = {label: 0 for label in MARKER_COUNT_KEYS.values()}
    for value, label in MARKER_COUNT_KEYS.items():
        counts[label] = int((dataframe == value).sum(numeric_only=False).sum())
    return counts


def _add_derived_columns(dataframe: pd.DataFrame) -> None:
    received_at = dataframe["접수일"] if "접수일" in dataframe.columns else pd.Series(pd.NaT, index=dataframe.index)
    received_month = received_at.dt.month

    dataframe["접수연도"] = received_at.dt.year.astype("Int64")
    dataframe["접수월"] = received_month.astype("Int64")
    dataframe["접수분기"] = received_at.dt.quarter.map(lambda value: f"Q{value}" if pd.notna(value) else pd.NA)
    dataframe["접수반기"] = received_month.map(_half_from_month)
    dataframe["기간_연월"] = received_at.dt.strftime("%Y-%m").astype("string")
    dataframe.loc[received_at.isna(), "기간_연월"] = pd.NA

    if "상태" in dataframe.columns:
        dataframe["처리상태구분"] = dataframe["상태"].map(_status_group)
    else:
        dataframe["처리상태구분"] = "미완료"

    if "업무유형" in dataframe.columns:
        dataframe["업무유형구분"] = dataframe["업무유형"].map(_work_type_group)
    else:
        dataframe["업무유형구분"] = "기타"

    downtime = dataframe[DOWNTIME_COLUMN] if DOWNTIME_COLUMN in dataframe.columns else pd.Series(pd.NA, index=dataframe.index)
    dataframe["라인중단_입력여부"] = downtime.notna().map(lambda value: "입력" if value else "미입력")
    dataframe["라인중단_발생여부"] = (downtime.fillna(0) > 0).map(lambda value: "발생" if value else "미발생/미입력")


def _half_from_month(month: object) -> object:
    if pd.isna(month):
        return pd.NA
    return "H1" if int(month) <= 6 else "H2"


def _status_group(value: object) -> str:
    return "완료" if str(value).strip() == "처리완료" else "미완료"


def _work_type_group(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    if "긴급" in text:
        return "긴급방문"
    if "일반" in text:
        return "일반방문"
    if "원격" in text:
        return "원격지원"
    if "부품수리" in text or "클레임" in text:
        return "부품수리/클레임"
    if "VOC" in text.upper():
        return "VOC"
    return "기타"