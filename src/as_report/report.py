from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from .cli import ReportOutput, generate_report as generate_cli_report


def generate_report(
    input_path: str | Path,
    output_dir: str | Path,
    period: str,
    year: int | None = None,
    half: str | None = None,
    quarter: str | None = None,
    start: str | None = None,
    end: str | None = None,
) -> ReportOutput:
    """Compatibility wrapper around the CLI report pipeline."""
    return generate_cli_report(
        Namespace(
            input=str(input_path),
            output=str(output_dir),
            period=period,
            year=year,
            half=half,
            quarter=quarter,
            start=start,
            end=end,
        )
    )