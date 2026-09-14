# Changelog

검증된 변경과 근거만 기록한다. 과거 테스트 결과를 현재 재검증 결과로 취급하지 않는다.

## 2026-09-14 — ASR-M002 연결 조사

- 사용자 지정 JohnnyHan93/Johnny-AI-OS의 private/main 및 HEAD 385fd85dece8c8108a6d736ede70e43c177bf7b9 확인.
- 원격은 상위 OS 저장소로 확인. 실제 앱은 별도 구현 저장소로 연결하라는 원격 규칙과 A/S 루트 직접 연결의 구조 충돌 발견.
- 저장 위치 결정 전 git 초기화·commit·push 보류. 로컬 TASKS/CHANGELOG만 갱신. 소스·Raw/Master·보고서 및 원격 변경 없음.

## 2026-09-14 — ASR-M001

- 01 MASTER / 02 ENGINE / 03 OUTPUT / 04 UI / 05 QA 역할과 승인·검수 흐름 정의.
- ARCHITECTURE.md, TASKS.md 추가. 신규 작업 현황은 TASKS.md에서 관리.
- AGENTS.md에 공용 기억 규칙 추가. 기존 외부 관리표는 명시적 대조 전까지 과거 참조로 유지.
- Word 시각 검수 미완료, PDF 코드/과거 문서 차이, 대표 pair P0 보존.
- 런타임 변경 없음. Git 저장소/remote 미확인으로 commit/push 없음.
- 검증 증거: MD/completion report/MASTER_memory_setup_completion.md.

## 2026-09-14 — ASR-M002 전용 저장소 생성

- 사용자 승인으로 JohnnyHan93/AS-Report private 저장소 생성. Johnny-AI-OS는 보존.
- 현재 폴더 Git 초기화, allowlist .gitignore 적용. 업무 입력/설정/보고서/환경/임시파일 제외.
- 최초 게시 기준 canonical tests: 142 passed. 최종 commit 및 원격 동일성은 TASKS.md 완료 기록 참조.

- 게시 확인: main 초기 commit `16e69ea2ddb5dafe48aa1820ad0fa3a442bfe6cf`, 91개 파일, private 확인. 비캐시 기준 107개 파일 해시 불변. ASR-M002 완료.
