from __future__ import annotations

import csv
import hashlib

import pytest

from as_report.input_contract import inspect_csv
from as_report.loader import DataLoadError, load_input


def write_csv(tmp_path, headers, rows, encoding="utf-8-sig"):
    path = tmp_path / "input.csv"
    with path.open("w", encoding=encoding, newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(headers)
        writer.writerows(rows)
    return path


@pytest.mark.parametrize("headers,values,expected", [
    (["고장원인"], ["canonical"], "고장원인"),
    (["고장유형"], ["alias"], "고장유형"),
    (["고장원인", "고장유형"], ["", "alias"], "고장원인"),
    (["unknown"], ["value"], None),
])
def test_alias_contract(tmp_path, headers, values, expected):
    result = inspect_csv(write_csv(tmp_path, ["접수일", *headers], [["2026-01-01", *values]]))
    assert result.field_mapping.get("고장원인") == expected
    assert bool(result.alias_applications) == (expected == "고장유형")
    assert result.rows[0].raw_values == ("2026-01-01", *values)
    assert result.features["failure_type_distribution"]["status"] == (
        "available" if expected and values[0] else "unavailable")


def test_reordered_extra_headers_and_dyone_are_not_substituted(tmp_path):
    path = write_csv(tmp_path, [" 고객사(DYONE) ", "접수일", "*ID", "extra"],
                     [["customer", "2026-01-01", "001", "NA"]])
    before = path.read_bytes()
    result = inspect_csv(path)
    assert result.original_headers[0] == " 고객사(DYONE) "
    assert "고객사" not in result.field_mapping
    assert "extra" in result.unmapped_headers
    assert result.features["customer_distribution"]["reasons"] == ["missing_column:고객사"]
    assert result.rows[0].original_id == "001"
    assert result.sha256 == hashlib.sha256(before).hexdigest()
    assert path.read_bytes() == before


@pytest.mark.parametrize("headers,error", [
    (["접수일", "접수일"], "duplicate_raw_header"),
    (["접수일", " 접수일 "], "duplicate_normalized_header"),
    (["접수일", ""], "blank_header"),
])
def test_invalid_headers_disable_mapping(tmp_path, headers, error):
    result = inspect_csv(write_csv(tmp_path, headers, [["2026-01-01", "value"]]))
    assert error in result.structural_errors
    assert not result.field_mapping
    assert all(f["status"] == "unavailable" for f in result.features.values())
    assert result.date_summary["valid"] is None


def test_ids_dates_and_physical_lines(tmp_path):
    result = inspect_csv(write_csv(tmp_path, ["*ID", "접수일", "접수 내용 (요약)"], [
        ["001", "2026-01-01", "first\nsecond"],
        ["001", "2026/02/02", "request"],
        ["", "", ""],
        ["NA", "2026-02-30", ""],
        [" 001 ", "--", ""],
    ]))
    assert result.row_count == 5
    assert result.id_summary == dict(column_present=True, missing=1, unique_nonempty=3,
                                     duplicate_values=1, duplicate_rows=2, unassessed=0)
    assert [r.original_id for r in result.rows] == ["001", "001", "", "NA", " 001 "]
    assert result.rows[0].line_start == 2 and result.rows[0].line_end == 3
    assert result.rows[1].line_start == 4
    assert result.date_summary["valid"] == 2
    assert result.date_summary["missing"] == 1
    assert result.date_summary["invalid"] == 2
    assert sum(result.date_summary[k] for k in ("valid", "missing", "invalid", "unassessed")) == 5
    assert result.features["follow_up_evidence"]["usable_rows"] == 2


def test_missing_fields_are_not_zero(tmp_path):
    result = inspect_csv(write_csv(tmp_path, ["unknown"], [["value"]]))
    assert result.date_summary["valid"] is None
    assert result.date_summary["unassessed"] == 1
    assert result.id_summary["missing"] is None
    assert result.field_summary["상태"]["nonempty"] is None
    assert all(f["status"] == "unavailable" for f in result.features.values())


def test_empty_status_is_not_missing_column(tmp_path):
    result = inspect_csv(write_csv(tmp_path, ["접수일", "상태"], [["2026-01-01", " "]]))
    assert result.field_summary["상태"] == dict(column_present=True, missing=1, nonempty=0)
    assert result.features["status_distribution"]["reasons"] == ["no_usable_rows"]
    assert result.features["period_records"]["status"] == "available"


@pytest.mark.parametrize("encoding", ["utf-8-sig", "cp949"])
def test_encoding(tmp_path, encoding):
    result = inspect_csv(write_csv(tmp_path, ["접수일"], [["2026-01-01"]], encoding))
    assert result.encoding == encoding
    assert result.date_summary["valid"] == 1


def test_ragged_rows_are_not_silently_repaired(tmp_path):
    result = inspect_csv(write_csv(tmp_path, ["접수일", "*ID"], [["2026-01-01"]]))
    assert result.structural_errors == ("row_width_mismatch",)
    assert result.rows[0].raw_values == ("2026-01-01",)


def test_empty_file_and_header_only(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_bytes(b"")
    assert inspect_csv(path).structural_errors == ("missing_header",)
    result = inspect_csv(write_csv(tmp_path, ["접수일"], []))
    assert result.row_count == 0
    assert result.features["period_records"]["status"] == "unavailable"


def test_legacy_loading_remains_strict(tmp_path):
    path = write_csv(tmp_path, ["접수일"], [["2026-01-01"]])
    assert inspect_csv(path).features["period_records"]["status"] == "available"
    with pytest.raises(DataLoadError, match="필수 컬럼"):
        load_input(path)


def test_malformed_csv_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text('접수일\n"unterminated', encoding="utf-8")
    with pytest.raises(DataLoadError, match="구문 오류"):
        inspect_csv(path)


def test_header_reordering_and_partial_rows(tmp_path):
    path = write_csv(tmp_path, ["상태", "extra", "접수일", "고객사"], [
        ["전달 완료", "x", "2026-01-01", "A"],
        ["처리완료", "y", "bad-date", "B"],
        ["", "z", "2026-01-02", ""],
    ])
    result = inspect_csv(path)
    assert result.features["status_distribution"]["usable_rows"] == 1
    assert result.features["customer_distribution"]["usable_rows"] == 1
    assert result.features["period_records"]["usable_rows"] == 2
    assert result.features["follow_up_evidence"]["usable_rows"] is None
    assert result.rows[0].raw_values[0] == "전달 완료"
    assert result.field_summary["상태"]["missing"] == 1


@pytest.mark.parametrize("size", [131071, 131072, 131073, 524288])
def test_long_fields_keep_original_text_and_line_positions(tmp_path, size):
    from as_report.loader import REQUIRED_COLUMNS

    value = '가"\r\n' + '나' * (size - 4)
    headers = list(REQUIRED_COLUMNS)
    row = ["value"] * len(headers)
    row[headers.index("*ID")] = "001"
    row[headers.index("접수일")] = "2026-01-01"
    row[headers.index("처리내용/진행상황 (요약)")] = value
    path = write_csv(tmp_path, headers, [row, row])
    before = path.read_bytes()
    limit = csv.field_size_limit()
    result = inspect_csv(path)
    assert csv.field_size_limit() == limit
    assert result.rows[0].raw_values[headers.index("처리내용/진행상황 (요약)")] == value
    assert (result.rows[0].line_start, result.rows[0].line_end, result.rows[1].line_start) == (2, 3, 4)
    assert result.rows[0].original_id == "001"
    assert result.date_summary["valid"] == 2
    assert load_input(path).dataframe["처리내용/진행상황 (요약)"].iloc[0] == value
    assert before == path.read_bytes()


def test_shared_limit_unchanged_during_concurrent_success_and_failure(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    good = write_csv(tmp_path, ["접수일", "접수 내용 (요약)"], [["2026-01-01", "가" * 200000]])
    bad = tmp_path / "bad.csv"
    bad.write_text('접수일\n"unclosed', encoding="utf-8")
    before = csv.field_size_limit()
    try:
        csv.field_size_limit(32)

        def check(index):
            if index % 2:
                with pytest.raises(DataLoadError, match="구문 오류"):
                    inspect_csv(bad)
            else:
                assert inspect_csv(good).row_count == 1
            assert csv.field_size_limit() == 32
            with pytest.raises(csv.Error, match="field larger"):
                list(csv.reader(["a" * 33]))

        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(check, range(12)))
        assert csv.field_size_limit() == 32
    finally:
        csv.field_size_limit(before)


@pytest.mark.parametrize("result", [b'{"error":"resource"}', None])
def test_worker_resource_and_launch_errors_do_not_change_limit(tmp_path, monkeypatch, result):
    from as_report import input_contract
    from subprocess import CompletedProcess

    path = write_csv(tmp_path, ["접수일"], [["2026-01-01"]])
    limit = csv.field_size_limit()

    def run(*args, **kwargs):
        if result is None:
            raise OSError("unavailable")
        return CompletedProcess(args, 0, stdout=result)

    monkeypatch.setattr(input_contract.subprocess, "run", run)
    with pytest.raises(DataLoadError) as error:
        inspect_csv(path)
    assert "구문 오류" not in str(error.value)
    assert csv.field_size_limit() == limit
