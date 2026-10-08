## 2026-10-08 — 연구소 인계 개발 자료 게시

- 게시: `6c4d65a494f457d2b887dd96165c5d9308672e99` main push와 원격 SHA 일치 확인. focused 32 / 게시 사본 전체 167 / 추가 QA 29 passed. 보호 기준 61개 불변. ASR-M005 DONE은 게시 작업만의 완료다.
- 독립 CSV 점검 구현·테스트와 설계·과거 완료/QA 기록의 게시용 사본을 준비했다. 원본 기록과 보호 입력은 보존한다.
- 인계 안내·현재 구현/설계 경계·설치 의존성·게시 제외 정책을 정리했다. ASR-E001 REVIEW와 대표 pair 차단을 유지한다.
- 현재 검증·게시 결과는 docs/publication_20261008.md에서 확인한다. 과거 테스트 수치는 재실행 결과가 아니다.

# Changelog

## 2026-09-15 — ASR-E001 QA-E001-01 수정 (REVIEW)

- 긴 CSV 셀 파싱을 격리 프로세스로 실행하여 부모 공용 필드 제한 변경 없이 원문 보존. 구문 오류와 자원/실행 오류 안내 분리.
- 경계·한글·따옴표·개행·동시 호출·공용 설정 및 예외 회귀 7개 추가. 기존 독립 QA 실패 테스트 보존 후 통과.
- focused 61 passed, 전체 167 passed. import/compile 및 명시 CSV 실파일 검증 통과. 보호 입력/보고서/독립 테스트 11개 hash·mtime·크기 불변.
- 상세 증거는 ASR_E001_input_contract_completion.md. UI 연결·후속 작업·대표 재생성 없음. 독립 재검수 및 Master 수락 대기.

## 2026-09-15 — ASR-E001 QA 결함 재작업 배정

- Master가 QA-E001-01(P2)을 수락: csv 기본 필드 한도로 정상 131,073자 셀을 구문 오류로 거부한다.
- 전체 suite 통과와 별개로 독립 경계 테스트 실패가 남아 DONE 보류. 기존 승인 범위 내 REPORT 재작업 READY.
- 긴 필드 원문 보존·경계 회귀·csv 공용 설정 영향 검증을 수락 기준에 추가. 이번 변경은 문서만이며 UI 연결/다음 기능은 착수하지 않음.

## 2026-09-14 — ASR-E001 독립 UI / QA

- 검증만 수행: 기존+독립 focused 53 passed/1 failed, canonical 160 passed (47.26s), import/메모리 compile 통과.
- P2 QA-E001-01 재현: 단일 셀 131,073자인 정상 CSV는 기존 loader 성공, 신규 입력 점검은 기본 csv 크기 제한으로 구문 오류 처리. 소스 수정 없음.
- src/tests/data/reports/BAT 비캐시 99개 파일 불변. UI 연결·ASR-U001·대표 재생성 없음. 상세 재현/검수 HEAD와 파일 해시는 TASKS 및 ASR_E001_independent_QA.md 참조.
- REVIEW 유지, 결함 처리와 최종 수락은 Master에게 인계. commit/push 없음.


## 2026-09-14 — ASR-E001 Master 기술 검토

- 독립 CSV 점검 모듈·테스트 및 제출 증거 검토. 수정 요구 결함 미발견.
- Master focused 25 passed, 실제 CSV 읽기 및 원본 불변 재확인. 전체 160 passed는 Report 실행 증거로 구분.
- 별도 UI / QA 검증 대기로 REVIEW 유지. UI 통합 및 다음 구현 미착수.

## 2026-09-14 — ASR-E001 (REVIEW)

- 사용자 직접 승인한 독립 CSV 입력 점검 계층 추가: input_contract.py. 기존 loader/CLI/UI/보고서 경로 미연결.
- 원본 헤더/셀/ID/행 위치 보존, 승인 alias, 중복 헤더·날짜·열 누락 검사 및 기능별 입력 가용성 제공. 상태/후보 계산 변경 없음.
- 회귀 테스트 18개 추가. import/compile, 초기 focused 24 passed, 최종 pytest tests 160 passed. 지정 Downloads CSV 읽기와 원본 불변 확인.
- 기존 src/data/reports 73개 파일 크기·mtime·SHA-256 불변. 대표/validation 생성 없음. 상세 증거: MD/completion report/ASR_E001_input_contract_completion.md.
- Master/독립 QA 검토 대기. 다른 작업 착수 및 commit/push 없음.

## 2026-09-14 — ASR-M004 설계 결정 확정

- 사용자 승인: 처리완료만 완료, 전달 완료 별도, 상태 공란 미입력.
- 1차 산출물은 내부 PDF + 검토 Excel, 담당자 메모는 Excel에서 수동 관리. 앱 재업로드·자동 승계는 후속 단계.
- 설계 문서와 TASKS에 결정 반영. 첫 Report 구현 초안 ASR-E001을 입력 점검 계층으로 한정하고 수락·검증 기준 구체화. 구현 승인 전 CANDIDATE 유지.
- 문서만 수정. 기존 데이터·코드·보고서 변경과 Git 게시 없음.

## 2026-09-14 — ASR-M004 Master 설계 검토

- 상세 설계와 cleaner/legacy_features 완료 기준 차이를 직접 확인. REVIEW 유지, 구현 자동 승인 없음.
- 상태 사전·PDF/Excel 1차 범위는 사용자 결정 대기. 수동 메모의 실행 간 승계, 후보 문맥 판별, 모집단과 제외 범위는 추가 명세 필요.
- 설계 MD의 Git 제외 상태 확인. 로컬 문서만 갱신하고 소스/데이터/보고서 및 원격은 변경하지 않음.

검증된 변경과 근거만 기록한다. 과거 테스트 결과를 현재 재검증 결과로 취급하지 않는다.

## 2026-09-14 — ASR-M004 Report 상세 설계 (REVIEW)

- 사용자 직접 승인 범위로 MD/ASR_M004_CS_aftermarket_report_design.md 작성. CS 집계, 이슈 후속 조치, 스페어파트/개조/유지보수 검토 근거와 제외, CSV 입력 계약, 권장 산출물을 분리.
- 현재 코드의 완료 상태 기준 불일치 확인. 임의 계산 통합 없이 원본 상태 분포와 추가 승인 항목으로 기록.
- Master 조사 profile은 기존 근거로 참조했으며 새 원본 조사나 후보 정확도 검증으로 주장하지 않음.
- src/tests/data/reports 비캐시 96개 파일의 크기·수정시각·해시 전후 불변 확인. pytest 생략: docs-only / source unchanged. 대표/validation 재생성 없음.
- TASKS.md에 REVIEW 및 Master 검토 요청 기록. ASR-E001/ASR-U001 착수, 커밋, 원격 게시 없음.

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
