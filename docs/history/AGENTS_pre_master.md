> 과거 규칙의 참고 사본이며 현재 작업 지침이 아닙니다. 현재 규칙은 루트 AGENTS.md를 따릅니다.

# AGENTS.md

## 1. Purpose

This file defines the repository-level operating rules for Codex and other implementation agents working on the A/S report automation project.

Codex must read this file before inspecting, editing, generating, moving, deleting, or regenerating any project file.

The project is already in internal use. Work must therefore prioritize:

1. data integrity
2. report reproducibility
3. output consistency
4. user-visible interpretation safety
5. minimal, reviewable changes
6. evidence-based completion

Current operational status belongs in `MD\CURRENT_STATUS.md` and the Google Drive project control sheet. Historical task documents and report artifacts are stored in the verified external archive, not accumulated in the active project folder.

---

## 2. Project Identity and Root

Project name:

```text
AS Report / A/S 분석 리포트 자동 생성 도구
```

Project root:

```text
<PROJECT_ROOT>
```

The current folder is the project root. Do not create another nested project folder such as:

```text
as_report_tool
AS report\AS report
```

Primary purpose:

- analyze accumulated ES issue report data
- generate period-based A/S analysis reports
- support CLI, BAT, and Streamlit operation
- produce HTML reports and Excel verification workbooks
- provide data-quality, matching, repeat-candidate, and review-candidate outputs without inventing causes or responsibility

Official report-period column:

```text
접수일
```

Do not use `등록일` or `수정일` as the report-period basis unless an explicitly approved task defines a separate non-reporting use.

---

## 3. Source-of-Truth Priority

When instructions conflict, use the following priority:

1. the user's current explicit instruction
2. the approved task instruction for the current work
3. `AS Report Project Control` rows whose status is `Ready for Codex`
4. this `AGENTS.md`
5. `README.md`
6. current completion reports
7. historical planning notes

Google Drive control sheet:

```text
AS Report Project Control
```

Execution rules:

- Execute only one approved `Ready for Codex` task at a time.
- Do not automatically start tasks marked `Candidate`, `Backlog`, `Pending Team Check`, `Decision Required`, `Blocked`, or `Update Required`.
- Do not auto-chain into the next task after completion.
- If a P0 gate is open, do not bypass it through a lower-priority task.
- If source documents disagree, stop and report the exact conflict.

---

## 4. Protected Paths and Non-Negotiable Rules

Protected read-only inputs:

```text
data\raw
data\master
```

Without explicit user approval, do not:

- modify
- overwrite
- normalize in place
- move
- rename
- delete
- merge
- archive
- replace

any file under those paths.

Additional protected items:

```text
.venv
reports\users
AS_Report.bat
existing representative reports
existing validation reports
```

Do not perform cleanup, archive movement, deletion, or folder reorganization unless the task explicitly authorizes it.

Verified historical archive:

```text
<LOCAL_ARCHIVE>\AS_report_history_20260902.zip
```

Do not overwrite or delete this archive during ordinary project work.

Do not delete unclear files. Leave them in place and report them.

Do not automatically modify firewall rules.

Do not add:

- a new application framework
- a database
- AI API calls
- a crawler
- fuzzy matching
- automatic external synchronization
- always-on server configuration
- DaouOffice Works integration

unless explicitly approved in a dedicated task.

---

## 5. Current System Baseline

The project already includes:

- CLI report generation
- BAT launchers
- Streamlit operation screen
- HTML report generation
- Excel summary generation
- comparison analysis
- repeat issue candidates
- Raw data-quality validation
- standard-name mapping preview
- Master-data matching preview
- user-separated output support
- quality-feedback review candidates
- schema compatibility for `고장유형` to internal `고장원인`

Preserve verified safe behavior.

Do not preserve a behavior that has been confirmed unsafe when the approved task explicitly addresses that behavior.

Examples of confirmed unsafe behavior that may be corrected only through an approved task:

- selecting a Raw file solely because its filename date is newest
- showing an old HTML file as if it were the current run result
- allowing representative and user outputs to overwrite each other
- treating mismatched HTML and Excel files as one representative pair
- allowing handoff copies to break root pytest collection

---

## 6. P0 Stop Conditions

Stop and report `Blocked` instead of completing when any of the following applies.

### 6.1 Representative pair mismatch

Representative HTML and representative Excel are a paired artifact.

Do not share them as one representative set unless the following are identical or traceably linked:

```text
run_id
Raw file identity
Raw row count
Raw 접수일 range
analysis period
filters
Master input identity
analysis version
creation event
```

If HTML and Excel were generated from different inputs or at different approved runs:

- mark the pair invalid
- do not regenerate only one side
- do not share them as one set
- do not update representative history as if the pair were valid
- wait for Raw scope and regeneration approval

### 6.2 Raw coverage uncertainty

A newer export must not be treated as a cumulative baseline merely because its filename is newer.

If a new Raw has a shorter date range or substantially fewer rows than the approved baseline:

- do not replace the baseline
- do not merge automatically
- do not regenerate representative outputs
- record row count, date range, unique `*ID` count, and schema difference
- wait for user approval of full export or merge strategy

### 6.3 Protected input change

If a task would require modifying `data\raw` or `data\master` without explicit approval, stop.

### 6.4 Unreproducible representative output

If a representative report references an input file that is no longer available or identifiable, do not claim reproducibility.

### 6.5 Failed required validation

If required focused tests or required runtime checks fail, report blocked or partial completion.

---

## 7. Raw File Selection and Coverage Rules

Primary Raw pattern:

```text
data\raw\04. ES_ 이슈사항 보고_*.csv
```

Never use a rule equivalent to:

```text
Use the latest filename.
```

Raw selection must consider:

```text
file name
file size
file modified time
row count
column count
unique *ID count
minimum 접수일
maximum 접수일
schema
approved baseline status
user selection
```

Default Raw behavior:

1. Prefer an explicitly approved baseline or user-selected file.
2. Do not automatically promote a shorter rolling export to cumulative baseline.
3. If the correct default is uncertain, require user selection.
4. Refresh the available-file list during Streamlit operation when practical; do not rely only on import-time discovery.
5. Never copy a selected upload into `data\raw` without approval.

Raw coverage metadata should be shown or recorded before representative generation.

---

## 8. Raw Provenance and Run Metadata

Every report-generation run should record, where supported:

```text
run_id
output owner
Raw filename
Raw path or safe identifier
Raw file size
Raw modified time
Raw row count
Raw unique *ID count
Raw minimum 접수일
Raw maximum 접수일
Raw schema or column list
Master filename(s)
analysis period
filters
analysis version
generated HTML path
generated Excel path
creation timestamp
```

A file hash may be added if performance and implementation scope allow it.

The metadata must be sufficient to answer:

```text
Which data produced this file?
Can the same run be reproduced?
Do the HTML and Excel belong to the same run?
```

`reports\_index\report_history.csv` must not record only one side of a representative pair when both HTML and Excel are expected.

---

## 9. Raw Merge Rules

Raw merging is a separate approval-required task.

Do not implement or execute merging as part of:

- schema alias fixes
- UI fixes
- report-layout changes
- test configuration fixes
- documentation synchronization

When a merge is approved, `*ID` is the primary candidate key unless the task specifies otherwise.

Before implementation, define:

```text
same-ID precedence
changed-record handling
new-record handling
missing-record handling
deleted-record handling
schema difference handling
```

Required merge validation:

```text
input row counts
input unique ID counts
overlap ID count
output row count
output unique ID count
duplicate ID count
minimum/maximum 접수일
yearly 접수 counts
changed-field summary
```

Do not silently deduplicate and call the result complete.

---

## 10. Canonical Schema and Alias Rules

External Raw column names and internal canonical column names are different concepts.

External schema:

```text
columns exported by the groupware form
```

Canonical schema:

```text
columns used internally by analysis and report code
```

Current approved alias:

```text
고장유형 -> 고장원인
```

Alias precedence:

1. If canonical `고장원인` exists, use it.
2. If canonical is absent and alias `고장유형` exists, create the canonical column in the in-memory DataFrame before required-column validation.
3. If both exist, never overwrite populated canonical values.
4. Preserve the external alias column unless the approved task says otherwise.
5. If neither exists, keep the required-column error.
6. Never modify the Raw file bytes to apply an alias.

Adding any new alias requires:

- evidence from an actual header
- explicit mapping definition
- backward-compatibility test
- alias-only test
- both-columns test
- neither-column test

---

## 11. Missing Data and Inference Rules

If a value is missing, display or classify it as:

```text
미입력
```

or another explicitly defined missing-state label.

Do not infer missing values as confirmed values.

Automatic guesses must be labeled as one of:

```text
preview
recommendation
candidate
confidence-based result
review required
```

Never write inferred values back into Raw or Master automatically.

---

## 12. Report Text and Interpretation Safety

Do not invent or automatically assert:

- root cause
- responsibility
- fault attribution
- customer impact
- cost saving
- improvement effect
- recurrence reason
- technical mechanism not present in input
- field cases not present in input

Do not turn a repeated issue candidate into a confirmed root cause.

Do not turn a period increase or decrease into a cause statement.

Preferred wording:

```text
전년 동기 대비 접수 건수는 12건 증가했습니다.
동일 조건으로 2건 이상 접수된 반복 검토 후보가 5개 확인되었습니다.
라인 중단 시간 입력 건 기준 총 중단 시간은 320분입니다.
해당 항목은 입력 데이터 기준 검토 후보입니다.
```

Avoid wording such as:

```text
설비 노후화로 인해 증가했습니다.
관리 미흡으로 반복 발생했습니다.
해당 부품이 원인입니다.
고객 영향이 발생했습니다.
개선 시 비용 절감이 가능합니다.
```

---

## 13. Terminology and Metric Definitions

Do not use `고장률` unless an approved task defines the denominator, numerator, unit, exclusions, and display method.

Preferred terms:

```text
AS 접수율
고장성 AS 접수율
대당 AS 접수건수
대당 고장성 AS 접수건수
반복 검토 후보
매칭 미리보기
추천값
검토 필요
미입력
```

### 13.1 Per-robot-model metric

Unless another approved definition exists:

```text
대당 AS 접수건수
= Master에 매칭된 해당 로봇 기종 AS 접수건수 / 해당 로봇 기종 설치대수
```

This is not automatically a percentage. Do not append `%` unless the calculation is actually a percentage.

The user-visible result should include, where practical:

```text
전체 AS 접수건수
로봇 기종 매칭 건수
미매칭 건수
매칭률
설치대수
대당 AS 접수건수
```

### 13.2 Controller-based metric

Controller-based installation metrics must not be shown to users when controller matching coverage is materially lower than robot-model matching coverage or when robot-to-controller mapping is incomplete.

Current default display policy:

```text
Show robot-model-based installation metrics.
Hide controller-based installation metrics from HTML, Excel, and Streamlit unless a dedicated task validates matching coverage and re-approves display.
```

Internal controller calculations may remain if removing them would create unnecessary risk, but they must not be presented as reliable user-facing metrics.

---

## 14. Repeat Issue Candidate Rules

Repeat issue candidates are reference candidates only.

Default minimum count:

```text
2 or more records with the same approved grouping condition
```

Recommended grouping keys:

```text
고객사 + 대분류 + 중분류
고객사 + 소분류 (고장부품)
고객사 + 로보트 기종 + 소분류 (고장부품)
BOOTH + LINE + 공정 + 대분류
로보트 기종 + 소분류 (고장부품)
```

Expected columns:

```text
반복 기준
조건값
접수 건수
라인 중단 총 시간
최초 접수일
최근 접수일
관련 ID 목록
```

Display rules:

- remove repeated key labels from the displayed condition value
- exclude a candidate if all grouping values are missing
- mark mostly-missing conditions as low-confidence or data-quality review items
- never label a candidate as confirmed cause

---

## 15. Raw Data Quality Rules

Raw quality validation must distinguish:

```text
보완 필요
정상 공란
조건부 제외
해당없음
다중대상
미확인
오류값
```

Conditional fields:

```text
유/무상
제조사
```

These fields are required only when the approved business rule requires them, including:

```text
업무유형 = A/S대응(부품수리/클레임처리)
```

Otherwise, missing values may be classified as conditional exclusion rather than an error.

Manual-review outputs should support groupware searching without relying only on ID.

Recommended search keys:

```text
접수일 + 접수내용 요약 키워드
접수일 + 고객사 + 업무유형
접수일 + 접수사원 + 접수내용 일부 키워드
접수일 범위 + 고객사 + 로봇/설비 키워드
```

---

## 16. Standard Name Mapping Rules

Standard-name mapping must not overwrite original Raw columns automatically.

Mapping files under:

```text
config\standard_names
```

are user-maintained reference files.

Unknown names must be exported for review before confirmed standardization.

Allowed:

```text
preview
candidate mapping
confidence display
review list
```

Not allowed without approval:

```text
confirmed replacement
Raw write-back
Master write-back
fuzzy matching
```

---

## 17. Master Data Analysis Rules

Official Master inputs are under:

```text
data\master
```

Do not modify Master files automatically.

Customer robot Master may be used for:

```text
고객사별 설치대수
로봇 기종별 대당 AS 접수건수
로봇 기종 매칭 미리보기
미매칭 AS 목록
```

Controller-based metrics are subject to the coverage rule in Section 13.2.

Failure-part Master may be used for:

```text
대분류/중분류/소분류 유효성 검증
고장성 AS 판정
부품분류별 접수 추이
분류 누락/불일치 후보
```

Matching is preview/reference unless explicitly confirmed.

Do not treat a matching result as a confirmed source value.

---

## 18. Output Classes and Paths

Output types must remain separated.

### 18.1 Representative outputs

```text
reports\as_report_2026.html
reports\as_report_2026_summary.xlsx
```

Representative outputs may be updated only by an explicitly approved representative-regeneration task after all P0 gates are cleared.

### 18.2 User/run outputs

Preferred structure:

```text
reports\users\<sanitized_owner>\<run_id>\
```

Recommended contents:

```text
report.html
report_summary.xlsx
run_metadata.json
```

General Streamlit operation must not silently overwrite representative outputs.

### 18.3 Validation outputs

```text
reports\validation\
```

Validation files are not representative files.

### 18.4 Index and history

```text
reports\_index\report_history.csv
```

History should identify both HTML and Excel when both are generated.

---

## 19. HTML / PDF / Print Rules

HTML is the primary presentation and meeting report.

PDF generation is performed through browser print unless automatic export is explicitly approved.

Keep HTML print-friendly.

Do not add interaction that breaks printing.

When HTML generation or layout changes:

- create validation HTML only
- inspect section presence
- inspect long-text behavior
- inspect chart rendering
- inspect browser print/PDF preview
- do not regenerate representative HTML unless separately approved

---

## 20. Excel Rules

Excel is used for:

- detailed verification
- table copy/paste
- calculation backup
- review candidates
- supplemental analysis

Do not rename or remove existing sheets without approval.

Known added sheets include:

```text
14_Comparison
15_Repeat_Issues
16_Raw_Quality_Check
17_Completion_Status
18_Claim_Manufacturer
19_Controller_Rate
20_Quality_Feedback
```

The existence of an internal sheet does not automatically approve its user-facing interpretation.

If controller metrics are hidden by policy, an existing controller sheet may remain for compatibility only if clearly excluded from user-facing distribution and documented in the approved task.

When Excel structure changes:

- create validation Excel only
- open the workbook programmatically
- verify required sheets and headers
- verify formulas/values as applicable
- do not regenerate representative Excel unless separately approved

---

## 21. Streamlit Rules

Streamlit is the operation and preview screen. It is not itself the final report document.

### 21.1 Current-run preview integrity

HTML preview must be tied to the current session or current run.

Do not show an existing HTML merely because a period/filter-derived path exists.

Before showing a file as the current preview, verify available metadata such as:

```text
Raw identity
period
filters
run_id
creation event
```

If the current run has no matching HTML, show a clear message such as:

```text
현재 조건으로 생성된 HTML 리포트가 없습니다. 먼저 HTML 리포트를 생성하십시오.
```

### 21.2 Raw list refresh

Do not rely only on a module-import-time Raw file list.

When a user refreshes or re-runs the Streamlit app, newly added files should be discoverable where practical.

### 21.3 Shared host operation

When teammates access by URL:

- generated files exist on the host PC
- users should download their own copies
- user/run outputs should be separated
- representative files should not be silently overwritten
- firewall rules must not be changed automatically

---

## 22. Codex Work Procedure

### 22.1 Before editing

1. Read this `AGENTS.md`.
2. Read the approved task instruction.
3. Check `AS Report Project Control` status when the task depends on project state.
4. Inspect only the source, tests, outputs, and completion reports relevant to the task.
5. Record allowed scope, forbidden scope, output scope, and delete/archive scope.
6. Check open P0 gates.
7. Summarize expected impact in five lines or fewer.
8. Confirm protected paths exist.
9. Capture timestamps or metadata when the task requires proving files were not regenerated.

### 22.2 During implementation

1. Make the smallest necessary change.
2. Reuse existing modules.
3. Do not rewrite large files from scratch.
4. Do not add unrelated features.
5. Do not bundle separate risks into one patch unless the approved task explicitly groups them.
6. Approved intentional behavior changes may proceed.
7. If impact exceeds the approved scope, stop and report.
8. Do not auto-start another task.

### 22.3 Avoid

Do not:

```text
recreate the project
create duplicate project folders
rewrite app.py from scratch
rewrite analyzer.py from scratch
rewrite report_html.py from scratch
rewrite report_excel.py from scratch
rename Excel sheets without approval
delete BAT files
delete reports
move files to archive without approval
add a framework
add a database
add AI API calls
add firewall changes
apply fuzzy matching without approval
apply preview mappings as confirmed values
regenerate representative outputs as a side effect
merge or replace Raw as a side effect
```

---

## 23. Important Files

Core modules:

```text
src\as_report\loader.py
src\as_report\cleaner.py
src\as_report\period.py
src\as_report\analyzer.py
src\as_report\narrative.py
src\as_report\comparison.py
src\as_report\repeat_issue.py
src\as_report\legacy_features.py
src\as_report\quality_feedback.py
src\as_report\report_html.py
src\as_report\report_excel.py
src\as_report\app.py
src\as_report\ui_state.py
src\as_report\ui_components.py
src\as_report\output.py
src\as_report\cli.py
src\as_report\templates\report_template.html
src\as_report\presentation\build_report.ps1
src\as_report\resources\DY_PPT_Template_16x9.pptx
```

Operational and test files:

```text
README.md
AGENTS.md
tests\
pytest.ini
pyproject.toml
reports\_index\report_history.csv
AS_Report.bat
```

Optional areas, if present:

```text
src\as_report\quality\
src\as_report\standardization\
src\as_report\master\
config\standard_names\
```

Do not assume every optional file or folder exists. Inspect first.

---

## 24. Execution Commands

Recommended import check:

```bat
.\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'src'); import as_report; print(as_report.__file__)"
```

Compile changed Python files:

```bat
.\.venv\Scripts\python.exe -m py_compile <changed_python_file>
```

Canonical full source-test command:

```bat
.\.venv\Scripts\python.exe -m pytest tests --basetemp "<PROJECT_ROOT>\tmp\pytest_<task>" -p no:cacheprovider
```

Do not use root `pytest` as the only completion gate until test discovery is configured to exclude copied handoff tests.

Root pytest may be used after confirming configuration excludes:

```text
_chatgpt_handoff
MD
archive
tmp
```

Run Streamlit locally:

```bat
AS_Report.bat --local
```

Run Streamlit host mode:

```bat
AS_Report.bat --host
```

Use an explicit input path for CLI runs. Do not substitute the newest filename automatically.

---

## 25. Testing Rules

Testing order:

1. import check
2. `py_compile` changed source
3. focused tests for the changed area
4. canonical `pytest tests`
5. root pytest only when relevant and configured
6. real-file runtime reproduction when the original defect depended on a real file

Examples of focused tests:

```bat
pytest tests\test_loader.py
pytest tests\test_cleaner.py tests\test_analyzer.py
pytest tests\test_comparison.py
pytest tests\test_repeat_issue.py
pytest tests\test_raw_data_quality_checker.py
pytest tests\test_standard_name_mapper.py
pytest tests\test_output_manager.py
pytest tests\test_ui_state.py
```

Rules:

- Fix only failures related to the approved scope.
- Do not delete tests to obtain a pass.
- Do not repeatedly run the full suite after every tiny edit.
- Add small focused tests when a regression path is not covered.
- For real-file schema defects, unit tests alone are not sufficient if runtime verification is feasible.

---

## 26. Conditional Validation by Task Type

### 26.1 All code tasks

Required:

```text
protected paths unchanged
import check
focused tests
pytest tests
changed-file inventory
scope check
completion report
```

### 26.2 Loader/schema tasks

Also required:

```text
legacy schema test
alias-only schema test
both-columns precedence test
neither-column failure test
real input runtime check when available
```

### 26.3 HTML tasks

Also required:

```text
validation HTML only
section and wording checks
browser view
print/PDF preview when user-facing layout changes
```

### 26.4 Excel tasks

Also required:

```text
validation workbook only
workbook open check
required sheet/header checks
```

### 26.5 Representative regeneration tasks

Also required:

```text
all P0 gates cleared
approved Raw baseline
same-run HTML and Excel generation
paired metadata match
history update for both outputs
manual visual check
```

### 26.6 Docs-only tasks

Tests may be skipped when no source or configuration changed.

Record:

```text
why tests were skipped
source timestamps unchanged
Raw/master unchanged
representative/validation outputs unchanged
```

### 26.7 Pytest configuration tasks

Required:

```text
root pytest collection succeeds
pytest tests still succeeds
no test file deletion
handoff copies remain available
```

---

## 27. Completion and Handoff Rules

Completion reports belong under:

```text
MD\completion report\
```

Handoff manifests belong under:

```text
MD\_chatgpt_handoff\<task>\MANIFEST.md
```

Keep only the current handoff in the active project. Historical handoffs belong in the external archive and Google Drive project control history.

A completion report must include:

```markdown
# Completion Report

## Task Summary
## Modified Files
## Created Files
## Protected Files Check
## Test Results
## Runtime Validation
## Output/Report Impact
## Known Limitations
## Remaining Risks
## Recommended Next Step
```

Do not claim `Completed` when:

- the real defect file was not verified and runtime validation was required
- a required test failed
- a P0 blocker remains inside the task's acceptance gate
- representative pair metadata does not match
- protected files changed without approval

Use accurate statuses such as:

```text
Implemented / Runtime Check Pending
Conditionally Completed
Blocked
Review Required
Completed
```

---

## 28. Control Sheet Update Rules

After an approved task, update the relevant rows in:

```text
00_Control_Tower
01_Task_History
03_Risk_and_Rules
04_Next_Actions
05_Codex_Instructions
```

Update status only from actual evidence:

- changed files
- test counts
- runtime result
- output timestamps
- completion report

Do not mark a risk closed merely because code was written.

Do not mark a representative output valid until paired regeneration and validation are complete.

Do not automatically change unrelated Candidate or Backlog rows.

---

## 29. Completion Checklist

Before reporting completion, verify only the items applicable to the task.

### Always

```text
AGENTS.md exists
README.md exists
src\as_report exists
tests exists
data\raw exists
data\master exists
reports exists
reports\users exists
Raw/master unchanged unless explicitly approved
no duplicate project folder created
no unrelated refactor performed
completion report created
```

### When code changed

```text
import passes
changed Python compiles
focused tests pass
pytest tests passes or failure is accurately reported
```

### When UI changed

```text
Streamlit opens
current-run preview behavior verified
```

### When HTML changed

```text
validation HTML opens
browser and print behavior verified as required
```

### When Excel changed

```text
validation workbook opens
required sheets/headers verified
```

### When representative outputs changed

```text
Raw baseline approved
HTML and Excel generated together
metadata matches
history contains both
manual visual check recorded
```

---

## 30. Final Operating Principle

This project must prefer a smaller trustworthy result over a larger misleading result.

When coverage, matching, provenance, or output pairing is insufficient:

```text
hide the unreliable metric
show the coverage limitation
block representative sharing
request a decision
```

Do not fill gaps through confident-sounding inference.
