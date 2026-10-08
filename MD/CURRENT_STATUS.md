## 2026-10-08 연구소 인계 현황

이번 변경은 전체 개발 자료의 GitHub 게시 준비와 재현성 검증이다. [인계 안내](../docs/README.md)와 [게시 검증](../docs/publication_20261008.md)을 현재 기준으로 사용한다. 아래 9월 실행 기록은 과거 증거이며 이번 실행 결과가 아니다.

ASR-E001은 REVIEW로 유지하며 UI 연결은 미구현이다. CS/애프터마켓 상세 설계와 기존 분석 구현을 구분한다. 현재 PDF는 Edge/Chrome 경로이고 PowerPoint가 필요한 경로는 기존 발표용 PPT다. 대표 pair 차단·Word 시각 검수 미완료는 유지한다.

# A/S Report Current Status

Updated: 2026-09-02

## Operating Baseline

- Entry point: `AS_Report.bat`
- Default UI: Streamlit
- Report delivery: DY 16:9 PPT/PDF download only
- Normal analysis input: one explicitly selected `04. ES_ 이슈사항 보고` CSV
- Report period column: `접수일`
- Raw/Master files: protected and unchanged
- Customer robot Master and failure-part Master linkage: disabled

## Streamlit Policy

- Local mode: summary, PPT/PDF download, Raw detail/remediation and standard-name review
- Team host mode: summary and PPT/PDF download
- Full local paths are not displayed.
- PPT/PDF work files are temporary and are not automatically saved under `reports`.
- Microsoft PowerPoint on an interactive Windows session is required for PPT/PDF generation.

## Representative Files

```text
reports/as_report_2026.html
reports/as_report_2026_summary.xlsx
```

These files are retained unchanged for compatibility. They are not verified as a same-run pair and must not be shared as one representative set or regenerated without a separately approved task.

## Project Diet

- Historical reports, validation outputs, documents and handoffs were preserved before cleanup.
- Archive: `C:\Users\johnny\AS report_archive\AS_report_history_20260902.zip`
- Archive SHA-256: `B71DA613CEE62D4D37427BD521AC2B1CC725B87BDF4D1B00CF6290519181596A`
- Archive manifest rows verified: 612
- Missing archive entries: 0
- Hash mismatches: 0

## Current Checks

- `AS_Report.bat --check`: passed
- Import and changed-file compile checks: passed
- `pytest tests`: 99 passed
- Root pytest collection: 99 passed
- Local Streamlit HTTP check: 200
- PPT/PDF download runtime check: passed in the interactive Windows session
  - PPTX: 7,442,813 bytes
  - PDF: 206,308 bytes
- Raw/Master and representative SHA-256 comparison: unchanged
- Final active size including the latest handoff: 454,185,516 bytes (433.15 MiB)
- Final active file count including the latest handoff: 14,855
- Active report history: reset to a header-only file; previous history remains in the archive and external quarantine

## Active Structure

The project root now contains only the operating allowlist:

```text
.venv
config
data
MD
reports
src
tests
AGENTS.md
AS_Report.bat
pyproject.toml
README.md
```

The only root BAT file is `AS_Report.bat`. Historical files removed from the active project are preserved in the verified ZIP and, where deletion was not permitted, in:

```text
C:\Users\johnny\AS report_archive\quarantine_20260902
```

## Remaining Team Check

- Download the PPT and PDF once from Streamlit.
- Confirm font rendering, page order, charts and tables on the actual meeting display.
- Keep representative paired regeneration blocked until a separate approved task clears the input and pair gates.

Historical details are available in the external archive and the Google Drive **AS Report Project Control** spreadsheet.

## Master update — 2026-09-14

위 2026-09-02 기록은 당시 스냅샷이다. 신규 작업/승인의 기준은 `TASKS.md`, 현재 코드 구조는 `ARCHITECTURE.md`이다.

- V2 Word/PPTX가 추가되어 있다. 기존 V2 완료보고서 상태는 Implemented / Runtime Check Pending이며 Word 시각 검수가 남아 있다.
- 현재 PDF는 report_pdf.py와 브라우저 인쇄 경로를 사용한다. PowerPoint는 발표용 PPT 생성에 필요하다. 과거 PDF/99 tests 기록은 현재 검증을 대체하지 않는다.
- 대표 HTML/Excel pair 미확인 제한은 유지한다.
- 로컬 폴더는 Git 저장소가 아니므로 GitHub 공용 기억 게시와 커밋은 아직 없다.
- 기존 외부 관리표의 현 상태는 이번 작업에서 조회/동기화하지 않았다.
- 실제 루트에는 tmp와 추가 문서 등이 있으므로 위 allowlist는 현재 전체 파일 목록이 아니다. 정리/이동은 수행하지 않았다.


## GitHub setup — 2026-09-14

사용자 승인으로 전용 private 저장소 JohnnyHan93/AS-Report를 생성하고 현재 폴더를 Git 초기화했다. 위 Git 미구축 설명은 이전 시점 기록이다. 최초 게시 및 검증 결과는 TASKS.md ASR-M002와 MASTER_github_setup_completion.md를 따른다. 업무 데이터/설정/산출물은 Git에 게시하지 않는다. 기존 대표 pair P0와 Word 시각 검수 제한은 유지한다.
