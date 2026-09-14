from __future__ import annotations

from typing import Any

import pandas as pd

MISSING_LABEL = "미입력"
CLAIM_WORK_TYPE_TOKEN = "부품수리/클레임처리"
COMPLETED_STATUS_VALUES = {"처리완료", "전달 완료", "완료", "조치완료", "종결", "완료됨"}

CLAIM_ISSUE_COLUMNS = [
    ("접수일", "접수일"),
    ("상태", "처리상태"),
    ("업무유형", "업무유형"),
    ("유/무상", "유/무상"),
    ("제조사", "제조사"),
    ("고객사", "고객사"),
    ("BOOTH", "BOOTH"),
    ("LINE", "LINE"),
    ("공정", "공정"),
    ("ZONE", "ZONE"),
    ("로보트 NO", "로보트 NO"),
    ("로보트 기종", "로보트 기종"),
    ("대분류", "대분류"),
    ("중분류", "중분류"),
    ("소분류 (고장부품)", "소분류 (고장부품)"),
    ("접수 내용 (요약)", "접수내용"),
    ("처리내용/진행상황 (요약)", "조치이력"),
]


def build_legacy_features(dataframe: pd.DataFrame) -> dict[str, Any]:
    """Build AS25 additive legacy-derived analysis outputs from report-period data."""
    claim = build_claim_analysis(dataframe)
    completion = build_completion_analysis(dataframe)
    return {
        **claim,
        **completion,
    }


def build_claim_analysis(dataframe: pd.DataFrame) -> dict[str, Any]:
    if dataframe.empty or "업무유형" not in dataframe.columns:
        return {
            "claim_summary": _claim_summary_frame(0, "업무유형 컬럼 없음"),
            "claim_by_manufacturer": _empty_frame(["제조사", "접수 건수", "유상 건수", "무상 건수", "미입력 건수", "비중"]),
            "claim_by_paid_type": _empty_frame(["유/무상", "접수 건수", "비중"]),
            "claim_by_part_category": _empty_frame(["대분류", "중분류", "소분류 (고장부품)", "접수 건수"]),
            "claim_issue_list": _empty_frame([label for _, label in CLAIM_ISSUE_COLUMNS]),
            "claim_note": "업무유형 컬럼이 없어 클레임/제조사 검토를 제한했습니다.",
        }

    work_type = dataframe["업무유형"].fillna("").astype(str)
    claim_rows = dataframe.loc[work_type.str.contains(CLAIM_WORK_TYPE_TOKEN, regex=False, na=False)].copy()
    total = int(len(claim_rows))
    if total == 0:
        return {
            "claim_summary": _claim_summary_frame(0, "대상 없음"),
            "claim_by_manufacturer": _empty_frame(["제조사", "접수 건수", "유상 건수", "무상 건수", "미입력 건수", "비중"]),
            "claim_by_paid_type": _empty_frame(["유/무상", "접수 건수", "비중"]),
            "claim_by_part_category": _empty_frame(["대분류", "중분류", "소분류 (고장부품)", "접수 건수"]),
            "claim_issue_list": _empty_frame([label for _, label in CLAIM_ISSUE_COLUMNS]),
            "claim_note": "부품수리/클레임처리 대상 접수 건이 없습니다.",
        }

    paid = _display_series(claim_rows, "유/무상")
    manufacturer = _display_series(claim_rows, "제조사")
    summary = _claim_summary_frame(
        total,
        "입력값 기준",
        paid_count=int((paid == "유상").sum()),
        free_count=int((paid == "무상").sum()),
        missing_paid_count=int((paid == MISSING_LABEL).sum()),
        missing_manufacturer_count=int((manufacturer == MISSING_LABEL).sum()),
        manufacturer_count=int(manufacturer.loc[manufacturer != MISSING_LABEL].nunique()),
    )

    by_manufacturer = _claim_by_manufacturer(claim_rows, manufacturer, paid)
    by_paid_type = _count_share_frame(paid, "유/무상", total)
    by_part_category = _claim_by_part_category(claim_rows)
    issue_list = _claim_issue_list(claim_rows)
    return {
        "claim_summary": summary,
        "claim_by_manufacturer": by_manufacturer,
        "claim_by_paid_type": by_paid_type,
        "claim_by_part_category": by_part_category,
        "claim_issue_list": issue_list,
        "claim_note": "업무유형 입력값 기준 검토용입니다. 입력값을 검토할 뿐 추가 판단을 확정하지 않습니다.",
    }


def build_completion_analysis(dataframe: pd.DataFrame) -> dict[str, Any]:
    status_column = "상태" if "상태" in dataframe.columns else "처리상태" if "처리상태" in dataframe.columns else None
    if status_column is None:
        return {
            "completion_kpi": pd.DataFrame(
                [
                    {"항목": "분석 대상 접수 건수", "값": int(len(dataframe))},
                    {"항목": "처리완료 건수", "값": 0},
                    {"항목": "진행/미완료 건수", "값": 0},
                    {"항목": "상태 미입력 건수", "값": int(len(dataframe))},
                    {"항목": "처리완료율", "값": 0.0},
                    {"항목": "제한 사유", "값": "상태 컬럼 없음"},
                ]
            ),
            "monthly_completion_trend": _empty_frame(["기간_연월", "접수 건수", "처리완료 건수", "진행/미완료 건수", "상태 미입력 건수", "처리완료율"]),
            "open_status_breakdown": _empty_frame(["상태값", "건수"]),
            "completion_note": "상태 컬럼이 없어 처리 상태 요약을 제한했습니다.",
        }

    status = _display_series(dataframe, status_column)
    completed_mask = status.isin(COMPLETED_STATUS_VALUES)
    missing_mask = status.eq(MISSING_LABEL)
    total = int(len(dataframe))
    completed = int(completed_mask.sum())
    missing = int(missing_mask.sum())
    incomplete = int(total - completed - missing)
    completion_rate = round(completed / total * 100, 1) if total else 0.0

    completion_kpi = pd.DataFrame(
        [
            {"항목": "분석 대상 접수 건수", "값": total},
            {"항목": "처리완료 건수", "값": completed},
            {"항목": "진행/미완료 건수", "값": incomplete},
            {"항목": "상태 미입력 건수", "값": missing},
            {"항목": "처리완료율", "값": completion_rate},
        ]
    )
    trend = _monthly_completion_trend(dataframe, status, completed_mask, missing_mask)
    open_breakdown = status.loc[~completed_mask].value_counts(dropna=False).rename_axis("상태값").reset_index(name="건수")
    return {
        "completion_kpi": completion_kpi,
        "monthly_completion_trend": trend,
        "open_status_breakdown": open_breakdown,
        "completion_note": "처리 상태 입력값 기준 업무 처리 현황입니다.",
    }


def empty_controller_features(note: str) -> dict[str, Any]:
    return {
        "controller_install_summary": _empty_frame(
            ["컨트롤러", "설치대수", "AS 접수 건수", "고장성 AS 접수 건수", "설치대수 대비 AS 접수율", "설치대수 대비 고장성 AS 접수율", "대당 AS 접수건수", "매칭 상태/비고"]
        ),
        "install_year_as_rate": _empty_frame(["설치연도", "설치대수", "AS 접수 건수", "고장성 AS 접수 건수", "설치대수 대비 AS 접수율", "설치대수 대비 고장성 AS 접수율", "대당 AS 접수건수"]),
        "controller_unmatched_preview": _empty_frame(["접수일", "고객사", "BOOTH", "LINE", "공정", "ZONE", "로보트 NO", "로보트 기종", "업무유형", "대분류", "중분류", "소분류 (고장부품)", "매칭 상태", "매칭 비고"]),
        "controller_note": note,
    }


def empty_robot_model_features(note: str) -> dict[str, Any]:
    return {
        "robot_model_install_summary": _empty_frame(
            ["로보트 기종", "설치대수", "AS 접수 건수", "대당 AS 접수건수", "매칭 상태/비고"]
        ),
        "robot_model_match_summary": _empty_frame(["항목", "값"]),
        "robot_model_unmatched_preview": _empty_frame(
            ["접수일", "고객사", "BOOTH", "LINE", "공정", "ZONE", "로보트 NO", "로보트 기종", "업무유형", "대분류", "중분류", "소분류 (고장부품)", "매칭 상태", "매칭 비고"]
        ),
        "robot_model_note": note,
    }


def merge_controller_features(legacy_features: dict[str, Any], master_result: dict[str, Any] | None) -> dict[str, Any]:
    merged = dict(legacy_features)
    if not master_result or master_result.get("status") not in {None, "OK"}:
        error = master_result.get("error", "Master 분석 결과가 없습니다.") if master_result else "Master 분석 결과가 없습니다."
        merged.update(empty_controller_features(error))
        merged.update(empty_robot_model_features(error))
        return merged
    for key in [
        "controller_install_summary",
        "install_year_as_rate",
        "controller_unmatched_preview",
        "controller_note",
        "robot_model_install_summary",
        "robot_model_match_summary",
        "robot_model_unmatched_preview",
        "robot_model_note",
    ]:
        if key in master_result:
            merged[key] = master_result[key]
    return merged


def _claim_summary_frame(
    total: int,
    status: str,
    paid_count: int = 0,
    free_count: int = 0,
    missing_paid_count: int = 0,
    missing_manufacturer_count: int = 0,
    manufacturer_count: int = 0,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"항목": "클레임/부품수리 대상 건수", "값": total},
            {"항목": "유상 건수", "값": paid_count},
            {"항목": "무상 건수", "값": free_count},
            {"항목": "유/무상 미입력 건수", "값": missing_paid_count},
            {"항목": "제조사 미입력 건수", "값": missing_manufacturer_count},
            {"항목": "제조사 수", "값": manufacturer_count},
            {"항목": "검토 상태", "값": status},
        ]
    )


def _claim_by_manufacturer(dataframe: pd.DataFrame, manufacturer: pd.Series, paid: pd.Series) -> pd.DataFrame:
    if dataframe.empty:
        return _empty_frame(["제조사", "접수 건수", "유상 건수", "무상 건수", "미입력 건수", "비중"])
    working = pd.DataFrame({"제조사": manufacturer, "유/무상": paid})
    total = len(working)
    rows = []
    for name, group in working.groupby("제조사", dropna=False):
        rows.append(
            {
                "제조사": name,
                "접수 건수": int(len(group)),
                "유상 건수": int((group["유/무상"] == "유상").sum()),
                "무상 건수": int((group["유/무상"] == "무상").sum()),
                "미입력 건수": int((group["유/무상"] == MISSING_LABEL).sum()),
                "비중": round(len(group) / total * 100, 1) if total else 0.0,
            }
        )
    return pd.DataFrame(rows).sort_values(["접수 건수", "제조사"], ascending=[False, True]).reset_index(drop=True)


def _claim_by_part_category(dataframe: pd.DataFrame) -> pd.DataFrame:
    columns = ["대분류", "중분류", "소분류 (고장부품)"]
    if dataframe.empty:
        return _empty_frame(columns + ["접수 건수"])
    working = pd.DataFrame({column: _display_series(dataframe, column) for column in columns})
    result = working.groupby(columns, dropna=False).size().reset_index(name="접수 건수")
    return result.sort_values("접수 건수", ascending=False).reset_index(drop=True)


def _claim_issue_list(dataframe: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, record in dataframe.iterrows():
        rows.append({label: _display_value(record.get(source)) for source, label in CLAIM_ISSUE_COLUMNS})
    return pd.DataFrame(rows, columns=[label for _, label in CLAIM_ISSUE_COLUMNS])


def _monthly_completion_trend(dataframe: pd.DataFrame, status: pd.Series, completed_mask: pd.Series, missing_mask: pd.Series) -> pd.DataFrame:
    if "기간_연월" not in dataframe.columns:
        return _empty_frame(["기간_연월", "접수 건수", "처리완료 건수", "진행/미완료 건수", "상태 미입력 건수", "처리완료율"])
    working = pd.DataFrame(
        {
            "기간_연월": _display_series(dataframe, "기간_연월"),
            "completed": completed_mask,
            "missing": missing_mask,
            "status": status,
        }
    )
    rows = []
    for month, group in working.groupby("기간_연월", dropna=False):
        total = int(len(group))
        completed = int(group["completed"].sum())
        missing = int(group["missing"].sum())
        rows.append(
            {
                "기간_연월": month,
                "접수 건수": total,
                "처리완료 건수": completed,
                "진행/미완료 건수": int(total - completed - missing),
                "상태 미입력 건수": missing,
                "처리완료율": round(completed / total * 100, 1) if total else 0.0,
            }
        )
    if not rows:
        return _empty_frame(["기간_연월", "접수 건수", "처리완료 건수", "진행/미완료 건수", "상태 미입력 건수", "처리완료율"])
    return pd.DataFrame(rows).sort_values("기간_연월").reset_index(drop=True)


def _count_share_frame(series: pd.Series, label_name: str, total: int) -> pd.DataFrame:
    counts = series.value_counts(dropna=False).rename_axis(label_name).reset_index(name="접수 건수")
    counts["비중"] = counts["접수 건수"].map(lambda value: round(value / total * 100, 1) if total else 0.0)
    return counts


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


def _empty_frame(columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=columns)
