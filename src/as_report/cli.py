from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .analyzer import analyze
from .cleaner import clean_data
from .loader import DataLoadError, load_input
from .narrative import build_narrative
from .output import append_report_history, write_run_metadata
from .period import PeriodError, PeriodSelection, build_period_range, filter_by_period
from .provenance import build_raw_only_provenance
from .quality import analyze_raw_data_quality
from .report_excel import write_excel_report
from .report_html import write_html_report


@dataclass(frozen=True)
class ReportOutput:
    html_path: Path
    excel_path: Path
    total_count: int
    period_label: str
    metadata_path: Path
    run_id: str
    input_set_id: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ES 이슈사항보고 데이터로 A/S 분석 리포트를 생성합니다.")
    parser.add_argument("--input", required=True, help="04. ES_ 이슈사항 보고 CSV 또는 Excel 파일 경로")
    parser.add_argument("--period", required=True, choices=("year", "half", "quarter", "custom"), help="분석 기간 유형")
    parser.add_argument("--year", type=int, help="분석 연도")
    parser.add_argument("--half", choices=("H1", "H2", "h1", "h2"), help="반기: H1 또는 H2")
    parser.add_argument("--quarter", choices=("Q1", "Q2", "Q3", "Q4", "q1", "q2", "q3", "q4"), help="분기: Q1~Q4")
    parser.add_argument("--start", help="사용자 지정 시작일: YYYY-MM-DD")
    parser.add_argument("--end", help="사용자 지정 종료일: YYYY-MM-DD")
    parser.add_argument("--output", default="reports", help="리포트 출력 폴더")
    return parser


def generate_report(args: argparse.Namespace) -> ReportOutput:
    loaded = load_input(args.input)
    source_data = clean_data(loaded.dataframe)
    period_range = build_period_range(
        PeriodSelection(
            period=args.period,
            year=args.year,
            half=args.half,
            quarter=args.quarter,
            start=args.start,
            end=args.end,
        )
    )
    period_data = filter_by_period(source_data, period_range)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    created_at = datetime.now().isoformat(timespec="seconds")
    analysis = analyze(source_data, period_data, period_range=period_range, comparison_source_data=source_data, source_period_data=period_data)
    analysis["raw_quality"] = analyze_raw_data_quality(
        loaded.dataframe,
        source_path=loaded.metadata.path,
        start_date=period_range.start_date,
        end_date=period_range.end_date,
    )
    raw_provenance = build_raw_only_provenance(loaded.metadata.path, loaded.dataframe)
    analysis["input_provenance"] = raw_provenance
    narrative_lines = build_narrative(
        analysis,
        period_label=period_range.label,
        start_date=period_range.start_date.isoformat(),
        end_date=period_range.end_date.isoformat(),
    )

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    html_path = output_dir / f"as_report_{period_range.filename_label}.html"
    excel_path = output_dir / f"as_report_{period_range.filename_label}_summary.xlsx"
    metadata_path = output_dir / f"as_report_{period_range.filename_label}_run_metadata.json"

    write_html_report(
        html_path,
        analysis,
        narrative_lines,
        period_label=period_range.label,
        start_date=period_range.start_date.isoformat(),
        end_date=period_range.end_date.isoformat(),
        source_file_name=loaded.metadata.file_name,
    )
    write_excel_report(excel_path, analysis)

    run_metadata = build_cli_run_metadata(
        raw_provenance,
        run_id=run_id,
        period_range=period_range,
        html_path=html_path,
        excel_path=excel_path,
        created_at=created_at,
    )
    write_run_metadata(metadata_path, run_metadata)
    _append_cli_pair_history(
        raw_provenance,
        run_id=run_id,
        period_range=period_range,
        html_path=html_path,
        excel_path=excel_path,
        metadata_path=metadata_path,
        history_base_dir=output_dir,
    )

    return ReportOutput(
        html_path=html_path,
        excel_path=excel_path,
        total_count=analysis["kpi"]["총 접수 건수"],
        period_label=period_range.label,
        metadata_path=metadata_path,
        run_id=run_id,
        input_set_id="",
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        output = generate_report(args)
    except (DataLoadError, PeriodError, ValueError, FileNotFoundError, OSError) as error:
        print("[오류] A/S 리포트 생성에 실패했습니다.")
        print(f"원인: {error}")
        print("조치: 입력 파일 경로, 필수 컬럼, 기간 옵션을 확인한 뒤 다시 실행하세요.")
        return 1

    print("A/S 리포트 생성 완료")
    print(f"분석 기간: {output.period_label}")
    print(f"총 접수 건수: {output.total_count}건")
    print(f"HTML 리포트: {output.html_path}")
    print(f"Excel 요약: {output.excel_path}")
    return 0


def build_cli_run_metadata(
    raw_provenance: dict,
    *,
    run_id: str,
    period_range,
    html_path: Path,
    excel_path: Path,
    created_at: str | None = None,
) -> dict:
    return {
        "run_id": run_id,
        "analysis_mode": "raw_only",
        "input_signature": raw_provenance.get("input_signature", ""),
        "inputs": raw_provenance,
        "period": {
            "type": period_range.period,
            "label": period_range.label,
            "start_date": period_range.start_date.isoformat(),
            "end_date": period_range.end_date.isoformat(),
        },
        "filters": {},
        "output_owner": "cli",
        "outputs": {
            "html_path": str(html_path),
            "excel_path": str(excel_path),
        },
        "created_at": created_at or datetime.now().isoformat(timespec="seconds"),
    }


def _append_cli_pair_history(
    raw_provenance: dict,
    *,
    run_id: str,
    period_range,
    html_path: Path,
    excel_path: Path,
    metadata_path: Path,
    history_base_dir: Path,
) -> None:
    files = raw_provenance.get("files", {})
    raw = files.get("as_raw", {})
    common = {
        "run_id": run_id,
        "input_set_id": "",
        "input_set_signature": raw_provenance.get("input_signature", ""),
        "user_name": "cli",
        "period_type": period_range.period,
        "start_date": period_range.start_date.isoformat(),
        "end_date": period_range.end_date.isoformat(),
        "source_file": raw.get("file_name", ""),
        "source_path": raw.get("path", ""),
        "source_sha256": raw.get("sha256", ""),
        "source_row_count": raw.get("row_count", ""),
        "source_date_min": raw.get("date_min", ""),
        "source_date_max": raw.get("date_max", ""),
        "customer_master_file": "",
        "customer_master_sha256": "",
        "failure_master_file": "",
        "failure_master_sha256": "",
        "run_metadata_path": metadata_path,
        "status": "success",
        "note": "same-run CLI raw-only pair",
    }
    append_report_history({**common, "output_type": "html", "output_path": html_path}, base_dir=history_base_dir)
    append_report_history({**common, "output_type": "excel", "output_path": excel_path}, base_dir=history_base_dir)


if __name__ == "__main__":
    raise SystemExit(main())
