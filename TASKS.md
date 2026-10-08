## 2026-10-08 — ASR-M005 연구소 인계 GitHub 업데이트 / MASTER / DONE

- 완료: 개발 자료 커밋 `6c4d65a494f457d2b887dd96165c5d9308672e99` main push 및 원격 SHA 일치 확인. 후속 완료 기록은 Git 이력으로 추적한다.
- 검증: focused 32 passed, 게시 사본 canonical 167 passed, 추가 QA 29 passed. 보호 기준 61개 파일 불변. 문서 링크·게시 제외 정책·필수 자산 검사 통과. 세부 한계는 게시 검증 문서에 명시했다.

- 승인: 사용자의 전체 개발 자료 게시 범위 선택 및 계획 구현·커밋·푸시 직접 요청.
- 범위: 최신 코드/테스트 게시, 실행 자산 확인, 민감 내용을 제외한 설계·과거 기록 사본, 현황 문서, 인계 재현성 검증 및 기존 비공개 main 업데이트.
- 제외: 고객 원본/실제 보고서/운영 config/백업/자격증명, DY CS Agent, 새 기능·UI 연결·대표 생성·권한 변경.
- ASR-E001 REVIEW와 기존 P0를 유지한다. 아래 과거 commit 없음·Git 미연결 문구는 당시 기록이다. 현재 원격은 JohnnyHan93/AS-Report private/main으로 확인했다.
- 완료 기준: 게시 파일 검사, import/compile/focused/full 및 게시 사본 재현, 보호 파일 불변, 로컬/원격 SHA 일치. 증거는 [게시 검증](docs/publication_20261008.md).
- 문서 목록: [연구소 인계](docs/README.md). 로컬 완료기록 원본과 GitHub 게시용 사본을 구분한다.

# Tasks

기준일: 2026-09-14. 신규 작업 현황의 기준 문서. Master: 이 작업(01 Master / Integration).

## 운영 규칙

CANDIDATE -> READY -> IN_PROGRESS -> REVIEW -> DONE. READY는 승인 근거가 있어야 한다. BLOCKED는 실제 정지 조건에만 사용한다. 담당자는 승인된 한 건만 처리하고 자동으로 다음 작업을 시작하지 않는다. 완료 전 QA 증거와 Master 수락을 남긴다. Git 미연결 동안 Commit은 `없음`으로 기록한다.

| ID | 우선순위 | 담당 | 상태 | 목표 |
| --- | --- | --- | --- | --- |
| ASR-M001 | P1 | MASTER | DONE | 로컬 공용 기억 문서와 역할·승인 규칙 구축 |
| ASR-M002 | P1 | MASTER | DONE | 전용 비공개 저장소 연결 및 최초 게시 |
| ASR-M003 | P2 | MASTER | CANDIDATE | 과거 관리표 승인 이력 대조 |
| ASR-M004 | P1 | MASTER | REVIEW | CSV 기반 목적·입력·산출물 재정립안 |
| ASR-E001 | P1 | REPORT | REVIEW | QA-E001-01 긴 CSV 셀 입력 결함 보완 |
| ASR-U001 | P1 | UI / QA | CANDIDATE | 입력 점검·열 대응 확인·분석 가능 범위 표시 |
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
- 최초 게시 Commit: 16e69ea2ddb5dafe48aa1820ad0fa3a442bfe6cf. main push 성공, origin/main 추적 설정.
- 검증/수락: 142 tests passed; 원격 private 확인; 게시 91개 파일, 보호 경로 미게시; 비캐시 기준 107개 SHA-256 변경 0개. Master 문서·범위 검수 완료.
- 완료 기록 커밋은 git log에서 확인하며, 이 task의 초기 소스 기준 SHA는 위 값을 유지한다.
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

## ASR-M004 — 목적·산출물 재정립안

### 현재 결정 — 2026-09-14 사용자 “확정”

- 확정: 처리완료만 완료, 전달 완료 별도, 공란 미입력. 내부 회의 PDF + 검토 Excel. 담당자 메모는 Excel 수동 관리, 앱 재업로드·자동 승계는 후속 단계.
- 위 3개 사항에 대한 이전 결정 대기 문구는 이 기록으로 대체한다. 설계 문서에도 동일 결정 기록. 코드에 적용 완료됐다는 뜻은 아니다.
- ASR-M004는 남은 상세 정의(CS 포함 목록, 완료율 분모/표시, 후보 규칙/검증, 반복·중단 표시) 때문에 REVIEW 유지한다. 전체 요구사항을 DONE으로 과장하지 않는다.
- 다음 작업 초안: ASR-E001. 설계 확정 응답은 구현 착수 요청과 구분하므로 CANDIDATE 유지. Master가 범위·수락 기준을 아래에 구체화했다.

### Report 상세 설계 배정

### Master 상세 설계 검토 — 2026-09-14

- 결과: REVIEW 유지. 목적·원본 추적·분석별 가용성·매출 추정 제한의 설계 방향은 수용한다. 제품 정의 최종 확정이나 구현 READY 승격은 아직 하지 않는다.
- 직접 확인: cleaner.py:83은 처리완료만 완료, legacy_features.py:9는 전달 완료 등 6개 상태를 완료로 취급한다. 이름이 유사한 완료 지표가 다른 정의를 사용한다는 지적은 타당하다. 코드 수정 없음.
- 상태 권장안: 처리완료 / 전달 완료 / 접수·진행중 / 미입력 / 기타 원본값을 분리한다. 완료율을 제공한다면 처리완료만 분자로 하는 명시적 이름·분모를 사용한다. 사용자 결정 대기.
- 1차 범위 권장안: 내부 회의용 PDF + 검토용 Excel, 수동 담당자 기록은 다운로드한 Excel에서 관리. 다음 생성 시 메모가 자동 유지된다고 약속하지 않는다. 재업로드/병합/수동 기록 영속성은 별도 설계이며 사용자 결정 대기.
- 보완 1: 스냅샷 추적용 파일해시+행번호는 실행 간 안정 키가 아니다. 향후 메모 승계에는 고유 ID의 변경/중복/삭제 처리와 충돌 규칙이 필요하다.
- 보완 2: 후보 규칙은 단어 탐지를 넘어 고객 요청·부정·철회·기처리 여부를 판별할 구체적 규칙/검증표가 아직 없다. 초기에는 근거 확인 대기와 담당자 확인을 구분하며 자동 요청 확정으로 구현하지 않는다.
- 보완 3: CS 업무유형 포함 목록과 기타/미입력 처리 확정 전, 전체 ES 현황과 CS 대상 집계를 혼용하지 않는다. 주사용자는 CS팀으로 확정됐으므로 미확정 항목은 독자·회의 용도/포함 기준/형식이다.
- 보완 4: 반복·중단시간은 초기 Master 제안과 Report의 제외 제안이 다르다. 현재 presentation 경로에서 제외 문자열은 확인했으나 모든 출력의 업무상 제외 승인을 이 코드만으로 확정하지 않는다. 기존 표시 정책을 유지하고 신규 보고 노출 여부는 결정표에서 별도 확정한다.
- 공유 점검: git check-ignore 결과 설계 MD는 제외 대상이다. 로컬 검토 상태를 유지하고 Git 게시 시 해당 설계 파일만 명시적으로 추적 허용해야 한다. 원본 데이터·tmp를 함께 게시하지 않는다.
- 검증: 상세 설계 전 문단 및 관련 코드 정적 검토. 이번 Master 변경은 TASKS/CHANGELOG 문서만, pytest 생략. 기존 Report 수정 보존. 원본/보고서/소스 수정 및 외부 게시 없음.

### Report 제출 기록 (보존)

- 승인: 2026-09-14 사용자 직접 요청으로 ASR-M004의 CS 운영/후속 조치/애프터마켓/입력 계약/산출물 상세 설계만 승인.
- 담당: REPORT (ENGINE + OUTPUT). 상세 설계 상태: REVIEW. Master의 상위 REVIEW 상태는 유지. 구현 작업은 시작하지 않음.
- 허용: 설계 Markdown 생성, 이 배정 기록 및 CHANGELOG 갱신. 제외: 코드·테스트 수정, UI 변경, 입력 수정, 대표·validation 생성, 외부 게시.
- 근거: Master 입력 조사 tmp/mission_input_profile.json 및 현재 loader/분석 계약. 조사 결과는 기존 증거로 구분하며 원본 재검증으로 주장하지 않는다.
- 결과 문서: [CS 운영 및 애프터마켓 상세 설계](docs/design/ASR_M004_CS_aftermarket_report_design.md). CS 집계, 이슈 후속 조치표, 3종 후보 선정/제외, 열 계약, 산출물 권장안을 작성. 현재 가능/추가 데이터/승인 필요를 구분.
- 주요 검토사항: cleaner의 처리완료 기준과 legacy_features의 완료 집합 불일치 확인. 원본 상태 분포를 우선 제안하며 전달 완료/미입력의 합산 기준은 Master/사용자 결정 필요. 라인 중단 재노출, Master 연결, 매출/수요 추정 없음.
- 검증: 문서 필수 5개 범위 및 원문 추적·제외 규칙 검토. src/tests/data/reports 비캐시 96개 파일의 경로·크기·UTC 수정시각·SHA-256 합성 해시 전후 일치: 8EE66BEF54E99C290CE5DB6CA404AE29AAF94819A5831639864649E5BD38FF7C. pytest 생략: docs-only / source unchanged.
- 변경: 설계 문서 신규, 이 Report 배정 기록 및 CHANGELOG만 수정. 시작 전 존재한 Master의 TASKS 변경 유지. 코드·UI·Raw/Master·대표/validation 변경 및 재생성 없음.
- Commit: 이번 작업 없음; 읽은 기준 HEAD a1a09d550c3c0ec696659cd06ec65e4fe427b60a. push/외부 동기화 없음.
- QA/Master: Report 자체 문서·범위 검토, 독립 QA 및 Master 수락 대기. 다음 행동은 Master의 CS 모집단/상태 사전/산출물/후보 규칙 검토이며 자동 후속 착수 금지.

- 승인 근거: 사용자의 프로젝트 목적/산출물 재정립 요청, CSV 열 일부 변동 가능 설명 및 “이어서 진행”. 승인 범위는 입력 조사와 재정립안 작성이다. 제품 구현·기존 출력 폐기 승인이 아니다.
- 역할: Master가 목적/완료 기준 정리, Report가 분석·보고서 계약, UI / QA가 화면·검증 계약 담당. 기존 ENGINE/OUTPUT은 Report, UI/QA는 UI / QA로 묶어 운영한다.
- 상태: REVIEW. 제안 작성 및 읽기 전용 확인 완료, 주사용자·사용 목적·최종 형식 결정은 미확정.
- 입력: 사용자가 지정한 Downloads CSV를 제자리에서 읽었다. data/raw로 복사하거나 승인 baseline으로 승격하지 않는다. 파일별 조사 결과는 로컬 tmp/mission_input_profile.json이며 원본/집계값을 GitHub에 자동 게시하지 않는다.
- Observed: 현재 loader는 18개 필수 열과 승인된 고장유형 별칭을 사용한다. cleaner는 처리완료 외 상태를 미완료로 분류한다. DYONE 접미 열과 기존 열이 공존한다.
- 사용자 확정 방향: 고객사 고장 대응을 담당하는 CS팀이 사용자이며, 스페어파트 판매·개조·유지보수 등 애프터마켓 업무까지 연결하고자 한다. 이는 방향 승인이고 자동 영업 판단/외부 전송/매출 추정 구현 승인은 아니다.
- 목적 제안: CS팀의 고객사 고장 대응 현황과 미해결·반복 검토 대상을 정리하고, 원문 근거가 있는 후속 서비스 및 애프터마켓 검토 후보를 담당자가 판단할 수 있게 제공한다. 선택한 CSV의 품질·coverage를 함께 표시하고 결과를 재현 가능하게 만든다.
- 업무 구분 제안: CS 운영 현황 / 기술·품질 검토 / 애프터마켓 검토 후보를 구분한다. 반복 접수나 장비 연식만으로 고장 원인·교체 필요·개조 효과·구매 의사를 확정하지 않는다.
- 애프터마켓 최소 산출물 제안: 원본 *ID와 고객/설비 식별정보, 원문 근거, 후보 유형(스페어파트/개조/유지보수), 후보로 올린 규칙, 추가 확인사항, 담당자 판단·다음 조치. 담당자 입력은 원본과 분리한다. 비어 있는 항목은 추정으로 채우지 않는다.
- 근거 한계: 조사 CSV에는 견적·수주·판매금액 열이 없다. 매출/수주율/전환율·예상매출은 현재 CSV만으로 제공하지 않는다. 사업 기회 진행 관리와 판매 데이터 연계는 별도 범위 승인 후 설계한다.
- 미확정: 전체 ES 업무와 A/S 업무의 포함 기준, 독자/회의 목적, 완료·전달완료·미입력 상태 정의, 우선 산출물 형식. 전체 CSV 행 수를 고장성 A/S 접수건수로 부르지 않는다.
- 산출물 제안: (1) 요약 보고서: 기간/범위/주요 분포·변화/검토 후보/한계, (2) 검증·상세자료: 집계 근거/제외·미입력/원본 행 추적, (3) 동일 실행 메타데이터. PDF·Word·PPT·Excel 중 우선 형식은 사용자 결정 전 확정하지 않는다. 기존 HTML/Excel은 유지한다.
- 입력 계약 제안: 열 순서·추가 열은 수용하고 원본 보존. 이름 변경은 승인된 정확한 매핑만 적용. 유사 이름·DYONE 접미 열을 자동 병합하지 않는다. 필수 열 누락과 셀 미입력을 구분한다. 중복/정규화 후 충돌하는 헤더는 매핑 전에 알린다.
- 분석별 조건 제안: 접수일이 없으면 기간 보고 불가, 날짜 불명 행은 제외 수 표시 및 검토 목록 유지. 상태가 없으면 완료 지표를 숨기고, 상태 공란은 미입력으로 구분한다. 고객/기종/고장유형/중단시간이 없으면 해당 분석만 사용 불가로 표시하며 0으로 채우지 않는다. *ID 누락은 원본 행 위치로 추적하되 고유 이슈 수/중복 제거 판단은 제한한다. 중복 ID 처리 규칙은 별도 확정하며 자동 삭제하지 않는다.
- 시계열 조건: 관측 min/max만으로 기간 전체 수집을 보증하지 않는다. 비교기간 coverage와 정의가 맞을 때만 증감 해석을 허용한다. 입력이 수시 갱신된 스냅샷이면 과거 시점의 완료/미완료 상태로 소급 해석하지 않는다.
- 수락 기준: 사용자 목적·독자·산출물·집계 단위와 기능별 필수 열/누락 처리/상태 정의를 확정하고 후속 작업에 승인 근거를 기록한다.
- 검증: 원본 CSV 구조·헤더·ID·날짜 점검, 현재 loader 읽기 검사, 소스 정적 확인. 구현 변경이 없어 전체 테스트 재실행은 생략. 기존 대표 보고서 재생성 및 Raw/Master 수정 없음.
- 다음: 목적과 우선 산출물 결정 후 ASR-E001/ASR-U001 범위를 구체화한다. 현재는 후보이며 자동 착수하지 않는다.

### 산출물 구성 제안 — CS팀 및 애프터마켓 방향 반영

1. CS 운영 보고: 기간별 접수/업무 유형/원본 상태 분포, 고객·설비별 현황, 입력된 중단시간, 반복 검토 후보, 미입력·제외 범위. 과거 완료일 데이터가 없으면 처리 소요시간이나 당시 잔여 건수를 만들지 않는다.
2. 이슈·후속 조치 검토표: 원본 ID와 접수/조치 기록을 추적하고 미해결 여부는 합의한 상태 규칙으로 판정한다. 우선순위·담당·기한이 원본에 없으면 담당자가 별도 입력한다.
3. 애프터마켓 후보 검토표: 스페어파트 문의·교체 요청, 개조 요청, 유지보수/점검 요청 등 확인 가능한 기록부터 규칙 기반으로 제시한다. 키워드 언급만으로 수요를 확정하지 않는다. 제안 규칙과 제외 조건은 Report 구현 전에 사용자와 확정한다.

위 세 산출물은 업무상 역할이며 세 파일을 반드시 생성한다는 뜻이 아니다. 보고용 PDF/PPT와 검토용 Excel 등 전달 형식은 아직 미확정이다.

## ASR-E001 — 분석별 입력 계약 (REPORT / REVIEW — QA 재작업)

- 재작업 착수: 2026-09-15 사용자 직접 QA-E001-01 수정 승인 / REPORT. 긴 셀 및 공용 CSV 설정 영향 수정·회귀만 수행. UI 연결·후속 작업 없음.
- 재제출: REVIEW. input_contract.py의 파싱을 격리 Python 프로세스로 실행하여 부모 csv.field_size_limit를 변경하지 않음. 셀 크기 상한은 입력 전체 문자열 길이로 설정, 원문 보존. 구문/자원/실행 오류 구분.
- 검증: import(공용 설정 불변 포함)/compile 통과. 보존된 독립 QA 29개 포함 focused 61 passed (101.58s), canonical pytest tests 167 passed (89.72s). basetemp tmp/pytest_e001_rework_focused 및 tmp/pytest_e001_rework_all, -p no:cacheprovider -q.
- 경계/격리: 131071/131072/131073/524288자와 한글/따옴표/CRLF/후속 행/기존 loader 호환, 공용 한도 32에서 동시 성공/구문실패 및 독립 reader 영향 없음, 자원/실행 실패 모의 통과.
- 실파일: 명시 Downloads CSV 읽기 및 loader 행 수/날짜 분해 일치. data/reports/Downloads 원본/독립 QA 테스트 11개 hash·mtime·크기 불변. 기존 QA 테스트 수정/삭제 없음.
- 증거: MD/completion report/ASR_E001_input_contract_completion.md의 2026-09-15 재작업 기록. 변경은 허용 source/test 및 완료보고서/TASKS/CHANGELOG만. 대표·validation 생성/UI 연결/다음 작업/commit/push 없음.
- 제한/다음: 별도 프로세스 시작·메모리 복사 비용 추가. 실제 자원 고갈 실험은 미수행. Report 재검증 통과이며 독립 UI / QA 재검수와 Master DONE 수락은 대기.

### Master QA 판정 및 재작업 배정 — 2026-09-15

- 판단: 독립 QA 완료는 제품 통과가 아니다. 53 passed/1 failed 및 canonical 160 passed를 함께 검토했다. 정상 CSV 긴 셀 거부 결함 QA-E001-01(P2)을 수락하고 DONE을 보류한다. 앞선 Master의 결함 미발견 기록은 당시 검토 범위 결과이며 이번 QA가 이를 보완한다.
- 승인 근거: 기존 사용자 ASR-E001 구현 승인과 현재 Master의 검토·배정 역할 및 “이어서 진행”. 신규 기능이 아니라 승인된 CSV 입력 점검의 호환성 결함 수정이다. 원래 범위 내 재작업으로 READY, 담당 REPORT.
- 확인한 구현 SHA-256: input_contract.py 202A89113D71B08F49B51E808FFCB798696A6BC99C78E79706A89F280CEA6675, test_input_contract.py 22507DD052BF773F07F83D7FCA9EB5D8394F80065B0A257119731A8BFD3402FF. QA 보고와 현재 작업트리 기준으로 검토했다.
- 수정 범위: input_contract.py의 csv 필드 크기 처리와 관련 오류 안내, tests/test_input_contract.py의 경계 회귀, 완료보고서·TASKS·CHANGELOG. 기존 loader/UI/분석/렌더러는 수정하지 않는다.
- 기대 동작: 기존 loader가 읽을 수 있는 정상 CSV의 131,073자 셀을 원문 손실 없이 검사한다. 131,071/131,072/131,073자 및 더 긴 합성 필드를 검증하고, 한글·따옴표·셀 내부 개행·후속 행의 위치와 값이 보존되어야 한다. 임의 자르기나 행 건너뛰기 금지.
- 구현 주의: csv.field_size_limit는 프로세스 공용 설정이다. 변경 시 기존 값 복원, 예외 경로, 동시 호출 영향을 검토하고 전역 변경을 모듈 import의 부작용으로 남기지 않는다. 구문 오류와 크기/자원 제한을 혼동하지 않는다. 새 업무상 제한을 조용히 추가하지 않는다.
- 수락 기준: QA의 기존 실패 테스트를 수정/삭제하지 않고 통과, 해당 경계를 정식 tests에 추가, 기존 loader와 정상 긴 필드 호환, 원문/ID/날짜/행위치 계약 유지. import/compile/focused/canonical 및 명시 실파일 읽기·보호 파일 불변 검사, HIGH 완료보고서 갱신.
- 재검수: Report 수정 후 REVIEW 제출 → UI / QA가 보존된 독립 테스트와 새 경계/공용 설정 영향 검증 → Master DONE 판단. ASR-U001 자동 착수 금지.
- 이번 Master 작업: QA 보고서·TASKS·코드 해시 확인 및 문서 갱신만. QA 재현 실행/소스 수정/원격 게시를 수행한 것으로 주장하지 않는다.

### 독립 UI / QA 결과 — 2026-09-14 (REVIEW / Master 최종 검토 대기)

- 승인/담당: 사용자 직접 ASR-E001 독립 QA 요청 / UI·QA. 구현 담당과 별도 검증이며 이번 QA의 런타임 수정은 없음. ASR-U001/UI 연결 미착수.
- 검수 기준 HEAD: `a1a09d550c3c0ec696659cd06ec65e4fe427b60a`. 구현/신규 테스트는 미추적 working-tree 파일이므로 이 commit의 내용으로 간주하지 않는다. input_contract.py SHA-256 `202a89113d71b08f49b51e808ffcb798696a6bc99c78e79706a89f280cea6675`, test_input_contract.py SHA-256 `22507dd052bf773f07f83d7fca9eb5d8394f80065b0a257119731a8bfd3402ff`. 이번 commit/push 없음.
- Observed: 기존 계약+loader 25개 및 독립 synthetic 29개 실행: **53 passed, 1 failed (1.60s)**. 독립 테스트만은 28 passed/1 failed. canonical `pytest tests`: **160 passed (47.26s)**, 이번 QA 직접 실행 결과. Import 및 메모리 compile 통과(검증만이므로 pyc 생성 생략).
- 확인 범위: 윤년/월말/시간/날짜 허용·거부 경계, 날짜 분해 합계, legacy/alias-only/both/neither, 기존 loader 전후 DataFrame 동등성 및 필수 열 실패, 원문 ID 선행0/NULL, 다중 물리 행, 열 누락/행 너비 오류의 매핑 중단, 기능별 날짜·비공란 교집합, JSON 직렬화, 긴 한글 텍스트 경계. 기존 tests의 재정렬/추가/DYONE/중복 헤더/인코딩 검증도 통과.
- **QA-E001-01 / P2 / 재현 결함**: 정상 CSV의 단일 셀 131,073자에서 inspect_csv가 `DataLoadError: CSV 구문 오류: 물리 행 2`로 파일 전체를 거부한다. 내부 원인은 `_csv.Error: field larger than field limit (131072)` (input_contract.py:115~120). 131,071/131,072자는 통과. 18개 필수 열을 가진 동일 합성 CSV는 기존 load_input으로 1행 로드된다. 계약에 명시되지 않은 크기 제한과 잘못된 구문 오류 안내이며, 새 점검을 연결하면 기존에 읽을 수 있던 긴 기록을 거부할 수 있다. 현재 UI는 미연결이므로 실제 UI 회귀가 발생했다고 주장하지 않는다.
- 재현: `.venv/Scripts/python.exe tmp/asr_e001_independent_qa_20260914/repro_long_field.py`. 원본 보존 합성 CSV와 결과 `repro_result.json` 포함. 재현 스크립트는 synthetic 파일만 tmp에 기록한다. 수정 권고는 Master가 텍스트 크기 정책과 정확한 오류 구분을 확정한 후 별도 수정·재검증 배정하는 것. 이번에는 수정하지 않았다.
- focused 명령: `.venv/Scripts/python.exe -m pytest tests/test_input_contract.py tests/test_loader.py tmp/asr_e001_independent_qa_20260914/test_independent_contract.py --basetemp tmp/pytest_e001_independent_focused_20260914 -p no:cacheprovider -q`.
- canonical 명령: `.venv/Scripts/python.exe -m pytest tests --basetemp tmp/pytest_e001_independent_all_20260914 -p no:cacheprovider -q`. 로그: `tmp/asr_e001_independent_qa_20260914/focused.log`, `canonical.log`.
- 보호/범위: src/tests/data/reports/BAT 비캐시 99개 파일 크기·mtime·SHA-256 전후 동일, 해당 범위 파일 추가 없음. 원본 데이터 읽기 재검증은 이번 handoff의 synthetic-only 범위에 따라 미수행; Report/Master의 실파일 증거와 구분한다. 대표/기존 validation 출력·UI·소스·기존 tests 수정 및 보고서 재생성 없음. P0 유지.
- 기록: `MD/completion report/ASR_E001_independent_QA.md`, TASKS 해당 항목, CHANGELOG 해당 기록 및 새 tmp 증거만 작성. 기존 미커밋 변경 보존.
- 판단/다음: 독립 QA 증거 제출, 미해결 P2 1건 때문에 무조건 통과/DONE으로 판단하지 않는다. **Master에게 결함 처리 범위·수락 여부 최종 검토를 인계한다.** 후속 작업 자동 착수 없음.

### Master 검토 결과 — 2026-09-14

- 코드 검토: input_contract.py와 test_input_contract.py 전체, 기존 loader 연결 관계 및 실제 입력 검증 스크립트/결과 확인. 승인된 독립 점검 계층 범위 내에서 수정 요청할 결함은 발견하지 못했다.
- 직접 검증: 입력 계약+기존 loader focused 25 passed (0.62s), basetemp tmp/pytest_master_e001_review. Report의 초기 24 passed와 구분한다. 최종 테스트 파일 기준은 18+7=25개다.
- 직접 실제 입력 검증: 명시 Downloads CSV 3,220행, 구조 오류 없음, 날짜 유효 3,218/공란 2/오류 0, 기존 loader 행 수 일치 및 크기·수정시각·SHA-256 불변. 기존 진단 파일 덮어쓰기 없음.
- 전체 160 passed/import/compile/보호 파일 비교는 Report 제출 증거로 검토했다. Master가 전체 테스트를 다시 실행한 것은 아니다. 소스 변경이 없어 반복 실행은 생략했다.
- 판단: Master 기술 검토 통과. 작업 계약에 지정된 별도 UI / QA 검증은 아직 제출되지 않았으므로 상태는 REVIEW 유지. 코드가 현재 UI/기존 분석에 통합된 것으로 표현하지 않는다.
- QA 인계 범위: ASR-E001 검증만 수행. UI 연결이나 ASR-U001 구현을 시작하지 않는다. 코드 원본 보존, synthetic CSV 및 새 tmp 검증만 사용하고 재현 가능한 결함/결과를 기록한다.
- UI 계약 주의: usable_rows는 날짜 유효+필드 비공란 행 수로, 전체 접수/CS/클레임/완료 건수가 아니다. column_present는 구조 오류 시 매핑 가용 여부와 함께 읽어야 하며, original_headers와 structural_errors를 함께 표시해야 한다. 원본 행/제외·미입력은 보존한다.
- 다음: UI / QA의 별도 검증 결과를 받아 Master가 최종 DONE 판단. 이번 Master 검토는 문서만 갱신, 코드/데이터/보고서 변경 및 commit/push 없음.

- 승인: 2026-09-14 사용자 직접 ASR-E001 구현 승인. 아래 첫 구현 단위만 READY 승인 후 REPORT 소유로 IN_PROGRESS 착수. UI/상태 계산/후속 후보 구현 제외.
- 제출: REPORT 구현 및 자체 검증 후 REVIEW. 독립 UI / QA 검증과 Master 수락 대기.
- 변경: 새 src/as_report/input_contract.py, tests/test_input_contract.py, 이 기록 및 CHANGELOG. 기존 loader/CLI/UI/렌더러 수정 없음.
- 결과: inspect_csv의 파일/원문/매핑/행·ID·날짜/기능 가용성 계약. 승인 alias만 적용하고 중복 헤더·구조 오류에는 매핑 중단. 입력 근거 가용성을 실제 지표/후보 승인과 구분.
- 검증: import/compile 통과, 초기 focused 24 passed, 최종 canonical 160 passed (신규 18개 포함). 명시 Downloads CSV 실측 읽기·기존 loader 행 수 일치·날짜 분해·원본 불변 통과. 로컬 tmp/asr_e001_validation/result.json 참고.
- 보호 확인: 기존 src/data/reports 비캐시 73개 파일 크기·mtime·SHA-256 동일. 기존 tests 수정 없음. Raw/Master·대표/validation 재생성/수정 없음. P0 유지.
- 증거: MD/completion report/ASR_E001_input_contract_completion.md. 기존 Master CHANGELOG CRLF 공백 경고는 범위 밖으로 보존.
- Commit: 이번 작업 commit/push 없음. 다음: Master 계약/증거 검토. ASR-U001 자동 착수하지 않음.
- 범위 제안: 외부 헤더와 내부 필드 분리, 승인 매핑, 기능별 가용성 검사, 누락과 미입력 구분. 기존 계산 재사용.
- 제외: Raw/Master 수정·자동 병합·fuzzy matching·대표 재생성·전체 모듈 재작성.
- 수락 기준: 열 재정렬/추가/이름 변경/필수·선택 열 누락/중복 헤더/alias 우선순위/공란·잘못된 날짜에 대한 회귀 및 실제 파일 읽기 검증. 기존 HTML/Excel 회귀 없음.

### 첫 구현 단위 — 기존 경로와 분리한 입력 점검 결과

- 담당: Report 구현, UI / QA 검증, Master 증거 검토. 위험도 HIGH (loader/schema).
- 목표: CSV를 읽어 원본 헤더·행 식별·필드 매핑·분석별 가용성을 반환하는 입력 점검 계층을 추가한다. 업무 모집단/완료율/후보 자동 분류 정의에 의존하지 않는 범위다.
- 허용 범위: 새 입력 계약 모듈, 필요한 최소 loader 재사용/분리, 관련 tests. 기존 load_input 기본 필수 열 검증과 CLI/Streamlit 실행 경로는 유지한다. UI 연결·렌더러 전환은 이 작업에서 하지 않는다.
- 결과 계약: 파일 hash/encoding/원본 헤더/행 수, 원본 행 위치, 원본 ID의 누락·중복 상태, 승인 alias 적용 내역, 접수일 유효/오류 수, 기능별 available/unavailable 및 사유. 내부 기능명은 코드 수준 계약이며 사용자 화면 문구는 UI 작업에서 설계한다.
- 처리 규칙: 열 순서/추가 열 수용; 모르는 이름은 미매핑; 승인 alias만 적용; DYONE 열 자동 대체 금지; 원본 ID 텍스트 보존; 원본 헤더 및 공백 정리 후 중복 탐지; 날짜 누락과 오류 분리. 파일해시+행위치는 실행 내 추적키이며 실행 간 메모 병합키가 아니다.
- 완료 기준: 결과의 행 수와 제외/유효 분해 일치, 열 누락 시 관련 기능 사유 반환, 0으로 위장하지 않음. legacy/alias-only/both/neither 및 재정렬·추가·중복 헤더·ID 선행0·ID 누락/중복·날짜 오류를 테스트한다.
- 실제 입력 검증: 사용자가 제공한 Downloads CSV를 명시적으로 읽어 확인하며 data/raw로 복사하지 않는다. 원본 및 보호 파일 해시 불변 증거를 남긴다. 진단 결과는 tmp의 새 경로에만 저장한다.
- 필수 증거: import, 변경 Python compile, focused tests, canonical tests, 실제 파일 읽기 검사, 변경 파일 목록, HIGH 완료보고서. 구현 후 REVIEW로 넘긴다. 별도 UI/산출물 생성이 없는 이 단계에서 보고서 렌더링 완료를 주장하지 않는다.
- 제외: 상태 계산 통합, CS 포함 목록 확정, 후보 추출, PDF/Excel 생성/교체, Raw/Master 수정, 설치수 지표, 외부 API/전송, 메모 저장·병합.

## ASR-U001 — 입력 확인 및 검수 (UI / QA / CANDIDATE)

- 승인: 미기록. ASR-M004와 ASR-E001 계약에 의존한다.
- 범위 제안: 파일 선택 → 구조·coverage 확인 → 필요한 열 대응 확인 → 기간/필터 → 가능한 분석 → 보고서 검수·다운로드.
- 수락 기준: 미확인 매핑을 확정처럼 표시하지 않고, 불가능한 분석 사유·제외 행 수를 보여준다. 입력/조건 변경 시 과거 다운로드가 현재 결과로 남지 않는다. 실제 UI 및 산출물 검수 증거 기록.
- 제외: 분석 정의 임의 변경, 자동 원본 수정, 대표 출력 재생성.

## 작업 기록 양식 (필드)

새 ID / 우선순위 / 담당 / 상태 / 승인 근거 / 목표 / 허용·금지 범위 / 의존성 / 수락 기준 / 변경 파일 / 검증 명령·결과·증거 경로 / 데이터·산출물 영향 / 실제 Commit SHA / QA / Master 수락 / 다음 행동을 기록한다.

## 담당 작업 시작 지시문

AGENTS.md, ARCHITECTURE.md, TASKS.md를 읽고 내 담당의 승인 근거가 있는 최우선 READY 한 건을 수행한다. 없으면 착수하지 않는다. 변경 전 담당과 범위를 기록하고 검증 후 해당 task와 CHANGELOG를 갱신한다. Git 연결 시 실제 commit SHA를 기록하고 REVIEW로 넘긴다. 보호 입력·대표 출력 승인과 P0를 우회하지 않는다.
