> 역사 기록의 게시용 사본입니다. 당시 결과·미완료 사항을 보존하며 현재 승인이나 새 테스트 결과를 뜻하지 않습니다. 최신 상태는 [TASKS](../../TASKS.md)와 [인계 안내](../README.md)를 확인하십시오. 로컬 진단·handoff·실제 산출물 참조는 GitHub에 포함되지 않습니다.

# Completion Report

## Task Summary

파일 만들기 실행 중 PowerPoint 창이 표시되는 원인을 확인하고, PowerPoint가 허용하는 문서 창 비표시 방식으로 수정했다.

상태: `Completed`

## Root Cause

초기 코드의 `$ppt.Visible = -1`은 PowerPoint 자동 생성 창을 화면에 표시했다. 이를 `$ppt.Visible = 0`으로 바꾸는 방식은 PowerPoint가 애플리케이션 창 숨김을 허용하지 않아 `Invalid request. Hiding the application window is not allowed.` 오류를 발생시켰다.

최종 해결은 `Application.Visible`을 설정하지 않고, `Presentations.Open(..., WithWindow=$false)`로 문서 창을 만들지 않는 방식이다.

## Changes

- `$ppt.Visible` 설정을 제거
- `Presentations.Open(..., WithWindow=$false)` 유지
- `$ppt.DisplayAlerts = 1`로 PowerPoint의 `ppAlertsNone` 적용
- PowerShell을 `-WindowStyle Hidden`, `CREATE_NO_WINDOW`로 실행
- PowerShell 출력 형식을 Text/UTF-8로 지정해 CLIXML 오류 메시지 노출 방지
- PowerShell progress 출력을 숨김 처리
- HTML PDF 변환은 독립 임시 브라우저 프로필을 사용
- Edge의 비동기 PDF 기록을 최대 30초 확인하고 임시 캐시 잠금은 안전하게 정리
- 기존 템플릿 열기, 슬라이드 생성, 저장, 종료 흐름은 변경하지 않음
- PPT와 HTML 기반 PDF 생성 분리 흐름은 유지
- 대표 HTML/Excel, Raw/master, validation reports는 변경하지 않음

## Modified Files

- `src\as_report\presentation\build_report.ps1`
- `src\as_report\report_presentation.py`
- `tests\test_report_presentation.py`

## Validation

- PowerShell parser: Pass
- Python compile: Pass
- Focused pytest: `18 passed`
- Full `pytest tests`: `108 passed`
- `$ppt.Visible` 설정 제거 확인: Pass
- `WithWindow=false` 확인: Pass
- 숨김 PowerShell 실행 옵션 확인: Pass
- 실제 PowerPoint 템플릿 열기: `opened_without_window=True`
- 전체 PPT/PDF 임시 생성: Pass
  - PPTX: `7,458,126 bytes`
  - PDF: `288,341 bytes`

실제 PowerPoint COM으로 회사 템플릿을 열고 문서 창 수가 0인지 확인한 뒤 정상 종료했다. 테스트 데이터로 Streamlit과 동일한 전체 PPT/PDF 생성 함수를 실행해 두 다운로드 파일의 바이트 반환까지 확인했다.

## Protected Files Check

- `data\raw` 수정/이동/삭제: No
- `data\master` 수정/이동/삭제: No
- 대표 `reports\as_report_2026.html`: No change
- 대표 `reports\as_report_2026_summary.xlsx`: No change
- validation reports: No change
- reports cleanup/archive: No
- 계산·분석·HTML·Excel 구조 변경: No

## Handoff

전달 폴더:

`MD\_chatgpt_handoff\PPT_background_generation_fix\`

수정 파일, 테스트 파일, 완료보고서, MANIFEST를 복사했다. Raw/master, `.venv`, archive, 대표 reports, validation reports는 복사하지 않았다.

## Recommended Next Step

Streamlit에서 실제 분석 결과로 PPT·PDF 다운로드를 실행해 최종 문구와 시각 배치를 확인한다.
