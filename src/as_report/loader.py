from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

CSV_ENCODINGS = ("utf-8-sig", "utf-8", "cp949", "euc-kr")

FAILURE_CAUSE_ALIAS = "고장유형"
FAILURE_CAUSE_COLUMN = "고장원인"

REQUIRED_COLUMNS = [
    "*ID",
    "상태",
    "접수일",
    "업무유형",
    "고객사",
    "BOOTH",
    "LINE",
    "공정",
    "ZONE",
    "로보트 NO",
    "로보트 기종",
    "고장원인",
    "라인 중단 시간 (분)",
    "소분류 (고장부품)",
    "중분류",
    "대분류",
    "처리내용/진행상황 (요약)",
    "처리 내용/진행상황 (자세히)",
]


@dataclass(frozen=True)
class FileMetadata:
    path: Path
    file_name: str
    suffix: str
    encoding: str | None = None


@dataclass(frozen=True)
class LoadedData:
    dataframe: pd.DataFrame
    metadata: FileMetadata


class DataLoadError(ValueError):
    """Raised when the source file cannot be loaded or validated."""


def load_input(path: str | Path, required_columns: list[str] | None = None) -> LoadedData:
    source_path = Path(path)
    if not source_path.exists():
        raise DataLoadError(f"입력 파일을 찾을 수 없습니다: {source_path}")
    if not source_path.is_file():
        raise DataLoadError(f"입력 경로가 파일이 아닙니다: {source_path}")

    suffix = source_path.suffix.lower()
    if suffix == ".csv":
        dataframe, encoding = _read_csv_with_fallback(source_path)
    elif suffix in {".xlsx", ".xls"}:
        dataframe = pd.read_excel(source_path)
        encoding = None
    else:
        raise DataLoadError("지원하지 않는 파일 형식입니다. CSV, XLSX, XLS 파일을 사용하세요.")

    dataframe = dataframe.copy()
    dataframe.columns = [str(column).strip() for column in dataframe.columns]
    required = required_columns or REQUIRED_COLUMNS
    _apply_required_column_aliases(dataframe, required)
    validate_required_columns(dataframe, required)

    return LoadedData(
        dataframe=dataframe,
        metadata=FileMetadata(
            path=source_path,
            file_name=source_path.name,
            suffix=suffix,
            encoding=encoding,
        ),
    )


def validate_required_columns(dataframe: pd.DataFrame, required_columns: list[str] | None = None) -> None:
    required = required_columns or REQUIRED_COLUMNS
    missing = [column for column in required if column not in dataframe.columns]
    if missing:
        missing_text = ", ".join(missing)
        raise DataLoadError(f"필수 컬럼이 누락되었습니다: {missing_text}")


def _apply_required_column_aliases(dataframe: pd.DataFrame, required_columns: list[str]) -> None:
    """Populate canonical analysis columns from approved source-header aliases."""
    if FAILURE_CAUSE_COLUMN not in required_columns:
        return
    if FAILURE_CAUSE_COLUMN in dataframe.columns:
        return
    if FAILURE_CAUSE_ALIAS in dataframe.columns:
        dataframe[FAILURE_CAUSE_COLUMN] = dataframe[FAILURE_CAUSE_ALIAS]


def _read_csv_with_fallback(path: Path) -> tuple[pd.DataFrame, str]:
    errors: list[str] = []
    for encoding in CSV_ENCODINGS:
        try:
            return pd.read_csv(path, encoding=encoding), encoding
        except UnicodeDecodeError as error:
            errors.append(f"{encoding}: {error}")
    detail = " | ".join(errors)
    raise DataLoadError(f"CSV 인코딩을 확인할 수 없습니다. 시도한 인코딩: {', '.join(CSV_ENCODINGS)}. {detail}")
