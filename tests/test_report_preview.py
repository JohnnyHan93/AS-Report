from datetime import date
from copy import deepcopy

import pandas as pd
import pytest

from as_report.analyzer import analyze
from as_report.cleaner import clean_data
from as_report.loader import REQUIRED_COLUMNS
from as_report.period import PeriodRange
from as_report.report_pdf import render_pdf_report
from as_report.report_presentation import build_presentation_payload
from as_report.report_preview import SLIDE_TITLES, build_slide_preview, render_document_preview, render_slide_preview


@pytest.fixture
def payload():
    raw = pd.DataFrame([{**{key: None for key in REQUIRED_COLUMNS},
                         '접수일': '2026-01-10', '상태': '처리완료',
                         '업무유형': 'A/S대응(부품수리/클레임처리)',
                         '고객사': '<script>alert(1)</script>', '제조사': '검토 제조사'}])
    data = clean_data(raw)
    period = PeriodRange('year', date(2026, 1, 1), date(2026, 12, 31), '2026', '2026')
    return build_presentation_payload(analyze(data, data, period), [], period_range=period, filter_summary='없음')


def test_all_slide_previews_preserve_payload_and_safe_text(payload):
    before = deepcopy(payload)
    assert len(SLIDE_TITLES) == 11
    for index, title in enumerate(SLIDE_TITLES):
        html = render_slide_preview(payload, index)
        assert f'<title>{title}</title>' in html
        assert f'{index + 1:02d} / 11' in html
        assert '<script>' not in html
        assert 'data:image/png;base64,' in html
        assert '고장률' not in html
    assert payload == before
    assert '&lt;script&gt;' in render_slide_preview(payload, 4)
    claim = build_slide_preview(payload, 9)
    assert claim['metrics'] == payload['work_type_details']['claim']['kpis']
    assert claim['panels'][1]['rows'] == payload['manufacturers']
    assert build_slide_preview(payload, 10)['details'] == [payload['work_type_details'][key] for key in ('voc', 'other')]
    with pytest.raises(ValueError):
        build_slide_preview(payload, 11)


def test_pdf_preview_retains_export_body_and_adds_only_screen_style(payload):
    output = render_pdf_report(payload)
    preview = render_document_preview(payload)
    assert output.split('<body>', 1)[1] == preview.split('<body>', 1)[1]
    assert '@media screen' in preview
    assert preview.count('class="page"') == output.count('class="page"')
    assert '<script>' not in preview


def test_empty_slide_keeps_empty_state_without_inventing_rows(payload):
    payload['monthly'] = []
    payload['monthly_completion'] = []
    html = render_slide_preview(payload, 3)
    assert html.count('표시할 데이터가 없습니다.') == 2
