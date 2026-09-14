from __future__ import annotations

import pandas as pd

from as_report.standardization import (
    apply_standard_name_preview,
    ensure_standard_name_files,
    extract_unknown_standard_names,
    load_standard_name_mapping,
)
from as_report.standardization.standard_name_mapper import MAPPING_COLUMNS


def test_mapping_csv_files_are_created_header_only(tmp_path) -> None:
    paths = ensure_standard_name_files(tmp_path)

    assert "customer_names.csv" in paths
    for path in paths.values():
        dataframe = pd.read_csv(path, dtype=str, encoding="utf-8-sig")
        assert list(dataframe.columns) == MAPPING_COLUMNS
        assert dataframe.empty


def test_empty_mapping_does_not_overwrite_original_values() -> None:
    source = pd.DataFrame({"고객사": ["원본고객"], "접수일": ["2026-01-01"]})

    preview, unknown = apply_standard_name_preview(source, {})

    assert source.columns.tolist() == ["고객사", "접수일"]
    assert preview.loc[0, "고객사"] == "원본고객"
    assert preview.loc[0, "고객사_표준명_후보"] == "원본고객"
    assert preview.loc[0, "고객사_표준명_매핑상태"] == "미매핑"
    assert unknown.loc[0, "raw_name"] == "원본고객"


def test_enabled_mapping_creates_preview_column_value(tmp_path) -> None:
    ensure_standard_name_files(tmp_path)
    (tmp_path / "customer_names.csv").write_text(
        "raw_name,standard_name,field_name,note,enabled\n원본고객,표준고객,고객사,,TRUE\n",
        encoding="utf-8-sig",
    )
    mappings = load_standard_name_mapping(tmp_path)
    source = pd.DataFrame({"고객사": ["원본고객"], "접수일": ["2026-01-01"]})

    preview, unknown = apply_standard_name_preview(source, mappings)

    assert preview.loc[0, "고객사_표준명_후보"] == "표준고객"
    assert preview.loc[0, "고객사_표준명_매핑상태"] == "매핑됨"
    assert unknown.empty


def test_unknown_values_are_extracted_with_counts() -> None:
    source = pd.DataFrame(
        {
            "고객사": ["A", "A", "B", "선택안함"],
            "접수일": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"],
            "접수 내용 (요약)": ["a issue", "a issue 2", "b issue", "blank"],
        }
    )

    unknown = extract_unknown_standard_names(source, {"고객사": {"B": "표준B"}})

    assert len(unknown) == 1
    assert unknown.loc[0, "raw_name"] == "A"
    assert unknown.loc[0, "count"] == 2
    assert unknown.loc[0, "recommended_mapping_file"] == "customer_names.csv"


def test_missing_target_columns_do_not_raise() -> None:
    source = pd.DataFrame({"접수일": ["2026-01-01"], "상태": ["처리완료"]})

    preview, unknown = apply_standard_name_preview(source, {})

    assert preview.equals(source)
    assert unknown.empty


def test_original_dataframe_is_not_modified_in_place() -> None:
    source = pd.DataFrame({"LINE": ["L1"]})
    original_columns = source.columns.tolist()

    apply_standard_name_preview(source, {"LINE": {"L1": "LINE-1"}})

    assert source.columns.tolist() == original_columns
