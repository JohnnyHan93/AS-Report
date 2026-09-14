from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

import pandas as pd


def build_raw_only_provenance(path: str | Path, dataframe: pd.DataFrame) -> dict[str, Any]:
    """Build reproducibility metadata for one 04 ES issue Raw input."""
    source_path = Path(path)
    stat = source_path.stat()
    id_values = _non_empty_text(dataframe.get("*ID", pd.Series(dtype="object")))
    dates = pd.to_datetime(dataframe.get("접수일", pd.Series(dtype="object")), errors="coerce").dropna()
    raw_identity = {
        "role": "as_raw",
        "path": str(source_path),
        "file_name": source_path.name,
        "size": stat.st_size,
        "modified_time_ns": stat.st_mtime_ns,
        "sha256": _hash_file(source_path),
        "row_count": int(len(dataframe)),
        "column_count": int(len(dataframe.columns)),
        "unique_id_count": int(id_values.nunique()),
        "duplicate_id_count": int(len(id_values) - id_values.nunique()),
        "columns": [str(column) for column in dataframe.columns],
        "date_min": dates.min().date().isoformat() if not dates.empty else "",
        "date_max": dates.max().date().isoformat() if not dates.empty else "",
    }
    signature_source = "|".join(
        (
            raw_identity["path"],
            raw_identity["sha256"],
            str(raw_identity["row_count"]),
            raw_identity["date_min"],
            raw_identity["date_max"],
        )
    )
    return {
        "analysis_mode": "raw_only",
        "input_signature": sha256(signature_source.encode("utf-8")).hexdigest(),
        "files": {"as_raw": raw_identity},
    }


def _non_empty_text(series: pd.Series) -> pd.Series:
    values = series.dropna().astype(str).str.strip()
    return values.loc[values.ne("")]


def _hash_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
