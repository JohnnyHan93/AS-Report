> **연구소 인계 · 2026-10-08**: [개발 자료·설계·과거 검증 목록](docs/README.md)을 먼저 확인하십시오. 최신 CSV 점검 모듈은 REVIEW이며 UI 연결·새 CS/애프터마켓 PDF·Excel 완성이나 운영 배포를 뜻하지 않습니다. 실제 고객 입력·보고서는 저장소에 없습니다.

# A/S 리포트 도구

ES 이슈사항 보고 CSV를 기간별로 분석하고, 회사 DY 16:9 양식을 적용한 PPT와 PDF를 내려받는 Windows용 Streamlit 도구입니다.

## 시작하기

프로젝트 루트의 아래 파일만 실행합니다.

```text
AS_Report.bat
```

메뉴:

```text
1. 내 PC에서 실행
2. 팀 공유 모드로 실행
3. 실행환경 복구
0. 종료
```

처음 실행할 때 `.venv`가 없으면 자동으로 만들고 필요한 패키지를 설치합니다. 평상시에는 기존 환경을 사용해 바로 실행합니다.

명령행으로 실행할 수도 있습니다.

```bat
AS_Report.bat --local
AS_Report.bat --host
AS_Report.bat --repair
AS_Report.bat --check
```

팀 공유 모드는 `0.0.0.0:8501`에서 실행합니다. 방화벽 규칙은 자동 변경하지 않습니다.

## 사용 순서

1. `data/raw`에서 Raw CSV를 선택하거나 파일을 직접 올립니다.
2. 기간과 필터를 선택합니다.
3. **선택한 조건으로 분석 시작**을 누릅니다.
4. 화면 요약을 확인합니다.
5. **PPT·PDF 다운로드 준비**를 누른 뒤 필요한 파일을 내려받습니다.

월간 리포트는 별도 월간 옵션 대신 사용자 지정 기간에서 월 시작일과 종료일을 선택합니다.

## 화면 및 다운로드 정책

- Streamlit 화면에는 전체 파일 경로를 표시하지 않습니다.
- PPT/PDF 중간 파일은 임시 폴더에서만 만들고 다운로드 데이터로 읽은 뒤 정리합니다.
- 정상 리포트 다운로드는 프로젝트 `reports` 폴더에 자동 저장하지 않습니다.
- localhost 접속자에게만 Raw 상세 분석, 보완 자료, 표준명 검토 기능을 표시합니다.
- 팀 URL 접속자는 핵심 요약과 PPT/PDF 다운로드 기능을 사용합니다.
- 발표용 PPT 생성에는 Microsoft PowerPoint가 설치된 Windows 로그인 세션이 필요합니다. PDF 생성에는 Edge 또는 Chrome이 필요합니다.

## 구조화 보고서 V2

로컬 운영자는 분석 후 **리포트 다운로드 → 구조화 보고서 V2 · Word / PPTX**에서 문서를 선택해 생성할 수 있습니다.
Word는 상세 표를 포함하고, V2 PPTX는 회사 양식에 요약 표와 차트를 배치합니다. 긴 표는 PPTX에 처음 8행을 표시하고 전체 내용은 Word와 `report_payload.json`에 보존합니다.

두 형식은 동일한 ReportPayload를 사용하며, 입력 파일 해시·기간·필터·분석 ID가 문서 내부에 기록됩니다. 출처 누락이나 식별정보 불일치 시 생성을 제한합니다. `report_qc.json`에는 자동 검수 결과가 담깁니다.

V2 Word/PPTX 생성은 PowerPoint 실행이나 외부 AI 서비스를 사용하지 않으며 다운로드용 메모리에서만 처리합니다. 기존 발표용 11장 PPT/PDF 및 HTML/Excel 경로는 유지합니다. V2 PPTX는 기존 11장 발표용 PPT와 별도 형식입니다.

다른 PC에서는 `pyproject.toml`의 `python-docx`, `python-pptx` 의존성을 설치해야 합니다. 기존 가상환경은 `python -m pip install -e .`로 업데이트할 수 있습니다.

## 입력 기준

정상 분석 입력은 사용자가 명시적으로 선택한 아래 패턴의 CSV 한 파일입니다.

```text
data/raw/04. ES_ 이슈사항 보고_*.csv
```

- 공식 기간 기준 컬럼은 `접수일`입니다.
- 새 파일이라는 이유만으로 누적 Raw로 자동 확정하지 않습니다.
- `data/raw`와 `data/master`는 읽기 전용 보호 입력입니다.
- 고객사 로봇 Master와 고장부품 Master는 현재 정상 분석 경로에 연결하지 않습니다.

## 주요 폴더

```text
AS report
├─ AS_Report.bat
├─ AGENTS.md
├─ README.md
├─ pyproject.toml
├─ .venv
├─ src
├─ tests
├─ config
├─ data
├─ reports
└─ MD
```

- `src/as_report`: 애플리케이션과 분석 코드
- `src/as_report/resources`: DY PPT 기본 양식
- `tests`: 회귀 테스트
- `config/standard_names`: 사용자가 관리하는 표준명 참조 파일
- `data/raw`, `data/master`: 보호 입력
- `reports`: 대표 호환 파일과 localhost 검토 산출물
- `MD/CURRENT_STATUS.md`: 현재 상태와 남은 제한
- `MD/_chatgpt_handoff`: 최신 GPT 전달본

## 대표 HTML/Excel

아래 파일은 기존 CLI 호환성을 위해 유지합니다.

```text
reports/as_report_2026.html
reports/as_report_2026_summary.xlsx
```

현재 두 파일은 동일 실행에서 생성된 유효 pair로 확인되지 않았으므로 하나의 대표 세트로 공유하지 않습니다. 별도 승인 없이 수정하거나 재생성하지 않습니다.

고급 사용자는 CLI를 계속 사용할 수 있습니다.

```bat
.venv\Scripts\python.exe -m as_report.cli --input "data\raw\04. ES_ 이슈사항 보고_20260630.csv" --period year --year 2026 --output reports
```

## 개발 확인

```bat
AS_Report.bat --check
.venv\Scripts\python.exe -m pytest tests -p no:cacheprovider
```

개발 의존성이 필요한 새 환경:

```bat
.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

## 운영 안전

- Raw/Master 원본을 자동 수정하거나 병합하지 않습니다.
- 추정값을 확정값으로 기록하지 않습니다.
- 원인, 책임, 고객 영향, 비용 절감, 개선 효과를 입력 근거 없이 자동 단정하지 않습니다.
- 대표 파일 재생성, reports 정리, 외부 연동은 각각 승인된 작업에서만 수행합니다.
- 상세 규칙은 `AGENTS.md`, 현재 상태는 `MD/CURRENT_STATUS.md`를 확인합니다.

## 과거 이력

정리 전 문서, 완료보고서, handoff, validation 및 사용자 산출물은 아래 외부 보관 ZIP에 해시 manifest와 함께 보존합니다.

```text
C:\Users\johnny\AS report_archive\AS_report_history_20260902.zip
```

기존 진행 이력은 Google Drive의 **AS Report Project Control**에 남아 있습니다. 신규 작업 상태와 승인 기준은 `TASKS.md`이며 과거 승인과의 대조는 별도 작업으로 관리합니다.

## 개발 작업의 공용 기억

작업 시작 전 `AGENTS.md`, `ARCHITECTURE.md`, `TASKS.md`를 확인합니다. 신규 작업/승인은 `TASKS.md`, 주요 변경은 `CHANGELOG.md`에 남깁니다. 기존 Google Drive 관리표는 과거 승인 대조용이며 자동 동기화하지 않습니다. 전용 비공개 저장소는 https://github.com/JohnnyHan93/AS-Report 입니다. 게시 검증 상태는 TASKS.md의 ASR-M002에 기록합니다.

현재 PDF는 Edge/Chrome으로 임시 HTML을 인쇄하며, PowerPoint는 발표용 PPT 생성에 필요합니다. V2 Word/PPTX는 별도 메모리 생성 경로입니다. 과거 문서의 PowerPoint 기반 PDF 설명보다 현재 코드 구조는 `ARCHITECTURE.md`를 참고합니다.



## GitHub와 로컬 입력

GitHub에는 소스, 테스트, 기본 템플릿과 공용 문서를 저장합니다. `data/`, `config/`, `reports/`, `.venv/`, `tmp/` 및 과거 handoff 원본은 `.gitignore`로 제외합니다. 새 clone에는 실제 업무 입력과 사용자 표준명 설정이 없으므로 승인된 로컬 입력을 별도로 준비해야 합니다. 실제 데이터를 테스트 fixture나 소스에 붙여 넣지 않습니다. 설계·과거 완료보고서·인계 목록의 검토된 게시용 사본은 [개발 자료 목록](docs/README.md)에 있습니다. 원본 진단 로그와 실제 산출물은 로컬에만 보존합니다.
