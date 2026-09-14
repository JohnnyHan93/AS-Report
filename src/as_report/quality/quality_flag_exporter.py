from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from as_report.output import build_timestamped_filename, get_run_timestamp

QUALITY_FLAG_EXPORT_COLUMNS = [
    "*ID",
    "접수일",
    "고객사",
    "업무유형",
    "보완필요여부",
    "보완우선순위",
    "보완필요필드",
    "보완메모",
    "대상구분_정제",
    "위치상태_정제",
    "로보트대상수_정제",
    "로봇대상수_정제",
    "분류상태_정제",
]


def export_quality_flags_csv(quality_result: dict[str, Any], output_dir: str | Path, timestamp: str | None = None) -> str:
    """Export raw quality flags to CSV without requiring every optional column."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    csv_path = output_path / build_timestamped_filename("raw_data_quality_flags", ".csv", timestamp or get_run_timestamp())

    quality_flags = quality_result.get("quality_flags_df", pd.DataFrame())
    if quality_flags.empty:
        pd.DataFrame(columns=QUALITY_FLAG_EXPORT_COLUMNS).to_csv(csv_path, index=False, encoding="utf-8-sig")
        return str(csv_path)

    output = quality_flags.copy()
    if "로봇대상수_정제" not in output.columns and "로보트대상수_정제" in output.columns:
        output["로봇대상수_정제"] = output["로보트대상수_정제"]
    columns = [column for column in QUALITY_FLAG_EXPORT_COLUMNS if column in output.columns]
    output[columns].to_csv(csv_path, index=False, encoding="utf-8-sig")
    return str(csv_path)
