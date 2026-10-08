> 역사 기록의 게시용 사본입니다. 당시 결과·미완료 사항을 보존하며 현재 승인이나 새 테스트 결과를 뜻하지 않습니다. 최신 상태는 [TASKS](../../TASKS.md)와 [인계 안내](../README.md)를 확인하십시오. 로컬 진단·handoff·실제 산출물 참조는 GitHub에 포함되지 않습니다.

# Completion Report

## Task Summary

Status: **Completed**

The active A/S Report project was reduced to the approved operating structure and its Windows entry points were consolidated into one launcher, `AS_Report.bat`. Historical outputs and documents were preserved in a verified external ZIP before they were removed from the active workspace. Because irreversible deletion was not permitted by the execution environment, cleanup targets were moved to an external quarantine instead of being permanently deleted.

## Modified Files

- `AGENTS.md`: current compact structure, single launcher, archive location, and current handoff policy
- `README.md`: concise installation and operation guide for the single launcher and PPT/PDF download flow
- `pyproject.toml`: runtime dependencies, `dev` pytest extra, package data for HTML/PPTX/PowerShell resources
- `src/as_report/report_presentation.py`: PPT template and builder paths now resolve from package resources
- `MD/CURRENT_STATUS.md`: post-cleanup operating baseline and validation evidence
- `reports/_index/report_history.csv`: reset to the approved header-only active history

## Created Files

- `AS_Report.bat`
- `src/as_report/resources/DY_PPT_Template_16x9.pptx`
- `MD/CURRENT_STATUS.md`
- `MD/completion report/PROJECT_DIET_single_launcher_completion.md`
- `MD/_chatgpt_handoff/PROJECT_DIET_single_launcher/MANIFEST.md`

## Archive And Cleanup

### Verified archive

- Path: `<LOCAL_ARCHIVE>\AS_report_history_20260902.zip`
- Size: 69,971,067 bytes
- SHA-256: `B71DA613CEE62D4D37427BD521AC2B1CC725B87BDF4D1B00CF6290519181596A`
- Manifest payload rows: 612
- Missing entries: 0
- Hash mismatches: 0

The archive contains historical reports, validation outputs, user outputs, completion documents, handoffs, the legacy 2025 ZIP, external refactor material, old BAT files, and the pre-cleanup README. Raw, Master, `.venv`, and regenerable caches were intentionally not duplicated into the ZIP.

### Recoverable quarantine

Irreversible removal was rejected by the execution safety layer. Cleanup targets were therefore moved to:

`<LOCAL_ARCHIVE>\quarantine_20260902`

This preserves recovery while removing the files from the active project. The quarantine includes old launchers, historical MD files, root handoffs, validation/user outputs, cache directories, old requirements, artifacts/assets, and the previous report history copy.

### Active size comparison

| Metric | Before | After | Change |
| --- | ---: | ---: | ---: |
| Files | 18,996 | 14,855 | -4,141 |
| Bytes | 1,670,513,549 | 454,185,516 | -1,216,328,033 |
| Approximate size | 1.556 GiB | 433.15 MiB | about 72.8% smaller |

The final size includes the latest GPT handoff copy, including the 8.15 MB PPT template. The remaining size is dominated by the retained `.venv`, as approved.

## Single Launcher

`AS_Report.bat` is the only BAT file at the project root and supports:

```text
AS_Report.bat --local
AS_Report.bat --host
AS_Report.bat --repair
AS_Report.bat --check
```

The interactive menu provides local mode, team host mode, environment repair, and exit. Host mode preserves `0.0.0.0:8501` and does not modify firewall rules. The existing Python CLI remains available through `python -m as_report.cli`.

Windows `cmd.exe` required the launcher to use CP949 with CRLF for reliable Korean menu output. The launcher still selects the Korean code page explicitly and presents readable Korean guidance.

## Protected Files Check

Raw, Master, and representative report hashes match the pre-cleanup baseline.

| Protected file | SHA-256 result |
| --- | --- |
| `data/raw/04. ES_ 이슈사항 보고_20260619.csv` | unchanged |
| `data/raw/04. ES_ 이슈사항 보고_20260630.csv` | unchanged |
| `data/master/00. ES_고장부품 분류_20260619.csv` | unchanged |
| `data/master/00. ES_고장부품 분류_20260630.csv` | unchanged |
| `data/master/08. ES_고객사 로보트 리스트 (Customer Robot List)_20260619.csv` | unchanged |
| `reports/as_report_2026.html` | unchanged |
| `reports/as_report_2026_summary.xlsx` | unchanged |

Representative HTML/Excel were not regenerated and remain blocked as an unverified pair.

## Test Results

- Import check: passed
- `py_compile` for `report_presentation.py` and `app.py`: passed
- `AS_Report.bat --check`: passed
- Focused presentation/output-context tests: **9 passed**
- Canonical `pytest tests`: **99 passed**
- Root pytest discovery: **99 passed**
- Source/test cache after validation: 0 `__pycache__` directories, 0 `.pyc` files

An editable install attempt with build isolation could not reach PyPI, and the offline no-build-isolation attempt found no local `setuptools.build_meta`. This did not affect the retained environment, imports, launcher check, or tests. Environment creation/repair still requires access to the configured Python package source when dependencies are absent.

## Runtime Validation

- Local Streamlit start: passed
- HTTP endpoint: `127.0.0.1:8517`, status 200
- PPT/PDF runtime generation in the interactive Windows session: passed
  - generated PPTX bytes: 7,442,813
  - generated PDF bytes: 206,308
- PPT/PDF generation used temporary files only; no report was automatically saved to the project
- Streamlit displays selected file names rather than full local paths
- Raw detail/remediation and standard-name review remain restricted to localhost

## Output/Report Impact

- Representative reports: unchanged
- Validation reports: archived externally; active directory recreated empty
- User outputs: archived externally; active directory recreated empty
- Active report history: header only
- Existing report generation logic and analysis logic: unchanged
- PPT template: moved from the removed root assets area into package resources

## Project Control Sheet

The following tabs in **AS Report Project Control** were updated from the completed evidence:

- `00_Control_Tower`: compact active size, single launcher, verified archive, representative-pair block retained
- `01_Task_History`: `PROJECT-DIET-20260902` recorded as Completed with test/runtime evidence
- `03_Risk_and_Rules`: `PROJECT-STRUCTURE-001` active rule added
- `04_Next_Actions`: `ARCHIVE-RETENTION-001` added as `Pending Team Check`; no automatic follow-up was started
- `05_Codex_Instructions`: compact project operation and archive hash recorded

Existing P0 Raw scope and representative-pair blocks were not closed or weakened.

## Known Limitations

- `.venv` remains about 425 MB by design for immediate operation.
- `--repair` may require network/package-index access if dependencies are not locally cached.
- PPT/PDF generation requires Microsoft PowerPoint and an interactive Windows user session.
- The representative HTML and Excel remain an unverified pair and must not be distributed as one current set.
- Final meeting-display font and print appearance still benefit from one team visual check.

## Remaining Risks

- Do not delete the external ZIP or quarantine until the team confirms the compact project has been used successfully.
- Do not treat historical files in the quarantine as active project inputs.
- Do not regenerate the representative pair without a separate approved task and approved Raw scope.

## Recommended Next Step

Run `AS_Report.bat --local`, generate and download one PPT/PDF pair, and complete the remaining team visual check. Keep representative paired regeneration blocked until separately approved.
