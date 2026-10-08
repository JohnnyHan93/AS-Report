# 연구소 인계 안내

기준일: 2026-10-08. A/S Report의 개발 자료만 공유하며 DY CS Agent는 별도 프로젝트다.

## 먼저 읽기

- [실행·설치](../README.md), [구조](../ARCHITECTURE.md), [현재 작업](../TASKS.md), [공통 규칙](../AGENTS.md)
- [CS 운영·애프터마켓 상세 설계](design/ASR_M004_CS_aftermarket_report_design.md): 내부 PDF + 검토 Excel 목표, 상태 정의, 후보의 근거·제외 조건. 전체 기능 구현 완료를 뜻하지 않는다.
- [입력 계약 구현·재작업 기록](history/ASR_E001_input_contract_completion.md), [초기 독립 QA](history/ASR_E001_independent_QA.md)

## 현재 사용과 개발 목표

기존 Streamlit/CLI, HTML·Excel, 발표용 PPT·PDF, V2 Word·PPTX 경로는 유지한다. ASR-E001의 `inspect_csv(explicit_path)`는 원문과 행 위치를 보존하는 독립 입력 점검 API이며 기존 UI/분석 경로에 연결되지 않았다. 긴 셀 파싱은 별도 Python 프로세스에서 수행하여 부모 프로세스의 CSV 설정을 변경하지 않는다.

완료 기준은 처리완료만 완료, 전달 완료 별도, 공란 미입력으로 설계상 확정됐다. 기존 계산의 정의 차이는 아직 남아 있다. 새 CS 모집단·완료율 분모·후보 규칙은 추가 결정이 필요하다. 후보는 판매·원인·기술적 필요 확정이 아니다.

ASR-E001은 REVIEW, UI 연결은 CANDIDATE다. 이번 게시 검증은 연구소 인계 재현성 확인이며 독립 QA 최종 수락이나 운영 배포 승인을 대신하지 않는다. Word 시각 검수와 현재 PPT/PDF 운영 검증은 별도다. 기존 대표 HTML/Excel은 같은 실행 pair가 검증되지 않아 공유 대상에서 제외한다.

## 데이터 없이 시작하기

Windows에서 저장소를 clone하고 Python 3.10 이상으로 가상환경을 만든 뒤 `python -m pip install -e ".[dev]"`를 실행한다. 현재 PC의 가상환경·설치 프로그램·모델이나 다른 앱은 저장소에 포함하지 않는다. 발표용 PPT는 PowerPoint 로그인 세션, PDF는 Edge/Chrome이 필요하다. V2 Word/PPTX는 python-docx/python-pptx로 생성한다.

`AS_Report.bat --local`로 시작하고 승인된 CSV를 명시적으로 선택하거나 업로드한다. Raw를 파일명 최신순으로 확정하지 않는다. 표준명 CSV는 기능 최초 사용 시 `config/standard_names`에 헤더만 생성되므로 회사 매핑 자료는 저장소 없이도 초기화 가능하다. 개인 `active_input_set.json`은 전달하지 않는다.

회귀 테스트는 합성 입력을 자체 생성한다. 고객 자료 없이 `python -m pytest tests --basetemp tmp/pytest_research -p no:cacheprovider`로 실행한다. 추가 QA 사본은 다음과 같이 실행한다.

```powershell
python -m pytest tests/test_input_contract.py tests/test_loader.py docs/qa/test_independent_contract.py --basetemp tmp/pytest_research_qa -p no:cacheprovider
```

추가 QA 사본의 기대값은 원본과 동일하다. 과거 53 passed / 1 failed는 수정 전 기록이며 수정 후 61 passed는 Report가 남긴 기록이다. 이번 게시 검증은 아래 별도 완료보고서에서 확인한다.

## 게시·제외 정책

코드·테스트·실행 스크립트·회사 기본 템플릿·설계·현재 작업 문서·과거 완료기록의 검토된 사본만 게시한다. 로컬 완료보고서 원본은 보존하고 실제 업무 집계 수치와 개인 경로는 사본에서 제거했다.

Raw/Master, 고객 CSV, 실제 보고서·payload·QC 결과, 사용자별 출력, 운영 매핑/config, 가상환경, 임시 진단·로그·캐시, 외부 archive/백업, 중복 handoff 소스는 제외한다. 원본 자료와 아카이브는 수정·이동·삭제하지 않는다. 과거 문서 속 로컬 파일 참조는 연구소에서 열 수 있는 링크가 아니다.

## 과거 기록 목록

- [최초 비공개 저장소 게시 검증](../MD/completion%20report/MASTER_github_setup_completion.md)
- [ASR_E001_independent_QA](history/ASR_E001_independent_QA.md)
- [ASR_E001_input_contract_completion](history/ASR_E001_input_contract_completion.md)
- [MASTER_memory_setup_completion](history/MASTER_memory_setup_completion.md)
- [PPT_background_generation_fix_completion](history/PPT_background_generation_fix_completion.md)
- [PPT_pdf_compact_layout_completion](history/PPT_pdf_compact_layout_completion.md)
- [PPT_PDF_final_composition_completion](history/PPT_PDF_final_composition_completion.md)
- [PPT_PDF_html_based_pdf_generation_completion](history/PPT_PDF_html_based_pdf_generation_completion.md)
- [PROJECT_DIET_single_launcher_completion](history/PROJECT_DIET_single_launcher_completion.md)
- [REPORT_TOOL_V2_completion](history/REPORT_TOOL_V2_completion.md)
- [AGENTS_pre_master](history/AGENTS_pre_master.md)

## 이번 게시 검증

[GitHub 업데이트 검증 기록](publication_20261008.md)

### Historical handoff inventories

- [PPT_background_generation_fix_manifest](history/PPT_background_generation_fix_manifest.md)
- [PPT_pdf_compact_layout_manifest](history/PPT_pdf_compact_layout_manifest.md)
- [PPT_PDF_final_composition_manifest](history/PPT_PDF_final_composition_manifest.md)
- [PPT_PDF_html_based_pdf_generation_manifest](history/PPT_PDF_html_based_pdf_generation_manifest.md)
- [PROJECT_DIET_single_launcher_manifest](history/PROJECT_DIET_single_launcher_manifest.md)
