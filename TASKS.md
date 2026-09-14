# Tasks

기준일: 2026-09-14. 신규 작업 현황의 기준 문서. Master: 이 작업(01 Master / Integration).

## 운영 규칙

CANDIDATE -> READY -> IN_PROGRESS -> REVIEW -> DONE. READY는 승인 근거가 있어야 한다. BLOCKED는 실제 정지 조건에만 사용한다. 담당자는 승인된 한 건만 처리하고 자동으로 다음 작업을 시작하지 않는다. 완료 전 QA 증거와 Master 수락을 남긴다. Git 미연결 동안 Commit은 `없음`으로 기록한다.

| ID | 우선순위 | 담당 | 상태 | 목표 |
| --- | --- | --- | --- | --- |
| ASR-M001 | P1 | MASTER | DONE | 로컬 공용 기억 문서와 역할·승인 규칙 구축 |
| ASR-M002 | P1 | MASTER | IN_PROGRESS | 전용 비공개 저장소 연결 및 최초 게시 |
| ASR-Q001 | P1 | OUTPUT + QA | CANDIDATE | V2 Word 시각 검수 완료 |
| ASR-Q002 | P1 | QA | CANDIDATE | 현재 PPT/PDF 다운로드 경로 운영 검증 |
| ASR-R001 | P0 | MASTER | BLOCKED | 대표 HTML/Excel 동일 실행 pair 검증·재생성 승인 |

## ASR-M001 — 공용 기억 구축

- 승인: 2026-09-14 사용자가 제시한 저장소 공용 기억 방식으로 01 Master 수행 요청.
- 범위: AGENTS, ARCHITECTURE, TASKS, CHANGELOG 및 README/CURRENT_STATUS 연결·상태 설명.
- 제외: 런타임 수정, 데이터/산출물 변경, 외부 동기화, GitHub 게시, 다른 작업 착수.
- 수락 기준: 코드 기반 모듈 지도, 단일 신규 작업 큐, 역할/상태/승인 규칙, 기존 미검증 항목 보존.
- 검증: 문서 참조 경로 확인; 소스/테스트/설정/Raw/Master/reports/BAT의 변경 전후 SHA-256 비교. 상세 결과는 `MD/completion report/MASTER_memory_setup_completion.md`.
- QA/Master 수락: 동일 담당자의 문서·범위 검토로 LOW 문서 작업 완료. 독립 QA 수행 주장은 없음.
- Commit: 없음. 현재 폴더는 Git 저장소가 아님.
- 다음: ASR-M002에 실제 저장소 URL 또는 checkout 경로를 제공받는다.

## ASR-M002 — 전용 저장소 연결

- 승인: 2026-09-14 사용자가 JohnnyHan93/AS-Report 비공개 저장소 신규 생성 및 현재 로컬 폴더 연결에 “진행”으로 승인.
- 목표: 현재 소스와 공용 기억 문서를 전용 저장소 main에 게시하고 동일 commit을 검증한다.
- 원격: https://github.com/JohnnyHan93/AS-Report (private 확인, 신규 생성).
- 로컬: C:\Users\johnny\AS report. 기존 Johnny-AI-OS에는 변경하지 않는다.
- 게시 범위: 소스/테스트/회사 기본 템플릿/BAT/패키지 설정/공용 Markdown.
- 제외: data, config, reports, .venv, tmp, 기존 handoff와 과거 완료보고서, 자격증명. .gitignore allowlist 적용.
- 수락 기준: private, main, origin URL, 로컬/원격 SHA 일치; 제외 파일 미추적; 보호 파일 불변; 테스트 결과 기록.
- 검증: 최초 게시 전 canonical tests, git diff --cached, ls-files, ls-remote 및 readback.
- Commit: 최초 게시 후 아래 완료 기록에 실제 SHA 기록.
- 과거 관리표 승인 대조는 이번 저장소 생성 요청의 범위가 아니므로 별도 CANDIDATE ASR-M003으로 분리한다.

## ASR-M003 — 과거 승인 이력 대조 (CANDIDATE / MASTER / P2)

- 승인: 미기록. 기존 Project Control과 현재 TASKS의 승인·상태를 근거 자료로 대조한다.
- 자동 외부 동기화와 미승인 task 승격은 금지한다.
- 수락 기준: 관련 행의 승인 출처와 충돌·미확인 항목을 기록한다.

## ASR-Q001 — V2 Word 검수

- 승인: 후속 작업 승인 미기록. 기존 상태는 Implemented / Runtime Check Pending.
- 근거: `MD/completion report/REPORT_TOOL_V2_completion.md`.
- 목표: 정상 렌더링 환경에서 DOCX 페이지, 긴 한글, 표 분할, 필수 내용, 동일 실행 식별정보 확인.
- 범위: 새 validation-only 산출물과 검수 기록. 수정 필요 시 범위를 먼저 확정.
- 제외: 대표 재생성, Raw/Master 변경, 환경 패키지 임의 변경.
- 수락 기준: 재열기/내용 검사와 전체 페이지 시각 검수 증거, 미해결 문제 명시, Master 수락.
- 검증: Documents 스킬 및 AGENTS 위험도별 기준. 과거 142 passed를 새 실행 결과로 기록하지 않는다.

## ASR-Q002 — 현재 PPT/PDF 운영 검증

- 승인: 미기록.
- 근거: 현재 PDF는 report_pdf.py 기반이고 과거 HTML 전체 보고서 PDF 완료보고서와 다름.
- 목표: 선택된 명시적 입력/기간으로 다운로드, 페이지·차트·긴 표 확인, 형식별 실패 분리 확인.
- 범위: 현재 코드 및 새 검증 산출물. 기능 수정은 발견 후 별도 범위 확정.
- 수락 기준: 실제 실행 환경/입력 식별정보와 성공·실패 결과, 시각 검수, 보호 파일 불변 증거.
- 검증: presentation/app 관련 테스트와 실제 다운로드. 최종 사용자 표시 환경 확인은 미수행이면 별도 표기.

## ASR-R001 — 대표 pair P0

- 정지 근거: CURRENT_STATUS와 README에 기존 pair 미확인 기록. 이번 작업에서 pair 유효성 재검증 안 함.
- 해제 조건: 사용자 승인 입력 범위 및 대표 동시 재생성 승인, Raw coverage 확인, 같은 run_id/출처/기간/필터/버전 검증.
- 금지: 한쪽만 재생성, 유효 대표 세트로 공유, 코드 구현만으로 P0 종료.
- 이 P0는 대표 출력 작업에 적용되며 무관한 문서 작업을 막지 않는다.

## 작업 기록 양식

새 ID / 우선순위 / 담당 / 상태 / 승인 근거 / 목표 / 허용·금지 범위 / 의존성 / 수락 기준 / 변경 파일 / 검증 명령·결과·증거 경로 / 데이터·산출물 영향 / 실제 Commit SHA / QA / Master 수락 / 다음 행동을 기록한다.

## 담당 작업 시작 지시문

AGENTS.md, ARCHITECTURE.md, TASKS.md를 읽고 내 담당의 승인 근거가 있는 최우선 READY 한 건을 수행한다. 없으면 착수하지 않는다. 변경 전 담당과 범위를 기록하고 검증 후 해당 task와 CHANGELOG를 갱신한다. Git 연결 시 실제 commit SHA를 기록하고 REVIEW로 넘긴다. 보호 입력·대표 출력 승인과 P0를 우회하지 않는다.
