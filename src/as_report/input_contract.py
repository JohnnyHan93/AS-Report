"""Read-only CSV inspection; deliberately not wired into the legacy pipeline.

Availability describes input evidence, not permission to publish a metric.
Raw cell strings and physical line positions are retained without normalization.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .loader import CSV_ENCODINGS, FAILURE_CAUSE_ALIAS, FAILURE_CAUSE_COLUMN, REQUIRED_COLUMNS, DataLoadError

CONTRACT_VERSION = "1"
KNOWN_FIELDS = tuple(dict.fromkeys([
    *REQUIRED_COLUMNS, "접수 내용 (요약)", "접수 내용 (자세히)", "제조사", "유/무상",
]))
# All features are period-scoped. Status counts do not imply completion rules.
FEATURE_FIELDS = {
    "period_records": (),
    "status_distribution": ("상태",),
    "work_type_distribution": ("업무유형",),
    "customer_distribution": ("고객사",),
    "robot_model_distribution": ("로보트 기종",),
    "part_distribution": ("소분류 (고장부품)",),
    "failure_type_distribution": (FAILURE_CAUSE_COLUMN,),
    "claim_manufacturer_review": ("업무유형", "제조사"),
}
TEXT_FIELDS = ("접수 내용 (요약)", "접수 내용 (자세히)",
               "처리내용/진행상황 (요약)", "처리 내용/진행상황 (자세히)")
DATE_FORMATS = tuple(
    date + time
    for date in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d")
    for time in ("", " %H:%M", " %H:%M:%S", "T%H:%M:%S")
)


@dataclass(frozen=True)
class InspectedRow:
    record_number: int
    line_start: int
    line_end: int
    source_key: str
    raw_values: tuple[str, ...]
    original_id: str | None
    id_state: str
    date_state: str
    received_date: str | None


@dataclass(frozen=True)
class InputInspection:
    contract_version: str
    file_name: str
    sha256: str
    encoding: str
    original_headers: tuple[str, ...]
    normalized_headers: tuple[str, ...]
    row_count: int
    rows: tuple[InspectedRow, ...]
    field_mapping: dict[str, str]
    alias_applications: tuple[dict[str, str], ...]
    unmapped_headers: tuple[str, ...]
    structural_errors: tuple[str, ...]
    id_summary: dict[str, Any]
    date_summary: dict[str, Any]
    field_summary: dict[str, dict[str, Any]]
    features: dict[str, dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _date(value: str) -> str | None:
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return None


# csv.field_size_limit is interpreter-global, including unrelated CSV readers.
# Isolate parsing rather than temporarily changing a shared process setting.
_CSV_WORKER = r'''
import csv, io, json, sys
try:
    text = sys.stdin.buffer.read().decode("utf-8")
    csv.field_size_limit(max(1, len(text)))
    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    headers = next(reader, [])
    records = []
    while True:
        start = reader.line_num + 1
        values = next(reader, None)
        if values is None:
            break
        records.append([start, reader.line_num, values])
    result = {"headers": headers, "records": records}
except csv.Error as error:
    result = {"error": "resource" if "field limit" in str(error) else "syntax",
              "line": reader.line_num}
except (MemoryError, OverflowError):
    result = {"error": "resource"}
sys.stdout.buffer.write(json.dumps(result, ensure_ascii=True).encode("ascii"))
'''


def _read_records(text: str) -> tuple[tuple[str, ...], list[tuple[int, int, tuple[str, ...]]]]:
    try:
        process = subprocess.run(
            [sys.executable, "-I", "-c", _CSV_WORKER], input=text.encode("utf-8"),
            capture_output=True, check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, MemoryError) as error:
        raise DataLoadError("CSV 점검 프로세스를 실행할 수 없습니다. 실행 환경과 가용 메모리를 확인하세요.") from error
    if process.returncode:
        raise DataLoadError("CSV 점검 프로세스가 종료되었습니다. 실행 환경과 가용 자원을 확인하세요.")
    result = json.loads(process.stdout)
    if result.get("error") == "resource":
        raise DataLoadError("CSV 크기 또는 메모리 자원 제한으로 점검하지 못했습니다. 원문은 변경하지 않았습니다.")
    if result.get("error") == "syntax":
        raise DataLoadError(f"CSV 구문 오류: 물리 행 {result['line']}")
    return tuple(result["headers"]), [(start, end, tuple(values)) for start, end, values in result["records"]]


def inspect_csv(path: str | Path) -> InputInspection:
    """Inspect one explicitly selected comma-delimited CSV without writing it.

    Missing fields have None counts, not zero. Duplicated headers and malformed
    row widths disable mapping; they never silently overwrite cells. source_key
    is snapshot-local and MUST NOT be used to merge notes across exports.
    """
    source = Path(path)
    if source.suffix.lower() != ".csv" or not source.is_file():
        raise DataLoadError("입력 점검에는 존재하는 CSV 파일을 지정해야 합니다.")
    raw = source.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    for encoding in CSV_ENCODINGS:
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise DataLoadError("CSV 인코딩을 확인할 수 없습니다.")
    headers, records = _read_records(text)
    normalized = tuple(h.strip() for h in headers)
    errors: list[str] = []
    if not headers:
        errors.append("missing_header")
    if any(not h for h in normalized):
        errors.append("blank_header")
    if any(n > 1 for n in Counter(headers).values()):
        errors.append("duplicate_raw_header")
    if any(n > 1 for n in Counter(normalized).values()):
        errors.append("duplicate_normalized_header")
    if any(len(values) != len(headers) for _, _, values in records):
        errors.append("row_width_mismatch")
    mapping: dict[str, str] = {}
    aliases = []
    if not errors:
        mapping = {h: headers[normalized.index(h)] for h in KNOWN_FIELDS if h in normalized}
        if FAILURE_CAUSE_COLUMN not in mapping and FAILURE_CAUSE_ALIAS in normalized:
            origin = headers[normalized.index(FAILURE_CAUSE_ALIAS)]
            mapping[FAILURE_CAUSE_COLUMN] = origin
            aliases.append({"source": origin, "target": FAILURE_CAUSE_COLUMN,
                            "rule": "approved_failure_type_alias"})
    indexes = {field: headers.index(origin) for field, origin in mapping.items()}

    def cell(values: tuple[str, ...], field: str) -> str | None:
        return values[indexes[field]] if field in indexes else None

    ids = [cell(values, "*ID") for _, _, values in records]
    id_counts = Counter(value for value in ids if value is not None and value.strip())
    rows = []
    for number, (start, end, values) in enumerate(records, 1):
        identifier = cell(values, "*ID")
        id_state = ("column_missing" if identifier is None else "missing" if not identifier.strip()
                    else "duplicate" if id_counts[identifier] > 1 else "unique")
        date_text = cell(values, "접수일")
        parsed = _date(date_text) if date_text is not None and date_text.strip() else None
        date_state = ("column_missing" if date_text is None else "missing" if not date_text.strip()
                      else "valid" if parsed is not None else "invalid")
        if errors:
            id_state = date_state = "structure_unavailable"
        rows.append(InspectedRow(number, start, end, f"{digest}:{number}", values,
                                 identifier, id_state, date_state, parsed))
    date_counts = Counter(row.date_state for row in rows)
    dates = [row.received_date for row in rows if row.received_date is not None]
    date_present = "접수일" in mapping
    date_summary = {
        "column_present": date_present,
        "valid": date_counts["valid"] if date_present else None,
        "missing": date_counts["missing"] if date_present else None,
        "invalid": date_counts["invalid"] if date_present else None,
        "unassessed": 0 if date_present else len(rows),
        "min": min(dates) if dates else None, "max": max(dates) if dates else None,
    }
    id_present = "*ID" in mapping
    id_summary = {
        "column_present": id_present,
        "missing": sum(row.id_state == "missing" for row in rows) if id_present else None,
        "unique_nonempty": len(id_counts) if id_present else None,
        "duplicate_values": sum(n > 1 for n in id_counts.values()) if id_present else None,
        "duplicate_rows": sum(n for n in id_counts.values() if n > 1) if id_present else None,
        "unassessed": 0 if id_present else len(rows),
    }
    fields = {}
    for field in KNOWN_FIELDS:
        present = field in mapping
        blank = sum(not (cell(values, field) or "").strip() for _, _, values in records)
        fields[field] = {"column_present": present, "missing": blank if present else None,
                         "nonempty": len(rows) - blank if present else None}
    features = {}
    requirements = {**FEATURE_FIELDS, "follow_up_evidence": ()}
    for name, required in requirements.items():
        reasons = list(errors)
        missing = [f for f in ("접수일", *required) if f not in mapping]
        reasons.extend(f"missing_column:{f}" for f in missing)
        if date_present and not dates:
            reasons.append("no_valid_received_date")
        eligible = [row for row in rows if row.date_state == "valid"]
        if name == "follow_up_evidence":
            if not any(f in mapping for f in TEXT_FIELDS):
                reasons.append("missing_evidence_columns")
            eligible = [row for row in eligible if any(
                (cell(row.raw_values, f) or "").strip() for f in TEXT_FIELDS)]
        else:
            eligible = [row for row in eligible if all(
                (cell(row.raw_values, f) or "").strip() for f in required)]
        if not eligible and not reasons:
            reasons.append("no_usable_rows")
        available = not reasons
        features[name] = {"status": "available" if available else "unavailable",
                          "reasons": reasons, "usable_rows": len(eligible) if not errors and not missing
                          and "missing_evidence_columns" not in reasons else None,
                          "note": "input_evidence_only_not_metric_approval"}
    mapped_sources = set(mapping.values())
    return InputInspection(CONTRACT_VERSION, source.name, digest, encoding, headers, normalized,
                           len(rows), tuple(rows), mapping, tuple(aliases),
                           tuple(h for h in headers if h not in mapped_sources), tuple(errors),
                           id_summary, date_summary, fields, features)
