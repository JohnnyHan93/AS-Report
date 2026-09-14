from __future__ import annotations

from typing import Any

import pandas as pd

from .comparison import analyze_comparison
from .legacy_features import build_legacy_features
from .period import PeriodRange
from .quality_feedback import build_quality_feedback_candidates
from .repeat_issue import find_repeat_issues

DOWNTIME_COLUMN = "라인 중단 시간 (분)"
OPEN_ISSUE_COLUMNS = [
    "*ID",
    "상태",
    "접수일",
    "업무유형",
    "고객사",
    "BOOTH",
    "LINE",
    "공정",
    "로보트 NO",
    "로보트 기종",
    "고장원인",
    "소분류 (고장부품)",
    "중분류",
    "대분류",
    "처리사원",
    "접수 내용 (요약)",
    "처리내용/진행상황 (요약)",
]
DOWNTIME_TOP_COLUMNS = [
    "*ID",
    "상태",
    "접수일",
    "업무유형",
    "고객사",
    "BOOTH",
    "LINE",
    "공정",
    "로보트 NO",
    "로보트 기종",
    "고장원인",
    DOWNTIME_COLUMN,
    "소분류 (고장부품)",
    "중분류",
    "대분류",
    "처리사원",
    "접수 내용 (요약)",
    "처리내용/진행상황 (요약)",
]


def analyze(
    source_data: pd.DataFrame,
    period_data: pd.DataFrame,
    period_range: PeriodRange | None = None,
    comparison_source_data: pd.DataFrame | None = None,
    source_period_data: pd.DataFrame | None = None,
) -> dict[str, Any]:
    tables = build_tables(period_data)
    kpi = build_kpi(period_data)
    quality = build_quality(source_data, period_data)
    comparison_base = comparison_source_data if comparison_source_data is not None else source_data
    comparison = analyze_comparison(comparison_base, period_data, period_range, source_period_data=source_period_data) if period_range else pd.DataFrame()
    repeat_issues = find_repeat_issues(period_data)
    legacy_features = build_legacy_features(period_data)
    quality_feedback = build_quality_feedback_candidates(period_data)
    presentation_work_types = build_presentation_work_types(period_data)
    return {
        "kpi": kpi,
        "tables": tables,
        "quality": quality,
        "comparison": comparison,
        "repeat_issues": repeat_issues,
        "legacy_features": legacy_features,
        "quality_feedback": quality_feedback,
        "presentation_work_types": presentation_work_types,
    }


def build_presentation_work_types(dataframe: pd.DataFrame) -> dict[str, pd.DataFrame]:
    summary_columns = [
        "업무유형구분",
        "접수 건수",
        "전체 비중",
        "처리완료 건수",
        "미완료 건수",
        "처리완료율",
    ]
    monthly_columns = ["업무유형구분", "기간_연월", "접수 건수"]
    customer_columns = ["업무유형구분", "고객사", "접수 건수"]
    monthly_status_columns = ["기간_연월", "접수 건수", "처리완료 건수", "미완료 건수", "처리완료율"]
    if dataframe.empty or "업무유형구분" not in dataframe.columns:
        return {
            "summary": pd.DataFrame(columns=summary_columns),
            "monthly": pd.DataFrame(columns=monthly_columns),
            "customers": pd.DataFrame(columns=customer_columns),
            "monthly_status": pd.DataFrame(columns=monthly_status_columns),
            "manufacturers": pd.DataFrame(columns=["제조사", "접수 건수"]),
        }

    working = dataframe.copy()
    working["업무유형구분"] = working["업무유형구분"].fillna("기타").astype(str)
    status = working.get("처리상태구분", pd.Series("미완료", index=working.index)).fillna("미완료")
    working["_처리완료"] = status.eq("완료")
    total = int(len(working))

    summary = (
        working.groupby("업무유형구분", dropna=False)
        .agg(**{"접수 건수": ("업무유형구분", "size"), "처리완료 건수": ("_처리완료", "sum")})
        .reset_index()
    )
    summary["접수 건수"] = summary["접수 건수"].astype(int)
    summary["처리완료 건수"] = summary["처리완료 건수"].astype(int)
    summary["미완료 건수"] = summary["접수 건수"] - summary["처리완료 건수"]
    summary["전체 비중"] = summary["접수 건수"].map(
        lambda value: round(value / total * 100, 1) if total else 0.0
    )
    summary["처리완료율"] = summary.apply(
        lambda row: round(row["처리완료 건수"] / row["접수 건수"] * 100, 1)
        if row["접수 건수"]
        else 0.0,
        axis=1,
    )
    summary = summary[summary_columns].sort_values(
        ["접수 건수", "업무유형구분"], ascending=[False, True]
    ).reset_index(drop=True)

    if "기간_연월" in working.columns:
        monthly = (
            working.dropna(subset=["기간_연월"])
            .groupby(["업무유형구분", "기간_연월"], dropna=False)
            .size()
            .reset_index(name="접수 건수")
            .sort_values(["업무유형구분", "기간_연월"])
            .reset_index(drop=True)
        )
        monthly_status = (
            working.dropna(subset=["기간_연월"]).groupby("기간_연월")
            .agg(**{"접수 건수": ("업무유형구분", "size"), "처리완료 건수": ("_처리완료", "sum")})
            .reset_index()
        )
        monthly_status["미완료 건수"] = monthly_status["접수 건수"] - monthly_status["처리완료 건수"]
        monthly_status["처리완료율"] = (
            monthly_status["처리완료 건수"] / monthly_status["접수 건수"] * 100
        ).round(1)
    else:
        monthly = pd.DataFrame(columns=monthly_columns)
        monthly_status = pd.DataFrame(columns=monthly_status_columns)

    if "고객사" in working.columns:
        customer_working = working.assign(고객사=working["고객사"].fillna("미입력").astype(str))
        customers = (
            customer_working.groupby(["업무유형구분", "고객사"], dropna=False)
            .size()
            .reset_index(name="접수 건수")
            .sort_values(["업무유형구분", "접수 건수", "고객사"], ascending=[True, False, True])
            .reset_index(drop=True)
        )
    else:
        customers = pd.DataFrame(columns=customer_columns)

    claims = working.loc[working["업무유형구분"].eq("부품수리/클레임")]
    manufacturers = (
        claims.get("제조사", pd.Series(index=claims.index, dtype="object"))
        .fillna("미입력").astype(str).replace(r"^\s*$", "미입력", regex=True)
        .value_counts().rename_axis("제조사").reset_index(name="접수 건수")
    )
    return {
        "summary": summary, "monthly": monthly, "customers": customers,
        "monthly_status": monthly_status[monthly_status_columns], "manufacturers": manufacturers,
    }


def build_kpi(dataframe: pd.DataFrame) -> dict[str, Any]:
    total = int(len(dataframe))
    completed = int((dataframe.get("처리상태구분", pd.Series(index=dataframe.index, dtype="object")) == "완료").sum())
    incomplete = total - completed
    work_counts = dataframe.get("업무유형구분", pd.Series(index=dataframe.index, dtype="object")).fillna("기타").value_counts()
    downtime = pd.to_numeric(dataframe.get(DOWNTIME_COLUMN, pd.Series(index=dataframe.index, dtype="float")), errors="coerce")
    downtime_input = int(downtime.notna().sum())
    downtime_occurred = int((downtime.fillna(0) > 0).sum())

    return {
        "총 접수 건수": total,
        "처리완료 건수": completed,
        "미완료 건수": incomplete,
        "처리완료율": round((completed / total * 100), 1) if total else 0.0,
        "긴급방문 건수": int(work_counts.get("긴급방문", 0)),
        "일반방문 건수": int(work_counts.get("일반방문", 0)),
        "원격지원 건수": int(work_counts.get("원격지원", 0)),
        "부품수리/클레임 건수": int(work_counts.get("부품수리/클레임", 0)),
        "VOC 건수": int(work_counts.get("VOC", 0)),
        "기타 업무유형 건수": int(work_counts.get("기타", 0)),
        "라인 중단 시간 입력 건수": downtime_input,
        "라인 중단 발생 건수": downtime_occurred,
        "라인 중단 총 시간": float(downtime.dropna().sum()) if downtime_input else 0.0,
        "라인 중단 평균 시간": round(float(downtime.dropna().mean()), 1) if downtime_input else 0.0,
        "라인 중단 최대 시간": float(downtime.dropna().max()) if downtime_input else 0.0,
        "고객사 미입력 건수": missing_count(dataframe, "고객사"),
        "대분류 미입력 건수": missing_count(dataframe, "대분류"),
        "중분류 미입력 건수": missing_count(dataframe, "중분류"),
        "소분류 미입력 건수": missing_count(dataframe, "소분류 (고장부품)"),
        "접수일 누락 건수": missing_count(dataframe, "접수일"),
    }


def build_tables(dataframe: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {
        "월별 접수 건수": count_by(dataframe, "기간_연월", "기간_연월", "접수 건수", sort_index=True),
        "월별 라인 중단 시간": sum_by(dataframe, "기간_연월", DOWNTIME_COLUMN, "기간_연월", "라인 중단 시간", sort_index=True),
        "업무유형구분별 접수 건수": count_by(dataframe, "업무유형구분", "업무유형구분", "접수 건수"),
        "상태별 접수 건수": count_by(dataframe, "상태", "상태", "접수 건수"),
        "고객사별 접수 건수 TOP 20": count_by(dataframe, "고객사", "고객사", "접수 건수", top=20),
        "고객사별 라인 중단 시간 TOP 20": sum_by(dataframe, "고객사", DOWNTIME_COLUMN, "고객사", "라인 중단 시간", top=20),
        "BOOTH별 접수 건수": count_by(dataframe, "BOOTH", "BOOTH", "접수 건수"),
        "LINE별 접수 건수": count_by(dataframe, "LINE", "LINE", "접수 건수"),
        "공정별 접수 건수": count_by(dataframe, "공정", "공정", "접수 건수"),
        "로보트 기종별 접수 건수": count_by(dataframe, "로보트 기종", "로보트 기종", "접수 건수"),
        "고장원인별 접수 건수": count_by(dataframe, "고장원인", "고장원인", "접수 건수"),
        "대분류별 접수 건수": count_by(dataframe, "대분류", "대분류", "접수 건수"),
        "중분류별 접수 건수": count_by(dataframe, "중분류", "중분류", "접수 건수"),
        "소분류 고장부품별 접수 건수 TOP 20": count_by(dataframe, "소분류 (고장부품)", "소분류 (고장부품)", "접수 건수", top=20),
        "대분류별 라인 중단 시간": sum_by(dataframe, "대분류", DOWNTIME_COLUMN, "대분류", "라인 중단 시간"),
        "소분류 고장부품별 라인 중단 시간 TOP 20": sum_by(dataframe, "소분류 (고장부품)", DOWNTIME_COLUMN, "소분류 (고장부품)", "라인 중단 시간", top=20),
        "처리사원별 처리 건수": count_by(dataframe, "처리사원", "처리사원", "처리 건수"),
        "진행중/미완료 이슈 목록": open_issues(dataframe),
        "라인 중단 시간 TOP 20 이슈 목록": downtime_top_issues(dataframe),
    }


def build_quality(source_data: pd.DataFrame, period_data: pd.DataFrame) -> dict[str, Any]:
    cleaning_counts = source_data.attrs.get("cleaning_counts", {})
    downtime = pd.to_numeric(period_data.get(DOWNTIME_COLUMN, pd.Series(index=period_data.index, dtype="float")), errors="coerce")
    return {
        "전체 원본 건수": int(len(source_data)),
        "분석 대상 건수": int(len(period_data)),
        "접수일 누락 건수": missing_count(period_data, "접수일"),
        "고객사 미입력 건수": missing_count(period_data, "고객사"),
        "BOOTH 미입력 건수": missing_count(period_data, "BOOTH"),
        "LINE 미입력 건수": missing_count(period_data, "LINE"),
        "공정 미입력 건수": missing_count(period_data, "공정"),
        "로보트 기종 미입력 건수": missing_count(period_data, "로보트 기종"),
        "고장원인 미입력 건수": missing_count(period_data, "고장원인"),
        "라인 중단 시간 미입력 건수": int(downtime.isna().sum()),
        "대분류 미입력 건수": missing_count(period_data, "대분류"),
        "중분류 미입력 건수": missing_count(period_data, "중분류"),
        "소분류 미입력 건수": missing_count(period_data, "소분류 (고장부품)"),
        "선택안함 정리 건수": int(cleaning_counts.get("선택안함 정리 건수", 0)),
        "-- 정리 건수": int(cleaning_counts.get("-- 정리 건수", 0)),
        "#NAME? 정리 건수": int(cleaning_counts.get("#NAME? 정리 건수", 0)),
    }


def count_by(dataframe: pd.DataFrame, column: str, label_name: str, count_name: str, top: int | None = None, sort_index: bool = False) -> pd.DataFrame:
    if dataframe.empty or column not in dataframe.columns:
        return pd.DataFrame(columns=[label_name, count_name])
    series = dataframe[column].fillna("미분류").astype(str)
    result = series.value_counts(dropna=False).rename_axis(label_name).reset_index(name=count_name)
    if sort_index:
        result = result.sort_values(label_name).reset_index(drop=True)
    if top:
        result = result.head(top)
    return result


def sum_by(dataframe: pd.DataFrame, group_column: str, value_column: str, label_name: str, value_name: str, top: int | None = None, sort_index: bool = False) -> pd.DataFrame:
    if dataframe.empty or group_column not in dataframe.columns or value_column not in dataframe.columns:
        return pd.DataFrame(columns=[label_name, value_name])
    working = dataframe.copy()
    working[group_column] = working[group_column].fillna("미분류").astype(str)
    working[value_column] = pd.to_numeric(working[value_column], errors="coerce").fillna(0)
    result = working.groupby(group_column, dropna=False)[value_column].sum().reset_index()
    result.columns = [label_name, value_name]
    if sort_index:
        result = result.sort_values(label_name)
    else:
        result = result.sort_values(value_name, ascending=False)
    if top:
        result = result.head(top)
    return result.reset_index(drop=True)


def open_issues(dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataframe.empty:
        return _select_columns(dataframe, OPEN_ISSUE_COLUMNS)
    status = dataframe.get("처리상태구분", pd.Series("미완료", index=dataframe.index))
    return _select_columns(dataframe.loc[status != "완료"], OPEN_ISSUE_COLUMNS)


def downtime_top_issues(dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataframe.empty or DOWNTIME_COLUMN not in dataframe.columns:
        return _select_columns(dataframe, DOWNTIME_TOP_COLUMNS)
    working = dataframe.copy()
    working[DOWNTIME_COLUMN] = pd.to_numeric(working[DOWNTIME_COLUMN], errors="coerce")
    working = working.loc[working[DOWNTIME_COLUMN].fillna(0) > 0].sort_values(DOWNTIME_COLUMN, ascending=False).head(20)
    return _select_columns(working, DOWNTIME_TOP_COLUMNS)


def _select_columns(dataframe: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    existing = [column for column in columns if column in dataframe.columns]
    return dataframe.loc[:, existing].copy()


def missing_count(dataframe: pd.DataFrame, column: str) -> int:
    if column not in dataframe.columns:
        return int(len(dataframe))
    return int(dataframe[column].isna().sum())
