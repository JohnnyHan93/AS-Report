> Historical handoff inventory only. Referenced copies remain local; this is not current operating approval.

# Handoff Manifest

## Task

PPT·PDF 최종 구성 및 문구 정돈

## Handoff Files

- `src/as_report/analyzer.py`
- `src/as_report/report_presentation.py`
- `src/as_report/presentation/build_report.ps1`
- `tests/test_report_presentation.py`
- `MD/completion report/PPT_PDF_final_composition_completion.md`
- `MD/_chatgpt_handoff/PPT_PDF_final_composition/MANIFEST.md`

## Purpose

11장 PPT 구성, 기존 HTML 형식 기반 PDF 변환, 업무유형별 전용 집계, 자연스러운 표시 문구, 하단 설명 제거, 제외 콘텐츠 비노출을 검토하기 위한 전달본입니다.

## Validation

- Focused tests: `6 passed`
- Full tests: `100 passed`
- Python compile: passed
- PowerShell parse: passed
- HTML 기반 PDF 변환 경로: Edge/Chrome headless 인쇄 방식으로 구현
- PowerPoint/PDF runtime generation: 현재 비대화형 세션 제약으로 pending

## Safety

- Raw/master 변경 없음
- 대표 HTML/Excel 변경 및 재생성 없음
- HTML/Excel 구조 변경 없음
- reports cleanup/archive 없음
- fuzzy matching, 원인·책임·고객 영향·비용 절감·개선 효과 추정 없음

## Excluded From Handoff

- `data/raw`
- `data/master`
- `.venv`
- `archive`
- 대표 reports
- 임시 PPT/PDF 파일
