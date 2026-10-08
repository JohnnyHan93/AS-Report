> Historical handoff inventory only. Referenced copies remain local; this is not current operating approval.

# Handoff Manifest

## Task

PPT/PDF HTML-based PDF generation separation

## Purpose

PPT는 회사 양식 기반 11장 요약본으로 유지하고, PDF는 기존 HTML 전체 구조를 회사 색상·도형 컨셉의 인쇄용 스타일로 변환한다.

## Handoff Copied Files

| Handoff path | Original path | Purpose |
|---|---|---|
| `src\as_report\report_presentation.py` | `src\as_report\report_presentation.py` | PPT/PDF 분리 생성 및 PDF 인쇄 스타일 |
| `src\as_report\app.py` | `src\as_report\app.py` | PPT/PDF 형식 차이 안내 |
| `tests\test_report_presentation.py` | `tests\test_report_presentation.py` | PDF 스타일·HTML 보존·분리 경로 회귀 테스트 |
| `PPT_PDF_html_based_pdf_generation_completion.md` | `MD\completion report\PPT_PDF_html_based_pdf_generation_completion.md` | 작업 결과와 검증 기록 |
| `MANIFEST.md` | `MD\_chatgpt_handoff\PPT_PDF_html_based_pdf_generation\MANIFEST.md` | 전달 파일 목록 |

## Test Results

- Import check: Pass
- Python compile: Pass
- Focused pytest: `15 passed`
- Full `pytest tests`: `105 passed`
- Browser executable discovery: Edge/Chrome found
- Actual PDF render: Pending due execution approval limitation

## Safety Statements

- Raw/master unchanged
- Calculation, HTML data, Excel structure, and report analysis unchanged
- Representative HTML/Excel not regenerated
- Validation reports not regenerated
- No reports cleanup or archive operation
- No Raw/master files copied here
- No validation or representative output copied here

## Known Limitation

Actual PPT/PDF download runtime needs confirmation in an interactive Windows session with PowerPoint and a supported browser available.

## Next Step

Run the Streamlit download flow once and visually inspect the generated HTML-based PDF.
