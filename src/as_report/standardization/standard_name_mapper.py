from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

import pandas as pd

MAPPING_COLUMNS = ["raw_name", "standard_name", "field_name", "note", "enabled"]

STANDARD_NAME_FILES = {
    "customer_names.csv": "고객사",
    "booth_names.csv": "BOOTH",
    "line_names.csv": "LINE",
    "process_names.csv": "공정",
    "zone_names.csv": "ZONE",
    "equipment_names.csv": "설비명",
    "robot_no_names.csv": "로보트 NO",
    "robot_model_names.csv": "로보트 기종",
}

TARGET_FIELDS = list(STANDARD_NAME_FILES.values())
FIELD_TO_FILE = {field_name: file_name for file_name, field_name in STANDARD_NAME_FILES.items()}

FALSE_LIKE = {"false", "0", "n", "no", "off", "disabled", "아니오", "사용안함", "미사용"}
MISSING_LIKE = {"", "선택안함", "--", "#NAME?", "기타", "nan", "none", "null", "<na>"}


def ensure_standard_name_files(config_dir: str | Path = "config/standard_names") -> dict[str, Path]:
    """
    Ensure standard name mapping CSV files exist and return their paths.

    Files are created with header rows only. No fake mapping data is inserted.
    """
    config_path = Path(config_dir)
    config_path.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for file_name in STANDARD_NAME_FILES:
        path = config_path / file_name
        if not path.exists():
            with path.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(MAPPING_COLUMNS)
        paths[file_name] = path
    return paths


def load_standard_name_mapping(config_dir: str | Path = "config/standard_names") -> dict[str, dict[str, str]]:
    """
    Load enabled mappings from all standard name CSV files.

    Return format:
    {
        "고객사": {"원본명": "표준명"}
    }
    """
    paths = ensure_standard_name_files(config_dir)
    mappings: dict[str, dict[str, str]] = {field_name: {} for field_name in TARGET_FIELDS}
    for file_name, path in paths.items():
        default_field = STANDARD_NAME_FILES[file_name]
        try:
            dataframe = pd.read_csv(path, dtype=str, encoding="utf-8-sig").fillna("")
        except pd.errors.EmptyDataError:
            continue
        for column in MAPPING_COLUMNS:
            if column not in dataframe.columns:
                dataframe[column] = ""
        for _, row in dataframe.iterrows():
            if _is_disabled(row.get("enabled")):
                continue
            raw_name = _normalize_name(row.get("raw_name"))
            standard_name = _text(row.get("standard_name"))
            field_name = _text(row.get("field_name")) or default_field
            if not raw_name or not standard_name:
                continue
            mappings.setdefault(field_name, {})[raw_name] = standard_name
    return mappings


def apply_standard_name_preview(df: pd.DataFrame, mappings: dict[str, dict[str, str]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Return a copied dataframe with standard-name preview columns only.

    Original columns are never overwritten.
    """
    preview = df.copy(deep=True)
    for field_name in TARGET_FIELDS:
        if field_name not in preview.columns:
            continue
        field_mapping = mappings.get(field_name, {})
        candidate_column = f"{field_name}_표준명_후보"
        status_column = f"{field_name}_표준명_매핑상태"
        candidates = []
        statuses = []
        for value in preview[field_name]:
            normalized = _normalize_name(value)
            raw_text = _text(value)
            if not normalized:
                candidates.append("")
                statuses.append("원본값 없음")
            elif normalized in field_mapping:
                candidates.append(field_mapping[normalized])
                statuses.append("매핑됨")
            else:
                candidates.append(raw_text)
                statuses.append("미매핑")
        preview[candidate_column] = candidates
        preview[status_column] = statuses
    return preview, extract_unknown_standard_names(df, mappings)


def extract_unknown_standard_names(df: pd.DataFrame, mappings: dict[str, dict[str, str]]) -> pd.DataFrame:
    """Extract nonblank values not found in mapping CSVs from target columns."""
    rows: list[dict[str, Any]] = []
    for field_name in TARGET_FIELDS:
        if field_name not in df.columns:
            continue
        field_mapping = mappings.get(field_name, {})
        working = df.loc[df[field_name].map(_normalize_name).ne("")].copy()
        if working.empty:
            continue
        working["_standard_key"] = working[field_name].map(_normalize_name)
        unknown = working.loc[~working["_standard_key"].isin(field_mapping.keys())].copy()
        if unknown.empty:
            continue
        for raw_name, group in unknown.groupby(field_name, dropna=True, sort=True):
            raw_text = _text(raw_name)
            if not raw_text or _normalize_name(raw_text) in MISSING_LIKE:
                continue
            first = group.iloc[0]
            rows.append(
                {
                    "field_name": field_name,
                    "raw_name": raw_text,
                    "count": int(len(group)),
                    "example_접수일": _date_text(first.get("접수일")),
                    "example_접수내용": _example_content(first),
                    "recommended_mapping_file": FIELD_TO_FILE.get(field_name, ""),
                    "note": "매핑 CSV에 표준명 검토 필요",
                }
            )
    if not rows:
        return pd.DataFrame(
            columns=[
                "field_name",
                "raw_name",
                "count",
                "example_접수일",
                "example_접수내용",
                "recommended_mapping_file",
                "note",
            ]
        )
    result = pd.DataFrame(rows)
    return result.sort_values(["field_name", "count", "raw_name"], ascending=[True, False, True]).reset_index(drop=True)


def _normalize_name(value: Any) -> str:
    text = _text(value)
    if text.lower() in MISSING_LIKE:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def _is_disabled(value: Any) -> bool:
    text = _text(value).lower()
    return text in FALSE_LIKE


def _text(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def _date_text(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    try:
        return pd.Timestamp(value).strftime("%Y-%m-%d")
    except Exception:
        return str(value)


def _example_content(row: pd.Series) -> str:
    for column_name in ["접수 내용 (요약)", "접수 내용 (자세히)", "처리내용/진행상황 (요약)"]:
        value = _text(row.get(column_name))
        if value:
            return value
    return ""
