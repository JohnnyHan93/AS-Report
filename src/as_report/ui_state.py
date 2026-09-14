from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
MASTER_DIR = PROJECT_ROOT / "data" / "master"
LEGACY_RAW_FILE = RAW_DIR / "04. ES_ 이슈사항 보고_20260130 (1).csv"
RAW_FILE_PATTERN = "04. ES_ 이슈사항 보고*.csv"
FAILURE_PART_MASTER_PATTERN = "00. ES_고장부품 분류*.csv"
CUSTOMER_ROBOT_MASTER_PATTERN = "08. ES_고객사 로보트 리스트*.csv"
REPORTS_DIR = PROJECT_ROOT / "reports"
FILTER_COLUMNS = ["고객사", "업무유형구분", "상태", "대분류", "중분류", "로보트 기종", "처리사원"]


def list_raw_files(raw_dir: Path = RAW_DIR) -> list[Path]:
    """Return matching Raw files in stable newest-filename order without selecting one."""
    candidates = list(raw_dir.glob(RAW_FILE_PATTERN))
    return sorted(
        candidates,
        key=lambda path: (parse_filename_date(path.name) or -1, path.name),
        reverse=True,
    )


def resolve_default_raw_file(raw_dir: Path = RAW_DIR, legacy_file: Path = LEGACY_RAW_FILE) -> Path | None:
    """Return a default only when the Raw choice is unambiguous.

    A filename date does not establish that an export is cumulative. When more
    than one candidate exists, the Streamlit user must select the intended Raw
    file explicitly instead of silently switching to the newest filename.
    """
    if legacy_file.exists():
        return legacy_file
    candidates = list_raw_files(raw_dir)
    return candidates[0] if len(candidates) == 1 else None


def resolve_latest_file(directory: Path, pattern: str) -> Path | None:
    """Return the latest matching file by YYYYMMDD in filename, with name fallback."""
    candidates = sorted(directory.glob(pattern))
    if not candidates:
        return None

    dated_candidates = [(date_value, path) for path in candidates if (date_value := parse_filename_date(path.name)) is not None]
    if dated_candidates:
        return max(dated_candidates, key=lambda item: (item[0], item[1].name))[1]
    return candidates[-1]


def parse_filename_date(filename: str) -> int | None:
    """Extract a YYYYMMDD date token from a filename."""
    matches = re.findall(r"(?<!\d)(20\d{6})(?!\d)", filename)
    if not matches:
        return None
    return int(matches[-1])


def resolve_failure_part_master_file(master_dir: Path = MASTER_DIR) -> Path | None:
    return resolve_latest_file(master_dir, FAILURE_PART_MASTER_PATTERN)


def resolve_customer_robot_master_file(master_dir: Path = MASTER_DIR) -> Path | None:
    return resolve_latest_file(master_dir, CUSTOMER_ROBOT_MASTER_PATTERN)


DEFAULT_RAW_FILE = resolve_default_raw_file()
@dataclass(frozen=True)
class InputSource:
    path: Path
    display_name: str
    is_temporary: bool = False
