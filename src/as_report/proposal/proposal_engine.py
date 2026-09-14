from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import pandas as pd

from .proposal_rules import INSPECTION_RULES
from as_report.reporting import is_non_informative_token

CUSTOMER_COL = "고객사(Customer)"
PLANT_COL = "공장(plant)"
ROBOT_NO_COL = "Robot No"
INSTALL_YEAR_COL = "설치연도(Installation year)"
CONTROLLER_COL = "컨트롤러(Controller)"
TARGET_MODEL_COL = "본체(Manifold)"
PROCESS_MAJOR_COL = "공정-대분류 (major category)"
PROCESS_MIDDLE_COL = "공정-중분류 (middle category)"

PREVENTIVE_COLUMNS = [
    "source_row_index",
    "접수일",
    "고객사",
    "공장",
    "BOOTH",
    "LINE",
    "공정",
    "로보트 NO",
    "로보트 기종",
    "설치년도",
    "대분류",
    "중분류",
    "소분류 (고장부품)",
    "proposal_type",
    "inspection_item",
    "applicability_group",
    "matched_rule_id",
    "evidence",
    "evidence_as_count",
    "estimated_age_at_issue",
    "confidence",
    "top_candidate",
    "top_candidate_level",
    "reason",
    "warning",
]

HORIZONTAL_COLUMNS = [
    "source_customer",
    "source_factory",
    "source_robot_model",
    "source_robot_no",
    "source_installation_year",
    "source_issue_year",
    "source_part_category",
    "source_issue_summary",
    "estimated_age_at_issue",
    "target_customer",
    "target_factory",
    "target_booth",
    "target_line",
    "target_process",
    "target_robot_no",
    "target_robot_model",
    "target_controller",
    "target_installation_year",
    "target_age",
    "match_level",
    "proposal_type",
    "inspection_item",
    "confidence",
    "top_candidate",
    "top_candidate_level",
    "top_exclusion_reason",
    "reason",
    "warning",
]


@dataclass(frozen=True)
class ProposalResult:
    preventive_candidates: pd.DataFrame
    horizontal_candidates: pd.DataFrame
    summary: dict[str, Any]


def build_proposal_candidates(
    as_df: pd.DataFrame,
    customer_robot_master_df: pd.DataFrame,
    failure_part_master_df: pd.DataFrame | None = None,
    analysis_period: str = "",
    current_year: int | None = None,
) -> ProposalResult:
    """Build preview-only proposal candidates without mutating source data."""
    source = as_df.copy(deep=True)
    robot_master = customer_robot_master_df.copy(deep=True)
    current_year = current_year or date.today().year

    preventive = _build_preventive_candidates(source)
    horizontal = _build_horizontal_candidates(preventive, source, robot_master, current_year)
    preventive_top_count = int(preventive.get("top_candidate", pd.Series(dtype=bool)).fillna(False).sum()) if not preventive.empty else 0
    horizontal_top_count = int(horizontal.get("top_candidate", pd.Series(dtype=bool)).fillna(False).sum()) if not horizontal.empty else 0
    summary = {
        "analysis_period": analysis_period,
        "as_analysis_row_count": int(len(source)),
        "failure_part_master_row_count": int(len(failure_part_master_df)) if failure_part_master_df is not None else 0,
        "preventive_inspection_candidate_count": int(len(preventive)),
        "preventive_top_candidate_count": preventive_top_count,
        "horizontal_deployment_candidate_count": int(len(horizontal)),
        "horizontal_top_candidate_count": horizontal_top_count,
        "proposal_top_candidate_count": preventive_top_count + horizontal_top_count,
    }
    return ProposalResult(preventive, horizontal, summary)


def _build_preventive_candidates(as_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    evidence_counts = _evidence_counts(as_df)
    for index, row in as_df.iterrows():
        rule = _match_rule(row)
        if rule is None:
            continue
        issue_year = _date_year(row.get("접수일"))
        install_year = _year(row.get("설치년도"))
        estimated_age = issue_year - install_year if issue_year and install_year else ""
        warning = "" if estimated_age != "" else "설치년도 또는 접수연도 누락으로 사용연차 계산 제외"
        confidence = "medium" if estimated_age != "" else "low"
        top_candidate = bool(confidence != "low" and not is_non_informative_token(row.get("소분류 (고장부품)")))
        rows.append(
            {
                "source_row_index": index,
                "접수일": _date_text(row.get("접수일")),
                "고객사": _text(row.get("고객사")),
                "공장": _text(row.get("공장")),
                "BOOTH": _text(row.get("BOOTH")),
                "LINE": _text(row.get("LINE")),
                "공정": _text(row.get("공정")),
                "로보트 NO": _text(row.get("로보트 NO")),
                "로보트 기종": _text(row.get("로보트 기종")),
                "설치년도": install_year or "",
                "대분류": _text(row.get("대분류")),
                "중분류": _text(row.get("중분류")),
                "소분류 (고장부품)": _text(row.get("소분류 (고장부품)")),
                "proposal_type": "preventive_inspection_candidate",
                "inspection_item": rule.inspection_item,
                "applicability_group": rule.applicability_group,
                "matched_rule_id": rule.rule_id,
                "evidence": _evidence_text(row),
                "evidence_as_count": evidence_counts.get(_evidence_key(row), 1),
                "estimated_age_at_issue": estimated_age,
                "confidence": confidence,
                "top_candidate": top_candidate,
                "top_candidate_level": "Medium" if top_candidate else "TOP 제외",
                "reason": f"{rule.inspection_item} 관련 키워드 검출({rule.rule_id})",
                "warning": warning,
            }
        )
    return pd.DataFrame(rows, columns=PREVENTIVE_COLUMNS)


def _build_horizontal_candidates(preventive_df: pd.DataFrame, as_df: pd.DataFrame, robot_master_df: pd.DataFrame, current_year: int) -> pd.DataFrame:
    if preventive_df.empty or robot_master_df.empty:
        return pd.DataFrame(columns=HORIZONTAL_COLUMNS)

    rows: list[dict[str, Any]] = []
    for _, candidate in preventive_df.iterrows():
        source_install_year = _year(candidate.get("설치년도"))
        source_issue_year = _date_year(candidate.get("접수일"))
        if not source_install_year or not source_issue_year:
            continue
        estimated_age = source_issue_year - source_install_year
        source_record = as_df.loc[candidate["source_row_index"]] if candidate["source_row_index"] in as_df.index else pd.Series(dtype="object")
        source_master = _find_source_master(source_record, robot_master_df)
        source_context = _source_context(candidate, source_master)

        for _, target in robot_master_df.iterrows():
            target_install_year = _year(target.get(INSTALL_YEAR_COL))
            match_level = _horizontal_match_level(source_context, target, source_install_year, target_install_year)
            if match_level == "":
                continue
            if _same_robot(source_context, target):
                continue
            warning = ""
            target_age: int | str = ""
            if target_install_year:
                target_age = current_year - target_install_year
                if target_age < estimated_age - 1:
                    continue
            else:
                match_level = "manual_review"
                warning = "target 설치연도 누락으로 사용연차 기반 판단 제외"
            confidence = _confidence(match_level)
            top_candidate_level, top_candidate, top_exclusion_reason = _horizontal_top_decision(
                match_level=match_level,
                source_part_category=candidate.get("소분류 (고장부품)", ""),
                target_factory=target.get(PLANT_COL),
                target_install_year=target_install_year,
            )
            rows.append(
                {
                    "source_customer": source_context["customer"],
                    "source_factory": source_context["factory"],
                    "source_robot_model": source_context["robot_model"],
                    "source_robot_no": source_context["robot_no"],
                    "source_installation_year": source_install_year,
                    "source_issue_year": source_issue_year,
                    "source_part_category": candidate.get("소분류 (고장부품)", ""),
                    "source_issue_summary": _text(source_record.get("접수 내용 (요약)")),
                    "estimated_age_at_issue": estimated_age,
                    "target_customer": _text(target.get(CUSTOMER_COL)),
                    "target_factory": _text(target.get(PLANT_COL)),
                    "target_booth": _text(target.get("BOOTH")),
                    "target_line": _text(target.get("LINE")),
                    "target_process": _target_process(target),
                    "target_robot_no": _text(target.get(ROBOT_NO_COL)),
                    "target_robot_model": _target_model(target),
                    "target_controller": _text(target.get(CONTROLLER_COL)),
                    "target_installation_year": target_install_year or "",
                    "target_age": target_age,
                    "match_level": match_level,
                    "proposal_type": "horizontal_deployment_candidate",
                    "inspection_item": candidate.get("inspection_item", "현장 확인 필요"),
                    "confidence": confidence,
                    "top_candidate": top_candidate,
                    "top_candidate_level": top_candidate_level,
                    "top_exclusion_reason": top_exclusion_reason,
                    "reason": _horizontal_reason(match_level),
                    "warning": warning,
                }
            )

    return pd.DataFrame(rows, columns=HORIZONTAL_COLUMNS).drop_duplicates().reset_index(drop=True)


def _match_rule(row: pd.Series) -> Any | None:
    text = _combined_issue_text(row).lower()
    for rule in INSPECTION_RULES:
        if any(keyword.lower() in text for keyword in rule.keywords):
            return rule
    return None


def _combined_issue_text(row: pd.Series) -> str:
    fields = ["대분류", "중분류", "소분류 (고장부품)", "고장원인", "접수 내용 (요약)", "접수 내용 (자세히)", "처리내용/진행상황 (요약)"]
    return " ".join(_text(row.get(field)) for field in fields)


def _evidence_text(row: pd.Series) -> str:
    values = [_text(row.get(field)) for field in ["소분류 (고장부품)", "중분류", "고장원인", "접수 내용 (요약)"]]
    return " / ".join([value for value in values if value])


def _evidence_counts(as_df: pd.DataFrame) -> dict[tuple[str, str, str], int]:
    counts: dict[tuple[str, str, str], int] = {}
    for _, row in as_df.iterrows():
        key = _evidence_key(row)
        counts[key] = counts.get(key, 0) + 1
    return counts


def _evidence_key(row: pd.Series) -> tuple[str, str, str]:
    return (_norm(row.get("고객사")), _norm(row.get("중분류")), _norm(row.get("소분류 (고장부품)")))


def _find_source_master(source_record: pd.Series, robot_master_df: pd.DataFrame) -> pd.Series:
    if robot_master_df.empty:
        return pd.Series(dtype="object")
    customer = _norm(source_record.get("고객사"))
    booth = _norm(source_record.get("BOOTH"))
    line = _norm(source_record.get("LINE"))
    robot_no = _norm(source_record.get("로보트 NO"))
    master = robot_master_df.copy()
    mask = (
        master.get(CUSTOMER_COL, pd.Series(index=master.index, dtype="object")).map(_norm).eq(customer)
        & master.get("BOOTH", pd.Series(index=master.index, dtype="object")).map(_norm).eq(booth)
        & master.get("LINE", pd.Series(index=master.index, dtype="object")).map(_norm).eq(line)
        & master.get(ROBOT_NO_COL, pd.Series(index=master.index, dtype="object")).map(_norm).eq(robot_no)
    )
    matched = master.loc[mask]
    return matched.iloc[0] if not matched.empty else pd.Series(dtype="object")


def _source_context(candidate: pd.Series, source_master: pd.Series) -> dict[str, str]:
    return {
        "customer": _text(candidate.get("고객사")),
        "factory": _text(source_master.get(PLANT_COL)),
        "booth": _text(candidate.get("BOOTH")),
        "line": _text(candidate.get("LINE")),
        "robot_no": _text(candidate.get("로보트 NO")),
        "robot_model": _text(candidate.get("로보트 기종")) or _target_model(source_master),
        "controller": _text(source_master.get(CONTROLLER_COL)),
        "process": _target_process(source_master),
    }


def _horizontal_match_level(source: dict[str, str], target: pd.Series, source_install_year: int, target_install_year: int | None) -> str:
    target_model = _target_model(target)
    target_controller = _text(target.get(CONTROLLER_COL))
    target_process = _target_process(target)
    if source["robot_model"] and target_model and _norm(source["robot_model"]) == _norm(target_model):
        if target_install_year == source_install_year:
            return "same_model_same_install_year"
        if target_install_year and abs(target_install_year - source_install_year) <= 1:
            return "same_model_near_install_year"
        if target_install_year is None:
            return "manual_review"
    if source["controller"] and source["process"] and _norm(source["controller"]) == _norm(target_controller) and _norm(source["process"]) == _norm(target_process):
        return "same_controller_same_process"
    if source["customer"] and _norm(source["customer"]) == _norm(target.get(CUSTOMER_COL)) and _norm(source["line"]) != _norm(target.get("LINE")):
        return "same_customer_other_line"
    if source["factory"] and _norm(source["factory"]) == _norm(target.get(PLANT_COL)) and _norm(source["robot_no"]) != _norm(target.get(ROBOT_NO_COL)):
        return "same_factory_other_robot"
    return ""


def _same_robot(source: dict[str, str], target: pd.Series) -> bool:
    return (
        _norm(source["customer"]) == _norm(target.get(CUSTOMER_COL))
        and _norm(source["booth"]) == _norm(target.get("BOOTH"))
        and _norm(source["line"]) == _norm(target.get("LINE"))
        and _norm(source["robot_no"]) == _norm(target.get(ROBOT_NO_COL))
    )


def _confidence(match_level: str) -> str:
    if match_level == "same_model_same_install_year":
        return "high"
    if match_level in {"same_model_near_install_year", "same_controller_same_process"}:
        return "medium"
    return "low"


def _horizontal_top_decision(
    match_level: str,
    source_part_category: Any,
    target_factory: Any,
    target_install_year: int | None,
) -> tuple[str, bool, str]:
    if is_non_informative_token(source_part_category):
        return "TOP 제외", False, "source_part_category 비정보성 값"
    if is_non_informative_token(target_factory):
        return "Low", False, "target_factory 없음"
    if target_install_year is None:
        return "TOP 제외", False, "설치년도 없음"
    if match_level == "same_model_same_install_year":
        return "High", True, ""
    if match_level == "same_model_near_install_year":
        return "Medium", True, ""
    if match_level == "same_customer_other_line":
        return "Low", False, "same_customer_other_line은 TOP 제외"
    return "Low", False, "TOP 기준 외 match_level"


def _horizontal_reason(match_level: str) -> str:
    reasons = {
        "same_model_same_install_year": "동일 모델 및 동일 설치연도 기준 수평전개 검토 후보",
        "same_model_near_install_year": "동일 모델 및 근접 설치연도 기준 수평전개 검토 후보",
        "same_controller_same_process": "동일 컨트롤러 및 공정 기준 수평전개 검토 후보",
        "same_customer_other_line": "동일 고객사 내 다른 라인 검토 후보",
        "same_factory_other_robot": "동일 공장 내 다른 로봇 검토 후보",
        "manual_review": "설치연도 누락으로 담당자 검토 필요",
    }
    return reasons.get(match_level, "검토 후보")


def _target_model(row: pd.Series) -> str:
    return _text(row.get(TARGET_MODEL_COL))


def _target_process(row: pd.Series) -> str:
    return " ".join([value for value in [_text(row.get(PROCESS_MAJOR_COL)), _text(row.get(PROCESS_MIDDLE_COL))] if value])


def _year(value: Any) -> int | None:
    text = _text(value)
    if not text:
        return None
    try:
        number = int(float(text[:4]))
    except ValueError:
        return None
    return number if 1900 <= number <= 2100 else None


def _date_year(value: Any) -> int | None:
    timestamp = pd.to_datetime(value, errors="coerce")
    if pd.isna(timestamp):
        return None
    return int(timestamp.year)


def _date_text(value: Any) -> str:
    timestamp = pd.to_datetime(value, errors="coerce")
    if pd.isna(timestamp):
        return ""
    return timestamp.strftime("%Y-%m-%d")


def _text(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def _norm(value: Any) -> str:
    return " ".join(_text(value).upper().split())
