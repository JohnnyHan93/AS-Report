from __future__ import annotations

from typing import Any

import pandas as pd

MISSING_TOKENS = {"", "미입력", "미분류", "선택안함", "--", "nan", "None", "NaN", "<NA>"}

CUSTOMER_COL = "고객사(Customer)"
LOCATION_COL = "위치(Location)"
PLANT_COL = "공장(plant)"
ROBOT_NO_COL = "Robot No"
MASTER_MAJOR_COL = "대분류"
MASTER_MIDDLE_COL = "중분류"
MASTER_PART_COL = "품명"
AS_MAJOR_COL = "대분류"
AS_MIDDLE_COL = "중분류"
AS_PART_COL = "소분류 (고장부품)"


def validate_customer_robot_master(dataframe: pd.DataFrame) -> dict[str, pd.DataFrame | dict[str, Any]]:
    required = ["*ID", CUSTOMER_COL, LOCATION_COL, PLANT_COL, "BOOTH", "LINE", "ZONE", ROBOT_NO_COL, "컨트롤러(Controller)", "설치연도(Installation year)"]
    return {
        "summary": _quality_summary(dataframe, required),
        "field_quality_df": _field_quality(dataframe, required),
    }


def validate_failure_part_master(dataframe: pd.DataFrame) -> dict[str, pd.DataFrame | dict[str, Any]]:
    required = ["*ID", MASTER_PART_COL, MASTER_MIDDLE_COL, MASTER_MAJOR_COL, "검색용", "제조사"]
    return {
        "summary": _quality_summary(dataframe, required),
        "field_quality_df": _field_quality(dataframe, required),
    }


def validate_failure_part_categories(as_df: pd.DataFrame, failure_master_df: pd.DataFrame) -> pd.DataFrame:
    master = failure_master_df.copy(deep=True)
    master["_major_key"] = master.get(MASTER_MAJOR_COL, pd.Series(index=master.index, dtype="object")).map(_norm)
    master["_middle_key"] = master.get(MASTER_MIDDLE_COL, pd.Series(index=master.index, dtype="object")).map(_norm)
    master["_part_key"] = master.get(MASTER_PART_COL, pd.Series(index=master.index, dtype="object")).map(_norm)
    full_keys = set(zip(master["_major_key"], master["_middle_key"], master["_part_key"]))
    major_middle_keys = set(zip(master["_major_key"], master["_middle_key"]))
    major_keys = set(master["_major_key"])
    part_lookup = {
        part: group[[MASTER_MAJOR_COL, MASTER_MIDDLE_COL, MASTER_PART_COL]].drop_duplicates().to_dict("records")
        for part, group in master.loc[master["_part_key"].ne("")].groupby("_part_key", dropna=False)
    }

    rows = []
    for index, row in as_df.iterrows():
        major = _norm(row.get(AS_MAJOR_COL))
        middle = _norm(row.get(AS_MIDDLE_COL))
        part = _norm(row.get(AS_PART_COL))
        result = _classify_category(major, middle, part, full_keys, major_middle_keys, major_keys, part_lookup)
        rows.append(
            {
                "as_row_index": index,
                "접수일": row.get("접수일", ""),
                "고객사": row.get("고객사", ""),
                "대분류": row.get(AS_MAJOR_COL, ""),
                "중분류": row.get(AS_MIDDLE_COL, ""),
                "소분류 (고장부품)": row.get(AS_PART_COL, ""),
                **result,
            }
        )
    return pd.DataFrame(rows)


def match_as_to_robot_master(as_df: pd.DataFrame, robot_master_df: pd.DataFrame) -> pd.DataFrame:
    master = robot_master_df.copy(deep=True)
    master["_customer_key"] = master.get(CUSTOMER_COL, pd.Series(index=master.index, dtype="object")).map(_norm)
    master["_booth_key"] = master.get("BOOTH", pd.Series(index=master.index, dtype="object")).map(_norm)
    master["_line_key"] = master.get("LINE", pd.Series(index=master.index, dtype="object")).map(_norm)
    master["_robot_key"] = master.get(ROBOT_NO_COL, pd.Series(index=master.index, dtype="object")).map(_norm)

    indexes = {
        "exact_robot": _group_index(master, ["_customer_key", "_booth_key", "_line_key", "_robot_key"]),
        "customer_robot": _group_index(master, ["_customer_key", "_robot_key"]),
        "location_only": _group_index(master, ["_customer_key", "_booth_key", "_line_key"]),
        "customer_only": _group_index(master, ["_customer_key"]),
    }

    rows = []
    for index, row in as_df.iterrows():
        keys = {
            "customer": _norm(row.get("고객사")),
            "booth": _norm(row.get("BOOTH")),
            "line": _norm(row.get("LINE")),
            "robot": _norm(row.get("로보트 NO")),
        }
        match = _match_robot(keys, indexes)
        rows.append(
            {
                "as_row_index": index,
                "접수일": row.get("접수일", ""),
                "고객사": row.get("고객사", ""),
                "BOOTH": row.get("BOOTH", ""),
                "LINE": row.get("LINE", ""),
                "로보트 NO": row.get("로보트 NO", ""),
                "로보트 기종": row.get("로보트 기종", ""),
                "match_level": match["match_level"],
                "match_confidence": match["match_confidence"],
                "matched_master_count": match["matched_master_count"],
                "matched_master_ids": match["matched_master_ids"],
                "match_note": match["match_note"],
            }
        )
    return pd.DataFrame(rows)


def _quality_summary(dataframe: pd.DataFrame, required_columns: list[str]) -> dict[str, Any]:
    return {
        "전체 행 수": int(len(dataframe)),
        "필수 컬럼 수": len(required_columns),
        "누락 필수 컬럼": ", ".join([column for column in required_columns if column not in dataframe.columns]),
        "*ID 중복 건수": int(dataframe["*ID"].duplicated().sum()) if "*ID" in dataframe.columns else 0,
    }


def _field_quality(dataframe: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    rows = []
    for column in columns:
        if column not in dataframe.columns:
            rows.append({"필드명": column, "결측/미입력 건수": len(dataframe), "결측률": 100.0, "고유값 수": 0})
            continue
        missing = int(dataframe[column].map(_is_missing).sum())
        rows.append(
            {
                "필드명": column,
                "결측/미입력 건수": missing,
                "결측률": round(missing / len(dataframe) * 100, 1) if len(dataframe) else 0.0,
                "고유값 수": int(dataframe[column].nunique(dropna=True)),
            }
        )
    return pd.DataFrame(rows)


def _classify_category(
    major: str,
    middle: str,
    part: str,
    full_keys: set[tuple[str, str, str]],
    major_middle_keys: set[tuple[str, str]],
    major_keys: set[str],
    part_lookup: dict[str, list[dict[str, Any]]],
) -> dict[str, str]:
    if not any([major, middle, part]):
        return _category_result("missing_category", "", "", "", "low", "대/중/소분류 모두 미입력")
    if part:
        if (major, middle, part) in full_keys:
            return _category_result("valid", major, middle, part, "high", "대/중/소분류 전체 매칭")
        candidates = part_lookup.get(part, [])
        if candidates:
            compatible = [
                candidate
                for candidate in candidates
                if (not major or _norm(candidate.get(MASTER_MAJOR_COL)) == major) and (not middle or _norm(candidate.get(MASTER_MIDDLE_COL)) == middle)
            ]
            if compatible:
                candidate = compatible[0]
                return _category_result(
                    "valid",
                    _text(candidate.get(MASTER_MAJOR_COL)),
                    _text(candidate.get(MASTER_MIDDLE_COL)),
                    _text(candidate.get(MASTER_PART_COL)),
                    "medium",
                    "소분류 기준 master 매칭",
                )
            return _category_result("invalid_combination", "", "", part, "low", "소분류는 존재하지만 대/중분류 조합이 불일치")
        return _category_result("unknown_category", major, middle, part, "low", "고장부품 master에서 소분류를 찾을 수 없음")
    if major and middle:
        if (major, middle) in major_middle_keys:
            return _category_result("missing_category", major, middle, "", "low", "대/중분류는 유효하나 소분류 미입력")
        if major in major_keys:
            return _category_result("invalid_combination", major, middle, "", "low", "중분류가 대분류에 속하지 않는 조합")
    return _category_result("unknown_category", major, middle, part, "low", "고장부품 master에서 분류 조합을 찾을 수 없음")


def _category_result(validity: str, major: str, middle: str, part: str, confidence: str, note: str) -> dict[str, str]:
    return {
        "category_validity": validity,
        "recommended_major_category": major,
        "recommended_middle_category": middle,
        "recommended_minor_category": part,
        "recommendation_confidence": confidence,
        "category_note": note,
        "is_fault_related_as": "Y" if validity == "valid" and confidence in {"high", "medium"} else "N",
    }


def _group_index(dataframe: pd.DataFrame, columns: list[str]) -> dict[tuple[str, ...], pd.DataFrame]:
    result: dict[tuple[str, ...], pd.DataFrame] = {}
    for key, group in dataframe.groupby(columns, dropna=False):
        values = key if isinstance(key, tuple) else (key,)
        if all(values):
            result[tuple(values)] = group
    return result


def _match_robot(keys: dict[str, str], indexes: dict[str, dict[tuple[str, ...], pd.DataFrame]]) -> dict[str, Any]:
    attempts = [
        ("exact_robot", "high", (keys["customer"], keys["booth"], keys["line"], keys["robot"])),
        ("customer_robot", "medium", (keys["customer"], keys["robot"])),
        ("location_only", "low", (keys["customer"], keys["booth"], keys["line"])),
        ("customer_only", "low", (keys["customer"],)),
    ]
    for level, confidence, key in attempts:
        if not all(key):
            continue
        group = indexes[level].get(key)
        if group is not None and not group.empty:
            ids = group.get("*ID", pd.Series(dtype="object")).dropna().astype(str).head(20).tolist()
            note = "고객사 기준 denominator 확인용" if level == "customer_only" else "매칭 후보"
            return {
                "match_level": level,
                "match_confidence": confidence,
                "matched_master_count": int(len(group)),
                "matched_master_ids": ", ".join(ids),
                "match_note": note,
            }
    return {"match_level": "unmatched", "match_confidence": "low", "matched_master_count": 0, "matched_master_ids": "", "match_note": "master 후보 없음"}


def _norm(value: Any) -> str:
    text = _text(value)
    if text in MISSING_TOKENS:
        return ""
    return " ".join(text.upper().split())


def _text(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def _is_missing(value: Any) -> bool:
    return _norm(value) == ""
