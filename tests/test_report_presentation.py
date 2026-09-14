from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from as_report.period import PeriodRange
import pytest

from as_report import report_presentation as presentation
from as_report.analyzer import analyze
from as_report.cleaner import clean_data
from as_report.report_pdf import render_pdf_report
from as_report.report_presentation import build_presentation_payload
from as_report.narrative import build_narrative


def _period_range() -> PeriodRange:
    return PeriodRange(
        period="year",
        label="2026",
        filename_label="2026",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
    )


def test_presentation_payload_uses_existing_analysis_outputs() -> None:
    analysis = {
        "kpi": {
            "총 접수 건수": 10,
            "처리완료 건수": 7,
            "미완료 건수": 3,
            "처리완료율": 70.0,
            "라인 중단 시간 입력 건수": 2,
            "라인 중단 총 시간": 90,
        },
        "tables": {
            "월별 접수 건수": pd.DataFrame([{"기간_연월": "2026-01", "접수 건수": 10}]),
            "월별 라인 중단 시간": pd.DataFrame([{"기간_연월": "2026-01", "라인 중단 시간": 90}]),
            "업무유형구분별 접수 건수": pd.DataFrame([{"업무유형구분": "일반방문", "접수 건수": 10}]),
            "고객사별 접수 건수 TOP 20": pd.DataFrame([{"고객사": "A사", "접수 건수": 10}]),
            "대분류별 접수 건수": pd.DataFrame([{"대분류": "Robot", "접수 건수": 8}]),
            "소분류 고장부품별 접수 건수 TOP 20": pd.DataFrame(
                [{"소분류 (고장부품)": "부품A", "접수 건수": 4}]
            ),
            "라인 중단 시간 TOP 20 이슈 목록": pd.DataFrame(),
        },
        "legacy_features": {},
        "quality_feedback": {},
        "repeat_issues": pd.DataFrame(),
    }

    payload = build_presentation_payload(
        analysis,
        ["입력 데이터 기준 요약입니다."],
        period_range=_period_range(),
        filter_summary="없음",
    )

    assert payload["period_label"] == "2026"
    assert payload["title"] == "A/S 현황 리포트"
    assert "업무유형 미입력 건을 포함합니다" in payload["other_description"]
    assert payload["kpis"][0] == {"label": "총 접수", "value": 10, "unit": "건"}
    assert payload["monthly"] == [{"기간_연월": "2026-01", "접수 건수": 10}]
    assert payload["customers"][0]["고객사"] == "A사"
    assert "source_path" not in payload
    assert "output_path" not in payload


def test_presentation_payload_returns_empty_sections_without_fake_data() -> None:
    payload = build_presentation_payload(
        {"kpi": {}, "tables": {}, "legacy_features": {}, "quality_feedback": {}},
        [],
        period_range=_period_range(),
        filter_summary="없음",
    )

    assert payload["monthly"] == []
    assert payload["customers"] == []
    assert set(payload["work_type_details"]) == {"emergency", "general", "remote", "claim", "voc", "other"}
    assert all(detail["kpis"] == [] for detail in payload["work_type_details"].values())


def test_presentation_payload_contains_work_type_detail_metrics() -> None:
    analysis = {
        "kpi": {"총 접수 건수": 3, "처리완료 건수": 2, "미완료 건수": 1, "처리완료율": 66.7},
        "tables": {"월별 접수 건수": pd.DataFrame()},
        "legacy_features": {},
        "presentation_work_types": {
            "summary": pd.DataFrame([
                {"업무유형구분": "긴급방문", "접수 건수": 2, "전체 비중": 66.7, "처리완료 건수": 1, "미완료 건수": 1, "처리완료율": 50.0},
                {"업무유형구분": "VOC", "접수 건수": 1, "전체 비중": 33.3, "처리완료 건수": 1, "미완료 건수": 0, "처리완료율": 100.0},
            ]),
            "monthly": pd.DataFrame([{"업무유형구분": "긴급방문", "기간_연월": "2026-01", "접수 건수": 2}]),
            "customers": pd.DataFrame([{"업무유형구분": "긴급방문", "고객사": "A사", "접수 건수": 2}]),
        },
    }
    payload = build_presentation_payload(analysis, [], period_range=_period_range(), filter_summary="없음")

    emergency = payload["work_type_details"]["emergency"]
    assert emergency["received"] == 2
    assert emergency["completed"] == 1
    assert emergency["incomplete"] == 1
    assert emergency["monthly"][0]["기간_연월"] == "2026-01"
    assert emergency["customers"][0]["고객사"] == "A사"


def test_narrative_customer_sentence_avoids_awkward_particle() -> None:
    analysis = {
        "kpi": {"총 접수 건수": 9, "처리완료 건수": 3},
        "tables": {
            "고객사별 접수 건수 TOP 20": pd.DataFrame([{"고객사": "현대 아산", "접수 건수": 9}]),
        },
        "comparison": pd.DataFrame(),
        "repeat_issues": pd.DataFrame(),
    }
    lines = build_narrative(analysis, "2026", "2026-01-01", "2026-12-31")

    assert any("현대 아산으로 9건입니다." in line for line in lines)
    assert all("현대 아산가" not in line for line in lines)


def test_presentation_builder_uses_voc_and_other_display_title() -> None:
    builder = (Path(__file__).resolve().parents[1] / "src" / "as_report" / "presentation" / "build_report.ps1").read_text(
        encoding="utf-8"
    )
    assert 'Add-Title $slide "VOC 및 기타 접수 현황"' in builder
    assert 'Add-Title $slide "VOC 및 기타 업무유형 접수 현황"' not in builder


def test_pdf_is_a_separate_escaped_static_report() -> None:
    payload = build_presentation_payload({}, [], period_range=_period_range(), filter_summary='<script>alert(1)</script>')
    html = render_pdf_report(payload)

    assert 'A/S 종합 현황' in html
    assert 'VOC 및 기타 접수 현황' in html
    assert 'A4 portrait' in html
    assert '&lt;script&gt;' in html
    assert '<script>' not in html
    assert '표시할 데이터가 없습니다' in html
    assert '업무유형 미입력 건을 포함합니다' in html
    assert 'Plotly' not in html
    assert '라인 중단' not in html
    assert '품질 피드백' not in html
    assert '반복 검토' not in html
    assert html.count('<section class="page">') == 4




def test_pdf_generation_path_is_independent_from_powerpoint_pdf_export() -> None:
    source = Path(__file__).resolve().parents[1] / "src" / "as_report" / "report_presentation.py"
    text = source.read_text(encoding="utf-8")

    assert "-SkipPdf" in text
    assert "_render_html_pdf(html_path, pdf_path)" in text


def test_powerpoint_builder_opens_without_a_document_window() -> None:
    builder = (Path(__file__).resolve().parents[1] / "src" / "as_report" / "presentation" / "build_report.ps1").read_text(
        encoding="utf-8"
    )

    assert "$ppt.Visible" not in builder
    assert "$ppt.DisplayAlerts = 1" in builder
    assert "$presentation = $ppt.Presentations.Open($TemplatePath, $false, $false, $false)" in builder
    assert "$ppt.Visible = -1" not in builder


def test_powerpoint_process_uses_hidden_text_mode() -> None:
    source = (Path(__file__).resolve().parents[1] / "src" / "as_report" / "report_presentation.py").read_text(
        encoding="utf-8"
    )

    assert '"-WindowStyle"' in source
    assert '"Hidden"' in source
    assert '"-OutputFormat"' in source
    assert '"Text"' in source
    assert 'creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)' in source


def test_pdf_browser_uses_an_isolated_hidden_profile() -> None:
    source = (Path(__file__).resolve().parents[1] / "src" / "as_report" / "report_presentation.py").read_text(
        encoding="utf-8"
    )

    assert 'prefix="as_report_pdf_browser_"' in source
    assert '"--headless=new"' in source
    assert 'f"--user-data-dir={profile_dir}"' in source
    assert "ignore_cleanup_errors=True" in source
    assert "PDF_RENDER_WAIT_SECONDS = 30" in source
    assert "while not pdf_path.exists()" in source


def test_monthly_completion_and_manufacturers_share_overall_classification() -> None:
    data = clean_data(pd.DataFrame([
        {"접수일": "2026-01-10", "상태": "처리완료", "업무유형": "부품수리", "제조사": "제조사 A"},
        {"접수일": "2026-01-11", "상태": "전달 완료", "업무유형": "클레임처리", "제조사": None},
        {"접수일": "2026-01-12", "상태": "진행중", "업무유형": "일반방문", "제조사": "제외"},
    ]))
    analysis = analyze(data, data)
    payload = build_presentation_payload(analysis, [], period_range=_period_range(), filter_summary="없음")
    assert payload['monthly_status'][0]['처리완료 건수'] == analysis['kpi']['처리완료 건수'] == 1
    assert payload['monthly_completion'][0]['처리완료율'] == 33.3
    assert sum(row['접수 건수'] for row in payload['manufacturers']) == payload['work_type_details']['claim']['received'] == 2
    assert {row['제조사'] for row in payload['manufacturers']} == {'제조사 A', '미입력'}
    assert sum(detail['completed'] for detail in payload['work_type_details'].values()) == 1


def test_long_period_is_not_silently_truncated() -> None:
    data = clean_data(pd.DataFrame([
        {"접수일": month, "상태": "처리완료", "업무유형": "일반방문"}
        for month in pd.date_range("2024-01-01", periods=25, freq="MS")
    ]))
    payload = build_presentation_payload(analyze(data, data), [], period_range=_period_range(), filter_summary="없음")
    assert len(payload['monthly']) == 25
    assert len(payload['monthly_completion']) == 25
    assert len(payload['work_type_details']['general']['monthly']) == 25
    html = render_pdf_report(payload)
    assert '2026-01' in html
    assert html.count('<section class="page">') == 6


@pytest.mark.parametrize('failed_format', ['ppt', 'pdf', None])
def test_download_generation_is_independent_and_temporary(monkeypatch, failed_format) -> None:
    paths = []

    def pdf(html_path, pdf_path):
        paths.extend([html_path, pdf_path])
        assert 'A/S 종합 현황' in html_path.read_text(encoding='utf-8')
        if failed_format == 'pdf':
            raise RuntimeError('CLIXML internal failure')
        pdf_path.write_bytes(b'%PDF-1.7\n%%EOF')

    def ppt(payload, pptx_path):
        paths.append(pptx_path)
        if failed_format == 'ppt':
            raise RuntimeError('CLIXML internal failure')
        pptx_path.write_bytes(b'PK-test-pptx')

    monkeypatch.setattr(presentation, '_render_html_pdf', pdf)
    monkeypatch.setattr(presentation, '_generate_pptx', ppt)
    bundle = presentation.generate_report_download_bundle({}, [], period_range=_period_range(), filter_summary='없음')
    assert bool(bundle.pdf_bytes) == (failed_format != 'pdf')
    assert bool(bundle.pptx_bytes) == (failed_format != 'ppt')
    assert len(bundle.errors) == (1 if failed_format else 0)
    assert 'CLIXML' not in ' '.join(bundle.errors)
    assert all(not path.exists() for path in paths)


def test_both_generation_failures_are_not_reported_as_success(monkeypatch) -> None:
    def fail(*args):
        raise RuntimeError('internal failure')
    monkeypatch.setattr(presentation, '_render_html_pdf', fail)
    monkeypatch.setattr(presentation, '_generate_pptx', fail)
    with pytest.raises(RuntimeError, match='PDF를 만들지 못했습니다'):
        presentation.generate_report_download_bundle({}, [], period_range=_period_range(), filter_summary='없음')


@pytest.mark.parametrize('detail, expected', [
    ('#< CLIXML HRESULT: 0x80070520', '로그인 세션'),
    ('0x80040154 Class not registered', 'PowerPoint 설치'),
    ('HRESULT 80010001', 'PowerPoint 사용 중'),
    ('8001010A application is busy', 'PowerPoint 사용 중'),
])
def test_ppt_errors_distinguish_session_installation_and_busy(detail, expected) -> None:
    message = presentation._ppt_error_message(detail)
    assert expected in message
    assert 'CLIXML' not in message


def test_ppt_timeout_releases_generation_lock(tmp_path, monkeypatch) -> None:
    import subprocess
    from threading import Lock
    lock = Lock()
    monkeypatch.setattr(presentation, 'PPT_GENERATION_LOCK', lock)
    def timeout(*args, **kwargs):
        assert lock.locked()
        raise subprocess.TimeoutExpired('powershell', 180)
    monkeypatch.setattr(presentation.subprocess, 'run', timeout)
    with pytest.raises(presentation.PptGenerationError, match='시간이 초과'):
        presentation._generate_pptx({}, tmp_path / 'report.pptx')
    assert not lock.locked()


def test_ppt_failure_reason_survives_in_partial_download_bundle(monkeypatch) -> None:
    def fail(*args):
        raise presentation.PptGenerationError(presentation._ppt_error_message('0x80070520'))
    def pdf(html_path, pdf_path):
        pdf_path.write_bytes(b'%PDF-1.7\n%%EOF')
    monkeypatch.setattr(presentation, '_generate_pptx', fail)
    monkeypatch.setattr(presentation, '_render_html_pdf', pdf)
    bundle = presentation.generate_report_download_bundle({}, [], period_range=_period_range(), filter_summary='없음')
    assert bundle.pdf_bytes
    assert not bundle.pptx_bytes
    assert '로그인 세션' in bundle.errors[0]
