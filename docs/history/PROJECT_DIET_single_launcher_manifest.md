> Historical handoff inventory only. Referenced copies remain local; this is not current operating approval.

# PROJECT_DIET_single_launcher Handoff

## Task Name

Project Diet and Single Launcher Consolidation

## Result

Completed. The active project uses one root launcher and the approved compact structure. Historical material is preserved externally.

## Archive

- Original archive: `<LOCAL_ARCHIVE>\AS_report_history_20260902.zip`
- Size: 69,971,067 bytes
- SHA-256: `B71DA613CEE62D4D37427BD521AC2B1CC725B87BDF4D1B00CF6290519181596A`
- Verified manifest rows: 612
- Missing entries: 0
- Hash mismatches: 0
- Recoverable cleanup quarantine: `<LOCAL_ARCHIVE>\quarantine_20260902`

## Handoff Copied Files

| Original path | Handoff copy | Purpose |
| --- | --- | --- |
| `AS_Report.bat` | `AS_Report.bat` | Single Windows launcher |
| `AGENTS.md` | `AGENTS.md` | Current repository operating rules |
| `README.md` | `README.md` | Current user operation guide |
| `pyproject.toml` | `pyproject.toml` | Package, dependency, test, and package-data configuration |
| `src/as_report/report_presentation.py` | `report_presentation.py` | PPT/PDF resource resolution |
| `src/as_report/resources/DY_PPT_Template_16x9.pptx` | `DY_PPT_Template_16x9.pptx` | Packaged presentation template |
| `MD/CURRENT_STATUS.md` | `CURRENT_STATUS.md` | Current operating baseline |
| `MD/completion report/PROJECT_DIET_single_launcher_completion.md` | `PROJECT_DIET_single_launcher_completion.md` | Completion evidence |
| this manifest | `MANIFEST.md` | Handoff inventory |

## Test Results

- Import check: passed
- Changed Python compile: passed
- `AS_Report.bat --check`: passed
- Focused tests: 9 passed
- `pytest tests`: 99 passed
- Root pytest: 99 passed
- Streamlit localhost HTTP: 200
- Temporary PPT/PDF generation: passed (7,442,813-byte PPTX; 206,308-byte PDF)

## Static Checks

- Root BAT count: 1
- Root launcher: `AS_Report.bat`
- Root allowlist: matched
- Active `reports/users`: empty
- Active `reports/validation`: empty
- Active report history: header only
- Source/test `__pycache__`: none
- Source/test `.pyc`: none

## Safety Statements

- Raw modified/moved/deleted: No
- Master modified/moved/deleted: No
- Representative HTML/Excel regenerated or edited: No
- Analysis/report calculation logic changed: No
- Validation reports regenerated: No
- Firewall changed: No
- Existing Python CLI removed: No
- External archive verified before active cleanup: Yes
- Cleanup was recoverable: Yes; files were moved to external quarantine instead of irreversible deletion

## Known Limitations

- `.venv` is retained for immediate operation and remains the main active size contributor.
- Environment repair may require package-index access.
- PowerPoint and an interactive Windows session are required for PPT/PDF creation.
- Representative HTML/Excel remain blocked as an unverified pair.

## Next Recommended Step

Complete one team visual check using a PPT/PDF pair downloaded from local Streamlit. Do not start representative paired regeneration without separate approval.
