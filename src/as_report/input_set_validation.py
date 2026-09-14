from __future__ import annotations

from collections import Counter
from datetime import datetime
import re
import unicodedata
from typing import Any

import pandas as pd

from .input_set import ApprovedInputSet, REQUIRED_INPUT_ROLES

ROBOT_MODEL_SOURCE_COLUMN = "본체(Manifold)"
AS_ROBOT_MODEL_COLUMN = "로보트 기종"
AS_PART_COLUMN = "소분류 (고장부품)"
MASTER_PART_COLUMN = "품명"

MISSING_VALUES = {"", "--", "미입력", "선택안함", "NAN", "NONE", "<NA>"}
NON_MODEL_KEYS = {"FANUC", "YASKAWA", "야스카와", "PAINT"}
HYPHEN_TRANSLATION = str.maketrans({character: "-" for character in "‐‑‒–—−﹘﹣－"})


def normalize_robot_model_key(value: Any) -> str:
    """Return only the approved, loss-limited robot-model normalization."""
    text = _text(value)
    if text.upper() in MISSING_VALUES:
        return ""
    normalized = unicodedata.normalize("NFKC", text).upper().translate(HYPHEN_TRANSLATION)
    return re.sub(r"\s+", "", normalized)


def build_input_set_validation(
    raw_df: pd.DataFrame,
    customer_robot_master_df: pd.DataFrame,
    failure_part_master_df: pd.DataFrame,
    input_set: ApprovedInputSet,
    *,
    run_id: str,
    period_type: str,
    period_label: str,
    start_date: str,
    end_date: str,
    filters: dict[str, Any] | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    """Build Gate B validation-only tables from the approved three-file set."""
    generated_at = created_at or datetime.now().isoformat(timespec="seconds")
    robot = build_robot_model_validation(raw_df, customer_robot_master_df)
    part = build_failure_part_validation(raw_df, failure_part_master_df)
    return {
        "validation_scope": "INPUT-BASELINE-20260720 Gate B validation-only",
        "run_id": run_id,
        "created_at": generated_at,
        "input_set_id": input_set.input_set_id,
        "input_set_signature": input_set.signature,
        "period_type": period_type,
        "period_label": period_label,
        "start_date": start_date,
        "end_date": end_date,
        "filters": filters or {},
        "run_summary": _run_summary_frame(
            input_set,
            run_id=run_id,
            period_type=period_type,
            period_label=period_label,
            start_date=start_date,
            end_date=end_date,
            filters=filters or {},
            created_at=generated_at,
        ),
        "input_file_identity": _input_file_identity_frame(input_set),
        **robot,
        **part,
        "validation_note": (
            "승인된 3개 입력 파일을 읽기 전용으로 비교한 validation-only 결과입니다. "
            "로봇 기종은 exact/안전 정규화 exact 비교만 사용하며 추정 보정하지 않습니다."
        ),
    }


def build_robot_model_validation(raw_df: pd.DataFrame, master_df: pd.DataFrame) -> dict[str, Any]:
    raw_series = raw_df.get(AS_ROBOT_MODEL_COLUMN, pd.Series(index=raw_df.index, dtype="object"))
    master_series = master_df.get(ROBOT_MODEL_SOURCE_COLUMN, pd.Series(index=master_df.index, dtype="object"))

    master_records = _robot_master_records(master_series)
    master_by_key = {record["robot_model_key"]: record for record in master_records if record["robot_model_key"]}
    master_keys = set(master_by_key)

    as_records: list[dict[str, Any]] = []
    exact_key_match_count = 0
    canonical_match_count = 0
    for index, value in raw_series.items():
        raw_value = _display_or_missing(value)
        key = normalize_robot_model_key(value)
        master_record = master_by_key.get(key)
        key_matches = bool(key and master_record)
        if key_matches:
            exact_key_match_count += 1

        status, canonical, note = _robot_match_result(value, key, master_record)
        if status in {"exact", "normalized_exact"}:
            canonical_match_count += 1
        source_row = raw_df.loc[index] if index in raw_df.index else pd.Series(dtype="object")
        as_records.append(
            {
                "as_row_index": index,
                "*ID": source_row.get("*ID", ""),
                "접수일": source_row.get("접수일", ""),
                "고객사": source_row.get("고객사", ""),
                "robot_model_raw": raw_value,
                "robot_model_key": key,
                "robot_model": canonical,
                "robot_model_match_status": status,
                "safe_key_in_master": "Y" if key_matches else "N",
                "검토 비고": note,
            }
        )

    as_match_df = pd.DataFrame(as_records)
    total_as = int(len(raw_df))
    raw_model_entered_count = int(
        raw_series.map(_text).map(lambda value: value not in {"", "--"}).sum()
    )
    valid_model_count = int(as_match_df["robot_model_key"].ne("").sum())
    missing_model_count = total_as - valid_model_count
    review_count = int(as_match_df["robot_model_match_status"].eq("review_required").sum())
    normalized_count = int(as_match_df["robot_model_match_status"].eq("normalized_exact").sum())
    exact_count = int(as_match_df["robot_model_match_status"].eq("exact").sum())

    match_summary = pd.DataFrame(
        [
            {"항목": "전체 AS 접수건수", "값": total_as},
            {"항목": "AS 로봇 기종 원문 입력(선택안함 포함)", "값": raw_model_entered_count},
            {"항목": "AS 로봇 기종 분석 유효 입력", "값": valid_model_count},
            {"항목": "AS 로봇 기종 미입력", "값": missing_model_count},
            {"항목": "설치자산 기종 안전 키 매칭", "값": exact_key_match_count},
            {"항목": "원문 입력 기준 모델 매칭률(%)", "값": _percent(exact_key_match_count, raw_model_entered_count)},
            {"항목": "분석 유효 입력 기준 모델 매칭률(%)", "값": _percent(exact_key_match_count, valid_model_count)},
            {"항목": "전체 AS 기준 모델 매칭 coverage(%)", "값": _percent(exact_key_match_count, total_as)},
            {"항목": "canonical exact", "값": exact_count},
            {"항목": "canonical normalized_exact", "값": normalized_count},
            {"항목": "canonical 적용 가능 AS 건수", "값": canonical_match_count},
            {"항목": "검토 필요 AS 건수", "값": review_count},
        ]
    )

    master_value_df = pd.DataFrame(master_records)
    master_input_count = int(master_series.map(normalize_robot_model_key).ne("").sum())
    master_missing_count = int(len(master_df) - master_input_count)
    master_review_rows = int(master_value_df.loc[master_value_df["robot_model_match_status"].eq("review_required"), "등록 행 수"].sum()) if not master_value_df.empty else 0
    master_mapped_rows = int(master_value_df.loc[master_value_df["robot_model_match_status"].isin(["exact", "normalized_exact"]), "등록 행 수"].sum()) if not master_value_df.empty else 0
    non_model_rows = int(master_value_df.loc[master_value_df["robot_model_key"].isin(NON_MODEL_KEYS), "등록 행 수"].sum()) if not master_value_df.empty else 0
    robot_quality = pd.DataFrame(
        [
            {"항목": "전체 등록 로봇 수", "값": int(len(master_df))},
            {"항목": "본체(Manifold) 입력", "값": master_input_count},
            {"항목": "본체(Manifold) 미입력", "값": master_missing_count},
            {"항목": "원본 모델값 종류 수", "값": int(master_series.map(_text).loc[lambda values: values.ne("")].nunique())},
            {"항목": "안전 정규화 키 종류 수", "값": int(master_series.map(normalize_robot_model_key).loc[lambda values: values.ne("")].nunique())},
            {"항목": "AS 입력과 exact/normalized-exact 비교 가능 등록 행", "값": master_mapped_rows},
            {"항목": "검토 필요 등록 행", "값": master_review_rows},
            {"항목": "제조사명/비모델값 등록 행", "값": non_model_rows},
        ]
    )

    install_summary = _robot_install_summary(master_value_df, as_match_df)
    unmatched_preview = as_match_df.loc[
        as_match_df["robot_model_match_status"].eq("review_required"),
        ["*ID", "접수일", "고객사", "robot_model_raw", "robot_model_key", "robot_model_match_status", "검토 비고"],
    ].copy()
    dimension_summary = _robot_dimension_summary(master_df)
    return {
        "robot_quality_summary": robot_quality,
        "robot_model_value_review": master_value_df,
        "robot_model_match_summary": match_summary,
        "robot_model_install_summary": install_summary,
        "robot_model_unmatched_preview": unmatched_preview,
        "robot_dimension_summary": dimension_summary,
        "robot_model_note": (
            "08 Master의 본체(Manifold)를 robot_model_raw로 보존하고 exact/안전 정규화 exact만 비교했습니다. "
            "분모는 현재 가동 수가 아닌 등록 설치대수이며, 제조사명·비모델값과 미승인 표기는 검토 대상으로 제외했습니다."
        ),
    }


def build_failure_part_validation(raw_df: pd.DataFrame, master_df: pd.DataFrame) -> dict[str, Any]:
    raw_part = raw_df.get(AS_PART_COLUMN, pd.Series(index=raw_df.index, dtype="object")).map(_text)
    master_part = master_df.get(MASTER_PART_COLUMN, pd.Series(index=master_df.index, dtype="object")).map(_text)
    master_groups = {
        name: group.copy()
        for name, group in master_df.assign(_part_name=master_part).loc[lambda frame: frame["_part_name"].ne("")].groupby("_part_name", dropna=False)
    }
    master_names = set(master_groups)

    records: list[dict[str, Any]] = []
    for index, part_name in raw_part.items():
        row = raw_df.loc[index] if index in raw_df.index else pd.Series(dtype="object")
        group = master_groups.get(part_name)
        exact_name = bool(part_name and group is not None)
        master_row_count = int(len(group)) if group is not None else 0
        hierarchy_set = _master_hierarchy_set(group) if group is not None else set()
        raw_hierarchy = (_text(row.get("대분류")), _text(row.get("중분류")))
        multi_value = bool(part_name and "," in part_name)
        duplicate_name = master_row_count > 1
        aopr_conflict = part_name.upper() == "AOPR" and len(hierarchy_set) > 1
        hierarchy_mismatch = exact_name and raw_hierarchy not in hierarchy_set
        reasons = []
        if not part_name:
            reasons.append("미입력")
        elif not exact_name:
            reasons.append("Master exact 미매칭")
        if multi_value:
            reasons.append("multi-value")
        if duplicate_name:
            reasons.append("중복명 후보")
        if aopr_conflict:
            reasons.append("AOPR 분류 충돌")
        if hierarchy_mismatch:
            reasons.append("대·중분류 불일치")
        records.append(
            {
                "*ID": row.get("*ID", ""),
                "접수일": row.get("접수일", ""),
                "고객사": row.get("고객사", ""),
                "대분류": row.get("대분류", ""),
                "중분류": row.get("중분류", ""),
                "소분류 (고장부품)": part_name or "미입력",
                "exact_match": "Y" if exact_name else "N",
                "master 동일 품명 행 수": master_row_count,
                "multi_value": "Y" if multi_value else "N",
                "duplicate_name_candidate": "Y" if duplicate_name else "N",
                "aopr_category_conflict": "Y" if aopr_conflict else "N",
                "hierarchy_mismatch": "Y" if hierarchy_mismatch else "N",
                "검토 사유": ", ".join(reasons),
            }
        )

    review = pd.DataFrame(records)
    valid = review["소분류 (고장부품)"].ne("미입력")
    exact = review["exact_match"].eq("Y")
    summary = pd.DataFrame(
        [
            {"항목": "전체 AS 접수건수", "값": int(len(raw_df))},
            {"항목": "고장부품 입력", "값": int(valid.sum())},
            {"항목": "고장부품 미입력", "값": int((~valid).sum())},
            {"항목": "품명 exact match", "값": int((valid & exact).sum())},
            {"항목": "품명 exact 미매칭", "값": int((valid & ~exact).sum())},
            {"항목": "품명 exact 매칭률(%)", "값": _percent(int((valid & exact).sum()), int(valid.sum()))},
            {"항목": "중복명 후보", "값": int(review["duplicate_name_candidate"].eq("Y").sum())},
            {"항목": "AOPR 분류 충돌", "값": int(review["aopr_category_conflict"].eq("Y").sum())},
            {"항목": "multi-value", "값": int(review["multi_value"].eq("Y").sum())},
            {"항목": "대·중분류 불일치", "값": int(review["hierarchy_mismatch"].eq("Y").sum())},
        ]
    )
    duplicate_rows = []
    for name, group in master_groups.items():
        if len(group) <= 1:
            continue
        hierarchy = _master_hierarchy_set(group)
        duplicate_rows.append(
            {
                "품명": name,
                "Master 행 수": int(len(group)),
                "대·중분류 조합 수": int(len(hierarchy)),
                "대·중분류 조합": " | ".join(f"{major} > {middle}" for major, middle in sorted(hierarchy)),
                "검토 상태": "분류 충돌 검토 필요" if len(hierarchy) > 1 else "중복 행 검토 필요",
            }
        )
    review_required = review.loc[review["검토 사유"].ne("")].copy()
    return {
        "part_quality_summary": summary,
        "part_duplicate_name_candidates": pd.DataFrame(duplicate_rows),
        "part_review_required": review_required,
        "part_validation_note": "품명 exact 비교만 사용했습니다. multi-value, 중복명, 분류 불일치는 자동 보정하지 않고 검토 대상으로 분리했습니다.",
    }


def _robot_master_records(master_series: pd.Series) -> list[dict[str, Any]]:
    grouped: dict[str, list[str]] = {}
    for value in master_series.tolist():
        key = normalize_robot_model_key(value)
        grouped.setdefault(key, []).append(_display_or_missing(value))

    records = []
    for key, raw_values in grouped.items():
        counts = Counter(raw_values)
        representative = counts.most_common(1)[0][0]
        if not key:
            status = "missing"
            canonical = ""
            note = "본체(Manifold) 미입력"
        elif key in NON_MODEL_KEYS:
            status = "review_required"
            canonical = ""
            note = "제조사명 또는 비모델 입력값"
        else:
            status = "review_required"
            canonical = ""
            note = "현재 AS 입력과 exact/normalized-exact 비교 전"
        records.append(
            {
                "robot_model_raw": representative,
                "robot_model_key": key,
                "robot_model": canonical,
                "robot_model_match_status": status,
                "등록 행 수": len(raw_values),
                "원본 표기 수": len(counts),
                "원본 표기": " | ".join(sorted(counts)),
                "검토 비고": note,
            }
        )

    # Master status becomes approved only when the current Raw has a matching
    # exact/normalized-exact key. The caller applies this from AS rows later.
    return records


def _robot_match_result(value: Any, key: str, master_record: dict[str, Any] | None) -> tuple[str, str, str]:
    raw_value = _text(value)
    if not key:
        return "missing", "", "로봇 기종 미입력"
    if key in NON_MODEL_KEYS:
        return "review_required", "", "제조사명 또는 비모델 입력값"
    if master_record is None:
        return "review_required", "", "등록 로봇 Master에서 안전 정규화 키를 찾을 수 없음"
    source_values = {item.strip() for item in str(master_record.get("원본 표기", "")).split("|") if item.strip()}
    status = "exact" if raw_value in source_values else "normalized_exact"
    canonical = str(master_record.get("robot_model_raw", ""))
    master_record["robot_model"] = canonical
    master_record["robot_model_match_status"] = status
    master_record["검토 비고"] = "현재 AS 입력과 exact 비교" if status == "exact" else "현재 AS 입력과 안전 정규화 exact 비교"
    return status, canonical, master_record["검토 비고"]


def _robot_install_summary(master_value_df: pd.DataFrame, as_match_df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "로보트 기종",
        "robot_model_key",
        "등록 설치대수",
        "매칭된 AS 접수건수",
        "등록 설치대수 기준 대당 AS 접수건수",
        "match status",
    ]
    if master_value_df.empty or as_match_df.empty:
        return pd.DataFrame(columns=columns)
    eligible_master = master_value_df.loc[master_value_df["robot_model_match_status"].isin(["exact", "normalized_exact"])].copy()
    eligible_as = as_match_df.loc[as_match_df["robot_model_match_status"].isin(["exact", "normalized_exact"])].copy()
    if eligible_master.empty:
        return pd.DataFrame(columns=columns)

    as_counts = eligible_as.groupby("robot_model_key", dropna=False).size().to_dict()
    rows = []
    for _, row in eligible_master.iterrows():
        installed = int(row["등록 행 수"])
        received = int(as_counts.get(row["robot_model_key"], 0))
        rows.append(
            {
                "로보트 기종": row["robot_model"],
                "robot_model_key": row["robot_model_key"],
                "등록 설치대수": installed,
                "매칭된 AS 접수건수": received,
                "등록 설치대수 기준 대당 AS 접수건수": round(received / installed, 3) if installed else 0.0,
                "match status": row["robot_model_match_status"],
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["등록 설치대수 기준 대당 AS 접수건수", "매칭된 AS 접수건수"], ascending=[False, False]
    ).reset_index(drop=True)


def _robot_dimension_summary(master_df: pd.DataFrame) -> pd.DataFrame:
    dimensions = {
        "설치연도": "설치연도(Installation year)",
        "고객사": "고객사(Customer)",
        "국가": "국가(country)",
        "공장": "공장(plant)",
        "컨트롤러": "컨트롤러(Controller)",
    }
    rows = []
    for label, column in dimensions.items():
        if column not in master_df.columns:
            rows.append({"구분": label, "입력값": "컬럼 없음", "등록 행 수": 0})
            continue
        values = master_df[column].map(_display_or_missing)
        for value, count in values.value_counts(dropna=False).head(20).items():
            rows.append({"구분": label, "입력값": value, "등록 행 수": int(count)})
    return pd.DataFrame(rows)


def _run_summary_frame(
    input_set: ApprovedInputSet,
    *,
    run_id: str,
    period_type: str,
    period_label: str,
    start_date: str,
    end_date: str,
    filters: dict[str, Any],
    created_at: str,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"항목": "검증 범위", "값": "Gate B validation-only"},
            {"항목": "input-set ID", "값": input_set.input_set_id},
            {"항목": "input-set signature", "값": input_set.signature},
            {"항목": "run_id", "값": run_id},
            {"항목": "생성시각", "값": created_at},
            {"항목": "분석 기간 유형", "값": period_type},
            {"항목": "분석 기간", "값": period_label},
            {"항목": "분석 시작일", "값": start_date},
            {"항목": "분석 종료일", "값": end_date},
            {"항목": "필터", "값": _filters_text(filters)},
        ]
    )


def _input_file_identity_frame(input_set: ApprovedInputSet) -> pd.DataFrame:
    rows = []
    for role in REQUIRED_INPUT_ROLES:
        identity = input_set.files[role]
        rows.append(
            {
                "role": role,
                "경로": str(identity.path),
                "SHA-256": identity.sha256,
                "행 수": identity.row_count,
                "열 수": identity.column_count,
                "고유 *ID 수": identity.unique_id_count,
                "중복 *ID 수": identity.duplicate_id_count,
                "접수일 최소": identity.date_min,
                "접수일 최대": identity.date_max,
            }
        )
    return pd.DataFrame(rows)


def _master_hierarchy_set(group: pd.DataFrame | None) -> set[tuple[str, str]]:
    if group is None or group.empty:
        return set()
    return {
        (_text(row.get("대분류")), _text(row.get("중분류")))
        for _, row in group.iterrows()
    }


def _filters_text(filters: dict[str, Any]) -> str:
    if not filters:
        return "없음"
    return ", ".join(f"{key}={value}" for key, value in sorted(filters.items()))


def _percent(numerator: int, denominator: int) -> float:
    return round(numerator / denominator * 100, 1) if denominator else 0.0


def _display_or_missing(value: Any) -> str:
    text = _text(value)
    return text if text and text.upper() not in MISSING_VALUES else "미입력"


def _text(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()
