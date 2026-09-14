from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from as_report.input_set import (
    AS_RAW_ROLE,
    CUSTOMER_ROBOT_MASTER_ROLE,
    FAILURE_PART_MASTER_ROLE,
    InputSetError,
    inspect_input_file,
    load_input_set,
)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")


def _record(path: Path, role: str, date_column: str = "") -> dict[str, object]:
    identity = inspect_input_file(path, role=role, date_column=date_column)
    record = identity.to_dict()
    record["id_column"] = "*ID"
    record["date_column"] = date_column
    record.pop("role")
    record.pop("file_name")
    record.pop("is_override")
    return record


def _manifest(tmp_path: Path) -> Path:
    raw = tmp_path / "raw.csv"
    robot = tmp_path / "robot.csv"
    part = tmp_path / "part.csv"
    _write_csv(raw, [{"*ID": "A1", "접수일": "2026-07-20", "고장유형": "입력"}])
    _write_csv(robot, [{"*ID": "R1", "본체(Manifold)": "GP25"}])
    _write_csv(part, [{"*ID": "P1", "품명": "AOPR"}])

    manifest = {
        "input_set_id": "TEST-INPUT-SET",
        "files": {
            AS_RAW_ROLE: _record(raw, AS_RAW_ROLE, "접수일"),
            CUSTOMER_ROBOT_MASTER_ROLE: _record(robot, CUSTOMER_ROBOT_MASTER_ROLE),
            FAILURE_PART_MASTER_ROLE: _record(part, FAILURE_PART_MASTER_ROLE),
        },
        "canonical_mappings": {
            "robot_model": {"source": "본체(Manifold)", "canonical": "robot_model", "status": "approval_required"}
        },
    }
    path = tmp_path / "input_set.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    return path


def test_load_input_set_validates_all_three_files(tmp_path) -> None:
    input_set = load_input_set(_manifest(tmp_path))

    assert input_set.input_set_id == "TEST-INPUT-SET"
    assert input_set.files[AS_RAW_ROLE].row_count == 1
    assert input_set.files[CUSTOMER_ROBOT_MASTER_ROLE].columns[-1] == "본체(Manifold)"
    assert input_set.files[FAILURE_PART_MASTER_ROLE].unique_id_count == 1
    assert input_set.to_provenance()["files"][AS_RAW_ROLE]["date_max"] == "2026-07-20"


def test_load_input_set_fails_closed_for_missing_file(tmp_path) -> None:
    path = _manifest(tmp_path)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["files"][FAILURE_PART_MASTER_ROLE]["path"] = str(tmp_path / "missing.csv")
    path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(InputSetError, match="Required input file not found"):
        load_input_set(path)


def test_load_input_set_fails_closed_when_file_bytes_change(tmp_path) -> None:
    path = _manifest(tmp_path)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    raw_path = Path(manifest["files"][AS_RAW_ROLE]["path"])
    raw_path.write_text(raw_path.read_text(encoding="utf-8-sig") + "\n", encoding="utf-8-sig")

    with pytest.raises(InputSetError, match="identity mismatch"):
        load_input_set(path)


def test_explicit_override_is_recorded_without_claiming_approved_identity(tmp_path) -> None:
    path = _manifest(tmp_path)
    override = tmp_path / "override.csv"
    _write_csv(override, [{"*ID": "A2", "접수일": "2026-07-21", "고장유형": "입력"}])

    input_set = load_input_set(path, overrides={AS_RAW_ROLE: override})

    assert input_set.has_overrides is True
    assert input_set.input_set_id == "TEST-INPUT-SET:override"
    assert input_set.files[AS_RAW_ROLE].is_override is True
    assert input_set.files[AS_RAW_ROLE].sha256 == hashlib.sha256(override.read_bytes()).hexdigest()

