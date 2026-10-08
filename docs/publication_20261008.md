# GitHub 개발 자료 업데이트 검증

2026-10-08 / ASR-M005 / MASTER / DONE (개발 자료 게시 범위)

개발 자료 커밋 `6c4d65a494f457d2b887dd96165c5d9308672e99`를 기존 private 저장소 main에 정상 push하고 원격 main과 로컬 SHA 일치를 확인했다. 이 완료 기록은 후속 문서 커밋으로 게시한다. 최종 HEAD는 Git 이력에서 확인한다. 기능 수락·운영 배포 완료를 뜻하지 않는다.

목적은 연구소에 전체 개발 자료를 인계하는 것이다. 기능 완료·운영 배포·연구소 접근권한 부여와 구분한다. 원격은 `JohnnyHan93/AS-Report`, private, main으로 확인했다.

코드·테스트·필수 자산과 검토한 문서만 게시한다. 실제 데이터·보고서·config·백업·로그는 제외한다. 과거 완료기록의 로컬 원본은 보존하고 게시용 사본에서 업무 집계 수치와 개인 경로를 제거했다.

## Task Summary

기존 main 기준 `a1a09d550c3c0ec696659cd06ec65e4fe427b60a` 이후의 입력 계약 코드·테스트와 개발 자료를 게시 대상으로 정리했다. ASR-E001은 REVIEW를 유지한다. 이번 검증은 게시 재현성 확인이며 별도 담당자의 최종 독립 QA 수락을 주장하지 않는다.

## Modified Files / Created Files

- 기존 수정: 게시 허용 목록, README·ARCHITECTURE·TASKS·CHANGELOG·CURRENT_STATUS.
- 미게시 구현: `src/as_report/input_contract.py`, `tests/test_input_contract.py`. 이번 게시 작업 중 런타임 코드와 기존 테스트 기대값은 변경하지 않았다.
- 추가 자료: docs의 인계 안내, 상세 설계 사본, 과거 완료/규칙/인계 목록, 합성 독립 QA 테스트 사본, 이 보고서. [목록](README.md).
- 최종 게시 목록 112개 파일 중 코드·테스트·필수 자산을 포함한 107개 파일로 격리 사본 검증 후 과거 인계 목록 5개를 추가했다. 추가/최종 수정은 Markdown과 허용 목록뿐이며 검증된 source/tests/pyproject 해시는 동일하다.

## Test Results

| 검사 | 이번 실행 결과 |
| --- | --- |
| 로컬 import / 변경 Python compile | PASS; compile 출력은 tmp에만 저장 |
| 입력 계약 + loader focused | 32 passed, 48.13초 |
| 게시 사본 전체 canonical tests | 167 passed, 96.79초 |
| 게시 사본 추가 독립 QA 테스트 | 29 passed, 47.22초 |
| 코드 import 위치 | 게시 사본 내부 경로 확인 |
| 문서 링크 / 필수 PPT·로고·스타일 자산 | PASS |
| 게시 범위 / 자격증명 패턴 / 문서 내용 검토 | 제외 경로 유입 없음, 탐지된 자격증명 패턴 없음, 실제 업무 집계 문장 제거 |

테스트 명령은 [인계 안내](README.md)에 있다. canonical 검증과 추가 QA 테스트는 고객 데이터·운영 config가 없는 별도 사본에서 실행했다. QA 사본은 로컬 보존 원본과 바이트가 동일하다. 원래 QA에서 실패한 131073자 합성 셀도 이번에는 통과했다.

## Protected Files Check

데이터·기존 reports·config·로컬 완료/설계/handoff 원본·BAT 등 기준 파일 61개는 SHA-256·크기·수정시각이 동일했다. 문서 수정 대상인 CURRENT_STATUS는 비교 제외를 명시했다. Raw/Master, 기존 대표/validation 보고서, 가상환경의 재설치·수정·정리는 수행하지 않았다. 외부 archive는 열거나 변경하지 않았다.

## Runtime Validation

기존 로컬 Python 환경을 사용해 게시 사본을 실행했다. 새 PC의 빈 가상환경 설치·PowerPoint·브라우저 인쇄·실제 다운로드·실제 고객 CSV 실행은 이번 범위에서 재검증하지 않았다. 합성 회귀 통과를 실제 운영 배포 성공으로 표현하지 않는다.

## Output/Report Impact

실제 보고서·원본·업무 config는 게시하지 않았다. 새 보고서 생성, UI 연결, 계산 변경, DY CS Agent 수정, 외부 관리표 동기화, 연구소 계정 초대 없음.

## Known Limitations / Remaining Risks

ASR-E001 재작업은 기존 Report 결과와 이번 게시 검증까지이며 최종 독립 수락 대기다. ASR-U001은 CANDIDATE다. CS 모집단·완료율 분모·후보 규칙 결정, Word 시각 검수, 현재 PPT/PDF 운영 검증과 대표 pair P0가 남아 있다. 회사 매핑 자료와 실제 입력은 승인된 별도 경로로 준비해야 한다.

## Recommended Next Step

게시 후 연구소는 인계 안내와 현재 TASKS를 읽고, 승인된 환경에서 설치·합성 검증부터 재현한다. 구성원 접근권한 부여와 운영 배포는 별도 작업이다.
