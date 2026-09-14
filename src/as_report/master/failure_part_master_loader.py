from __future__ import annotations

from pathlib import Path

from as_report.loader import LoadedData, load_input

FAILURE_PART_REQUIRED_COLUMNS = ["*ID", "품명", "중분류", "대분류", "검색용", "제조사"]


def load_failure_part_master(path: str | Path) -> LoadedData:
    """Load the failure-part classification master CSV without modifying it."""
    return load_input(path, required_columns=FAILURE_PART_REQUIRED_COLUMNS)
