from __future__ import annotations

from as_report.ui_state import list_raw_files, parse_filename_date, resolve_customer_robot_master_file, resolve_default_raw_file, resolve_failure_part_master_file, resolve_latest_file


def test_resolve_default_raw_file_returns_none_without_candidates(tmp_path) -> None:
    assert resolve_default_raw_file(tmp_path, tmp_path / "missing.csv") is None


def test_resolve_default_raw_file_prefers_legacy_file(tmp_path) -> None:
    legacy_file = tmp_path / "04. ES_ 이슈사항 보고_20260130 (1).csv"
    newer_file = tmp_path / "04. ES_ 이슈사항 보고_20260619.csv"
    legacy_file.write_text("legacy", encoding="utf-8")
    newer_file.write_text("newer", encoding="utf-8")

    assert resolve_default_raw_file(tmp_path, legacy_file) == legacy_file


def test_resolve_default_raw_file_requires_user_choice_when_multiple_files_exist(tmp_path) -> None:
    older_file = tmp_path / "04. ES_ 이슈사항 보고_20260130 (1).csv"
    newer_file = tmp_path / "04. ES_ 이슈사항 보고_20260619.csv"
    newest_file = tmp_path / "04. ES_ 이슈사항 보고_20260630.csv"
    unrelated_file = tmp_path / "other.csv"
    older_file.write_text("older", encoding="utf-8")
    newer_file.write_text("newer", encoding="utf-8")
    newest_file.write_text("newest", encoding="utf-8")
    unrelated_file.write_text("unrelated", encoding="utf-8")

    assert resolve_default_raw_file(tmp_path, tmp_path / "missing.csv") is None


def test_list_raw_files_returns_current_matching_files_in_newest_filename_order(tmp_path) -> None:
    older_file = tmp_path / "04. ES_ 이슈사항 보고_20260619.csv"
    newer_file = tmp_path / "04. ES_ 이슈사항 보고_20260630.csv"
    older_file.write_text("older", encoding="utf-8")

    assert list_raw_files(tmp_path) == [older_file]

    newer_file.write_text("newer", encoding="utf-8")
    assert list_raw_files(tmp_path) == [newer_file, older_file]


def test_resolve_latest_file_uses_filename_date_over_name_sort(tmp_path) -> None:
    newer = tmp_path / "04. ES_ 이슈사항 보고_20260630.csv"
    older_but_later_name = tmp_path / "04. ES_ 이슈사항 보고_zz_20260619.csv"
    newer.write_text("newer", encoding="utf-8")
    older_but_later_name.write_text("older", encoding="utf-8")

    assert resolve_latest_file(tmp_path, "04. ES_ 이슈사항 보고*.csv") == newer


def test_resolve_latest_file_falls_back_to_name_sort_without_dates(tmp_path) -> None:
    first = tmp_path / "04. ES_ 이슈사항 보고_alpha.csv"
    second = tmp_path / "04. ES_ 이슈사항 보고_beta.csv"
    first.write_text("first", encoding="utf-8")
    second.write_text("second", encoding="utf-8")

    assert resolve_latest_file(tmp_path, "04. ES_ 이슈사항 보고*.csv") == second


def test_parse_filename_date_returns_none_without_date() -> None:
    assert parse_filename_date("04. ES_ 이슈사항 보고_latest.csv") is None


def test_resolve_latest_master_files(tmp_path) -> None:
    old_failure = tmp_path / "00. ES_고장부품 분류_20260619.csv"
    new_failure = tmp_path / "00. ES_고장부품 분류_20260630.csv"
    robot_master = tmp_path / "08. ES_고객사 로보트 리스트 (Customer Robot List)_20260619.csv"
    old_failure.write_text("old", encoding="utf-8")
    new_failure.write_text("new", encoding="utf-8")
    robot_master.write_text("robot", encoding="utf-8")

    assert resolve_failure_part_master_file(tmp_path) == new_failure
    assert resolve_customer_robot_master_file(tmp_path) == robot_master
