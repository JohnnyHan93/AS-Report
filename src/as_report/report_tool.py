"""Download-only orchestration. Renderers do not read inputs or write reports."""
from dataclasses import asdict
import json

from .report_payload import ReportPayload
from .report_qc import check_artifacts, require_valid


def generate_structured_documents(payload: ReportPayload, formats: tuple[str, ...] = ("docx", "pptx")) -> dict[str, bytes]:
    if not formats or set(formats) - {"docx", "pptx"}:
        raise ValueError("Word 또는 PPTX 형식을 선택해 주세요.")
    issues = require_valid(payload)
    outputs = {}
    if "docx" in formats:
        from .report_docx import render_docx
        outputs["report.docx"] = render_docx(payload)
    if "pptx" in formats:
        from .report_pptx import render_pptx
        outputs["report.pptx"] = render_pptx(payload)
    issues.extend(check_artifacts(payload, outputs))
    if any(i.severity == "error" for i in issues):
        raise ValueError("생성 문서의 분석 식별정보가 일치하지 않습니다.")
    outputs["report_payload.json"] = payload.to_json().encode("utf-8")
    outputs["report_qc.json"] = json.dumps([asdict(i) for i in issues], ensure_ascii=False, indent=2).encode("utf-8")
    return outputs
