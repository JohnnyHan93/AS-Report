from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import hashlib
import ipaddress
from pathlib import Path
import tempfile
from typing import Any, MutableMapping
from urllib.parse import urlparse

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from as_report.analyzer import analyze
from as_report.cleaner import clean_data
from as_report.loader import DataLoadError, LoadedData, load_input
from as_report.narrative import build_narrative
from as_report.output import append_report_history, build_user_output_dirs
from as_report.period import PeriodError, PeriodRange, PeriodSelection, build_period_range, filter_by_period
from as_report.provenance import build_raw_only_provenance
from as_report.quality import analyze_raw_data_quality, export_manual_review_workbook, export_quality_flags_csv, write_quality_summary_markdown
from as_report.report_presentation import ReportDownloadBundle, build_presentation_payload, generate_report_download_bundle
from as_report.report_preview import SLIDE_TITLES, render_document_preview, render_slide_preview
from as_report.standardization import (
    apply_standard_name_preview,
    ensure_standard_name_files,
    export_standard_name_preview_csv,
    export_unknown_standard_names_workbook,
    load_standard_name_mapping,
)
from as_report.ui_components import quality_to_dataframe, show_kpi_cards, show_plotly_chart, show_table
from as_report.ui_state import (
    FILTER_COLUMNS,
    list_raw_files,
    PROJECT_ROOT,
    RAW_DIR,
    REPORTS_DIR,
    InputSource,
)

MISSING_LABEL = "미입력"
UPLOADED_SOURCE_STATE_KEY = "uploaded_input_source"
STANDARD_NAME_CONFIG_DIR = PROJECT_ROOT / "config" / "standard_names"
PERIOD_LABELS = {
    "연간": "year",
    "반기": "half",
    "분기": "quarter",
    "사용자 지정 기간": "custom",
}
THEME_MODE_OPTIONS = {
    "시스템 설정": "system",
    "기본 모드": "light",
    "다크 모드": "dark",
}
LIGHT_THEME_VALUES = {
    "app-bg": "#ffffff",
    "header-bg": "rgba(255, 255, 255, 0.95)",
    "sidebar-bg": "#f4f5f7",
    "surface": "#ffffff",
    "surface-soft": "#eaf1f8",
    "text": "#202b33",
    "muted": "#697780",
    "border": "#e0e5e9",
    "control-border": "#cbd3da",
    "tab-text": "#566671",
    "accent": "#005b9f",
    "accent-text": "#ffffff",
    "document-accent": "#23776a",
}
DARK_THEME_VALUES = {
    "app-bg": "#17191c",
    "header-bg": "rgba(23, 25, 28, 0.95)",
    "sidebar-bg": "#1e2125",
    "surface": "#22262a",
    "surface-soft": "#253749",
    "text": "#ecf2ef",
    "muted": "#a9bbb4",
    "border": "#354840",
    "control-border": "#486057",
    "tab-text": "#c9d8d2",
    "accent": "#79b7ea",
    "accent-text": "#102538",
    "document-accent": "#70c4b5",
}


@dataclass(frozen=True)
class AnalysisResult:
    analysis: dict[str, Any]
    narrative_lines: list[str]
    period_range: PeriodRange
    source_name: str
    filters: dict[str, list[str]]
    filter_summary: str
    raw_quality_result: dict[str, Any] | None = None
    output_owner: str = "default_user"
    standard_preview_df: pd.DataFrame | None = None
    unknown_standard_names_df: pd.DataFrame | None = None
    mapping_file_paths: dict[str, Path] | None = None
    context_signature: str = ""
    run_timestamp: str = ""
    input_provenance: dict[str, Any] | None = None


def main() -> None:
    st.set_page_config(page_title="A/S 리포트", layout="wide", initial_sidebar_state="expanded")
    theme_mode = render_theme_selector()
    apply_app_style(theme_mode)
    st.title("A/S 리포트")
    st.caption("접수 현황과 업무유형별 분석")
    output_owner = "download_only"
    localhost_access = is_localhost_request()

    with st.container(key="report_workspace"):
        setup_column, result_column = st.columns([0.30, 0.70], gap="large")
        with setup_column:
            result = render_analysis_setup(output_owner)
        with result_column:
            if result is None:
                st.subheader("리포트 작업 영역")
                st.markdown('<div class="report-empty"><span class="material-symbols-rounded">description</span><h3>아직 분석 결과가 없습니다</h3><p>접수 목록과 조회 기간을 선택해 주세요.</p></div>', unsafe_allow_html=True)
                return
            st.subheader("보고서")
            st.caption(f"{result.period_range.label} · {result.source_name}")
            labels = ["보고서 미리보기", "분석 요약", "리포트 다운로드"]
            if localhost_access:
                labels.append("데이터 검토")
            tabs = st.tabs(labels)
            with tabs[0]:
                render_report_preview(result)
            with tabs[1]:
                render_summary_preview(result)
            with tabs[2]:
                render_report_actions(
                    result,
                    localhost_access=localhost_access,
                    show_operator_materials=False,
                )
            if localhost_access:
                with tabs[3]:
                    with st.expander("상세 분석과 입력값", expanded=False):
                        render_preview(result, localhost_access=True, include_summary=False)
                    with st.expander("보완 자료 다운로드", expanded=False):
                        render_raw_quality_downloads(result)
                        render_standard_name_downloads(result)


def render_analysis_setup(output_owner: str) -> AnalysisResult | None:
    st.subheader("분석 조건")

    with st.container():
        st.markdown("##### 접수 목록")
        source = render_input_source(show_heading=False)
        if source is None:
            return None

        loaded = load_source(source)
        if loaded is None:
            return None

        cleaned = clean_data(loaded.dataframe)
        source_name = source.display_name
        render_data_profile(source_name, cleaned)

    with st.container():
        st.divider()
        st.markdown("##### 조회 기간")
        try:
            period_range = render_period_selector(cleaned, show_heading=False)
            period_data = filter_by_period(cleaned, period_range)
        except PeriodError as error:
            st.error(str(error))
            return None

    with st.container():
        st.markdown("##### 추가 필터")
        selected_filters = render_filter_selector(period_data, show_heading=False)
        filtered_data = apply_filters(period_data, selected_filters)
        filter_summary = summarize_filters(selected_filters)

    with st.container():
        st.divider()
        st.markdown(f"**분석 대상 {len(filtered_data):,}건**")
        st.caption(f"{period_range.start_date} ~ {period_range.end_date}")
        run_analysis = st.button(
            "분석 시작",
            type="primary",
            use_container_width=True,
            key="run_analysis_button",
            icon=":material/play_arrow:",
        )

    if run_analysis:
        st.session_state.pop("report_download_bundle", None)
        comparison_source_data = apply_filters(cleaned, selected_filters)
        result = build_analysis_result(
            loaded.dataframe,
            cleaned,
            period_data,
            filtered_data,
            comparison_source_data,
            period_range,
            source.path,
            source_name,
            selected_filters,
            filter_summary,
            output_owner,
        )
        st.session_state["analysis_result"] = result

    result = st.session_state.get("analysis_result")
    if result is None:
        st.caption("준비가 끝나면 분석 시작을 눌러 주세요.")
        return

    current_context_signature = build_analysis_context_signature(
        source_name,
        source.path,
        period_range,
        selected_filters,
        output_owner,
    )
    if result.context_signature != current_context_signature:
        st.info("선택한 조건이 이전 분석과 달라졌어요. 지금 조건으로 다시 분석을 시작해 주세요.")
        return
    return result


def is_localhost_request(ip_address: str | None = None, url: str | None = None) -> bool:
    if ip_address is None:
        try:
            ip_address = st.context.ip_address
        except Exception:
            ip_address = None
    if url is None:
        try:
            url = st.context.url
        except Exception:
            url = None
    if not url:
        try:
            url = str(st.context.headers.get("host", ""))
        except Exception:
            url = None

    candidate = str(ip_address or "").strip().strip("[]")
    if candidate.lower() == "localhost":
        return True
    if candidate:
        try:
            if ipaddress.ip_address(candidate).is_loopback:
                return True
        except ValueError:
            pass

    candidate_url = str(url)
    if candidate_url and "://" not in candidate_url:
        candidate_url = f"http://{candidate_url}"
    hostname = (urlparse(candidate_url).hostname or "").lower() if candidate_url else ""
    if hostname == "localhost":
        return True
    if hostname:
        try:
            return ipaddress.ip_address(hostname).is_loopback
        except ValueError:
            return False
    return False


def render_theme_selector() -> str:
    with st.sidebar:
        with st.container(key="company_logo"):
            st.image(str(Path(__file__).parent / "resources" / "company_logo.png"), width=190)
        st.markdown("### A/S 리포트")
        st.caption("접수 내역 분석")
        st.divider()
        with st.expander("사용법", expanded=False):
            st.markdown("1. 이슈사항 접수 목록을 선택합니다.\n2. 기간과 필터를 정하고 **분석 시작**을 누릅니다.\n3. **리포트 다운로드**에서 PPT와 PDF를 만듭니다.")
            st.caption("PPT는 회사 양식, PDF는 A4 보고서로 제공됩니다. 원본 파일은 바뀌지 않습니다.")
        st.subheader("화면 설정")
        selected_label = st.selectbox(
            "화면 모드",
            options=list(THEME_MODE_OPTIONS),
            index=0,
            key="app_theme_mode",
            help="시스템 설정은 현재 컴퓨터나 브라우저의 밝은/어두운 화면 설정을 따라갑니다.",
        )
        theme_mode = THEME_MODE_OPTIONS[selected_label]
        st.caption("다운로드 파일은 직접 보관해 주세요.")
        return theme_mode


def _theme_variable_block(values: dict[str, str], selector: str = ":root") -> str:
    declarations = "\n".join(f"            --{name}: {value};" for name, value in values.items())
    return f"{selector} {{\n{declarations}\n        }}"


def build_app_style_css(theme_mode: str) -> str:
    light_variables = _theme_variable_block(LIGHT_THEME_VALUES)
    dark_variables = _theme_variable_block(DARK_THEME_VALUES)
    if theme_mode == "light":
        theme_variables = light_variables
    elif theme_mode == "dark":
        theme_variables = dark_variables
    else:
        theme_variables = (
            f"{light_variables}\n"
            "        @media (prefers-color-scheme: dark) {\n"
            f"        {dark_variables}\n"
            "        }"
        )

    return f"""
        <style>
        {theme_variables}
        html, body, [data-testid="stApp"] {{
            background: var(--app-bg);
        }}
        [data-testid="stAppViewContainer"] {{
            color: var(--text);
            background: var(--app-bg);
        }}
        [data-testid="stHeader"] {{
            background: var(--header-bg);
        }}
        .block-container {{
            max-width: 1580px;
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            padding-inline: 2rem;
        }}
        [data-testid="stAppViewContainer"] h1 {{ font-size: 1.9rem; padding-bottom: .35rem; }}
        [data-testid="stAppViewContainer"] h2 {{ font-size: 1.2rem; }}
        [data-testid="stAppViewContainer"] h3 {{ font-size: 1.05rem; }}
        [data-testid="stAppViewContainer"] h5 {{ font-size: .95rem; }}
        [data-testid="stMarkdownContainer"] p {{ overflow-wrap: anywhere; }}
        .st-key-report_workspace {{ border-top: 3px solid var(--accent); padding-top: 1.25rem; }}
        .st-key-report_workspace:has(.st-key-report_pdf_canvas) {{ --accent: var(--document-accent); }}
        .st-key-report_ppt_canvas, .st-key-report_pdf_canvas {{ border: 1px solid var(--border); }}
        [data-testid="stCaptionContainer"] {{ opacity: 1; }}
        .st-key-company_logo {{ background: white; padding: .5rem; max-width: 210px; }}
        .report-empty {{ padding: 5rem 1rem; text-align: center; color: var(--muted); border: 1px solid var(--border); border-top: 4px solid var(--accent); background: var(--surface); }}
        .report-empty .material-symbols-rounded {{ font-family: 'Material Symbols Rounded'; font-size: 48px; color: var(--accent); }}
        .report-empty h3 {{ margin: 1rem 0 .5rem; color: var(--text); }}
        [data-testid="stFileUploaderDropzone"] {{ background: var(--surface); border: 1px dashed var(--control-border); }}
        [data-testid="stSidebar"] {{
            color: var(--text);
            background: var(--sidebar-bg);
            border-right: 1px solid var(--border);
        }}
        [data-testid="stAppViewContainer"] h1,
        [data-testid="stAppViewContainer"] h2,
        [data-testid="stAppViewContainer"] h3,
        [data-testid="stAppViewContainer"] h4,
        [data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stAppViewContainer"] label,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] label {{
            color: var(--text);
        }}
        [data-testid="stCaptionContainer"],
        [data-testid="stCaptionContainer"] p,
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"],
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{
            color: var(--muted) !important;
        }}
        [data-testid="stTextInput"] input,
        [data-testid="stSelectbox"] div[data-baseweb="select"] > div {{
            color: var(--text);
            background: var(--surface);
            border-color: var(--control-border);
        }}
        [data-testid="stMetric"] {{
            color: var(--text);
            background: var(--surface);
            border-bottom: 2px solid var(--border);
            padding: 0.6rem 0;
        }}
        [data-testid="stMetricValue"] {{ font-size: 1.7rem; font-variant-numeric: tabular-nums; }}
        [data-testid="stMetricLabel"] p {{ font-size: .8rem; }}
        [data-testid="stExpander"] {{
            color: var(--text);
            background: var(--surface);
            border-color: var(--border);
            border-radius: 6px;
        }}
        div[role="tablist"] {{ gap: 1rem; border-bottom: 1px solid var(--border); }}
        button[data-baseweb="tab"] {{
            color: var(--tab-text);
            background: transparent;
            border: none;
            border-radius: 0;
            padding: 0.55rem 0;
        }}
        button[data-baseweb="tab"] p {{
            color: var(--tab-text) !important;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            color: var(--accent);
            background: transparent;
            border-bottom: 2px solid var(--accent);
        }}
        button[data-baseweb="tab"][aria-selected="true"] p {{
            color: var(--accent) !important;
        }}
        [data-baseweb="tab-highlight"] {{ background-color: var(--accent); }}
        [data-testid="stBaseButton-segmented_controlActive"] {{
            color: var(--accent-text); background: var(--accent); border-color: var(--accent);
        }}
        [data-testid="stBaseButton-segmented_controlActive"] p {{ color: inherit !important; }}
        .stButton > button, .stDownloadButton > button {{
            color: var(--text);
            background: var(--surface);
            border-color: var(--control-border);
            border-radius: 6px;
            font-weight: 600;
        }}
        [data-testid="stAppViewContainer"] [data-testid="stBaseButton-primary"] {{
            color: var(--accent-text);
            background: var(--accent);
            border-color: var(--accent);
        }}
        .st-key-run_analysis_button button {{
            min-height: 3.25rem;
            font-size: 1rem;
            font-weight: 700;
        }}
        .stButton > button p, .stDownloadButton > button p {{
            color: inherit !important;
        }}
        div[role="listbox"] {{
            color: var(--text);
            background: var(--surface);
        }}
        @media (max-width: 900px) {{
            .block-container {{ padding-inline: 1rem; }}
            .st-key-report_workspace > [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap; }}
            .st-key-report_workspace > [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{ flex: 1 1 100%; width: 100%; }}
            .report-empty {{ padding: 2rem 1rem; }}
        }}
        </style>
        """


def apply_app_style(theme_mode: str) -> None:
    st.markdown(
        build_app_style_css(theme_mode),
        unsafe_allow_html=True,
    )


def render_input_source(*, show_heading: bool = True) -> InputSource | None:
    if show_heading:
        st.header("1. 데이터")
    mode = st.radio("파일 가져오기", ["내 파일 올리기", "저장된 파일 선택"], horizontal=True, label_visibility="collapsed")

    if mode == "저장된 파일 선택":
        if st.button("목록 새로고침", icon=":material/refresh:", type="tertiary"):
            st.rerun()

        raw_files = list_raw_files(RAW_DIR)
        if not raw_files:
            st.error("분석 가능한 Raw CSV 파일이 없습니다. 운영자에게 입력 파일 등록을 요청해 주세요.")
            return None

        placeholder = "분석할 파일을 선택하세요"
        selected_raw = st.selectbox(
            "이슈 데이터 파일",
            [placeholder, *raw_files],
            format_func=format_raw_file_choice,
            help="파일명만 보고 최신 파일을 자동 선택하지 않아요. 이번 분석에 사용할 파일을 직접 골라 주세요.",
        )
        if selected_raw == placeholder:
            st.info("분석할 파일을 골라 주세요. 새 파일이라고 해서 자동으로 선택되지는 않아요.")
            return None

        selected_path = Path(selected_raw)
        return InputSource(path=selected_path, display_name=selected_path.name)

    uploaded = st.file_uploader("이슈사항 접수 목록", type=["csv", "xlsx", "xls"])
    if uploaded is None:
        st.caption("CSV 또는 Excel 파일 한 개를 선택해 주세요.")
        return None
    return get_or_create_uploaded_source(uploaded.name, uploaded.getvalue(), st.session_state)


def format_raw_file_choice(value: str | Path) -> str:
    if isinstance(value, str):
        return value
    modified_at = datetime.fromtimestamp(value.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    return f"{value.name} ({modified_at})"


def write_uploaded_file(content: bytes, suffix: str) -> Path:
    temp_dir = Path(tempfile.gettempdir()) / "as_report_uploads"
    temp_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"uploaded_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}{suffix}"
    temp_path = temp_dir / safe_name
    temp_path.write_bytes(content)
    return temp_path


def get_or_create_uploaded_source(
    file_name: str,
    content: bytes,
    state: MutableMapping[str, Any],
) -> InputSource:
    """Keep one temporary upload path for an unchanged file during a session."""
    signature = f"{file_name}:{hashlib.sha256(content).hexdigest()}"
    stored = state.get(UPLOADED_SOURCE_STATE_KEY)
    if isinstance(stored, dict) and stored.get("signature") == signature:
        stored_path = Path(str(stored.get("path", "")))
        if stored_path.exists():
            return InputSource(path=stored_path, display_name=file_name, is_temporary=True)

    temp_path = write_uploaded_file(content, Path(file_name).suffix)
    state[UPLOADED_SOURCE_STATE_KEY] = {"signature": signature, "path": str(temp_path)}
    return InputSource(path=temp_path, display_name=file_name, is_temporary=True)


def load_source(source: InputSource) -> LoadedData | None:
    try:
        return load_input(source.path)
    except DataLoadError as error:
        st.error(f"데이터 로딩 오류: {error}")
        return None
    except Exception as error:
        st.error(f"데이터를 읽는 중 예상하지 못한 오류가 발생했습니다: {error}")
        return None


def render_data_profile(source_name: str, dataframe: pd.DataFrame) -> None:
    received_at = pd.to_datetime(dataframe.get("접수일", pd.Series(dtype="datetime64[ns]")), errors="coerce")
    min_date = received_at.min()
    max_date = received_at.max()
    first = "-" if pd.isna(min_date) else min_date.strftime("%Y-%m-%d")
    last = "-" if pd.isna(max_date) else max_date.strftime("%Y-%m-%d")
    st.caption(f"{len(dataframe):,}건 · 접수일 {first} ~ {last}")


def render_period_selector(dataframe: pd.DataFrame, *, show_heading: bool = True) -> PeriodRange:
    if show_heading:
        st.header("2. 기간")
    received_at = pd.to_datetime(dataframe["접수일"], errors="coerce")
    years = sorted([int(year) for year in received_at.dropna().dt.year.unique()])
    if not years:
        years = [date.today().year]
    default_year = int(received_at.max().year) if received_at.notna().any() else years[-1]
    default_year_index = years.index(default_year) if default_year in years else len(years) - 1

    period_label = st.radio(
        "기간 종류", list(PERIOD_LABELS.keys()), horizontal=True,
        help="월간 리포트는 사용자 지정 기간에서 해당 월의 첫날과 마지막 날을 선택합니다.",
    )
    period = PERIOD_LABELS[period_label]

    if period == "year":
        year = st.selectbox("연도", years, index=default_year_index)
        return build_period_range(PeriodSelection(period="year", year=int(year)))
    if period == "half":
        col1, col2 = st.columns(2)
        year = col1.selectbox("연도", years, index=default_year_index, key="half_year")
        half = col2.selectbox("반기", ["H1", "H2"])
        return build_period_range(PeriodSelection(period="half", year=int(year), half=half))
    if period == "quarter":
        col1, col2 = st.columns(2)
        year = col1.selectbox("연도", years, index=default_year_index, key="quarter_year")
        quarter = col2.selectbox("분기", ["Q1", "Q2", "Q3", "Q4"])
        return build_period_range(PeriodSelection(period="quarter", year=int(year), quarter=quarter))

    min_date = received_at.min().date() if received_at.notna().any() else date(default_year, 1, 1)
    max_date = received_at.max().date() if received_at.notna().any() else date(default_year, 12, 31)
    col1, col2 = st.columns(2)
    start = col1.date_input("시작일", value=min_date)
    end = col2.date_input("종료일", value=max_date)
    return build_period_range(PeriodSelection(period="custom", start=start.isoformat(), end=end.isoformat()))


def render_filter_selector(dataframe: pd.DataFrame, *, show_heading: bool = True) -> dict[str, list[str]]:
    if show_heading:
        st.header("3. 필터")
    selected: dict[str, list[str]] = {}
    with st.expander("필터 열기", expanded=False):
        st.caption("필터를 고르지 않으면 선택한 기간의 전체 데이터를 보여드려요.")
        columns = st.columns(2)
        for index, column_name in enumerate(FILTER_COLUMNS):
            if column_name not in dataframe.columns:
                selected[column_name] = []
                continue
            options = filter_options(dataframe[column_name])
            selected[column_name] = columns[index % 2].multiselect(column_name, options, default=[])
    return selected


def filter_options(series: pd.Series) -> list[str]:
    values = series.map(display_filter_value).dropna().astype(str).unique().tolist()
    return sorted(values)


def display_filter_value(value: Any) -> str:
    if pd.isna(value) or str(value).strip() == "":
        return MISSING_LABEL
    return str(value)


def apply_filters(dataframe: pd.DataFrame, filters: dict[str, list[str]]) -> pd.DataFrame:
    filtered = dataframe.copy()
    for column_name, selected_values in filters.items():
        if not selected_values or column_name not in filtered.columns:
            continue
        display_series = filtered[column_name].map(display_filter_value)
        filtered = filtered.loc[display_series.isin(selected_values)].copy()
    return filtered


def summarize_filters(filters: dict[str, list[str]]) -> str:
    parts = []
    for column_name, selected_values in filters.items():
        if selected_values:
            parts.append(f"{column_name}={', '.join(selected_values)}")
    return "없음" if not parts else " / ".join(parts)


def build_analysis_context_signature(
    source_name: str,
    source_path: Path,
    period_range: PeriodRange,
    selected_filters: dict[str, list[str]],
    output_owner: str,
) -> str:
    try:
        source_stat = source_path.stat()
        source_identity = f"{source_path.resolve()}:{source_stat.st_size}:{source_stat.st_mtime_ns}"
    except OSError:
        source_identity = str(source_path)
    filter_parts = [
        f"{column_name}={','.join(sorted(values))}"
        for column_name, values in sorted(selected_filters.items())
        if values
    ]
    return "|".join(
        [
            source_name,
            source_identity,
            period_range.period,
            period_range.start_date.isoformat(),
            period_range.end_date.isoformat(),
            output_owner,
            *filter_parts,
        ]
    )


def build_analysis_result(
    raw_data: pd.DataFrame,
    source_data: pd.DataFrame,
    source_period_data: pd.DataFrame,
    filtered_data: pd.DataFrame,
    comparison_source_data: pd.DataFrame,
    period_range: PeriodRange,
    source_path: Path,
    source_name: str,
    selected_filters: dict[str, list[str]],
    filter_summary: str,
    output_owner: str,
) -> AnalysisResult:
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    analysis = analyze(
        source_data,
        filtered_data,
        period_range=period_range,
        comparison_source_data=comparison_source_data,
        source_period_data=source_period_data,
    )
    raw_quality_result = analyze_raw_data_quality(
        raw_data,
        source_path=source_path,
        start_date=period_range.start_date,
        end_date=period_range.end_date,
    )
    analysis["raw_quality"] = raw_quality_result
    mapping_file_paths = ensure_standard_name_files(STANDARD_NAME_CONFIG_DIR)
    standard_mappings = load_standard_name_mapping(STANDARD_NAME_CONFIG_DIR)
    standard_preview_df, unknown_standard_names_df = apply_standard_name_preview(filtered_data, standard_mappings)
    input_provenance = build_raw_only_provenance(source_path, raw_data)
    if len(filtered_data) == 0:
        narrative_lines = ["분석 대상 조건에 해당하는 접수 이슈가 없습니다."]
    else:
        narrative_lines = build_narrative(
            analysis,
            period_label=period_range.label,
            start_date=period_range.start_date.isoformat(),
            end_date=period_range.end_date.isoformat(),
        )
    if filter_summary != "없음":
        narrative_lines.insert(1 if narrative_lines else 0, f"추가 필터 조건은 {filter_summary}입니다.")
    return AnalysisResult(
        analysis=analysis,
        narrative_lines=narrative_lines,
        period_range=period_range,
        source_name=source_name,
        filters=selected_filters,
        filter_summary=filter_summary,
        raw_quality_result=raw_quality_result,
        output_owner=output_owner,
        standard_preview_df=standard_preview_df,
        unknown_standard_names_df=unknown_standard_names_df,
        mapping_file_paths=mapping_file_paths,
        context_signature=build_analysis_context_signature(
            source_name,
            source_path,
            period_range,
            selected_filters,
            output_owner,
        ),
        run_timestamp=run_timestamp,
        input_provenance=input_provenance,
    )


def render_preview(result: AnalysisResult, *, localhost_access: bool, include_summary: bool = True) -> None:
    analysis = result.analysis
    tables = analysis["tables"]

    st.header("4. 결과 보기")
    st.caption("핵심 결과를 확인한 뒤 회사 기본 양식의 PPT와 PDF를 내려받을 수 있어요.")

    if not localhost_access:
        render_summary_preview(result)
        return

    if include_summary:
        summary_tab, advanced_tab, detail_tab = st.tabs(["한눈에 보기", "추가로 보기", "상세 데이터"])
        with summary_tab:
            render_summary_preview(result)
    else:
        advanced_tab, detail_tab = st.tabs(["추가 분석", "상세 데이터"])
    with advanced_tab:
        render_raw_quality_preview(result)
        render_legacy_features_preview(result)
        render_quality_feedback_preview(result)
        render_proposal_pause_notice()
    with detail_tab:
        with st.expander("추가 차트", expanded=False):
            chart_col1, chart_col2 = st.columns(2)
            with chart_col1:
                show_plotly_chart(tables["월별 라인 중단 시간"], "bar", "기간_연월", "라인 중단 시간", "월별 라인 중단 시간")
                show_plotly_chart(tables["대분류별 접수 건수"], "hbar", "대분류", "접수 건수", "대분류별 접수 건수")
            with chart_col2:
                show_plotly_chart(tables["고객사별 접수 건수 TOP 20"].head(10), "hbar", "고객사", "접수 건수", "고객사별 접수 건수 TOP 10")
                show_plotly_chart(tables["소분류 고장부품별 접수 건수 TOP 20"].head(10), "hbar", "소분류 (고장부품)", "접수 건수", "소분류 고장부품 TOP 10")

        with st.expander("주요 표", expanded=False):
            show_table("고객사별 접수 건수 TOP 20", tables["고객사별 접수 건수 TOP 20"])
            show_table("고객사별 라인 중단 시간 TOP 20", tables["고객사별 라인 중단 시간 TOP 20"])
            show_table("대분류별 접수 건수", tables["대분류별 접수 건수"])
            show_table("중분류별 접수 건수", tables["중분류별 접수 건수"])
            show_table("소분류 고장부품별 접수 건수 TOP 20", tables["소분류 고장부품별 접수 건수 TOP 20"])

        with st.expander("전년 동기 / 직전 기간 비교", expanded=False):
            st.caption("연간은 전년 동기만 비교하며, 반기/분기는 전년 동기와 직전 기간을 함께 비교합니다.")
            show_table("전년 동기 / 직전 기간 비교", analysis.get("comparison", pd.DataFrame()), height=360)

        with st.expander("반복 이슈 후보", expanded=False):
            st.caption("동일 고객사/분류/설비 조합이 2건 이상 반복된 후보입니다. 실제 동일 조건 여부는 담당자가 확인해야 합니다.")
            repeat_issues = analysis.get("repeat_issues", pd.DataFrame()).drop(columns=["관련 ID 목록"], errors="ignore").head(20)
            show_table("반복 검토 후보 TOP 20", repeat_issues, height=420)

        with st.expander("라인 중단 시간 TOP 20 이슈 목록", expanded=False):
            show_table("라인 중단 시간 TOP 20 이슈 목록", drop_id_column(tables["라인 중단 시간 TOP 20 이슈 목록"]), height=420)

        with st.expander("진행중/미완료 이슈 목록", expanded=False):
            show_table("진행중/미완료 이슈 목록", drop_id_column(tables["진행중/미완료 이슈 목록"]), height=420)

        with st.expander("데이터 품질 상태 요약", expanded=False):
            compact_quality = {
                "전체 원본 행 수": analysis["quality"].get("전체 원본 건수", 0),
                "선택 기간 분석 대상 행 수": analysis["quality"].get("분석 대상 건수", 0),
                "접수일 누락 건수": analysis["quality"].get("접수일 누락 건수", 0),
            }
            show_table("데이터 품질 상태 요약", quality_to_dataframe(compact_quality), height=220)
            st.caption("상세 Raw 품질 검토는 Raw 품질 검토 산출물의 Excel/Markdown/CSV를 사용합니다. 산출물은 원본 Raw 직접 수정 파일이 아닙니다.")


def render_summary_preview(result: AnalysisResult) -> None:
    analysis = result.analysis
    tables = analysis["tables"]
    payload = build_presentation_payload(
        analysis, result.narrative_lines, period_range=result.period_range, filter_summary=result.filter_summary,
    )
    for column, metric in zip(st.columns(4), payload["kpis"]):
        column.metric(metric["label"], f'{metric["value"]:,}{metric["unit"]}')
    with st.expander("요약 메모", expanded=False):
        for line in payload["narrative"]:
            st.write(f"- {line}")
    month_tab, work_tab, customer_tab = st.tabs(["월별 추이", "업무유형", "고객사"])
    with month_tab:
        show_plotly_chart(tables["월별 접수 건수"], "line", "기간_연월", "접수 건수", "월별 접수 건수")
    with work_tab:
        show_plotly_chart(tables["업무유형구분별 접수 건수"], "hbar", "업무유형구분", "접수 건수", "업무유형별 접수 건수")
    with customer_tab:
        show_plotly_chart(tables["고객사별 접수 건수 TOP 20"].head(10), "hbar", "고객사", "접수 건수", "접수 건수 상위 고객사")


def render_report_preview(result: AnalysisResult) -> None:
    selected = st.segmented_control(
        "보고서 양식", ["PPT", "PDF"], default="PPT", key="report_preview_format",
        selection_mode="single", help="PPT는 같은 집계 내용을 회사 색상의 웹 배치로 확인합니다. 실제 PPT의 도형 배치는 회사 템플릿을 따릅니다. PDF는 출력에 사용하는 본문입니다. 두 파일 모두 다운로드할 수 있습니다.",
    ) or "PPT"
    payload = build_presentation_payload(
        result.analysis, result.narrative_lines,
        period_range=result.period_range, filter_summary=result.filter_summary,
    )
    # Use the analysis event for a stable preview, never an existing report path.
    if result.run_timestamp:
        try:
            payload["created_at"] = datetime.strptime(result.run_timestamp, "%Y%m%d_%H%M%S_%f").strftime("%Y-%m-%d %H:%M")
        except ValueError:
            pass
    if selected == "PPT":
        index = st.selectbox(
            "슬라이드", range(len(SLIDE_TITLES)),
            format_func=lambda value: f"{value + 1:02d} · {SLIDE_TITLES[value]}",
            key="report_preview_slide",
        )
        html = render_slide_preview(payload, index)
    else:
        html = render_document_preview(payload)
    with st.container(key=f"report_{selected.lower()}_canvas"):
        components.html(html, height=720, scrolling=True)


def drop_id_column(dataframe: pd.DataFrame) -> pd.DataFrame:
    if "*ID" in dataframe.columns:
        return dataframe.drop(columns=["*ID"])
    return dataframe


def render_raw_quality_preview(result: AnalysisResult) -> None:
    quality_result = result.raw_quality_result
    if not quality_result:
        return
    summary = quality_result["summary"]
    status = quality_result["status"]
    with st.expander("Raw 데이터 확인", expanded=False):
        st.caption("Raw 데이터 품질은 보완 후보를 찾기 위한 검토 정보입니다. 자동추정/추천값은 확정값이 아니며 원본 CSV는 이 화면에서 수정하지 않습니다.")
        st.caption("수동 보완용 Excel은 보완 요청 대상과 근거를 확인하기 위한 산출물입니다. 처리 결과는 Excel 사본 또는 별도 검토 메모에 기록하세요.")
        st.caption("표준명칭은 원본 데이터를 자동 변경하지 않고 미리보기/Unknown 목록으로만 제공합니다.")
        if status == "BLOCKED":
            st.error(f"Raw 데이터 품질 생성 제한: {summary.get('blocked_reason', '확인 필요')}")
            return
        if status == "WARNING":
            st.warning("보완 필요 후보가 있습니다. 기존 리포트 생성은 계속 가능합니다.")
        else:
            st.success("보완 필요 후보가 없습니다.")

        columns = st.columns(5)
        columns[0].metric("분석 대상", f"{int(summary.get('분석 대상 건수', 0)):,}건")
        columns[1].metric("보완 필요", f"{int(summary.get('보완 필요 건수', 0)):,}건")
        columns[2].metric("우선순위 상", f"{int(summary.get('우선순위 상', 0)):,}건")
        columns[3].metric("우선순위 중/하", f"{int(summary.get('우선순위 중', 0)):,}/{int(summary.get('우선순위 하', 0)):,}건")
        columns[4].metric("정상 공백/조건부 제외", f"{int(summary.get('조건부 제외 건수', 0)):,}건")
        st.caption("상세 필드별 품질 현황과 보완 대상 목록은 다운로드 산출물에서 확인합니다. 판정은 정상 처리, 수정 요청, 보류/추가 확인, 조건부 제외 기준으로 기록합니다.")

        st.divider()
        st.subheader("표준명칭 미리보기 상태")
        mapping_paths = result.mapping_file_paths or {}
        mapping_status = pd.DataFrame(
            [
                {"mapping_file": file_name, "상태": "사용 가능" if Path(path).exists() else "확인 필요"}
                for file_name, path in mapping_paths.items()
            ]
        )
        show_table("표준명칭 매핑 파일 상태", mapping_status, height=260)

        unknown = result.unknown_standard_names_df if result.unknown_standard_names_df is not None else pd.DataFrame()
        st.metric("Unknown 명칭 수", f"{len(unknown):,}건")
        show_table("Unknown 명칭 목록 미리보기 TOP 30", unknown.head(30), height=360)

        standard_preview = result.standard_preview_df if result.standard_preview_df is not None else pd.DataFrame()
        preview_columns = standard_preview_columns(standard_preview)
        show_table("표준명칭 미리보기 TOP 30", standard_preview[preview_columns].head(30) if preview_columns else pd.DataFrame(), height=420)


def render_legacy_features_preview(result: AnalysisResult) -> None:
    legacy_features = result.analysis.get("legacy_features", {})
    if not legacy_features:
        return
    with st.expander("처리 상태·클레임 보기", expanded=False):
        st.caption("04. ES_ 이슈사항 보고 Raw의 클레임/제조사 입력값과 처리 상태를 확인하는 검토용 영역입니다.")

        st.subheader("처리 상태 요약")
        show_table("처리 상태 KPI", legacy_features.get("completion_kpi", pd.DataFrame()), height=220)
        show_table("월별 처리 상태 추이", legacy_features.get("monthly_completion_trend", pd.DataFrame()).head(12), height=320)

        st.subheader("클레임/제조사 검토")
        st.caption(legacy_features.get("claim_note", "입력값 기준 검토용입니다."))
        show_table("클레임/제조사 요약", legacy_features.get("claim_summary", pd.DataFrame()), height=240)
        show_table("제조사별 접수 TOP 10", legacy_features.get("claim_by_manufacturer", pd.DataFrame()).head(10), height=320)


def render_quality_feedback_preview(result: AnalysisResult) -> None:
    quality_feedback = result.analysis.get("quality_feedback", {})
    if not quality_feedback:
        return
    with st.expander("품질 피드백 후보 보기", expanded=False):
        st.caption(quality_feedback.get("quality_feedback_note", "입력값 기준 검토 후보입니다."))
        st.caption("표시 항목은 검토 후보이며, 원본 Raw를 자동 수정하지 않습니다.")
        show_table("품질 피드백 검토 후보 요약", quality_feedback.get("quality_feedback_summary", pd.DataFrame()), height=220)
        show_table("검토 후보 유형별 건수", quality_feedback.get("quality_feedback_by_candidate_type", pd.DataFrame()), height=240)
        show_table("클레임/제조사 입력 검토 후보 TOP 20", quality_feedback.get("quality_feedback_claim_candidates", pd.DataFrame()).head(20), height=360)
        show_table("유/무상/제조사 미입력 검토 후보 TOP 30", quality_feedback.get("quality_feedback_missing_field_candidates", pd.DataFrame()).head(30), height=420)
        show_table("부품/분류별 접수 검토 후보 TOP 20", quality_feedback.get("quality_feedback_part_category_candidates", pd.DataFrame()).head(20), height=360)


def render_proposal_pause_notice() -> None:
    with st.expander("제안 기능 (준비 중)", expanded=False):
        st.warning("제안 후보 기능은 아직 준비 중이에요. 담당자 확인 전에는 고객 자료로 사용하지 말아 주세요.")
        st.caption("현재 화면에서는 제안 후보 파일을 만들지 않습니다.")


def render_report_actions(
    result: AnalysisResult,
    *,
    localhost_access: bool,
    show_operator_materials: bool = True,
) -> None:
    st.subheader("리포트 다운로드")
    ppt_info, pdf_info = st.columns(2)
    with ppt_info:
        st.markdown("##### :material/slideshow: PowerPoint")
        st.caption("회사 양식 · 발표용 11장")
    with pdf_info:
        st.markdown("##### :material/picture_as_pdf: PDF")
        st.caption("A4 · 종합 현황과 업무유형별 상세")
    st.divider()

    stored = st.session_state.get("report_download_bundle")
    bundle: ReportDownloadBundle | None = None
    if isinstance(stored, dict) and stored.get("context_signature") == result.context_signature:
        candidate = stored.get("bundle")
        if isinstance(candidate, ReportDownloadBundle):
            bundle = candidate

    if st.button(
        "다시 만들기" if bundle else "PPT와 PDF 만들기",
        type="primary", use_container_width=True,
        icon=":material/description:", key="prepare_ppt_pdf_downloads",
    ):
        st.session_state.pop("report_download_bundle", None)
        bundle = None
        try:
            with st.spinner("리포트를 만들고 있습니다. 잠시만 기다려 주세요..."):
                bundle = generate_report_download_bundle(
                    result.analysis, result.narrative_lines,
                    period_range=result.period_range, filter_summary=result.filter_summary,
                )
            st.session_state["report_download_bundle"] = {
                "context_signature": result.context_signature, "bundle": bundle,
            }
        except Exception as error:
            st.error(str(error))

    if bundle is not None:
        for message in bundle.errors:
            st.warning(message)
        st.success("준비된 파일을 내려받으세요.")
        ppt_col, pdf_col = st.columns(2)
        if bundle.pptx_bytes:
            ppt_col.download_button(
                "PPT 다운로드", data=bundle.pptx_bytes, file_name=bundle.pptx_name,
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                key="download_ppt_report", use_container_width=True,
                icon=":material/download:", on_click="ignore",
            )
            ppt_col.caption(f"{len(bundle.pptx_bytes) / (1024 * 1024):.1f} MB")
        if bundle.pdf_bytes:
            pdf_col.download_button(
                "PDF 다운로드", data=bundle.pdf_bytes, file_name=bundle.pdf_name,
                mime="application/pdf", key="download_pdf_report", use_container_width=True,
                icon=":material/download:", on_click="ignore",
            )
            pdf_col.caption(f"{len(bundle.pdf_bytes) / 1024:.0f} KB")
    st.caption("생성 파일은 이 화면에서만 보관됩니다. 창을 닫기 전에 다운로드해 주세요.")

    if localhost_access:
        with st.expander("구조화 보고서 V2 · Word / PPTX", expanded=False):
            render_structured_report_actions(result)
        if show_operator_materials:
            with st.expander("운영자 보완 자료", expanded=False):
                render_raw_quality_downloads(result)
                render_standard_name_downloads(result)


def render_structured_report_actions(result: AnalysisResult) -> None:
    from as_report.report_payload import build_report_payload
    from as_report.report_tool import generate_structured_documents

    formats = st.multiselect("문서 형식", ["docx", "pptx"], default=["docx", "pptx"], key="v2_formats")
    state_key = (result.context_signature, result.run_timestamp, tuple(formats))
    stored = st.session_state.get("structured_report_downloads", {})
    outputs = stored.get("outputs", {}) if stored.get("key") == state_key else {}
    if st.button("V2 문서 만들기", key="prepare_v2_documents", disabled=not formats):
        outputs = {}
        st.session_state.pop("structured_report_downloads", None)
        try:
            generated_at = datetime.strptime(result.run_timestamp, "%Y%m%d_%H%M%S_%f").isoformat()
            payload = build_report_payload(
                result.analysis, result.narrative_lines, period_range=result.period_range,
                filters=result.filters, provenance=result.input_provenance,
                run_id=result.run_timestamp, owner=result.output_owner,
                generated_at=generated_at, analysis_version="as-report-0.1.0/payload-2.0",
            )
            with st.spinner("문서를 만들고 분석 조건을 확인하고 있습니다..."):
                outputs = generate_structured_documents(payload, tuple(formats))
            st.session_state["structured_report_downloads"] = {"key": state_key, "outputs": outputs}
        except (ValueError, ImportError, OSError) as error:
            st.error(f"V2 문서를 만들지 못했습니다: {error}")
    for name, content in outputs.items():
        st.download_button(name, content, file_name=name, key=f"v2_download_{name}", on_click="ignore")


def render_raw_quality_downloads(result: AnalysisResult) -> None:
    st.subheader("Raw 데이터 확인 파일")
    st.caption("이 영역은 localhost 운영자에게만 보여요. 입력값을 더 살펴봐야 할 때만 사용해 주세요.")
    st.caption("수동 보완용 Excel, Markdown, CSV는 원본 Raw 직접 수정 파일이 아닙니다.")
    if not result.raw_quality_result:
        st.info("Raw 품질 결과가 없으면 분석을 먼저 실행한 뒤 다시 확인하세요.")
        return

    user_output_dirs = build_user_output_dirs(REPORTS_DIR, result.output_owner)
    quality_col1, quality_col2, quality_col3 = st.columns(3)
    quality_excel_clicked = quality_col1.button("수동 보완용 Excel 준비", use_container_width=True)
    quality_markdown_clicked = quality_col2.button("Raw 품질 요약 준비", use_container_width=True)
    quality_csv_clicked = quality_col3.button("품질 플래그 CSV 준비", use_container_width=True)

    if quality_excel_clicked:
        quality_excel_path = Path(export_manual_review_workbook(result.raw_quality_result, REPORTS_DIR))
        record_output_history(result, "raw_quality_excel", quality_excel_path, note="localhost review output")
        st.success("수동 보완용 Excel이 준비됐어요.")
        st.download_button(
            "수동 보완용 Excel 다운로드",
            data=quality_excel_path.read_bytes(),
            file_name=quality_excel_path.name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_raw_quality_excel",
            use_container_width=True,
        )

    if quality_markdown_clicked:
        quality_markdown_path = Path(write_quality_summary_markdown(result.raw_quality_result, REPORTS_DIR))
        record_output_history(result, "raw_quality_markdown", quality_markdown_path, note="localhost review output")
        st.success("Raw 품질 요약이 준비됐어요.")
        st.download_button(
            "Raw 품질 요약 다운로드",
            data=quality_markdown_path.read_bytes(),
            file_name=quality_markdown_path.name,
            mime="text/markdown",
            key="download_raw_quality_markdown",
            use_container_width=True,
        )

    if quality_csv_clicked:
        quality_csv_path = Path(export_quality_flags_csv(result.raw_quality_result, user_output_dirs["quality"]))
        record_output_history(result, "raw_quality_flags_csv", quality_csv_path, note="localhost review output")
        st.success("품질 플래그 CSV가 준비됐어요.")
        st.download_button(
            "품질 플래그 CSV 다운로드",
            data=quality_csv_path.read_bytes(),
            file_name=quality_csv_path.name,
            mime="text/csv",
            key="download_raw_quality_flags",
            use_container_width=True,
        )


def render_standard_name_downloads(result: AnalysisResult) -> None:
    st.subheader("표준명 확인 파일")
    st.info("이 영역은 localhost 운영자에게만 보여요. 추천값을 확정된 표준명으로 자동 적용하지 않습니다.")
    if not result.raw_quality_result:
        st.info("표준명 확인 파일은 분석을 시작한 뒤 볼 수 있어요.")
        return

    user_output_dirs = build_user_output_dirs(REPORTS_DIR, result.output_owner)
    standard_col1, standard_col2, standard_col3 = st.columns(3)
    mapping_clicked = standard_col1.button("매핑 파일 상태 확인", use_container_width=True)
    unknown_clicked = standard_col2.button("Unknown 명칭 목록 준비", use_container_width=True)
    preview_clicked = standard_col3.button("표준명 미리보기 준비", use_container_width=True)

    if mapping_clicked:
        mapping_paths = ensure_standard_name_files(STANDARD_NAME_CONFIG_DIR)
        st.success("표준명칭 매핑 파일 상태를 확인했어요.")
        show_table(
            "표준명칭 매핑 파일",
            pd.DataFrame(
                [
                    {"mapping_file": name, "상태": "사용 가능" if Path(path).exists() else "확인 필요"}
                    for name, path in mapping_paths.items()
                ]
            ),
            height=300,
        )

    if unknown_clicked:
        unknown_df = result.unknown_standard_names_df if result.unknown_standard_names_df is not None else pd.DataFrame()
        unknown_workbook_path = Path(export_unknown_standard_names_workbook(unknown_df, user_output_dirs["standardization"]))
        record_output_history(result, "unknown_standard_names_xlsx", unknown_workbook_path, note="localhost review output")
        st.success("Unknown 명칭 목록이 준비됐어요.")
        st.download_button(
            "Unknown 명칭 목록 다운로드",
            data=unknown_workbook_path.read_bytes(),
            file_name=unknown_workbook_path.name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_unknown_standard_names",
            use_container_width=True,
        )

    if preview_clicked:
        standard_preview = result.standard_preview_df if result.standard_preview_df is not None else pd.DataFrame()
        preview_csv_path = Path(export_standard_name_preview_csv(standard_preview, user_output_dirs["standardization"]))
        record_output_history(result, "standard_name_preview_csv", preview_csv_path, note="localhost review output")
        st.success("표준명칭 미리보기가 준비됐어요.")
        st.download_button(
            "표준명칭 미리보기 다운로드",
            data=preview_csv_path.read_bytes(),
            file_name=preview_csv_path.name,
            mime="text/csv",
            key="download_standard_name_preview",
            use_container_width=True,
        )


def standard_preview_columns(dataframe: pd.DataFrame) -> list[str]:
    if dataframe.empty:
        return []
    base_columns = ["접수일", "고객사", "BOOTH", "LINE", "공정", "ZONE", "설비명", "로보트 NO", "로보트 기종"]
    preview_columns = [column for column in dataframe.columns if column.endswith("_표준명_후보") or column.endswith("_표준명_매핑상태")]
    return [column for column in [*base_columns, *preview_columns] if column in dataframe.columns]


def record_output_history(result: AnalysisResult, output_type: str, output_path: Path, status: str = "success", note: str = "") -> Path:
    provenance = result.input_provenance or {}
    files = provenance.get("files", {}) if isinstance(provenance, dict) else {}
    raw = files.get("as_raw", {}) if isinstance(files, dict) else {}
    metadata_path = output_path.parent / f"run_metadata_{result.run_timestamp}.json"
    return append_report_history(
        {
            "run_id": result.run_timestamp,
            "input_set_id": "",
            "input_set_signature": provenance.get("input_signature", ""),
            "user_name": result.output_owner,
            "period_type": result.period_range.period,
            "start_date": result.period_range.start_date.isoformat(),
            "end_date": result.period_range.end_date.isoformat(),
            "source_file": result.source_name,
            "source_path": raw.get("path", ""),
            "source_sha256": raw.get("sha256", ""),
            "source_row_count": raw.get("row_count", ""),
            "source_date_min": raw.get("date_min", ""),
            "source_date_max": raw.get("date_max", ""),
            "customer_master_file": "",
            "customer_master_sha256": "",
            "failure_master_file": "",
            "failure_master_sha256": "",
            "run_metadata_path": metadata_path if metadata_path.exists() else "",
            "output_type": output_type,
            "output_path": output_path,
            "status": status,
            "note": note,
        },
        base_dir=REPORTS_DIR,
    )


if __name__ == "__main__":
    main()
