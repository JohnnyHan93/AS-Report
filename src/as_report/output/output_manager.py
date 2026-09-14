from __future__ import annotations

import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

HISTORY_COLUMNS = [
    "created_at",
    "run_id",
    "input_set_id",
    "input_set_signature",
    "user_name",
    "period_type",
    "start_date",
    "end_date",
    "source_file",
    "source_path",
    "source_sha256",
    "source_row_count",
    "source_date_min",
    "source_date_max",
    "customer_master_file",
    "customer_master_sha256",
    "failure_master_file",
    "failure_master_sha256",
    "run_metadata_path",
    "output_type",
    "output_path",
    "status",
    "note",
]

WINDOWS_INVALID_CHARS = r'<>:"/\|?*'
RESERVED_WINDOWS_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}


def sanitize_user_name(user_name: str | None) -> str:
    """
    Convert a user-entered name to a safe Windows path segment.

    Korean names are kept. Characters that are invalid in Windows paths are
    replaced with underscores. Empty values become default_user.
    """
    text = "" if user_name is None else str(user_name).strip()
    if not text:
        return "default_user"

    translated = "".join("_" if char in WINDOWS_INVALID_CHARS or ord(char) < 32 else char for char in text)
    translated = re.sub(r"\s+", "_", translated)
    translated = translated.strip(" ._")
    if not translated or translated.upper() in RESERVED_WINDOWS_NAMES:
        return "default_user"
    return translated


def get_run_timestamp() -> str:
    """Return timestamp string: YYYYMMDD_HHMMSS."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def get_run_date() -> str:
    """Return date string: YYYYMMDD."""
    return datetime.now().strftime("%Y%m%d")


def build_user_output_dirs(base_dir: str | Path = "reports", user_name: str | None = None) -> dict[str, Path]:
    """
    Create and return user-separated output directories.

    Return keys: user_root, reports, quality, standardization, master_analysis,
    proposal, auto_fill_preview, logs, index.
    """
    base_path = Path(base_dir)
    safe_user = sanitize_user_name(user_name)
    user_root = base_path / "users" / safe_user / get_run_date()
    directories = {
        "user_root": user_root,
        "reports": user_root / "reports",
        "quality": user_root / "quality",
        "standardization": user_root / "standardization",
        "master_analysis": user_root / "master_analysis",
        "proposal": user_root / "proposal",
        "auto_fill_preview": user_root / "auto_fill_preview",
        "logs": user_root / "logs",
        "index": base_path / "_index",
    }
    for directory in directories.values():
        directory.mkdir(parents=True, exist_ok=True)
    return directories


def build_timestamped_filename(prefix: str, suffix: str, timestamp: str | None = None) -> str:
    """
    Return a safe timestamped filename.

    Example: AS_Report_year_20260101_20261231_20260619_101530.html
    """
    safe_prefix = _safe_filename_part(prefix)
    safe_suffix = suffix if suffix.startswith(".") else f".{suffix}"
    safe_suffix = _safe_suffix(safe_suffix)
    return f"{safe_prefix}_{timestamp or get_run_timestamp()}{safe_suffix}"


def append_report_history(record: dict[str, Any], base_dir: str | Path = "reports") -> Path:
    """
    Append one row to reports\\_index\\report_history.csv.

    Unknown record keys are ignored so the index remains stable.
    """
    index_dir = Path(base_dir) / "_index"
    index_dir.mkdir(parents=True, exist_ok=True)
    history_path = index_dir / "report_history.csv"

    row = {column: "" for column in HISTORY_COLUMNS}
    row.update({key: _stringify(value) for key, value in record.items() if key in HISTORY_COLUMNS})
    row["created_at"] = row["created_at"] or datetime.now().isoformat(timespec="seconds")
    row["user_name"] = sanitize_user_name(row["user_name"])

    _upgrade_history_schema(history_path)
    file_exists = history_path.exists() and history_path.stat().st_size > 0
    with history_path.open("a", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=HISTORY_COLUMNS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
    return history_path


def write_run_metadata(path: str | Path, metadata: dict[str, Any]) -> Path:
    """Write reproducibility metadata beside generated run outputs."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, default=_stringify),
        encoding="utf-8",
    )
    return output_path


def read_report_history(base_dir: str | Path = "reports", limit: int = 10) -> list[dict[str, str]]:
    """
    Read recent generated-output history from reports\\_index\\report_history.csv.

    This is display-only: it does not create directories, recalculate reports, or
    check whether recorded output files still exist.
    """
    if limit <= 0:
        return []

    base_path = Path(base_dir)
    history_path = base_path / "_index" / "report_history.csv"
    if not history_path.exists() or history_path.stat().st_size == 0:
        return []

    rows: list[dict[str, str]] = []
    try:
        with history_path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            for record in reader:
                row = {column: _stringify(record.get(column, "")) for column in HISTORY_COLUMNS}
                if not _is_history_output_path_allowed(row["output_path"]):
                    continue
                rows.append(row)
    except (csv.Error, OSError, UnicodeDecodeError):
        return []

    rows.reverse()
    return rows[:limit]


def _safe_filename_part(value: str) -> str:
    text = sanitize_user_name(value)
    text = re.sub(r"_+", "_", text)
    return text or "output"


def _safe_suffix(value: str) -> str:
    cleaned = "".join("_" if char in WINDOWS_INVALID_CHARS or ord(char) < 32 else char for char in value.strip())
    if not cleaned.startswith("."):
        cleaned = f".{cleaned}"
    return cleaned


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _upgrade_history_schema(history_path: Path) -> None:
    """Preserve existing rows when provenance columns are added."""
    if not history_path.exists() or history_path.stat().st_size == 0:
        return

    try:
        with history_path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            current_columns = list(reader.fieldnames or [])
            if current_columns == HISTORY_COLUMNS:
                return
            existing_rows = list(reader)
    except (csv.Error, OSError, UnicodeDecodeError) as error:
        raise OSError(f"Report history schema could not be read: {history_path}") from error

    migrated_rows = [
        {column: _stringify(row.get(column, "")) for column in HISTORY_COLUMNS}
        for row in existing_rows
    ]
    temp_path = history_path.with_suffix(f"{history_path.suffix}.tmp")
    try:
        with temp_path.open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=HISTORY_COLUMNS)
            writer.writeheader()
            writer.writerows(migrated_rows)
        temp_path.replace(history_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _is_history_output_path_allowed(output_path: str) -> bool:
    text = output_path.strip()
    if not text:
        return False

    normalized = text.replace("/", "\\").strip("\\").lower()
    protected_prefixes = (
        "data\\raw",
        "data\\master",
        "reports\\validation",
    )
    if any(normalized == prefix or normalized.startswith(f"{prefix}\\") for prefix in protected_prefixes):
        return False

    protected_segments = (
        "\\data\\raw\\",
        "\\data\\master\\",
        "\\reports\\validation\\",
    )
    padded = f"\\{normalized}\\"
    return not any(segment in padded for segment in protected_segments)
