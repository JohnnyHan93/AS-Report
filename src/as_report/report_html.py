from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
from jinja2 import Environment, FileSystemLoader, select_autoescape
from plotly.offline import get_plotlyjs

from .analyzer import DOWNTIME_COLUMN
from .narrative import build_quality_notes
from .repeat_issue import filter_main_repeat_issues
from .reporting.display_formatters import (
    evaluate_repeat_condition_quality,
    format_count,
    format_minutes,
    format_percent,
    format_repeat_condition_display,
)

TEMPLATE_DIR = Path(__file__).parent / "templates"
LAYOUT_VERSION = "AS17_BRIEFING"
OPEN_ISSUE_HTML_COLUMNS = [
    "접수일",
    "상태",
    "업무유형",
    "고객사",
    "BOOTH",
    "LINE",
    "공정",
    "로보트 NO",
    "로보트 기종",
    "고장원인",
    "소분류 (고장부품)",
    "중분류",
    "대분류",
    "처리사원",
    "접수 내용 (요약)",
    "처리내용/진행상황 (요약)",
]
DOWNTIME_ISSUE_HTML_COLUMNS = [
    "접수일",
    "상태",
    "업무유형",
    "고객사",
    "BOOTH",
    "LINE",
    "공정",
    "로보트 NO",
    "로보트 기종",
    "고장원인",
    DOWNTIME_COLUMN,
    "소분류 (고장부품)",
    "중분류",
    "대분류",
    "처리사원",
    "접수 내용 (요약)",
    "처리내용/진행상황 (요약)",
]
ISSUE_FULL_TEXT_COLUMNS = {"접수 내용 (요약)", "처리내용/진행상황 (요약)", "접수내용", "조치이력"}
TEXT_COLUMNS = ISSUE_FULL_TEXT_COLUMNS | {"고장원인"}
REPORT_COLORS = {
    "blue": "#2563eb",
    "green": "#16a34a",
    "amber": "#f59e0b",
    "red": "#dc2626",
    "purple": "#7c3aed",
    "cyan": "#0891b2",
    "slate": "#475569",
    "gray": "#64748b",
    "muted": "#94a3b8",
}
CHART_COLORS = [
    REPORT_COLORS["blue"],
    REPORT_COLORS["green"],
    REPORT_COLORS["amber"],
    REPORT_COLORS["purple"],
    REPORT_COLORS["cyan"],
    REPORT_COLORS["slate"],
    REPORT_COLORS["red"],
    REPORT_COLORS["gray"],
]
COMPARISON_COLOR_MAP = {
    "전년 동기 값": REPORT_COLORS["slate"],
    "직전 기간 값": REPORT_COLORS["amber"],
    "현재 기간 값": REPORT_COLORS["blue"],
}


def write_html_report(
    path: Path,
    analysis: dict[str, Any],
    narrative_lines: list[str],
    period_label: str,
    start_date: str,
    end_date: str,
    source_file_name: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("report_template.html")
    tables = analysis["tables"]
    charts = build_charts(tables)
    comparison = analysis.get("comparison", pd.DataFrame())
    repeat_issues = analysis.get("repeat_issues", pd.DataFrame())
    main_repeat_issues = filter_main_repeat_issues(repeat_issues)
    charts["comparison"] = comparison_chart(comparison)
    charts["repeat_issues"] = repeat_issue_chart(main_repeat_issues.head(10))
    raw_quality = analysis.get("raw_quality", {})
    charts.update(build_appendix_charts(tables, comparison, raw_quality))
    legacy_features = analysis.get("legacy_features", {})
    charts.update(build_legacy_feature_charts(legacy_features))
    quality_feedback = analysis.get("quality_feedback", {})
    charts.update(build_quality_feedback_charts(quality_feedback))
    safe_narrative_lines = [normalize_report_text(line) for line in narrative_lines]
    html = template.render(
        layout_version=LAYOUT_VERSION,
        title="A/S 분석 리포트",
        period_label=period_label,
        start_date=start_date,
        end_date=end_date,
        source_file_name=source_file_name,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        kpi=build_kpi_display(analysis["kpi"]),
        kpi_groups=build_kpi_groups(analysis),
        dashboard_cards=build_dashboard_cards(analysis),
        quality=build_quality_display(analysis["quality"]),
        raw_quality_available=bool(raw_quality),
        raw_quality_cards=build_raw_quality_cards(raw_quality),
        comparison_note=comparison_note(comparison),
        narrative_lines=safe_narrative_lines,
        charts=charts,
        tables=build_html_tables(tables),
        legacy_tables=build_legacy_html_tables(legacy_features),
        quality_feedback_tables=build_quality_feedback_html_tables(quality_feedback),
        legacy_notes={
            "claim": normalize_report_text(legacy_features.get("claim_note", "입력값 기준 검토용입니다.")),
            "completion": normalize_report_text(legacy_features.get("completion_note", "처리 상태 입력값 기준 업무 처리 현황입니다.")),
        },
        quality_feedback_note=normalize_report_text(quality_feedback.get("quality_feedback_note", "입력값 기준 검토 후보입니다.")),
        comparison_table=comparison_table_to_html(comparison),
        repeat_issues_table=repeat_issue_table_to_html(main_repeat_issues.head(20)),
        repeat_issue_count=len(main_repeat_issues),
        repeat_issue_total_count=len(repeat_issues),
        issue_counts={
            "open": len(tables["진행중/미완료 이슈 목록"]),
            "downtime_top": len(tables["라인 중단 시간 TOP 20 이슈 목록"]),
        },
        plotly_js=get_plotlyjs(),
        no_data=analysis["kpi"]["총 접수 건수"] == 0,
    )
    path.write_text(html, encoding="utf-8")


def build_dashboard_cards(analysis: dict[str, Any]) -> list[dict[str, str]]:
    kpi = analysis["kpi"]
    tables = analysis["tables"]
    top_work_type = top_label(tables.get("업무유형구분별 접수 건수"), "업무유형구분", "접수 건수")
    top_customer = top_label(tables.get("고객사별 접수 건수 TOP 20"), "고객사", "접수 건수")
    top_category = top_label(tables.get("대분류별 접수 건수"), "대분류", "접수 건수")
    return [
        {"label": "총 접수", "value": format_count(kpi["총 접수 건수"]), "detail": "선택 기간 기준", "tone": "primary"},
        {"label": "처리완료율", "value": format_percent(kpi["처리완료율"]), "detail": f"완료 {format_count(kpi['처리완료 건수'])}", "tone": "green"},
        {"label": "미완료", "value": format_count(kpi["미완료 건수"]), "detail": "진행중/미완료 이슈", "tone": "amber"},
        {"label": "라인 중단 시간(입력 건 기준)", "value": format_minutes(kpi["라인 중단 총 시간"]), "detail": f"입력 {format_count(kpi['라인 중단 시간 입력 건수'])}", "tone": "red"},
        {"label": "주요 업무유형", "value": top_work_type[0], "detail": count_text(top_work_type[1]), "tone": "blue"},
        {"label": "주요 고객사", "value": top_customer[0], "detail": count_text(top_customer[1]), "tone": "slate"},
        {"label": "주요 대분류", "value": top_category[0], "detail": count_text(top_category[1]), "tone": "slate"},
        build_raw_quality_dashboard_card(analysis.get("raw_quality")),
    ]


def build_kpi_display(kpi: dict[str, Any]) -> dict[str, str]:
    output: dict[str, str] = {}
    for key, value in kpi.items():
        if "율" in key:
            output[key] = format_percent(value)
        elif "건수" in key:
            output[key] = format_count(value)
        elif "시간" in key:
            output[key] = format_minutes(value)
        else:
            output[key] = str(value)
    return output


def build_kpi_groups(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    kpi = analysis["kpi"]
    tables = analysis["tables"]
    repeat_count = len(filter_main_repeat_issues(analysis.get("repeat_issues", pd.DataFrame())))
    repeat_total_count = len(analysis.get("repeat_issues", pd.DataFrame()))
    top_major = top_label(tables.get("대분류별 접수 건수"), "대분류", "접수 건수")
    top_middle = top_label(tables.get("중분류별 접수 건수"), "중분류", "접수 건수")
    top_part = top_label(tables.get("소분류 고장부품별 접수 건수 TOP 20"), "소분류 (고장부품)", "접수 건수")
    return [
        {
            "title": "접수/처리 현황",
            "items": [
                {"label": "총 접수 건수", "value": format_count(kpi.get("총 접수 건수", 0))},
                {"label": "처리완료 건수", "value": format_count(kpi.get("처리완료 건수", 0))},
                {"label": "미완료 건수", "value": format_count(kpi.get("미완료 건수", 0))},
                {"label": "처리완료율", "value": format_percent(kpi.get("처리완료율", 0))},
            ],
        },
        {
            "title": "이슈 성격",
            "items": [
                {"label": "긴급방문 건수", "value": format_count(kpi.get("긴급방문 건수", 0))},
                {"label": "주요 대분류", "value": f"{top_major[0]} ({count_text(top_major[1])})"},
                {"label": "주요 중분류", "value": f"{top_middle[0]} ({count_text(top_middle[1])})"},
                {"label": "주요 소분류", "value": f"{top_part[0]} ({count_text(top_part[1])})"},
            ],
        },
        {
            "title": "라인 영향",
            "items": [
                {"label": "라인 중단 시간(입력 건 기준)", "value": format_minutes(kpi.get("라인 중단 총 시간", 0))},
                {"label": "라인 중단 입력 건수", "value": format_count(kpi.get("라인 중단 시간 입력 건수", 0))},
                {"label": "라인 중단 발생 건수", "value": format_count(kpi.get("라인 중단 발생 건수", 0))},
                {"label": "라인 중단 최대 시간(입력 건 기준)", "value": format_minutes(kpi.get("라인 중단 최대 시간", 0))},
            ],
        },
        {
            "title": "반복 검토 후보",
            "items": [
                {"label": "메인 표시 반복 검토 후보 수", "value": format_count(repeat_count)},
                {"label": "전체 반복 검토 후보 수(Excel 기준)", "value": format_count(repeat_total_count)},
                {"label": "메인 반복 검토 기준", "value": "고객사 + 중분류 + 소분류"},
            ],
        },
    ]


def build_quality_display(quality: dict[str, Any]) -> dict[str, Any]:
    label_map = {
        "전체 원본 건수": "전체 원본 행 수",
        "분석 대상 건수": "선택 기간 분석 대상 행 수",
    }
    return {label_map.get(key, key): value for key, value in quality.items()}


def build_raw_quality_dashboard_card(raw_quality: dict[str, Any] | None) -> dict[str, str]:
    if not raw_quality:
        return {"label": "데이터 품질 상태", "value": "미확인", "detail": "Raw 품질 검증 결과 없음", "tone": "amber"}
    summary = raw_quality.get("summary", {})
    status = raw_quality.get("status", "미확인")
    tone = "green" if status == "PASS" else "red" if status == "BLOCKED" else "amber"
    return {
        "label": "데이터 품질 상태",
        "value": display_raw_quality_status(status),
        "detail": f"보완 필요 {format_count(summary.get('보완 필요 건수', 0))} / 우선순위 상 {format_count(summary.get('우선순위 상', 0))}",
        "tone": tone,
    }


def build_html_tables(tables: dict[str, pd.DataFrame]) -> dict[str, str]:
    html_tables: dict[str, str] = {}
    balanced_top_tables = {
        "대분류별 접수 건수",
        "중분류별 접수 건수",
        "소분류 고장부품별 접수 건수 TOP 20",
        "로보트 기종별 접수 건수",
        "BOOTH별 접수 건수",
        "LINE별 접수 건수",
        "공정별 접수 건수",
        "고장원인별 접수 건수",
        "대분류별 라인 중단 시간",
        "소분류 고장부품별 라인 중단 시간 TOP 20",
    }
    for name, dataframe in tables.items():
        if name == "진행중/미완료 이슈 목록":
            html_tables[name] = issue_table_to_html(dataframe, OPEN_ISSUE_HTML_COLUMNS)
        elif name == "라인 중단 시간 TOP 20 이슈 목록":
            html_tables[name] = issue_table_to_html(
                _positive_downtime_rows(dataframe, DOWNTIME_COLUMN),
                DOWNTIME_ISSUE_HTML_COLUMNS,
                empty_message="라인 중단 영향 항목이 없어 표시할 데이터가 없습니다.",
            )
        elif name in balanced_top_tables:
            display = _positive_downtime_rows(dataframe, "라인 중단 시간") if "라인 중단 시간" in dataframe.columns else dataframe
            html_tables[name] = dataframe_to_html(display.head(10), empty_message="라인 중단 영향 항목이 없어 표시할 데이터가 없습니다.")
        else:
            html_tables[name] = dataframe_to_html(dataframe)
    return html_tables


def build_charts(tables: dict[str, pd.DataFrame]) -> dict[str, str]:
    charts: dict[str, str] = {}
    charts["monthly_count"] = line_chart(tables["월별 접수 건수"], "기간_연월", "접수 건수", "월별 접수 추이")
    charts["monthly_downtime"] = bar_chart(tables["월별 라인 중단 시간"], "기간_연월", "라인 중단 시간", "월별 라인 중단 시간(입력 건 기준)")
    charts["work_type"] = donut_chart(tables["업무유형구분별 접수 건수"], "업무유형구분", "접수 건수", "업무유형 구성")
    charts["status"] = donut_chart(tables["상태별 접수 건수"], "상태", "접수 건수", "처리 상태 구성")
    charts["customer_top10"] = horizontal_bar_chart(tables["고객사별 접수 건수 TOP 20"].head(10), "고객사", "접수 건수", "고객사 TOP 10")
    customer_downtime = _positive_downtime_rows(tables["고객사별 라인 중단 시간 TOP 20"], "라인 중단 시간").head(10)
    charts["customer_downtime"] = horizontal_bar_chart(customer_downtime, "고객사", "라인 중단 시간", "고객사별 라인 중단 시간 TOP 10(입력 건 기준)")
    charts["category"] = horizontal_bar_chart(tables["대분류별 접수 건수"], "대분류", "접수 건수", "대분류별 접수 건수")
    charts["part_top10"] = horizontal_bar_chart(tables["소분류 고장부품별 접수 건수 TOP 20"].head(10), "소분류 (고장부품)", "접수 건수", "소분류 고장부품 TOP 10")
    return charts


def build_appendix_charts(
    tables: dict[str, pd.DataFrame],
    comparison: pd.DataFrame,
    raw_quality: dict[str, Any],
) -> dict[str, str]:
    return {
        "appendix_comparison": comparison_chart(comparison),
        "appendix_customer_top10": horizontal_bar_chart(
            tables["고객사별 접수 건수 TOP 20"].head(10),
            "고객사",
            "접수 건수",
            "고객사 상세 TOP 10",
        ),
        "appendix_equipment_top10": appendix_equipment_chart(tables),
        "appendix_open_issues": issue_summary_chart(
            tables["진행중/미완료 이슈 목록"],
            ["상태", "고객사"],
            "미완료 이슈 요약",
        ),
        "appendix_raw_quality": raw_quality_summary_chart(raw_quality),
    }


def build_legacy_feature_charts(legacy_features: dict[str, Any]) -> dict[str, str]:
    return {
        "completion_trend": line_chart(
            legacy_features.get("monthly_completion_trend", pd.DataFrame()),
            "기간_연월",
            "처리완료 건수",
            "월별 처리완료 건수",
        ),
        "claim_manufacturer": horizontal_bar_chart(
            legacy_features.get("claim_by_manufacturer", pd.DataFrame()).head(10),
            "제조사",
            "접수 건수",
            "제조사별 클레임/부품수리 접수 TOP 10",
        ),
    }


def build_quality_feedback_charts(quality_feedback: dict[str, Any]) -> dict[str, str]:
    return {
        "quality_feedback_type": horizontal_bar_chart(
            quality_feedback.get("quality_feedback_by_candidate_type", pd.DataFrame()),
            "검토 후보 유형",
            "관련 건수",
            "품질 피드백 검토 후보 유형별 건수",
        )
    }


def build_legacy_html_tables(legacy_features: dict[str, Any]) -> dict[str, str]:
    return {
        "claim_summary": dataframe_to_html(legacy_features.get("claim_summary", pd.DataFrame())),
        "claim_by_manufacturer": dataframe_to_html(legacy_features.get("claim_by_manufacturer", pd.DataFrame()).head(10)),
        "claim_by_paid_type": dataframe_to_html(legacy_features.get("claim_by_paid_type", pd.DataFrame())),
        "claim_by_part_category": dataframe_to_html(legacy_features.get("claim_by_part_category", pd.DataFrame()).head(20)),
        "claim_issue_list": issue_table_to_html(
            legacy_features.get("claim_issue_list", pd.DataFrame()).head(30),
            legacy_features.get("claim_issue_list", pd.DataFrame()).columns.tolist(),
        ),
        "completion_kpi": dataframe_to_html(legacy_features.get("completion_kpi", pd.DataFrame())),
        "monthly_completion_trend": dataframe_to_html(legacy_features.get("monthly_completion_trend", pd.DataFrame())),
        "open_status_breakdown": dataframe_to_html(legacy_features.get("open_status_breakdown", pd.DataFrame())),
    }


def build_quality_feedback_html_tables(quality_feedback: dict[str, Any]) -> dict[str, str]:
    issue_preview = quality_feedback.get("quality_feedback_issue_preview", pd.DataFrame())
    return {
        "summary": dataframe_to_html(quality_feedback.get("quality_feedback_summary", pd.DataFrame())),
        "type_summary": dataframe_to_html(quality_feedback.get("quality_feedback_by_candidate_type", pd.DataFrame())),
        "claim_candidates": dataframe_to_html(quality_feedback.get("quality_feedback_claim_candidates", pd.DataFrame()).head(20)),
        "missing_field_candidates": dataframe_to_html(quality_feedback.get("quality_feedback_missing_field_candidates", pd.DataFrame()).head(30)),
        "part_category_candidates": dataframe_to_html(quality_feedback.get("quality_feedback_part_category_candidates", pd.DataFrame()).head(20)),
        "issue_preview": issue_table_to_html(issue_preview.head(30), issue_preview.columns.tolist()),
    }


def appendix_equipment_chart(tables: dict[str, pd.DataFrame]) -> str:
    part_table = tables.get("소분류 고장부품별 접수 건수 TOP 20", pd.DataFrame()).head(10)
    if not _no_chart_data(part_table, "소분류 (고장부품)", "접수 건수"):
        return horizontal_bar_chart(part_table, "소분류 (고장부품)", "접수 건수", "설비/장비 상세 TOP 10")

    category_table = tables.get("대분류별 접수 건수", pd.DataFrame()).head(10)
    if not _no_chart_data(category_table, "대분류", "접수 건수"):
        return horizontal_bar_chart(category_table, "대분류", "접수 건수", "설비/장비 상세 TOP 10")

    return empty_state("설비/장비 상세 차트로 표시할 데이터가 없습니다.")


def issue_summary_chart(dataframe: pd.DataFrame, candidate_columns: list[str], title: str) -> str:
    if dataframe.empty:
        return empty_state("표시할 미완료 이슈 데이터가 없습니다.")

    for column in candidate_columns:
        if column not in dataframe.columns:
            continue
        series = dataframe[column].fillna("미입력").astype(str).str.strip()
        series = series.replace("", "미입력")
        counts = series.value_counts().head(10)
        if counts.empty or counts.sum() == 0:
            continue
        display = pd.DataFrame({"항목": counts.index.tolist(), "건수": counts.values.tolist()})
        return horizontal_bar_chart(display, "항목", "건수", title)

    return empty_state("미완료 이슈 요약 차트로 표시할 기준 컬럼이 없습니다.")


def raw_quality_summary_chart(raw_quality: dict[str, Any]) -> str:
    if not raw_quality:
        return empty_state("Raw 품질 검증 결과가 없습니다.")

    summary = raw_quality.get("summary", {})
    rows = [
        {"항목": "분석 대상 행 수", "건수": summary.get("분석 대상 건수", 0)},
        {"항목": "보완 필요 행 수", "건수": summary.get("보완 필요 건수", 0)},
        {"항목": "우선순위 상", "건수": summary.get("우선순위 상", 0)},
        {"항목": "우선순위 중", "건수": summary.get("우선순위 중", 0)},
        {"항목": "우선순위 하", "건수": summary.get("우선순위 하", 0)},
        {"항목": "조건부 제외", "건수": summary.get("조건부 제외 건수", 0)},
    ]
    display = pd.DataFrame(rows)
    display["건수"] = pd.to_numeric(display["건수"], errors="coerce").fillna(0)
    if display["건수"].sum() == 0:
        return empty_state("Raw 품질 요약 차트로 표시할 데이터가 없습니다.")
    return horizontal_bar_chart(display, "항목", "건수", "Raw 품질 요약")


def comparison_chart(dataframe: pd.DataFrame) -> str:
    melted, value_columns = comparison_chart_frame(dataframe)
    if melted.empty:
        return empty_state("비교 가능한 데이터가 없습니다.")

    fig = px.bar(
        melted,
        x="항목",
        y="값",
        color="비교 기준",
        barmode="group",
        title="주요 KPI 비교",
        category_orders={"비교 기준": value_columns},
        color_discrete_map=COMPARISON_COLOR_MAP,
    )
    fig.update_traces(texttemplate="%{y:,.0f}", textposition="outside", cliponaxis=False)
    apply_chart_layout(fig, height=380)
    fig.update_layout(xaxis={"automargin": True}, legend={"orientation": "h", "y": -0.2})
    return chart_html(fig)


def comparison_chart_frame(dataframe: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    required = {"항목", "현재 기간 값", "전년 동기 값", "직전 기간 값"}
    if dataframe.empty or not required.issubset(dataframe.columns):
        return pd.DataFrame(columns=["항목", "비교 기준", "값"]), []

    metrics = ["총 접수 건수", "처리완료 건수", "미완료 건수", "긴급방문 건수", "라인 중단 발생 건수", "라인 중단 시간(입력 건 기준)"]
    display = dataframe.loc[dataframe["항목"].isin(metrics), ["항목", "현재 기간 값", "전년 동기 값", "직전 기간 값"]].copy()
    if display.empty:
        return pd.DataFrame(columns=["항목", "비교 기준", "값"]), []

    for column in ["현재 기간 값", "전년 동기 값", "직전 기간 값"]:
        display[column] = pd.to_numeric(display[column], errors="coerce")
    value_columns = [column for column in ["전년 동기 값", "직전 기간 값", "현재 기간 값"] if column in display.columns]
    melted = display.melt(id_vars="항목", value_vars=value_columns, var_name="비교 기준", value_name="값").dropna(subset=["값"])
    melted["비교 기준"] = pd.Categorical(melted["비교 기준"], categories=value_columns, ordered=True)
    if melted.empty:
        return pd.DataFrame(columns=["항목", "비교 기준", "값"]), value_columns
    return melted, value_columns


def comparison_note(dataframe: pd.DataFrame) -> str:
    if dataframe.empty or "비교 주의" not in dataframe.columns:
        return ""
    note = str(dataframe["비교 주의"].dropna().iloc[0]) if dataframe["비교 주의"].dropna().any() else ""
    if note:
        return normalize_report_text(note)
    return ""


def repeat_issue_chart(dataframe: pd.DataFrame) -> str:
    required = {"반복 기준", "조건값", "접수 건수"}
    if dataframe.empty or not required.issubset(dataframe.columns):
        return empty_state("반복 검토 후보가 없습니다.")

    display = enrich_repeat_display(dataframe).sort_values("접수 건수", ascending=True)
    display["차트 표시값"] = display["조건값_표시"].map(lambda value: truncate_text(value, 78))
    fig = px.bar(
        display,
        x="접수 건수",
        y="차트 표시값",
        color="반복 기준",
        orientation="h",
        title="반복 검토 후보 TOP 10",
        hover_data=[column for column in ["조건값_품질"] if column in display.columns],
        color_discrete_sequence=CHART_COLORS,
    )
    fig.update_traces(texttemplate="%{x:,.0f}", textposition="outside", cliponaxis=False)
    apply_chart_layout(fig, height=max(380, 120 + len(display) * 34))
    fig.update_layout(yaxis={"automargin": True}, legend={"orientation": "h", "y": -0.25})
    return chart_html(fig)


def line_chart(dataframe: pd.DataFrame, x: str, y: str, title: str) -> str:
    if _no_chart_data(dataframe, x, y):
        return empty_state("선택 기간 기준 표시할 데이터가 없어 차트를 생략했습니다.")
    fig = px.line(dataframe, x=x, y=y, title=title, markers=True, text=y, color_discrete_sequence=[CHART_COLORS[0]])
    fig.update_traces(line={"color": CHART_COLORS[0], "width": 3}, marker={"color": CHART_COLORS[0], "size": 8}, textposition="top center")
    apply_chart_layout(fig, height=340)
    return chart_html(fig)


def bar_chart(dataframe: pd.DataFrame, x: str, y: str, title: str) -> str:
    if _no_chart_data(dataframe, x, y):
        message = "라인 중단 시간이 입력된 건이 없어 차트를 생략했습니다." if "라인 중단" in y else "선택 기간 기준 표시할 데이터가 없어 차트를 생략했습니다."
        return empty_state(message)
    display, y_display = _downtime_display_frame(dataframe, y)
    fig = px.bar(display, x=x, y=y_display, title=title, text=y_display, color_discrete_sequence=[CHART_COLORS[1]])
    fig.update_traces(marker_color=CHART_COLORS[1], textposition="outside", cliponaxis=False)
    apply_chart_layout(fig, height=340)
    return chart_html(fig)


def horizontal_bar_chart(dataframe: pd.DataFrame, label: str, value: str, title: str) -> str:
    if _no_chart_data(dataframe, label, value):
        message = "라인 중단 시간이 입력된 건이 없어 차트를 생략했습니다." if "라인 중단" in value else "선택 기간 기준 표시할 데이터가 없어 차트를 생략했습니다."
        return empty_state(message)
    display, value_display = _downtime_display_frame(dataframe, value)
    display = display.sort_values(value_display, ascending=True)
    fig = px.bar(display, x=value_display, y=label, title=title, text=value_display, orientation="h", color_discrete_sequence=CHART_COLORS)
    colors = [CHART_COLORS[index % len(CHART_COLORS)] for index in range(len(display))]
    fig.update_traces(marker_color=colors, textposition="outside", cliponaxis=False)
    apply_chart_layout(fig, height=max(340, 80 + len(display) * 30))
    fig.update_layout(yaxis={"automargin": True})
    return chart_html(fig)


def donut_chart(dataframe: pd.DataFrame, label: str, value: str, title: str) -> str:
    if _no_chart_data(dataframe, label, value):
        return empty_state("선택 기간 기준 표시할 데이터가 없어 차트를 생략했습니다.")
    fig = px.pie(dataframe, names=label, values=value, title=title, hole=0.55, color_discrete_sequence=CHART_COLORS)
    fig.update_traces(textposition="inside", textinfo="percent+label")
    apply_chart_layout(fig, height=340)
    fig.update_layout(showlegend=True, legend={"orientation": "h", "y": -0.15})
    return chart_html(fig)


def apply_chart_layout(fig, height: int) -> None:
    fig.update_layout(
        template="plotly_white",
        colorway=CHART_COLORS,
        height=height,
        margin={"l": 32, "r": 24, "t": 58, "b": 52},
        font={"family": "Malgun Gothic, Arial, sans-serif", "size": 12},
        title={"font": {"size": 16}},
    )


def chart_html(fig) -> str:
    return fig.to_html(full_html=False, include_plotlyjs=False, config={"displayModeBar": False, "responsive": True})


def empty_state(message: str) -> str:
    return f'<div class="empty-state empty-chart" role="note">{escape(normalize_report_text(message))}</div>'


def normalize_report_text(text: str) -> str:
    replacements = {
        "반복 이슈 후보": "반복 검토 후보",
        "반복 후보": "반복 검토 후보",
        "차트 코멘트": "확인 포인트",
        "비교 코멘트": "해석 시 주의",
        "반복 후보 코멘트": "참고 기준",
    }
    normalized = str(text)
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    return normalized


def _no_chart_data(dataframe: pd.DataFrame, label: str, value: str) -> bool:
    if dataframe.empty or label not in dataframe.columns or value not in dataframe.columns:
        return True
    values = pd.to_numeric(dataframe[value], errors="coerce")
    if values.notna().sum() == 0:
        return True
    return bool(values.fillna(0).sum() == 0)


def dataframe_to_html(dataframe: pd.DataFrame, empty_message: str = "데이터가 없습니다.") -> str:
    if dataframe.empty:
        return f'<p class="empty-table">{escape(empty_message)}</p>'
    display = dataframe.copy()
    display = display.rename(columns=_display_column_name)
    for column in display.columns:
        if pd.api.types.is_datetime64_any_dtype(display[column]):
            display[column] = display[column].dt.strftime("%Y-%m-%d").fillna("")
    table = display.to_html(index=False, classes="data-table", border=0, escape=True)
    return f'<div class="table-scroll">{table}</div>'


def comparison_table_to_html(dataframe: pd.DataFrame) -> str:
    if dataframe.empty:
        return dataframe_to_html(dataframe)
    preferred = [
        "항목",
        "전년 동기 값",
        "현재 기간 값",
        "전년 동기 대비 증감",
        "전년 동기 대비 증감률",
        "직전 기간 값",
        "직전 기간 대비 증감",
        "직전 기간 대비 증감률",
    ]
    return dataframe_to_html(dataframe.loc[:, [column for column in preferred if column in dataframe.columns]])


def issue_table_to_html(dataframe: pd.DataFrame, columns: list[str], empty_message: str = "데이터가 없습니다.") -> str:
    existing_columns = [column for column in columns if column in dataframe.columns and column != "*ID"]
    if dataframe.empty or not existing_columns:
        return f'<p class="empty-table">{escape(empty_message)}</p>'

    rows = ['<div class="issue-table-wrap"><table class="data-table issue-table">', '<thead><tr>']
    for column in existing_columns:
        rows.append(f"<th>{escape(_issue_display_column_name(column))}</th>")
    rows.append("</tr></thead><tbody>")

    for _, record in dataframe.loc[:, existing_columns].iterrows():
        rows.append("<tr>")
        for column in existing_columns:
            value = format_issue_cell(record[column])
            if column in ISSUE_FULL_TEXT_COLUMNS:
                rows.append(f'<td class="full-text-col"><div class="issue-text-full">{escape(value)}</div></td>')
            elif column in TEXT_COLUMNS:
                css_class = "text-col"
                rows.append(f'<td class="{css_class}"><div class="clamp-text" title="{escape(value)}">{escape(value)}</div></td>')
            else:
                css_class = "nowrap-col"
                rows.append(f'<td class="{css_class}">{escape(value)}</td>')
        rows.append("</tr>")
    rows.append("</tbody></table></div>")
    return "".join(rows)


def repeat_issue_table_to_html(dataframe: pd.DataFrame) -> str:
    display = enrich_repeat_display(dataframe).drop(columns=["관련 ID 목록"], errors="ignore")
    if "조건값_표시" in display.columns:
        display["조건값"] = display["조건값_표시"]
        display = display.drop(columns=["조건값_표시"])
    return dataframe_to_html(display)


def enrich_repeat_display(dataframe: pd.DataFrame) -> pd.DataFrame:
    display = dataframe.copy()
    if "조건값" in display.columns and "조건값_표시" not in display.columns:
        display["조건값_표시"] = display["조건값"].map(format_repeat_condition_display)
    if "조건값" in display.columns and "조건값_품질" not in display.columns:
        display["조건값_품질"] = display["조건값"].map(evaluate_repeat_condition_quality)
    return display


def build_raw_quality_cards(raw_quality: dict[str, Any]) -> list[dict[str, str]]:
    if not raw_quality:
        return [{"label": "품질 상태", "value": "미확인"}]
    summary = raw_quality.get("summary", {})
    return [
        {"label": "데이터 품질 상태", "value": display_raw_quality_status(raw_quality.get("status", "미확인"))},
        {"label": "선택 기간 분석 대상 행 수", "value": format_count(summary.get("분석 대상 건수", 0))},
        {"label": "보완 필요 행 수", "value": format_count(summary.get("보완 필요 건수", 0))},
        {"label": "우선순위 상", "value": format_count(summary.get("우선순위 상", 0))},
        {"label": "우선순위 중", "value": format_count(summary.get("우선순위 중", 0))},
        {"label": "우선순위 하", "value": format_count(summary.get("우선순위 하", 0))},
        {"label": "정상 공백/조건부 제외 필드 플래그 수", "value": format_count(summary.get("조건부 제외 건수", 0))},
    ]


def display_raw_quality_status(status: Any) -> str:
    return {
        "PASS": "정상",
        "WARNING": "보완 필요",
        "BLOCKED": "생성 제한",
    }.get(str(status), str(status))


def raw_quality_field_top_html(raw_quality: dict[str, Any]) -> str:
    dataframe = raw_quality.get("field_quality_df", pd.DataFrame()) if raw_quality else pd.DataFrame()
    if dataframe.empty or "실제 보완 필요 건수" not in dataframe.columns:
        return '<p class="empty-table">필드별 품질 데이터가 없습니다.</p>'
    columns = ["필드명", "실제 보완 필요 건수", "자동추정 가능 건수", "수동확인 필요 건수"]
    top = dataframe.sort_values("실제 보완 필요 건수", ascending=False).loc[:, [column for column in columns if column in dataframe.columns]].head(5)
    return dataframe_to_html(top)


def raw_quality_manual_preview_html(raw_quality: dict[str, Any]) -> str:
    dataframe = raw_quality.get("manual_review_targets_df", pd.DataFrame()) if raw_quality else pd.DataFrame()
    if dataframe.empty:
        return '<p class="empty-table">수동 보완 대상이 없습니다.</p>'
    columns = ["접수일", "고객사", "보완 필요 필드", "접수내용 요약 검색어"]
    return dataframe_to_html(dataframe.loc[:, [column for column in columns if column in dataframe.columns]].head(10))


def _positive_downtime_rows(dataframe: pd.DataFrame, value_column: str) -> pd.DataFrame:
    if dataframe.empty or value_column not in dataframe.columns:
        return dataframe
    values = pd.to_numeric(dataframe[value_column], errors="coerce")
    return dataframe.loc[values > 0].copy()


def _downtime_display_frame(dataframe: pd.DataFrame, value_column: str) -> tuple[pd.DataFrame, str]:
    if "라인 중단" not in value_column or "입력 건 기준" in value_column:
        return dataframe.copy(), value_column
    display_column = _display_column_name(value_column)
    display = dataframe.copy().rename(columns={value_column: display_column})
    return display, display_column


def _display_column_name(column: str) -> str:
    if "라인 중단 시간" in column and "입력 건 기준" not in column:
        return column.replace("라인 중단 시간", "라인 중단 시간(입력 건 기준)")
    return column


def _issue_display_column_name(column: str) -> str:
    issue_labels = {
        "상태": "처리상태",
        "접수 내용 (요약)": "접수내용",
        "처리내용/진행상황 (요약)": "조치이력",
    }
    return issue_labels.get(column, _display_column_name(column))


def truncate_text(value: Any, max_length: int) -> str:
    text = "" if pd.isna(value) else str(value)
    if len(text) <= max_length:
        return text
    return text[: max_length - 1] + "…"


def format_cell(value: Any) -> str:
    if pd.isna(value):
        return ""
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, float):
        if value.is_integer():
            return f"{int(value):,}"
        return f"{value:,.1f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def format_issue_cell(value: Any) -> str:
    text = format_cell(value)
    if not text.strip():
        return "미입력"
    return text


def top_label(dataframe: pd.DataFrame | None, label: str, value: str) -> tuple[str, int]:
    if dataframe is None or dataframe.empty or label not in dataframe.columns or value not in dataframe.columns:
        return "-", 0
    row = dataframe.iloc[0]
    return str(row[label]), int(row[value])


def count_text(value: Any) -> str:
    try:
        return f"{int(value):,}건"
    except (TypeError, ValueError):
        return "0건"


def minute_text(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0
    if number.is_integer():
        return f"{int(number):,}분"
    return f"{number:,.1f}분"
