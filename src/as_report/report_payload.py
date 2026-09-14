"""Deterministic presentation of existing analysis, without new calculations."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
import json
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal

import pandas as pd

EvidenceStatus = Literal["Observed", "Inferred", "Unverified"]


@dataclass(frozen=True)
class ReportTable:
    title: str
    columns: list[str]
    rows: list[list[Any]]
    source: str
    evidence_status: EvidenceStatus = "Observed"


@dataclass(frozen=True)
class ReportSection:
    key: str
    title: str
    paragraphs: list[str]
    tables: list[ReportTable]
    evidence_status: EvidenceStatus = "Observed"


@dataclass(frozen=True)
class ReportPayload:
    metadata: dict[str, Any]
    scope: dict[str, Any]
    sections: list[ReportSection]
    limitations: list[str]
    charts: list[dict[str, str]] = field(default_factory=list)
    schema_version: str = "2.0"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, allow_nan=False)

    @property
    def fingerprint(self) -> str:
        return sha256(self.to_json().encode("utf-8")).hexdigest()

    @classmethod
    def from_json(cls, value: str) -> ReportPayload:
        data = json.loads(value)
        data["sections"] = [ReportSection(**{**s, "tables": [ReportTable(**t) for t in s["tables"]]}) for s in data["sections"]]
        return cls(**data)


def _scalar(value: Any) -> Any:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (date, datetime, pd.Timestamp)):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return value if isinstance(value, (str, bool, int, float)) else str(value)


def _table(title: str, frame: Any, source: str, columns: list[str] | None = None) -> ReportTable:
    if not isinstance(frame, pd.DataFrame):
        frame = pd.DataFrame()
    if columns is not None:
        frame = frame.loc[:, [c for c in columns if c in frame.columns]]
    return ReportTable(title, [str(c) for c in frame.columns], [[_scalar(v) for v in row] for row in frame.itertuples(index=False, name=None)], source)


def build_report_payload(analysis: dict, narrative: list[str], *, period_range: Any,
                         filters: dict, provenance: dict | None, run_id: str,
                         owner: str, generated_at: str, analysis_version: str) -> ReportPayload:
    """Time and identity must be supplied by the run, never invented by a renderer."""
    raw = dict((provenance or {}).get("files", {}).get("as_raw", {}))
    # Local filesystem locations are unnecessary in downloadable provenance.
    raw.pop("path", None)
    metadata = {"run_id": run_id, "owner": owner, "generated_at": generated_at,
                "analysis_version": analysis_version, "raw_identity": raw,
                "master_identity": None, "analysis_mode": "raw_only"}
    scope = {"period": period_range.period, "start": period_range.start_date.isoformat(),
             "end": period_range.end_date.isoformat(), "label": period_range.label,
             "filters": {k: sorted(v) for k, v in sorted(filters.items())}}
    tables = analysis.get("tables", {})
    kpi = analysis.get("kpi", {})
    metric_keys = ["총 접수 건수", "처리완료 건수", "미완료 건수", "처리완료율"]
    metrics = ReportTable("주요 지표", ["지표", "값", "단위"],
                          [[k.replace("처리완료", "처리 완료"), _scalar(kpi.get(k)), "%" if k.endswith("율") else "건"] for k in metric_keys], "analysis.kpi")
    comparison = analysis.get("comparison", pd.DataFrame())
    if isinstance(comparison, pd.DataFrame) and "항목" in comparison:
        comparison = comparison.loc[~comparison["항목"].astype(str).str.contains("라인 중단", regex=False)]
    legacy = analysis.get("legacy_features", {})
    quality = analysis.get("quality", {})
    quality_rows = [[str(k), _scalar(v)] for k, v in quality.items() if pd.api.types.is_scalar(v)]
    sections = [
        ReportSection("executive_summary", "A/S 종합 현황", list(narrative), []),
        ReportSection("kpis", "주요 지표", [], [metrics]),
        ReportSection("period_comparison", "기간별 비교", [], [_table("기간별 비교", comparison, "analysis.comparison", ["항목", "현재 기간 값", "전년 동기 값", "전년 동기 대비 증감"]), _table("월별 접수 건수", tables.get("월별 접수 건수"), "analysis.tables.월별 접수 건수")]),
        ReportSection("categories", "고객사 및 업무유형 현황", [], [_table("고객사별 접수 건수", tables.get("고객사별 접수 건수 TOP 20"), "analysis.tables.고객사별 접수 건수 TOP 20"), _table("업무유형별 접수 건수", tables.get("업무유형구분별 접수 건수"), "analysis.tables.업무유형구분별 접수 건수")]),
        ReportSection("repeat_candidates", "반복 검토 후보", ["같은 조건의 접수 이력을 확인하는 검토 후보입니다."], [_table("반복 검토 후보", analysis.get("repeat_issues"), "analysis.repeat_issues", ["반복 기준", "조건값", "접수 건수", "최초 접수일", "최근 접수일"])], "Inferred"),
        ReportSection("quality_status", "입력 데이터 확인", ["입력값 확인용이며 원본 데이터를 자동 수정하지 않습니다."], [ReportTable("입력 데이터 현황", ["항목", "값"], quality_rows, "analysis.quality")]),
        ReportSection("claim_manufacturer", "클레임 및 제조사 현황", [str(legacy.get("claim_note", "해당 분석이 제공되지 않았습니다."))], [_table("제조사별 접수 건수", legacy.get("claim_by_manufacturer"), "analysis.legacy_features.claim_by_manufacturer", ["제조사", "접수 건수", "유상 건수", "무상 건수", "미입력 건수"])]),
    ]
    limitations = ["이 보고서는 선택한 접수일과 필터에 해당하는 입력 데이터를 사용합니다.", "고객사 로봇 및 고장부품 Master는 연동하지 않습니다.", "반복 검토 후보는 담당자의 추가 확인이 필요합니다."]
    for section in sections:
        if section.tables and not any(t.rows for t in section.tables):
            limitations.append(f"{section.title}: 표시할 데이터가 없습니다.")
    if not raw:
        limitations.append("원본 식별정보가 없어 문서 생성을 제한합니다.")
    sections.append(ReportSection("limitations", "확인 사항", limitations, [], "Unverified"))
    charts = []
    for section in sections:
        for table in section.tables:
            if table.title in {"월별 접수 건수", "업무유형별 접수 건수"} and len(table.columns) == 2 and table.rows:
                charts.append({"title": table.title, "section": section.key, "table": table.title, "kind": "bar", "x": table.columns[0], "y": table.columns[1]})
    return ReportPayload(metadata, scope, sections, limitations, charts)


def report_style() -> dict:
    return json.loads((Path(__file__).parent / "templates/report_tool/style.json").read_text(encoding="utf-8"))


def display_value(value: Any) -> str:
    return "미입력" if value is None else str(value)
