from __future__ import annotations

from datetime import date
import inspect
from pathlib import Path

import as_report.app as app
from as_report.period import PeriodRange


def _period_range() -> PeriodRange:
    return PeriodRange(
        period="year",
        label="2026",
        filename_label="2026",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
    )


def test_analysis_context_signature_changes_for_source_period_filter_and_owner() -> None:
    period_range = _period_range()
    source_a = Path(__file__)
    source_b = Path(__file__ + ".other")
    baseline = app.build_analysis_context_signature(
        "raw_a.csv",
        source_a,
        period_range,
        {"customer": ["A"]},
        "user_a",
    )

    assert baseline != app.build_analysis_context_signature("raw_b.csv", source_a, period_range, {"customer": ["A"]}, "user_a")
    assert baseline != app.build_analysis_context_signature("raw_a.csv", source_b, period_range, {"customer": ["A"]}, "user_a")
    assert baseline != app.build_analysis_context_signature("raw_a.csv", source_a, period_range, {"customer": ["B"]}, "user_a")
    assert baseline != app.build_analysis_context_signature("raw_a.csv", source_a, period_range, {"customer": ["A"]}, "user_b")


def test_localhost_detection_accepts_loopback_only() -> None:
    assert app.is_localhost_request("127.0.0.1") is True
    assert app.is_localhost_request("::1") is True
    assert app.is_localhost_request(url="http://localhost:8501") is True
    assert app.is_localhost_request("192.168.0.25") is False
    assert app.is_localhost_request(url="http://192.168.0.25:8501") is False


def test_report_ui_is_download_only_and_local_review_is_gated() -> None:
    source = inspect.getsource(app.render_report_actions)
    preview_source = inspect.getsource(app.render_preview)

    assert '"PPT와 PDF 만들기"' in source
    assert '"PPT 다운로드"' in source
    assert '"PDF 다운로드"' in source
    assert "write_html_report" not in source
    assert "write_excel_report" not in source
    assert "localhost_access" in source
    assert "if localhost_access" in source
    assert "localhost_access" in preview_source
    assert "render_raw_quality_preview(result)" in preview_source
    assert 'on_click="ignore"' in source


def test_uploaded_source_reuses_temp_path_for_the_same_session_upload(tmp_path, monkeypatch) -> None:
    written_paths = []

    def fake_write_uploaded_file(content: bytes, suffix: str) -> Path:
        path = tmp_path / f"upload_{len(written_paths)}{suffix}"
        path.write_bytes(content)
        written_paths.append(path)
        return path

    monkeypatch.setattr(app, "write_uploaded_file", fake_write_uploaded_file)
    state: dict[str, object] = {}

    first = app.get_or_create_uploaded_source("issues.csv", b"first upload", state)
    second = app.get_or_create_uploaded_source("issues.csv", b"first upload", state)
    changed = app.get_or_create_uploaded_source("issues.csv", b"changed upload", state)

    assert first.path == second.path
    assert changed.path != first.path
    assert len(written_paths) == 2


def test_main_places_period_and_filter_below_selected_data() -> None:
    source = inspect.getsource(app.render_analysis_setup)

    assert 'st.tabs(["1. 데이터", "2. 기간", "3. 필터"])' not in source
    assert 'st.markdown("##### 접수 목록")' in source
    assert 'st.markdown("##### 조회 기간")' in source
    assert 'st.markdown("##### 추가 필터")' in source
    assert "render_input_source(show_heading=False)" in source
    assert "render_period_selector(cleaned, show_heading=False)" in source
    assert "render_filter_selector(period_data, show_heading=False)" in source
    assert source.index("render_input_source(show_heading=False)") < source.index(
        "render_period_selector(cleaned, show_heading=False)"
    )
    assert source.index("render_period_selector(cleaned, show_heading=False)") < source.index(
        "render_filter_selector(period_data, show_heading=False)"
    )
    assert '"분석 시작"' in source
    assert 'key="run_analysis_button"' in source
    assert "준비가 끝나면 분석 시작" in source


def test_main_uses_friendly_usage_copy_and_subtle_style() -> None:
    main_source = inspect.getsource(app.main)
    light_style = app.build_app_style_css("light")

    assert 'st.expander("사용법"' in inspect.getsource(app.render_theme_selector)
    assert "팀 운영 안내" not in main_source
    assert 'st.title("A/S 리포트")' in main_source
    assert 'st.columns([0.30, 0.70]' in main_source
    assert 'labels = ["보고서 미리보기", "분석 요약", "리포트 다운로드"]' in main_source
    assert 'output_owner = "download_only"' in main_source
    assert "border-radius: 6px" in light_style
    assert "#005b9f" in light_style


def test_app_theme_supports_system_light_and_dark_modes() -> None:
    main_source = inspect.getsource(app.main)
    system_style = app.build_app_style_css("system")
    light_style = app.build_app_style_css("light")
    dark_style = app.build_app_style_css("dark")

    assert "theme_mode = render_theme_selector()" in main_source
    assert "apply_app_style(theme_mode)" in main_source
    assert set(app.THEME_MODE_OPTIONS.values()) == {"system", "light", "dark"}
    assert "@media (prefers-color-scheme: dark)" in system_style
    assert "@media (prefers-color-scheme: dark)" not in light_style
    assert "@media (prefers-color-scheme: dark)" not in dark_style
    assert app.LIGHT_THEME_VALUES["app-bg"] in light_style
    assert app.DARK_THEME_VALUES["app-bg"] in dark_style


def test_download_ui_keeps_analysis_and_only_offers_successful_formats(monkeypatch) -> None:
    from streamlit.testing.v1 import AppTest
    from as_report.report_presentation import ReportDownloadBundle

    def screen():
        from datetime import date
        from as_report.app import AnalysisResult, render_report_actions
        from as_report.period import PeriodRange
        result = AnalysisResult(
            analysis={}, narrative_lines=[],
            period_range=PeriodRange('year', date(2026, 1, 1), date(2026, 12, 31), '2026', '2026'),
            source_name='issues.csv', filters={}, filter_summary='없음', context_signature='current',
        )
        render_report_actions(result, localhost_access=False)

    monkeypatch.setattr(app, 'generate_report_download_bundle', lambda *args, **kwargs: ReportDownloadBundle(
        'report.pptx', b'', 'report.pdf', b'%PDF-1.7\n%%EOF', ('PPT 생성 실패',),
    ))
    at = AppTest.from_function(screen).run()
    assert not at.exception
    at.button(key='prepare_ppt_pdf_downloads').click().run()
    assert not at.exception
    assert len(at.get('download_button')) == 1
    assert at.get('download_button')[0].proto.label == 'PDF 다운로드'
    assert any(item.value == 'PPT 생성 실패' for item in at.warning)
    assert not at.tabs
    assert not any('보완 자료' in expander.label for expander in at.expander)
    at.run()
    assert len(at.get('download_button')) == 1

    def fail(*args, **kwargs):
        raise RuntimeError('재시도 실패')
    monkeypatch.setattr(app, 'generate_report_download_bundle', fail)
    at.button(key='prepare_ppt_pdf_downloads').click().run()
    assert not at.exception
    assert len(at.get('download_button')) == 0
    assert 'report_download_bundle' not in at.session_state


def test_workspace_has_no_duplicate_charts_and_hides_stale_downloads(monkeypatch) -> None:
    import pandas as pd
    from streamlit.testing.v1 import AppTest
    from as_report.analyzer import analyze
    from as_report.cleaner import clean_data
    from as_report.loader import LoadedData, FileMetadata, REQUIRED_COLUMNS
    from as_report.ui_state import InputSource
    from as_report.report_presentation import ReportDownloadBundle

    source = Path(__file__)
    raw = pd.DataFrame([{**{column: None for column in REQUIRED_COLUMNS},
                         '접수일': '2026-01-10', '상태': '처리완료',
                         '업무유형': '일반방문', '고객사': 'A사'}])
    data = clean_data(raw)
    monkeypatch.setattr(app, 'render_input_source', lambda **kwargs: InputSource(source, 'issues.csv'))
    monkeypatch.setattr(app, 'load_source', lambda *args: LoadedData(raw, FileMetadata(source, 'issues.csv', '.csv')))
    monkeypatch.setattr(app, 'is_localhost_request', lambda: True)
    def build(*args):
        period = args[5]
        return app.AnalysisResult(
            analyze(data, data, period), [], period, 'issues.csv', args[8], args[9],
            context_signature=app.build_analysis_context_signature('issues.csv', source, period, args[8], args[10]),
        )
    monkeypatch.setattr(app, 'build_analysis_result', build)
    monkeypatch.setattr(app, 'generate_report_download_bundle', lambda *args, **kwargs: ReportDownloadBundle(
        'report.pptx', b'PK-test', 'report.pdf', b'%PDF-1.7\n%%EOF',
    ))
    def screen():
        from as_report.app import main
        main()
    at = AppTest.from_function(screen).run()
    assert not at.exception
    at.button(key='run_analysis_button').click().run()
    assert not at.exception
    assert '데이터 검토' in [tab.label for tab in at.tabs]
    at.selectbox(key='report_preview_slide').set_value(9).run()
    assert not at.exception
    assert '제조사별 접수 건수' in at.get('iframe')[0].proto.srcdoc
    at.button_group(key='report_preview_format').set_value('PDF').run()
    assert not at.exception
    assert 'class="page"' in at.get('iframe')[0].proto.srcdoc
    at.button(key='prepare_ppt_pdf_downloads').click().run()
    assert not at.exception
    assert len(at.get('download_button')) == 2
    at.radio[0].set_value('분기').run()
    assert not at.exception
    assert not at.get('download_button')
