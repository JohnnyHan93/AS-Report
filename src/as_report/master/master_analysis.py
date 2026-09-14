from __future__ import annotations

from typing import Any

import pandas as pd

from .master_data_validator import (
    CUSTOMER_COL,
    MASTER_MAJOR_COL,
    MASTER_MIDDLE_COL,
    MASTER_PART_COL,
    ROBOT_NO_COL,
    validate_customer_robot_master,
    validate_failure_part_categories,
    validate_failure_part_master,
    match_as_to_robot_master,
)
from ..legacy_features import empty_controller_features, empty_robot_model_features

CONTROLLER_COLUMN_CANDIDATES = [
    "컨트롤러(Controller)",
    "컨트롤러",
    "제어기",
    "CONTROLLER",
    "Controller",
    "controller",
    "로봇제어기",
    "제어기명",
]
ROBOT_MODEL_COLUMN_CANDIDATES = [
    "로보트 기종",
    "로봇 기종",
    "Robot Model",
    "Robot Type",
    "Model",
]
INSTALL_YEAR_COLUMN_CANDIDATES = [
    "설치연도(Installation year)",
    "설치년도",
    "설치연도",
    "Installation year",
    "install_year",
]


def build_master_analysis_result(as_df: pd.DataFrame, customer_robot_master_df: pd.DataFrame, failure_part_master_df: pd.DataFrame) -> dict[str, Any]:
    """Build non-destructive master-data analysis outputs."""
    customer_quality = validate_customer_robot_master(customer_robot_master_df)
    failure_quality = validate_failure_part_master(failure_part_master_df)
    category_validation = validate_failure_part_categories(as_df, failure_part_master_df)
    robot_match_preview = match_as_to_robot_master(as_df, customer_robot_master_df)
    customer_rate = customer_as_rate_by_robot_count(as_df, customer_robot_master_df, category_validation)
    controller_features = controller_as_rate_by_install_count(as_df, customer_robot_master_df, category_validation, robot_match_preview)
    robot_model_features = robot_model_as_count_per_install(customer_robot_master_df, robot_match_preview, as_df)
    failure_trend = failure_part_trend(category_validation)
    summary = {
        "AS 분석 대상 행 수": int(len(as_df)),
        "로봇 master 행 수": int(len(customer_robot_master_df)),
        "고장부품 master 행 수": int(len(failure_part_master_df)),
        "로봇 master 매칭 행 수": int((robot_match_preview["match_level"] != "unmatched").sum()) if not robot_match_preview.empty else 0,
        "로봇 master 미매칭 행 수": int((robot_match_preview["match_level"] == "unmatched").sum()) if not robot_match_preview.empty else 0,
        "고장성 AS 행 수": int((category_validation["is_fault_related_as"] == "Y").sum()) if not category_validation.empty else 0,
    }
    return {
        "summary": summary,
        "customer_robot_quality": customer_quality,
        "failure_part_quality": failure_quality,
        "robot_match_preview_df": robot_match_preview,
        "unmatched_as_issues_df": robot_match_preview.loc[robot_match_preview["match_level"] == "unmatched"].copy() if not robot_match_preview.empty else pd.DataFrame(),
        "category_validation_df": category_validation,
        "customer_as_rate_df": customer_rate,
        "failure_part_trend_df": failure_trend,
        **controller_features,
        **robot_model_features,
    }


def controller_as_rate_by_install_count(
    as_df: pd.DataFrame,
    customer_robot_master_df: pd.DataFrame,
    category_validation_df: pd.DataFrame,
    robot_match_preview_df: pd.DataFrame,
) -> dict[str, Any]:
    controller_col = _first_existing_column(customer_robot_master_df, CONTROLLER_COLUMN_CANDIDATES)
    if controller_col is None:
        return empty_controller_features("컨트롤러 기준 컬럼 없음")

    install_year_col = _first_existing_column(customer_robot_master_df, INSTALL_YEAR_COLUMN_CANDIDATES)
    master = customer_robot_master_df.copy(deep=True)
    master["_controller"] = master[controller_col].map(_display_or_missing)
    master["_install_year"] = master[install_year_col].map(_display_or_missing) if install_year_col else "미입력"
    master_id_lookup = {
        _display_text(row.get("*ID")): row
        for _, row in master.iterrows()
        if _display_text(row.get("*ID"))
    }

    installed_by_controller = master.groupby("_controller", dropna=False).size().reset_index(name="설치대수").rename(columns={"_controller": "컨트롤러"})
    installed_by_year = master.groupby("_install_year", dropna=False).size().reset_index(name="설치대수").rename(columns={"_install_year": "설치연도"})

    safe_rows = []
    unmatched_rows = []
    fault_index = _fault_related_index_set(category_validation_df)
    for _, match in robot_match_preview_df.iterrows():
        master_id = _single_safe_master_id(match)
        as_row_index = match.get("as_row_index")
        if master_id and master_id in master_id_lookup:
            master_row = master_id_lookup[master_id]
            safe_rows.append(
                {
                    "as_row_index": as_row_index,
                    "컨트롤러": _display_or_missing(master_row.get(controller_col)),
                    "설치연도": _display_or_missing(master_row.get(install_year_col)) if install_year_col else "미입력",
                    "is_fault_related_as": "Y" if as_row_index in fault_index else "N",
                }
            )
        else:
            unmatched_rows.append(_controller_unmatched_record(as_df, match))

    safe = pd.DataFrame(safe_rows)
    controller_summary = _rate_summary(
        installed_by_controller,
        safe,
        group_column="컨트롤러",
        note_column=True,
    )
    install_year_summary = _rate_summary(
        installed_by_year,
        safe,
        group_column="설치연도",
        note_column=False,
    )
    return {
        "controller_install_summary": controller_summary,
        "install_year_as_rate": install_year_summary,
        "controller_unmatched_preview": pd.DataFrame(
            unmatched_rows,
            columns=["접수일", "고객사", "BOOTH", "LINE", "공정", "ZONE", "로보트 NO", "로보트 기종", "업무유형", "대분류", "중분류", "소분류 (고장부품)", "매칭 상태", "매칭 비고"],
        ),
        "controller_note": "Master 컨트롤러 기준 preview/reference입니다. 매칭 결과는 확정값이 아닙니다.",
    }


def robot_model_as_count_per_install(
    customer_robot_master_df: pd.DataFrame,
    robot_match_preview_df: pd.DataFrame,
    as_df: pd.DataFrame,
) -> dict[str, Any]:
    """Build a visible robot-model preview only when master has a model column.

    The existing controller calculation remains available internally, but it is
    not reused as a substitute for a robot-model denominator.
    """
    match_summary = _robot_master_match_summary(robot_match_preview_df)
    unmatched_preview = _unmatched_preview(as_df, robot_match_preview_df)
    model_col = _first_existing_column(customer_robot_master_df, ROBOT_MODEL_COLUMN_CANDIDATES)
    if model_col is None:
        result = empty_robot_model_features(
            "Master에 로보트 기종 기준 설치대수 컬럼이 없어 대당 AS 접수건수를 표시하지 않습니다. 로봇 master 매칭 현황만 제공합니다."
        )
        result["robot_model_match_summary"] = match_summary
        result["robot_model_unmatched_preview"] = unmatched_preview
        return result

    master = customer_robot_master_df.copy(deep=True)
    master["_robot_model"] = master[model_col].map(_display_or_missing)
    master_id_lookup = {
        _display_text(row.get("*ID")): row
        for _, row in master.iterrows()
        if _display_text(row.get("*ID"))
    }
    installed_by_model = master.groupby("_robot_model", dropna=False).size().reset_index(name="설치대수").rename(columns={"_robot_model": "로보트 기종"})

    safe_rows = []
    for _, match in robot_match_preview_df.iterrows():
        master_id = _single_safe_master_id(match)
        if master_id and master_id in master_id_lookup:
            safe_rows.append({"로보트 기종": _display_or_missing(master_id_lookup[master_id].get(model_col))})

    summary = _per_install_count_summary(installed_by_model, pd.DataFrame(safe_rows), "로보트 기종")
    return {
        "robot_model_install_summary": summary,
        "robot_model_match_summary": match_summary,
        "robot_model_unmatched_preview": unmatched_preview,
        "robot_model_note": "Master 로보트 기종 기준 preview/reference입니다. 단일 안전 매칭만 분자에 반영하며, 매칭 결과는 확정값이 아닙니다.",
    }


def _robot_master_match_summary(robot_match_preview_df: pd.DataFrame) -> pd.DataFrame:
    total = int(len(robot_match_preview_df))
    if robot_match_preview_df.empty or "match_level" not in robot_match_preview_df.columns:
        matched = 0
        unmatched = 0
    else:
        matched = int(robot_match_preview_df["match_level"].ne("unmatched").sum())
        unmatched = int(robot_match_preview_df["match_level"].eq("unmatched").sum())
    match_rate = round(matched / total * 100, 1) if total else 0.0
    return pd.DataFrame(
        [
            {"항목": "로봇 master 매칭 건수", "값": matched},
            {"항목": "로봇 master 미매칭 건수", "값": unmatched},
            {"항목": "로봇 master 매칭률(%)", "값": match_rate},
        ]
    )


def _unmatched_preview(as_df: pd.DataFrame, robot_match_preview_df: pd.DataFrame) -> pd.DataFrame:
    columns = ["접수일", "고객사", "BOOTH", "LINE", "공정", "ZONE", "로보트 NO", "로보트 기종", "업무유형", "대분류", "중분류", "소분류 (고장부품)", "매칭 상태", "매칭 비고"]
    if robot_match_preview_df.empty:
        return pd.DataFrame(columns=columns)
    rows = [
        _controller_unmatched_record(as_df, match)
        for _, match in robot_match_preview_df.loc[robot_match_preview_df["match_level"].eq("unmatched")].iterrows()
    ]
    return pd.DataFrame(rows, columns=columns)


def _per_install_count_summary(installed: pd.DataFrame, safe_matches: pd.DataFrame, group_column: str) -> pd.DataFrame:
    if safe_matches.empty:
        as_counts = pd.DataFrame(columns=[group_column, "AS 접수 건수"])
    else:
        as_counts = safe_matches.groupby(group_column, dropna=False).size().reset_index(name="AS 접수 건수")
    result = installed.merge(as_counts, on=group_column, how="left")
    result["AS 접수 건수"] = result["AS 접수 건수"].fillna(0).astype(int)
    result["대당 AS 접수건수"] = result.apply(
        lambda row: round(row["AS 접수 건수"] / row["설치대수"], 2) if row["설치대수"] else 0.0,
        axis=1,
    )
    result["매칭 상태/비고"] = "단일 안전 매칭 기준"
    return result.sort_values(["대당 AS 접수건수", "AS 접수 건수"], ascending=[False, False]).reset_index(drop=True)


def _rate_summary(installed: pd.DataFrame, safe_matches: pd.DataFrame, group_column: str, note_column: bool) -> pd.DataFrame:
    if safe_matches.empty:
        as_counts = pd.DataFrame(columns=[group_column, "AS 접수 건수", "고장성 AS 접수 건수"])
    else:
        as_counts = safe_matches.groupby(group_column, dropna=False).size().reset_index(name="AS 접수 건수")
        fault_counts = safe_matches.loc[safe_matches["is_fault_related_as"] == "Y"].groupby(group_column, dropna=False).size().reset_index(name="고장성 AS 접수 건수")
        as_counts = as_counts.merge(fault_counts, on=group_column, how="left")
    result = installed.merge(as_counts, on=group_column, how="left")
    for column in ["AS 접수 건수", "고장성 AS 접수 건수"]:
        result[column] = result[column].fillna(0).astype(int)
    result["설치대수 대비 AS 접수율"] = result.apply(lambda row: round(row["AS 접수 건수"] / row["설치대수"] * 100, 1) if row["설치대수"] else 0.0, axis=1)
    result["설치대수 대비 고장성 AS 접수율"] = result.apply(lambda row: round(row["고장성 AS 접수 건수"] / row["설치대수"] * 100, 1) if row["설치대수"] else 0.0, axis=1)
    result["대당 AS 접수건수"] = result.apply(lambda row: round(row["AS 접수 건수"] / row["설치대수"], 2) if row["설치대수"] else 0.0, axis=1)
    if note_column:
        result["매칭 상태/비고"] = "단일 안전 매칭 기준"
    return result.sort_values(["설치대수 대비 AS 접수율", "AS 접수 건수"], ascending=[False, False]).reset_index(drop=True)


def _controller_unmatched_record(as_df: pd.DataFrame, match: pd.Series) -> dict[str, Any]:
    as_row_index = match.get("as_row_index")
    row = as_df.loc[as_row_index] if as_row_index in as_df.index else pd.Series(dtype="object")
    return {
        "접수일": row.get("접수일", match.get("접수일", "")),
        "고객사": row.get("고객사", match.get("고객사", "")),
        "BOOTH": row.get("BOOTH", match.get("BOOTH", "")),
        "LINE": row.get("LINE", match.get("LINE", "")),
        "공정": row.get("공정", ""),
        "ZONE": row.get("ZONE", ""),
        "로보트 NO": row.get("로보트 NO", match.get("로보트 NO", "")),
        "로보트 기종": row.get("로보트 기종", match.get("로보트 기종", "")),
        "업무유형": row.get("업무유형", ""),
        "대분류": row.get("대분류", ""),
        "중분류": row.get("중분류", ""),
        "소분류 (고장부품)": row.get("소분류 (고장부품)", ""),
        "매칭 상태": match.get("match_level", ""),
        "매칭 비고": match.get("match_note", ""),
    }


def _single_safe_master_id(match: pd.Series) -> str:
    if int(match.get("matched_master_count", 0) or 0) != 1:
        return ""
    if match.get("match_confidence") not in {"high", "medium"}:
        return ""
    ids = [item.strip() for item in str(match.get("matched_master_ids", "")).split(",") if item.strip()]
    return ids[0] if len(ids) == 1 else ""


def _fault_related_index_set(category_validation_df: pd.DataFrame) -> set[Any]:
    if category_validation_df.empty or {"as_row_index", "is_fault_related_as"} - set(category_validation_df.columns):
        return set()
    return set(category_validation_df.loc[category_validation_df["is_fault_related_as"] == "Y", "as_row_index"].tolist())


def _first_existing_column(dataframe: pd.DataFrame, candidates: list[str]) -> str | None:
    for column in candidates:
        if column in dataframe.columns:
            return column
    return None


def _display_or_missing(value: Any) -> str:
    text = _display_text(value)
    return text if text else "미입력"


def customer_as_rate_by_robot_count(as_df: pd.DataFrame, customer_robot_master_df: pd.DataFrame, category_validation_df: pd.DataFrame) -> pd.DataFrame:
    installed = (
        customer_robot_master_df.assign(_customer=customer_robot_master_df[CUSTOMER_COL].map(_display_text))
        .loc[lambda df: df["_customer"].ne("")]
        .groupby("_customer", dropna=False)
        .size()
        .reset_index(name="설치 로봇 수")
        .rename(columns={"_customer": "고객사"})
    )
    as_counts = (
        as_df.assign(_customer=as_df.get("고객사", pd.Series(index=as_df.index, dtype="object")).map(_display_text))
        .loc[lambda df: df["_customer"].ne("")]
        .groupby("_customer", dropna=False)
        .size()
        .reset_index(name="총 AS 접수 건수")
        .rename(columns={"_customer": "고객사"})
    )
    if category_validation_df.empty:
        fault_counts = pd.DataFrame(columns=["고객사", "고장성 AS 접수 건수"])
    else:
        fault_counts = (
            category_validation_df.loc[category_validation_df["is_fault_related_as"] == "Y"]
            .assign(_customer=category_validation_df.loc[category_validation_df["is_fault_related_as"] == "Y", "고객사"].map(_display_text))
            .loc[lambda df: df["_customer"].ne("")]
            .groupby("_customer", dropna=False)
            .size()
            .reset_index(name="고장성 AS 접수 건수")
            .rename(columns={"_customer": "고객사"})
        )
    result = installed.merge(as_counts, on="고객사", how="left").merge(fault_counts, on="고객사", how="left")
    for column in ["총 AS 접수 건수", "고장성 AS 접수 건수"]:
        result[column] = result[column].fillna(0).astype(int)
    result["AS 접수율(100대당)"] = result.apply(lambda row: round(row["총 AS 접수 건수"] / row["설치 로봇 수"] * 100, 1) if row["설치 로봇 수"] else 0.0, axis=1)
    result["고장성 AS 접수율(100대당)"] = result.apply(lambda row: round(row["고장성 AS 접수 건수"] / row["설치 로봇 수"] * 100, 1) if row["설치 로봇 수"] else 0.0, axis=1)
    return result.sort_values(["고장성 AS 접수율(100대당)", "AS 접수율(100대당)", "총 AS 접수 건수"], ascending=[False, False, False]).reset_index(drop=True)


def failure_part_trend(category_validation_df: pd.DataFrame) -> pd.DataFrame:
    if category_validation_df.empty:
        return pd.DataFrame(columns=["대분류", "중분류", "소분류 (고장부품)", "고장성 AS 접수 건수"])
    valid = category_validation_df.loc[category_validation_df["is_fault_related_as"] == "Y"].copy()
    if valid.empty:
        return pd.DataFrame(columns=["대분류", "중분류", "소분류 (고장부품)", "고장성 AS 접수 건수"])
    valid["대분류"] = valid["recommended_major_category"].map(_display_text)
    valid["중분류"] = valid["recommended_middle_category"].map(_display_text)
    valid["소분류 (고장부품)"] = valid["recommended_minor_category"].map(_display_text)
    return (
        valid.groupby(["대분류", "중분류", "소분류 (고장부품)"], dropna=False)
        .size()
        .reset_index(name="고장성 AS 접수 건수")
        .sort_values("고장성 AS 접수 건수", ascending=False)
        .reset_index(drop=True)
    )


def _display_text(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text in {"", "미입력", "선택안함", "--", "nan", "None", "NaN", "<NA>"} else text
