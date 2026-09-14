"""Payload and embedded provenance checks. Raw table cells are not authored prose."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from io import BytesIO
import json
import math
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED, BadZipFile

from .report_payload import ReportPayload


@dataclass(frozen=True)
class QCIssue:
    severity: str
    code: str
    location: str
    message: str


def check_report(payload: ReportPayload) -> list[QCIssue]:
    issues: list[QCIssue] = []
    def add(code, location, message, severity="error"):
        issues.append(QCIssue(severity, code, location, message))
    for key in ("run_id", "owner", "generated_at", "analysis_version"):
        if not payload.metadata.get(key):
            add("missing_metadata", key, "생성 식별정보가 없습니다.")
    raw = payload.metadata.get("raw_identity") or {}
    if payload.schema_version != "2.0":
        add("unsupported_schema", "schema_version", "지원하지 않는 보고서 구조입니다.")
    for key, value in (("generated_at", payload.metadata.get("generated_at")),):
        try:
            datetime.fromisoformat(value)
        except (TypeError, ValueError):
            add("invalid_timestamp", key, "생성시각 형식이 올바르지 않습니다.")
    for key in ("file_name", "sha256", "row_count", "unique_id_count", "date_min", "date_max"):
        if key not in raw or raw[key] in (None, ""):
            add("missing_provenance", key, "원본 확인 정보가 없습니다.")
    if raw.get("sha256") and not re.fullmatch(r"[a-fA-F0-9]{64}", raw["sha256"]):
        add("invalid_hash", "raw_identity.sha256", "원본 해시 형식이 맞지 않습니다.")
    for location, value in (("raw.date_min", raw.get("date_min")), ("raw.date_max", raw.get("date_max")), ("scope.start", payload.scope.get("start")), ("scope.end", payload.scope.get("end"))):
        try:
            date.fromisoformat(value)
        except (TypeError, ValueError):
            add("invalid_date", location, "날짜 형식이 올바르지 않습니다.")
    for key in ("row_count", "unique_id_count"):
        if not isinstance(raw.get(key), int) or raw[key] < 0:
            add("invalid_coverage", key, "원본 건수 정보가 올바르지 않습니다.")
    for key in ("period", "start", "end", "filters"):
        if key not in payload.scope or payload.scope[key] is None or payload.scope[key] == "":
            add("missing_scope", key, "기간 또는 필터 정보가 없습니다.")
    if payload.scope.get("start", "") > payload.scope.get("end", ""):
        add("invalid_scope", "scope", "시작일이 종료일보다 늦습니다.")
    required = {"executive_summary", "kpis", "period_comparison", "categories", "repeat_candidates", "quality_status", "claim_manufacturer", "limitations"}
    if required - {s.key for s in payload.sections}:
        add("missing_sections", "sections", "필수 섹션이 없습니다.")
    if len({s.key for s in payload.sections}) != len(payload.sections):
        add("duplicate_sections", "sections", "중복 섹션이 있습니다.")
    forbidden = ("고장률", "귀책", "책임 소재", "원인 확정", "원인으로 확정", "고객 영향 발생", "비용 절감", "개선 효과 확인", "품질 문제로 확정")
    for section in payload.sections:
        if section.key == "kpis" and not any(t.rows for t in section.tables):
            add("missing_metric", "kpis", "핵심 지표 표가 없습니다.")
        if not section.title.strip():
            add("empty_title", section.key, "제목이 없습니다.")
        if section.evidence_status not in {"Observed", "Inferred", "Unverified"}:
            add("invalid_evidence", section.key, "근거 상태가 올바르지 않습니다.")
        for prose in [section.title, *section.paragraphs]:
            if any(word in prose for word in forbidden):
                add("unsafe_narrative", section.key, "작성 문구에 허용되지 않은 판단 표현이 있습니다.")
        for table in section.tables:
            if not table.source or table.evidence_status not in {"Observed", "Inferred", "Unverified"}:
                add("missing_evidence", table.title, "표의 출처 또는 근거 상태가 없습니다.")
            if not table.rows:
                add("empty_table", table.title, "표시할 데이터가 없습니다.", "warning")
            for row in table.rows:
                if len(row) != len(table.columns):
                    add("invalid_table", table.title, "표 열과 행의 크기가 다릅니다.")
                for value in row:
                    if isinstance(value, float) and not math.isfinite(value) or isinstance(value, str) and value in {"NaN", "nan", "None", "NaT"}:
                        add("invalid_value", table.title, "표시할 수 없는 값이 있습니다.")
                    if len(str(value)) > 160:
                        add("long_text", table.title, "긴 원문이 있어 문서 배치 확인이 필요합니다.", "warning")
                if section.key == "kpis" and len(row) == 3:
                    label, value, unit = row
                    if value is None:
                        add("missing_metric", str(label), "핵심 지표 값이 없습니다.")
                    if unit == "%" and (not str(label).endswith("율") or not isinstance(value, (int, float)) or not 0 <= value <= 100):
                        add("invalid_percentage", str(label), "비율 표시 또는 범위를 확인해야 합니다.")
    for chart in payload.charts:
        table = next((t for s in payload.sections if s.key == chart.get("section") for t in s.tables if t.title == chart.get("table")), None)
        if table is None or not table.rows or chart.get("x") not in table.columns or chart.get("y") not in table.columns:
            add("invalid_chart", chart.get("title", ""), "차트의 원본 표가 없거나 비어 있습니다.")
    return issues


def require_valid(payload: ReportPayload) -> list[QCIssue]:
    issues = check_report(payload)
    errors = [i for i in issues if i.severity == "error"]
    if errors:
        raise ValueError("문서 검수 실패: " + "; ".join(f"{i.code} ({i.location})" for i in errors))
    return issues


def artifact_identity(payload: ReportPayload) -> dict:
    return {"metadata": payload.metadata, "scope": payload.scope, "schema_version": payload.schema_version, "payload_sha256": payload.fingerprint}


def embed_identity(content: bytes, payload: ReportPayload) -> bytes:
    """Store same-run identity as an OOXML custom property, not a sidecar claim."""
    prop_ns = "http://schemas.openxmlformats.org/officeDocument/2006/custom-properties"
    vt = "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"
    ct = "http://schemas.openxmlformats.org/package/2006/content-types"
    rel = "http://schemas.openxmlformats.org/package/2006/relationships"
    with ZipFile(BytesIO(content)) as source:
        files = {n: source.read(n) for n in source.namelist()}
    props = ET.fromstring(files["docProps/custom.xml"]) if "docProps/custom.xml" in files else ET.Element(f"{{{prop_ns}}}Properties")
    for child in list(props):
        if child.get("name") == "ASReportIdentity":
            props.remove(child)
    pid = max([int(p.get("pid", "1")) for p in props] + [1]) + 1
    prop = ET.SubElement(props, f"{{{prop_ns}}}property", {"fmtid": "{D5CDD505-2E9C-101B-9397-08002B2CF9AE}", "pid": str(pid), "name": "ASReportIdentity"})
    ET.SubElement(prop, f"{{{vt}}}lpwstr").text = json.dumps(artifact_identity(payload), ensure_ascii=False, sort_keys=True)
    types = ET.fromstring(files["[Content_Types].xml"])
    if not any(p.get("PartName") == "/docProps/custom.xml" for p in types):
        ET.SubElement(types, f"{{{ct}}}Override", {"PartName": "/docProps/custom.xml", "ContentType": "application/vnd.openxmlformats-officedocument.custom-properties+xml"})
    rels = ET.fromstring(files["_rels/.rels"])
    if not any(p.get("Target") == "docProps/custom.xml" for p in rels):
        ids = {p.get("Id") for p in rels}
        rid = "rIdASReport"
        while rid in ids:
            rid += "X"
        ET.SubElement(rels, f"{{{rel}}}Relationship", {"Id": rid, "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/custom-properties", "Target": "docProps/custom.xml"})
    for name, root in (("docProps/custom.xml", props), ("[Content_Types].xml", types), ("_rels/.rels", rels)):
        files[name] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as target:
        for name, value in files.items():
            target.writestr(name, value)
    return output.getvalue()


def check_artifacts(payload: ReportPayload, artifacts: dict[str, bytes]) -> list[QCIssue]:
    issues = []
    for name, content in artifacts.items():
        try:
            with ZipFile(BytesIO(content)) as z:
                root = ET.fromstring(z.read("docProps/custom.xml"))
                identity = json.loads(next(p[0].text for p in root if p.get("name") == "ASReportIdentity"))
            if identity != artifact_identity(payload):
                raise ValueError("identity mismatch")
        except (ValueError, KeyError, StopIteration, ET.ParseError, OSError, BadZipFile) as error:
            issues.append(QCIssue("error", "artifact_mismatch", name, str(error)))
    if not artifacts:
        issues.append(QCIssue("error", "missing_artifacts", "outputs", "생성 파일이 없습니다."))
    return issues
