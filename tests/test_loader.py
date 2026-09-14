from __future__ import annotations

import pytest

from as_report.loader import DataLoadError, load_input
from conftest import sample_dataframe


def _write_input(dataframe, path):
    if path.suffix == ".csv":
        dataframe.to_csv(path, index=False, encoding="utf-8-sig")
    else:
        dataframe.to_excel(path, index=False)


def test_csv_loading(tmp_path):
    path = tmp_path / "issues.csv"
    sample_dataframe().to_csv(path, index=False, encoding="utf-8-sig")

    loaded = load_input(path)

    assert loaded.metadata.file_name == "issues.csv"
    assert loaded.metadata.encoding == "utf-8-sig"
    assert len(loaded.dataframe) == 3


def test_excel_loading(tmp_path):
    path = tmp_path / "issues.xlsx"
    sample_dataframe().to_excel(path, index=False)

    loaded = load_input(path)

    assert loaded.metadata.file_name == "issues.xlsx"
    assert len(loaded.dataframe) == 3


def test_missing_required_columns(tmp_path):
    path = tmp_path / "bad.csv"
    sample_dataframe().drop(columns=["고객사", "접수일"]).to_csv(path, index=False, encoding="utf-8-sig")

    with pytest.raises(DataLoadError) as error:
        load_input(path)

    assert "고객사" in str(error.value)
    assert "접수일" in str(error.value)


@pytest.mark.parametrize("suffix", [".csv", ".xlsx"])
def test_failure_cause_type_alias_populates_canonical_column(tmp_path, suffix):
    path = tmp_path / f"issues{suffix}"
    dataframe = sample_dataframe().rename(columns={"고장원인": "고장유형"})
    _write_input(dataframe, path)

    loaded = load_input(path)

    assert "고장유형" in loaded.dataframe.columns
    assert loaded.dataframe["고장원인"].tolist() == dataframe["고장유형"].tolist()


def test_existing_failure_cause_column_takes_precedence_over_alias(tmp_path):
    path = tmp_path / "issues.csv"
    dataframe = sample_dataframe()
    dataframe["고장유형"] = "alias value"
    _write_input(dataframe, path)

    loaded = load_input(path)

    assert loaded.dataframe["고장원인"].tolist() == dataframe["고장원인"].tolist()


def test_missing_failure_cause_and_alias_keeps_required_column_error(tmp_path):
    path = tmp_path / "issues.csv"
    dataframe = sample_dataframe().drop(columns=["고장원인"])
    _write_input(dataframe, path)

    with pytest.raises(DataLoadError) as error:
        load_input(path)

    assert "고장원인" in str(error.value)
