from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import base64
import json
import logging
import re
from pathlib import Path
import subprocess
import tempfile
import time
from threading import Lock
from typing import Any

import pandas as pd

from as_report.period import PeriodRange
from as_report.report_pdf import render_pdf_report

LOGGER = logging.getLogger(__name__)
PACKAGE_DIR = Path(__file__).resolve().parent
PPT_TEMPLATE_PATH = PACKAGE_DIR / "resources" / "DY_PPT_Template_16x9.pptx"
PRESENTATION_BUILDER_PATH = PACKAGE_DIR / "presentation" / "build_report.ps1"
PDF_BROWSER_CANDIDATES = (
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
)
PDF_RENDER_WAIT_SECONDS = 30
PPT_GENERATION_LOCK = Lock()


class PptGenerationError(RuntimeError):
    """A classified PowerPoint failure safe to show without internal paths or CLIXML."""


def _ppt_error_message(detail: str) -> str:
    text = detail.lower()
    if "80070520" in text or "logon session" in text:
        return "PPT 생성 오류 [로그인 세션]: 앱 실행 계정에서 PowerPoint를 사용할 수 없습니다. 운영자가 앱을 닫고 Windows에 로그인한 계정에서 AS_Report.bat로 다시 실행해 주세요."
    if "80040154" in text or "class not registered" in text:
        return "PPT 생성 오류 [PowerPoint 설치]: PowerPoint 자동화 구성 요소를 찾을 수 없습니다. 운영 PC의 PowerPoint 설치 상태를 확인해 주세요."
    if "80010001" in text or "8001010a" in text or "rejected by callee" in text:
        return "PPT 생성 오류 [PowerPoint 사용 중]: PowerPoint의 대화상자를 확인하고 잠시 후 다시 시도해 주세요."
    code = re.search(r"\b(?:0x)?(800[0-9a-f]{5})\b", text)
    suffix = f" ({code.group(1).upper()})" if code else ""
    return f"PPT 파일을 완성하지 못했습니다{suffix}. 다시 시도해 주세요. 문제가 계속되면 운영자에게 이 오류를 알려 주세요."


@dataclass(frozen=True)
class ReportDownloadBundle:
    pptx_name: str
    pptx_bytes: bytes
    pdf_name: str
    pdf_bytes: bytes
    errors: tuple[str, ...] = ()


def _records(
    dataframe: object,
    *,
    columns: list[str] | None = None,
    limit: int | None = 12,
) -> list[dict[str, Any]]:
    if not isinstance(dataframe, pd.DataFrame) or dataframe.empty:
        return []
    selected = dataframe.copy()
    if columns:
        available = [column for column in columns if column in selected.columns]
        selected = selected[available] if available else pd.DataFrame()
    if selected.empty:
        return []
    if limit is not None:
        selected = selected.head(limit)
    selected = selected.where(pd.notna(selected), "미입력")
    for column in selected.columns:
        selected[column] = selected[column].map(
            lambda value: value.strftime("%Y-%m-%d") if isinstance(value, (pd.Timestamp, datetime)) else value
        )
    return selected.to_dict(orient="records")


def _kpi_value(kpi: dict[str, Any], key: str, default: Any = 0) -> Any:
    value = kpi.get(key, default)
    if pd.isna(value):
        return default
    return value


def _work_type_payload(
    work_type: str,
    work_type_tables: dict[str, object],
    *,
    label: str,
) -> dict[str, Any]:
    summary = work_type_tables.get("summary")
    monthly = work_type_tables.get("monthly")
    customers = work_type_tables.get("customers")
    summary_row: dict[str, Any] = {}
    if isinstance(summary, pd.DataFrame) and not summary.empty and "업무유형구분" in summary.columns:
        matched = summary.loc[summary["업무유형구분"].astype(str) == work_type]
        if not matched.empty:
            summary_row = matched.iloc[0].to_dict()

    def records_for(dataframe: object, *, limit: int | None) -> list[dict[str, Any]]:
        if not isinstance(dataframe, pd.DataFrame) or dataframe.empty or "업무유형구분" not in dataframe.columns:
            return []
        return _records(dataframe.loc[dataframe["업무유형구분"].astype(str) == work_type], limit=limit)

    total = int(summary_row.get("접수 건수", 0) or 0)
    kpis = []
    if total:
        kpis = [
            {"label": "접수", "value": total, "unit": "건"},
            {"label": "전체 비중", "value": summary_row.get("전체 비중", 0), "unit": "%"},
            {"label": "처리 완료", "value": int(summary_row.get("처리완료 건수", 0) or 0), "unit": "건"},
            {"label": "미완료", "value": int(summary_row.get("미완료 건수", 0) or 0), "unit": "건"},
            {"label": "처리 완료율", "value": summary_row.get("처리완료율", 0), "unit": "%"},
        ]
    return {
        "label": label,
        "display_label": label,
        "slide_title": f"{label} 접수 현황",
        "received": total,
        "share": summary_row.get("전체 비중", 0),
        "completed": int(summary_row.get("처리완료 건수", 0) or 0),
        "incomplete": int(summary_row.get("미완료 건수", 0) or 0),
        "completion_rate": summary_row.get("처리완료율", 0),
        "kpis": kpis,
        "monthly": records_for(monthly, limit=None),
        "customers": records_for(customers, limit=10),
    }


def _filtered_narrative(lines: list[str]) -> list[str]:
    excluded = ("라인 중단", "라인중단", "품질 피드백", "반복 검토", "반복 후보")
    return [
        str(line).replace("처리완료율", "처리 완료율").replace("처리완료", "처리 완료")
        for line in lines if not any(token in str(line) for token in excluded)
    ][:5]


def _find_pdf_browser() -> Path:
    for candidate in PDF_BROWSER_CANDIDATES:
        if candidate.exists():
            return candidate
    raise RuntimeError("HTML 형식 PDF 변환을 위한 Microsoft Edge 또는 Chrome을 찾을 수 없습니다.")


def _render_html_pdf(html_path: Path, pdf_path: Path) -> None:
    browser = _find_pdf_browser()
    resolved_pdf_path = pdf_path.resolve()
    with tempfile.TemporaryDirectory(
        prefix="as_report_pdf_browser_",
        ignore_cleanup_errors=True,
    ) as profile_dir:
        completed = subprocess.run(
            [
                str(browser),
                "--headless=new",
                "--disable-gpu",
                "--no-sandbox",
                "--no-first-run",
                "--disable-extensions",
                "--allow-file-access-from-files",
                "--run-all-compositor-stages-before-draw",
                "--virtual-time-budget=5000",
                "--print-to-pdf-no-header",
                "--no-pdf-header-footer",
                f"--user-data-dir={profile_dir}",
                f"--print-to-pdf={resolved_pdf_path}",
                html_path.resolve().as_uri(),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=180,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        deadline = time.monotonic() + PDF_RENDER_WAIT_SECONDS
        while not pdf_path.exists() and time.monotonic() < deadline:
            time.sleep(0.25)
    if completed.returncode != 0 or not pdf_path.exists():
        detail = (completed.stderr or completed.stdout or "브라우저 PDF 변환에 실패했습니다.").strip()
        raise RuntimeError(f"HTML 형식 PDF 생성에 실패했습니다: {detail}")


def build_presentation_payload(
    analysis: dict[str, Any],
    narrative_lines: list[str],
    *,
    period_range: PeriodRange,
    filter_summary: str,
) -> dict[str, Any]:
    tables = analysis.get("tables", {})
    kpi = analysis.get("kpi", {})
    work_type_tables = analysis.get("presentation_work_types", {})
    monthly_completion = work_type_tables.get("monthly_status")

    work_type_details = {
        "emergency": _work_type_payload("긴급방문", work_type_tables, label="긴급방문"),
        "general": _work_type_payload("일반방문", work_type_tables, label="일반방문"),
        "remote": _work_type_payload("원격지원", work_type_tables, label="원격 지원"),
        "claim": _work_type_payload("부품수리/클레임", work_type_tables, label="부품 수리·클레임"),
        "voc": _work_type_payload("VOC", work_type_tables, label="VOC"),
        "other": _work_type_payload("기타", work_type_tables, label="기타"),
    }

    return {
        "title": "A/S 현황 리포트",
        "period_label": period_range.label,
        "period_range": f"{period_range.start_date.isoformat()} ~ {period_range.end_date.isoformat()}",
        "filter_summary": filter_summary,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "narrative": _filtered_narrative(narrative_lines),
        "kpis": [
            {"label": "총 접수", "value": _kpi_value(kpi, "총 접수 건수"), "unit": "건"},
            {"label": "처리 완료", "value": _kpi_value(kpi, "처리완료 건수"), "unit": "건"},
            {"label": "미완료", "value": _kpi_value(kpi, "미완료 건수"), "unit": "건"},
            {"label": "처리 완료율", "value": _kpi_value(kpi, "처리완료율"), "unit": "%"},
        ],
        "monthly": _records(tables.get("월별 접수 건수"), columns=["기간_연월", "접수 건수"], limit=None),
        "monthly_status": _records(monthly_completion, limit=None),
        "monthly_completion": _records(
            monthly_completion, columns=["기간_연월", "처리완료율"], limit=None
        ),
        "work_types": _records(
            tables.get("업무유형구분별 접수 건수"), columns=["업무유형구분", "접수 건수"], limit=8
        ),
        "customers": _records(
            tables.get("고객사별 접수 건수 TOP 20"), columns=["고객사", "접수 건수"], limit=10
        ),
        "categories": _records(
            tables.get("대분류별 접수 건수"), columns=["대분류", "접수 건수"], limit=10
        ),
        "parts": _records(
            tables.get("소분류 고장부품별 접수 건수 TOP 20"),
            columns=["소분류 (고장부품)", "접수 건수"],
            limit=10,
        ),
        "manufacturers": _records(
            work_type_tables.get("manufacturers"), columns=["제조사", "접수 건수"], limit=10
        ),
        "work_type_details": work_type_details,
        "other_description": "기타는 긴급방문·일반방문·원격지원·부품 수리·클레임·VOC로 구분되지 않은 원본 업무유형 입력 건이며, 업무유형 미입력 건을 포함합니다.",
    }


def _generate_pptx(payload: dict[str, Any], pptx_path: Path) -> None:
    if not PPT_TEMPLATE_PATH.exists():
        raise PptGenerationError("PPT 기본 양식을 찾을 수 없습니다. 운영자에게 회사 양식 파일 확인을 요청해 주세요.")
    if not PRESENTATION_BUILDER_PATH.exists():
        raise PptGenerationError("PPT 생성 도구를 찾을 수 없습니다. 운영자에게 앱 파일 확인을 요청해 주세요.")
    payload_path = pptx_path.with_suffix(".json")
    pdf_path = pptx_path.with_suffix(".unused.pdf")
    payload_path.write_text(json.dumps(payload, ensure_ascii=False, default=str), encoding="utf-8")

    def ps_quote(value: Path) -> str:
        return str(value).replace("'", "''")

    command = (
        "$utf8 = New-Object System.Text.UTF8Encoding($false); "
        "[Console]::OutputEncoding = $utf8; $OutputEncoding = $utf8; "
        "$ProgressPreference = 'SilentlyContinue'; "
        f"$source = Get-Content -LiteralPath '{ps_quote(PRESENTATION_BUILDER_PATH)}' -Raw -Encoding UTF8; "
        "$builder = [ScriptBlock]::Create($source); "
        f"& $builder -TemplatePath '{ps_quote(PPT_TEMPLATE_PATH)}' "
        f"-PayloadPath '{ps_quote(payload_path)}' "
        f"-PptxOutputPath '{ps_quote(pptx_path)}' "
        f"-PdfOutputPath '{ps_quote(pdf_path)}' -SkipPdf"
    )
    encoded_command = base64.b64encode(command.encode("utf-16le")).decode("ascii")
    if not PPT_GENERATION_LOCK.acquire(timeout=180):
        raise PptGenerationError("다른 PPT를 만들고 있습니다. 잠시 후 다시 시도해 주세요.")
    try:
        completed = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-STA",
            "-WindowStyle",
            "Hidden",
            "-OutputFormat",
            "Text",
            "-ExecutionPolicy",
            "Bypass",
            "-EncodedCommand",
            encoded_command,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=180,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except subprocess.TimeoutExpired as error:
        raise PptGenerationError("PPT 생성 시간이 초과되었습니다. PowerPoint의 대화상자를 확인한 뒤 다시 시도해 주세요.") from error
    finally:
        PPT_GENERATION_LOCK.release()
    if completed.returncode != 0 or not pptx_path.is_file():
        LOGGER.error("PowerPoint builder failed: %s", completed.stderr or completed.stdout)
        raise PptGenerationError(_ppt_error_message(completed.stderr or completed.stdout or ""))


def generate_report_download_bundle(
    analysis: dict[str, Any],
    narrative_lines: list[str],
    *,
    period_range: PeriodRange,
    filter_summary: str,
) -> ReportDownloadBundle:
    payload = build_presentation_payload(
        analysis, narrative_lines, period_range=period_range, filter_summary=filter_summary,
    )
    suffix = "_filtered" if filter_summary != "없음" else ""
    base_name = f"as_report_{period_range.filename_label}{suffix}"
    errors: list[str] = []
    pptx_bytes = b""
    pdf_bytes = b""

    with tempfile.TemporaryDirectory(prefix="as_report_download_") as temp_dir_text:
        temp_dir = Path(temp_dir_text)
        pptx_path = temp_dir / f"{base_name}.pptx"
        pdf_path = temp_dir / f"{base_name}.pdf"
        html_path = temp_dir / f"{base_name}.html"

        # Each format is independent: a PowerPoint error must not discard a valid PDF.
        try:
            html_path.write_text(render_pdf_report(payload), encoding="utf-8")
            _render_html_pdf(html_path, pdf_path)
            pdf_bytes = pdf_path.read_bytes()
            if not pdf_bytes.startswith(b"%PDF-") or b"%%EOF" not in pdf_bytes[-1024:]:
                raise RuntimeError("PDF output is incomplete")
        except Exception:
            LOGGER.exception("PDF download generation failed")
            pdf_bytes = b""
            errors.append("PDF를 만들지 못했습니다. Edge 또는 Chrome 실행 환경을 확인한 뒤 다시 시도해 주세요.")

        try:
            _generate_pptx(payload, pptx_path)
            pptx_bytes = pptx_path.read_bytes()
            if not pptx_bytes.startswith(b"PK"):
                raise RuntimeError("PPT output is incomplete")
        except PptGenerationError as error:
            LOGGER.exception("PPT download generation failed")
            pptx_bytes = b""
            errors.append(str(error))
        except Exception:
            LOGGER.exception("PPT download generation failed")
            pptx_bytes = b""
            errors.append(_ppt_error_message(""))

    if not pptx_bytes and not pdf_bytes:
        raise RuntimeError(" ".join(errors))
    return ReportDownloadBundle(
        pptx_name=f"{base_name}.pptx", pptx_bytes=pptx_bytes,
        pdf_name=f"{base_name}.pdf", pdf_bytes=pdf_bytes, errors=tuple(errors),
    )
