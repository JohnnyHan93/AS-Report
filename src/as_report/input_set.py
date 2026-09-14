from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from .loader import CSV_ENCODINGS

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ACTIVE_INPUT_SET_PATH = PROJECT_ROOT / "config" / "active_input_set.json"

AS_RAW_ROLE = "as_raw"
CUSTOMER_ROBOT_MASTER_ROLE = "customer_robot_master"
FAILURE_PART_MASTER_ROLE = "failure_part_master"
REQUIRED_INPUT_ROLES = (
    AS_RAW_ROLE,
    CUSTOMER_ROBOT_MASTER_ROLE,
    FAILURE_PART_MASTER_ROLE,
)


class InputSetError(ValueError):
    """Raised when an approved input-set manifest cannot be trusted."""


@dataclass(frozen=True)
class InputFileIdentity:
    role: str
    path: Path
    file_name: str
    size: int
    modified_time_ns: int
    sha256: str
    row_count: int
    column_count: int
    unique_id_count: int
    duplicate_id_count: int
    columns: tuple[str, ...]
    date_min: str = ""
    date_max: str = ""
    is_override: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "path": str(self.path),
            "file_name": self.file_name,
            "size": self.size,
            "modified_time_ns": self.modified_time_ns,
            "sha256": self.sha256,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "unique_id_count": self.unique_id_count,
            "duplicate_id_count": self.duplicate_id_count,
            "columns": list(self.columns),
            "date_min": self.date_min,
            "date_max": self.date_max,
            "is_override": self.is_override,
        }


@dataclass(frozen=True)
class ApprovedInputSet:
    input_set_id: str
    manifest_path: Path
    manifest_sha256: str
    files: Mapping[str, InputFileIdentity]
    canonical_mappings: Mapping[str, Any]
    has_overrides: bool = False

    @property
    def raw_path(self) -> Path:
        return self.files[AS_RAW_ROLE].path

    @property
    def customer_robot_master_path(self) -> Path:
        return self.files[CUSTOMER_ROBOT_MASTER_ROLE].path

    @property
    def failure_part_master_path(self) -> Path:
        return self.files[FAILURE_PART_MASTER_ROLE].path

    @property
    def signature(self) -> str:
        parts = [self.input_set_id, self.manifest_sha256]
        for role in REQUIRED_INPUT_ROLES:
            identity = self.files[role]
            parts.extend((role, str(identity.path.resolve()), identity.sha256))
        return sha256("|".join(parts).encode("utf-8")).hexdigest()

    def to_provenance(self) -> dict[str, Any]:
        return {
            "input_set_id": self.input_set_id,
            "input_set_signature": self.signature,
            "manifest_path": str(self.manifest_path),
            "manifest_sha256": self.manifest_sha256,
            "has_overrides": self.has_overrides,
            "files": {role: self.files[role].to_dict() for role in REQUIRED_INPUT_ROLES},
            "canonical_mappings": dict(self.canonical_mappings),
        }


def load_input_set(
    manifest_path: str | Path = ACTIVE_INPUT_SET_PATH,
    overrides: Mapping[str, str | Path | None] | None = None,
) -> ApprovedInputSet:
    path = Path(manifest_path)
    if not path.exists() or not path.is_file():
        raise InputSetError(f"Input-set manifest not found: {path}")

    try:
        manifest_bytes = path.read_bytes()
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise InputSetError(f"Input-set manifest could not be read: {path}: {error}") from error

    input_set_id = str(manifest.get("input_set_id", "")).strip()
    if not input_set_id:
        raise InputSetError("Input-set manifest is missing input_set_id")

    file_records = manifest.get("files")
    if not isinstance(file_records, dict):
        raise InputSetError("Input-set manifest files must be an object keyed by role")

    override_values = overrides or {}
    identities: dict[str, InputFileIdentity] = {}
    has_overrides = False
    for role in REQUIRED_INPUT_ROLES:
        expected = file_records.get(role)
        if not isinstance(expected, dict):
            raise InputSetError(f"Input-set manifest is missing role: {role}")

        override = override_values.get(role)
        is_override = override is not None and str(override).strip() != ""
        source_path = Path(override) if is_override else Path(str(expected.get("path", "")))
        actual = inspect_input_file(
            source_path,
            role=role,
            id_column=str(expected.get("id_column", "*ID")),
            date_column=str(expected.get("date_column", "")),
            is_override=is_override,
        )
        if not is_override:
            _validate_expected_identity(actual, expected)
        identities[role] = actual
        has_overrides = has_overrides or is_override

    return ApprovedInputSet(
        input_set_id=f"{input_set_id}:override" if has_overrides else input_set_id,
        manifest_path=path,
        manifest_sha256=sha256(manifest_bytes).hexdigest(),
        files=identities,
        canonical_mappings=manifest.get("canonical_mappings", {}),
        has_overrides=has_overrides,
    )


def inspect_input_file(
    path: str | Path,
    *,
    role: str,
    id_column: str = "*ID",
    date_column: str = "",
    is_override: bool = False,
) -> InputFileIdentity:
    source_path = Path(path)
    if not source_path.exists() or not source_path.is_file():
        raise InputSetError(f"Required input file not found for {role}: {source_path}")

    dataframe = _read_csv(source_path)
    dataframe.columns = [str(column).strip() for column in dataframe.columns]
    if id_column not in dataframe.columns:
        raise InputSetError(f"Required ID column '{id_column}' missing from {role}: {source_path}")

    id_values = dataframe[id_column].dropna().astype(str).str.strip()
    id_values = id_values.loc[id_values.ne("")]
    unique_id_count = int(id_values.nunique())
    duplicate_id_count = int(len(id_values) - unique_id_count)

    date_min = ""
    date_max = ""
    if date_column:
        if date_column not in dataframe.columns:
            raise InputSetError(f"Required date column '{date_column}' missing from {role}: {source_path}")
        dates = pd.to_datetime(dataframe[date_column], errors="coerce").dropna()
        if not dates.empty:
            date_min = dates.min().date().isoformat()
            date_max = dates.max().date().isoformat()

    stat = source_path.stat()
    return InputFileIdentity(
        role=role,
        path=source_path,
        file_name=source_path.name,
        size=stat.st_size,
        modified_time_ns=stat.st_mtime_ns,
        sha256=_hash_file(source_path),
        row_count=int(len(dataframe)),
        column_count=int(len(dataframe.columns)),
        unique_id_count=unique_id_count,
        duplicate_id_count=duplicate_id_count,
        columns=tuple(dataframe.columns),
        date_min=date_min,
        date_max=date_max,
        is_override=is_override,
    )


def _read_csv(path: Path) -> pd.DataFrame:
    errors: list[str] = []
    for encoding in CSV_ENCODINGS:
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError as error:
            errors.append(f"{encoding}: {error}")
    raise InputSetError(f"CSV encoding could not be resolved for {path}: {' | '.join(errors)}")


def _validate_expected_identity(actual: InputFileIdentity, expected: Mapping[str, Any]) -> None:
    checks = {
        "size": actual.size,
        "modified_time_ns": actual.modified_time_ns,
        "sha256": actual.sha256,
        "row_count": actual.row_count,
        "column_count": actual.column_count,
        "unique_id_count": actual.unique_id_count,
        "duplicate_id_count": actual.duplicate_id_count,
        "date_min": actual.date_min,
        "date_max": actual.date_max,
    }
    mismatches = []
    for key, value in checks.items():
        if key in expected and expected[key] != value:
            mismatches.append(f"{key}: expected={expected[key]!r}, actual={value!r}")

    expected_columns = expected.get("columns")
    if expected_columns is not None and list(actual.columns) != list(expected_columns):
        mismatches.append("columns: schema differs from approved manifest")

    if mismatches:
        detail = "; ".join(mismatches)
        raise InputSetError(f"Approved input identity mismatch for {actual.role}: {detail}")


def _hash_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

