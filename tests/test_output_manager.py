from __future__ import annotations

import pandas as pd

from as_report.output import (
    append_report_history,
    build_timestamped_filename,
    build_user_output_dirs,
    read_report_history,
    sanitize_user_name,
    write_run_metadata,
)


def test_empty_user_name_becomes_default_user() -> None:
    assert sanitize_user_name("") == "default_user"
    assert sanitize_user_name(None) == "default_user"


def test_invalid_windows_path_chars_are_sanitized() -> None:
    assert sanitize_user_name('kim<as>:"/\\|?*') == "kim_as"


def test_output_directories_are_created(tmp_path) -> None:
    dirs = build_user_output_dirs(tmp_path, "홍 길동")

    assert dirs["user_root"].exists()
    assert dirs["reports"].exists()
    assert dirs["quality"].exists()
    assert dirs["standardization"].exists()
    assert dirs["master_analysis"].exists()
    assert dirs["proposal"].exists()
    assert dirs["auto_fill_preview"].exists()
    assert dirs["logs"].exists()
    assert dirs["index"].exists()
    assert "홍_길동" in str(dirs["user_root"])


def test_timestamped_filename_includes_timestamp_and_suffix() -> None:
    filename = build_timestamped_filename("AS Report/year", "html", "20260619_101530")

    assert filename == "AS_Report_year_20260619_101530.html"


def test_report_history_csv_is_created_and_appended(tmp_path) -> None:
    append_report_history(
        {
            "user_name": "tester",
            "period_type": "year",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "source_file": "raw.csv",
            "output_type": "html",
            "output_path": "reports/out.html",
            "status": "success",
            "note": "first",
        },
        base_dir=tmp_path,
    )
    history_path = append_report_history(
        {
            "user_name": "tester",
            "period_type": "year",
            "output_type": "excel",
            "output_path": "reports/out.xlsx",
            "status": "success",
        },
        base_dir=tmp_path,
    )

    history = pd.read_csv(history_path)
    assert list(history["output_type"]) == ["html", "excel"]
    assert history_path.name == "report_history.csv"


def test_report_history_preserves_old_rows_when_provenance_columns_are_added(tmp_path) -> None:
    index_dir = tmp_path / "_index"
    index_dir.mkdir()
    history_path = index_dir / "report_history.csv"
    history_path.write_text(
        "created_at,user_name,period_type,start_date,end_date,source_file,output_type,output_path,status,note\n"
        "2026-07-20T12:00:00,tester,year,2026-01-01,2026-12-31,old.csv,html,reports/old.html,success,legacy\n",
        encoding="utf-8-sig",
    )

    append_report_history(
        {
            "run_id": "RUN-2",
            "input_set_id": "INPUT-2",
            "user_name": "tester",
            "period_type": "year",
            "source_file": "new.csv",
            "output_type": "excel",
            "output_path": "reports/new.xlsx",
            "status": "success",
        },
        base_dir=tmp_path,
    )

    history = pd.read_csv(history_path)
    assert list(history["source_file"]) == ["old.csv", "new.csv"]
    assert history.loc[1, "run_id"] == "RUN-2"
    assert history.loc[1, "input_set_id"] == "INPUT-2"


def test_write_run_metadata_uses_utf8_json(tmp_path) -> None:
    metadata_path = write_run_metadata(
        tmp_path / "run_metadata.json",
        {"run_id": "RUN-1", "input_set_id": "INPUT-1", "label": "검토"},
    )

    assert metadata_path.exists()
    assert "검토" in metadata_path.read_text(encoding="utf-8")


def test_read_report_history_missing_file_returns_empty(tmp_path) -> None:
    assert read_report_history(tmp_path) == []


def test_read_report_history_empty_file_returns_empty(tmp_path) -> None:
    index_dir = tmp_path / "_index"
    index_dir.mkdir()
    (index_dir / "report_history.csv").write_text("", encoding="utf-8-sig")

    assert read_report_history(tmp_path) == []


def test_read_report_history_filters_protected_paths_and_applies_limit(tmp_path) -> None:
    records = [
        ("html", "reports/out.html"),
        ("empty", ""),
        ("raw", "data/raw/source.csv"),
        ("master", "data/master/master.csv"),
        ("validation", "reports/validation/check.html"),
        ("excel", "reports/users/tester/out.xlsx"),
        ("csv", "C:/Users/johnny/AS report/reports/users/tester/out.csv"),
    ]
    for output_type, output_path in records:
        append_report_history(
            {
                "user_name": "tester",
                "period_type": "custom",
                "start_date": "2026-01-01",
                "end_date": "2026-01-31",
                "source_file": "raw.csv",
                "output_type": output_type,
                "output_path": output_path,
                "status": "success",
            },
            base_dir=tmp_path,
        )

    history = read_report_history(tmp_path, limit=2)

    assert [row["output_type"] for row in history] == ["csv", "excel"]
    assert all(row["output_path"] for row in history)


def test_read_report_history_excludes_absolute_protected_paths(tmp_path) -> None:
    for output_type, output_path in [
        ("raw", "C:/Users/johnny/AS report/data/raw/source.csv"),
        ("master", "C:/Users/johnny/AS report/data/master/master.csv"),
        ("validation", "C:/Users/johnny/AS report/reports/validation/check.html"),
        ("html", "C:/Users/johnny/AS report/reports/users/tester/out.html"),
    ]:
        append_report_history(
            {
                "user_name": "tester",
                "period_type": "year",
                "output_type": output_type,
                "output_path": output_path,
                "status": "success",
            },
            base_dir=tmp_path,
        )

    history = read_report_history(tmp_path, limit=10)

    assert [row["output_type"] for row in history] == ["html"]
