## 2026-10-08 개발 자료 게시 기준

- `input_contract.py`의 `inspect_csv(explicit_path) -> InputInspection`은 독립 입력 점검 API다. 원본 헤더·문자열·행 위치·입력 해시·날짜/열/분석별 가용성을 반환한다. 기존 loader/UI에 연결되지 않았다.
- CSV 파싱은 격리 Python 프로세스를 사용하며 부모 `csv.field_size_limit`를 바꾸지 않는다. 프로세스 시작과 메모리 복사 비용이 있다.
- [인계 문서](docs/README.md)에 현재 설계와 과거 증거를 분리했다. 아래 9월 구조 설명은 기존 경로를 설명하며 새 기능 승인 상태는 TASKS를 따른다.

# Architecture

확인일: 2026-09-14. 로컬 소스 정적 확인 기준이며 실행 검증 결과를 의미하지 않는다.

## 진입점과 데이터 흐름

- `AS_Report.bat`: Windows 실행 진입점. Streamlit local/host 및 환경 확인·복구.
- `src/as_report/app.py`: Raw 선택/업로드, 기간·필터, 분석 세션, 미리보기, 다운로드.
- `src/as_report/cli.py`: 명시적 입력을 분석하고 HTML/Excel 및 실행 메타데이터·이력을 생성하는 CLI.
- `loader.py` -> `cleaner.py` -> `period.py` -> `analyzer.py` / `narrative.py`: 입력, 메모리 정제, 접수일 범위, 분석과 문구. 앱 필터는 `app.py`에서 적용한다.
- `comparison.py`, `repeat_issue.py`, `legacy_features.py`, `quality_feedback.py`, `quality/`: 비교·반복 검토 후보·품질 분석 지원.
- `standardization/`: 표준명 검토. `master/`, `input_set.py`, `input_set_validation.py`: 참조/검증 지원 모듈. 모듈 존재가 정상 분석의 Master 연결 승인을 뜻하지 않는다. 현 운영은 Raw-only이다.

## 출력 경로

| 경로 | 모듈 | 특성 |
| --- | --- | --- |
| 기존 HTML/Excel | `report_html.py`, `report_excel.py`, `cli.py` | 기존 분석 결과를 직접 사용. V2 payload로 전환되지 않음 |
| 발표용 PPT | `report_presentation.py` -> `presentation/build_report.ps1` | 회사 템플릿과 PowerPoint 자동화 |
| 현재 PDF | `report_presentation.py` -> `report_pdf.py` -> `templates/report_pdf.html` -> Edge/Chrome | 임시 HTML을 브라우저로 PDF 변환. PPT 실패와 독립 처리 |
| V2 Word/PPTX | `report_payload.py` -> `report_tool.py` -> `report_docx.py` / `report_pptx.py` | 공통 ReportPayload, python-docx/python-pptx, 메모리 다운로드 |
| V2 QC | `report_qc.py` | 생성 전 payload 검사, 생성 후 문서 내부 식별정보 일치 확인 |
| 화면 미리보기 | `report_preview.py`, `ui_state.py`, `ui_components.py` | 현재 분석 세션 및 UI 지원 |
| 출처·저장 | `provenance.py`, `output/output_manager.py` | Raw 출처, 사용자 경로, 메타데이터와 이력 지원 |

V2는 `report_payload.json`, `report_qc.json`을 함께 반환한다. V2 스타일은 `templates/report_tool/style.json`, 회사 PPT 자산은 `resources/`에 있다. 외부 AI/플러그인을 필수 런타임으로 도입하지 않는다.

## 검증과 제한

- `tests/`: 분석, 입력, 출력, 미리보기, V2 회귀 테스트. pytest 설정은 `pyproject.toml`에 있다. 루트 `pytest.ini`는 현재 없다.
- V2 전용: `tests/test_report_tool_v2.py`; 기존 PPT/PDF: `tests/test_report_presentation.py`; 앱: `tests/test_app_output_context.py`, `tests/test_ui_state.py`.
- 실행 검증 명령과 위험도별 필수 검사는 `AGENTS.md` 9~11절을 따른다.
- V2 Word 시각 검수는 기존 완료보고서에서 미완료. 기존 142 passed 기록은 이번 실행 결과가 아니다.
- 과거 HTML 기반 PDF 완료보고서와 현재 `report_pdf.py` 호출 경로는 다르다. 과거 결과를 현재 PDF 검증으로 대체하지 않는다.
- 대표 HTML/Excel은 동일 실행 pair가 확인되지 않은 상태다. 변경·공유·재생성 승인이 없다.
- Raw/Master, 기존 산출물, 가상환경, BAT 보호 규칙은 `AGENTS.md`를 따른다.

## 공용 기억

규칙은 `AGENTS.md`, 작업/승인은 `TASKS.md`, 변경 결과는 `CHANGELOG.md`를 읽는다. 2026-09-14 전용 비공개 저장소 https://github.com/JohnnyHan93/AS-Report 를 생성했다. 현재 게시 검증은 TASKS.md의 ASR-M002를 따른다. Johnny-AI-OS는 별도 상위 관리 저장소로 보존한다.
