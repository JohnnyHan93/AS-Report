> 역사 기록의 게시용 사본입니다. 당시 결과·미완료 사항을 보존하며 현재 승인이나 새 테스트 결과를 뜻하지 않습니다. 최신 상태는 [TASKS](../../TASKS.md)와 [인계 안내](../README.md)를 확인하십시오. 로컬 진단·handoff·실제 산출물 참조는 GitHub에 포함되지 않습니다.

# Completion Report

## 2026-09-15 QA-E001-01 재작업

- 재작업 결과: REVIEW. canonical `.venv/Scripts/python.exe -m pytest tests --basetemp tmp/pytest_e001_rework_all -p no:cacheprovider -q`: 167 passed (89.72s). 독립 QA 재검수 및 Master 최종 수락 대기.

- 사용자 승인 범위: 정상 긴 CSV 셀 호환성과 공용 CSV 설정 영향만 수정. 기존 loader/UI/분석/렌더러, 독립 QA 테스트는 변경하지 않았다.
- 원인: csv.reader의 기본 131072자 제한을 일반 구문 오류로 보고했다.
- 수정: 표준 라이브러리 CSV 파싱을 `sys.executable -I` 별도 프로세스로 격리. 입력 문자열 전체 길이 이상을 셀 한도로 사용하여 새 업무상 크기 제한을 추가하지 않는다. 긴 셀을 자르거나 행을 건너뛰지 않는다. Windows 창은 CREATE_NO_WINDOW로 숨긴다.
- 공용 설정: 부모 프로세스의 csv.field_size_limit는 import/호출/실패/동시 실행 동안 변경하지 않는다. 따라서 원래 값을 덮어써 복원하는 경쟁도 없다. 격리 프로세스의 설정은 종료와 함께 사라진다. 외부 코드가 부모 설정을 임의 변경해도 점검 파서는 영향을 받지 않는다.
- 오류 구분: CSV 구문 오류와 크기/메모리 자원 오류, 프로세스 실행/종료 오류를 별도 안내한다. 원문/프로세스 stderr를 사용자 오류로 노출하지 않는다.
- 회귀 추가: 131071/131072/131073/524288자, 한글·따옴표·CRLF, 후속 행 위치·ID·날짜·원문 보존 및 기존 loader 호환. 공용 한도 32에서 4개 스레드 12회 성공/구문실패 혼합 호출 후 설정 유지와 독립 csv.reader 제한 유지. 자원 오류/프로세스 실행 실패도 설정 불변 검사.
- 독립 QA 테스트 원본은 수정/삭제하지 않았다. focused 실행 61 passed (101.58s): tests/test_input_contract.py, tests/test_loader.py, tmp/asr_e001_independent_qa_20260914/test_independent_contract.py; basetemp tmp/pytest_e001_rework_focused, -p no:cacheprovider -q.
- import 및 변경 source/test py_compile 통과. 명시 Downloads CSV 재검증: 기존 loader 행 수 일치, 날짜 분해 일치, 파일 hash/mtime/크기 불변. 기존 진단 파일은 덮어쓰지 않았다.
- 보호 비교: Raw/Master, reports, 지정 Downloads 원본 및 독립 QA 테스트 총 11개 파일 hash/mtime/크기 전후 동일.
- 제한: 프로세스 시작 및 JSON 전달 비용이 추가되며 입력/레코드의 메모리 복사 비용이 있다. 운영체제의 자원 한계까지 무제한 처리를 보장하지 않는다. 자원 부족 테스트는 오류 분기 모의이며 실제 메모리 고갈을 유발하지 않았다. UI 연결/대표·validation 생성/다음 작업/commit/push 없음.
- 기준 HEAD a1a09d550c3c0ec696659cd06ec65e4fe427b60a는 작업 전 저장소 기준이며 미커밋 수정 내용의 SHA가 아니다. 아래 2026-09-14 기록은 이전 구현 증거로 보존한다.

## Task Summary

ASR-E001 / REPORT / REVIEW, 2026-09-14. 사용자 직접 승인한 첫 구현 단위인 독립 CSV 입력 점검 계층만 구현했다. UI / QA 및 Master의 수락은 대기 중이다.

## Modified Files

- TASKS.md: 사용자 승인, 담당, IN_PROGRESS 및 REVIEW 증거 기록.
- CHANGELOG.md: 해당 작업 결과만 추가. 기존 Master 문서 변경 보존.

## Created Files

- src/as_report/input_contract.py
- tests/test_input_contract.py
- 이 완료보고서
- 로컬 진단: tmp/asr_e001_validation/check_real_input.py, result.json

## Input Contract

`inspect_csv(explicit_path) -> InputInspection`은 파일을 쓰지 않는다. `to_dict()`로 진단용 직렬화가 가능하다. 새 공개 API는 기존 load_input이나 CLI/Streamlit에 자동 연결되지 않는다.

- 동일 바이트에서 SHA-256/인코딩/원본 헤더/원본 셀/행 수를 구한다. ID 선행 0과 NA 등 문자열을 보존한다.
- record_number는 헤더 다음 1부터 시작하는 CSV 레코드 순서이며 line_start/end는 1부터 시작하는 물리 행이다. 따옴표 안 개행을 추적한다.
- source_key는 파일 해시+레코드 순번이다. 실행 간 메모 승계/병합키가 아니다.
- 헤더 공백 정리는 매핑에만 사용한다. 원본/공백 정리 후 중복, 빈 헤더, 행 너비 불일치는 구조 오류로 남기고 모든 매핑·기능을 제한한다. 구문 오류는 DataLoadError이다.
- 승인된 고장유형 별칭만 고장원인에 매핑한다. canonical 열이 있으면 공란이어도 우선한다. 모르는 이름과 DYONE는 자동 대체하지 않는다.
- ID 미입력/정확한 원문 ID 중복을 구분한다. 주변 공백이 다른 ID는 자동 병합하지 않는다.
- 날짜 상태는 valid/missing/invalid/column_missing/structure_unavailable이다. 열 누락 시 측정 건수는 None, unassessed에 행 수를 기록한다. 유효+공란+오류+미평가=전체 행 수이다.
- 날짜는 연-월-일, 연/월/일, 연.월.일과 명시된 시간 형식만 수용한다. 숫자 직렬값/모호한 월일연/새 형식은 자동 추정하지 않는다.
- feature status는 입력 근거의 가용성이다. usable_rows는 날짜 유효 및 해당 필드 비공란 행 수이며 업무 모집단 확정/클레임 건수/완료율이 아니다. 공란 행 삭제 또는 원문 보정은 수행하지 않는다.
- 제조사 검토 기능은 업무유형과 제조사 입력 존재성만 검사한다. 실제 클레임 필터·후속 요청 분류·단어 기반 후보 추출은 구현하지 않았다.
- 기능별 누락 열, 유효 날짜 없음, 사용 가능한 행 없음, 텍스트 열 없음과 구조 오류 사유를 반환한다. 미입력 값을 0건으로 대체하지 않는다. 데이터가 없는 열과 실제 0개의 유효 행을 구분한다.

## Protected Files Check

기존 src/data/reports 비캐시 73개 파일의 경로·크기·UTC 수정시각·SHA-256 전후 일치. 새 source 하나만 추가됐다. 지정 Downloads 입력도 크기·수정시각·SHA-256 전후 동일하다. Raw/Master 복사·수정·병합 및 대표/validation 재생성 없음. 기존 tests 삭제/수정 없음.

## Test Results

- Import: 프로젝트 .venv의 as_report 및 inspect_csv import 통과.
- Compile: `.venv/Scripts/python.exe -m py_compile src/as_report/input_contract.py tests/test_input_contract.py` 통과.
- 초기 focused: `.venv/Scripts/python.exe -m pytest tests/test_input_contract.py tests/test_loader.py --basetemp tmp/pytest_asr_e001_focused -p no:cacheprovider`: 24 passed.
- 최종 canonical: `.venv/Scripts/python.exe -m pytest tests --basetemp tmp/pytest_asr_e001_all -p no:cacheprovider`: 160 passed (52.33s). 신규 계약 18개 및 기존 loader/HTML/Excel/표현/V2 회귀 포함.
- 검증 항목: legacy/alias-only/both/neither, 재정렬·추가·미매핑, 중복 헤더, ID 선행0/공란/중복, 날짜 공란/오류, 다중 물리 행, 빈 파일·헤더만, 행 길이 오류, 인코딩, 기존 strict loader 유지.
- 전체 git diff --check는 작업 전부터 수정된 CHANGELOG의 기존 빈 줄 CRLF 공백 경고(15행)를 반환했다. 관련 없는 Master 문서 줄은 정리하지 않았다. 소스/테스트 실패가 아니다.

## Runtime Validation

명시 입력: Downloads의 `04. ES_ 이슈사항 보고_20260910 (1).csv`를 제자리에서 읽었다. data/raw로 복사하거나 baseline 승격하지 않았다.

`tmp/asr_e001_validation/check_real_input.py` 실행 통과. 상세 로컬 진단은 같은 폴더 result.json이다. 기존 loader와 행 수 일치, 날짜 분해 합계 일치, 원본 해시 불변을 assert했다. 개인정보·원문 행을 완료 문서에 복제하지 않았다. 파일 식별/품질 수치는 로컬 진단에만 남긴다.

## Output/Report Impact

보고서 생성, UI 변경, 기존 계산 변경 없음. HTML/Excel 렌더러 변경이 없으므로 별도 보고서 산출물/시각 검수는 수행하지 않았다. 대표 pair P0는 유지한다.

## Known Limitations

CSV 콤마 구분 형식 전용이다. 추가 날짜 형식·별칭·DYONE 우선순위는 별도 승인 필요. available은 열과 텍스트의 존재성이지 의미의 정확성·요청 유효성·기간 전체 coverage 보증이 아니다. 후속 UI 연결 전 필드 품질과 제외 사유를 함께 표시해야 한다.

## Remaining Risks

상태 계산 통합/CS 포함 목록/자동 후보 추출/메모 영속성은 이번 범위 밖이다. 기존 기능의 완료 상태 정의 차이는 수정하지 않았다. 독립 QA와 Master 검토 대기. git commit/push는 수행하지 않았다.

## Recommended Next Step

Master가 ASR-E001 결과 계약과 검증 증거를 검토한다. 승인 없이 ASR-U001 또는 다른 작업을 시작하지 않는다.
