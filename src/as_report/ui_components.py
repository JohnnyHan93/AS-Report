from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

DOWNTIME_COLUMN = "라인 중단 시간 (분)"


def show_kpi_cards(kpi: dict[str, Any]) -> None:
    items = [
        ("총 접수 건수", f"{int(kpi.get('총 접수 건수', 0)):,}건"),
        ("처리완료 건수", f"{int(kpi.get('처리완료 건수', 0)):,}건"),
        ("미완료 건수", f"{int(kpi.get('미완료 건수', 0)):,}건"),
        ("처리완료율", f"{float(kpi.get('처리완료율', 0)):.1f}%"),
        ("긴급방문 건수", f"{int(kpi.get('긴급방문 건수', 0)):,}건"),
        ("라인 중단 시간(입력 건 기준)", f"{float(kpi.get('라인 중단 총 시간', 0)):,.0f}분"),
        ("라인 중단 발생 건수", f"{int(kpi.get('라인 중단 발생 건수', 0)):,}건"),
        ("고객사 미입력 건수", f"{int(kpi.get('고객사 미입력 건수', 0)):,}건"),
    ]
    for row_start in range(0, len(items), 4):
        columns = st.columns(4)
        for column, (label, value) in zip(columns, items[row_start : row_start + 4]):
            column.metric(label, value)


def show_plotly_chart(dataframe: pd.DataFrame, chart_type: str, label: str, value: str, title: str) -> None:
    if dataframe.empty or label not in dataframe.columns or value not in dataframe.columns:
        st.info(f"{title}: 표시할 데이터가 없습니다.")
        return
    fig = build_chart(dataframe, chart_type, label, value, title)
    theme_mode = st.session_state.get("app_theme_mode", "시스템 설정")
    dark = theme_mode == "다크 모드" or (
        theme_mode == "시스템 설정" and st.context.theme.type == "dark"
    )
    fig.update_layout(
        template="plotly_dark" if dark else "plotly_white",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#ecf2ef" if dark else "#202b33",
    )
    st.plotly_chart(fig, use_container_width=True)


def build_chart(dataframe: pd.DataFrame, chart_type: str, label: str, value: str, title: str):
    display = dataframe.copy()
    if chart_type == "line":
        fig = px.line(display, x=label, y=value, title=title, markers=True, text=value)
        fig.update_traces(textposition="top center")
    elif chart_type == "donut":
        fig = px.pie(display, names=label, values=value, title=title, hole=0.5)
        fig.update_traces(textposition="inside", textinfo="percent+label")
    elif chart_type == "hbar":
        display = display.sort_values(value, ascending=True)
        fig = px.bar(display, x=value, y=label, title=title, orientation="h", text=value)
        fig.update_traces(textposition="outside", cliponaxis=False)
    else:
        fig = px.bar(display, x=label, y=value, title=title, text=value)
        fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(
        template="plotly_white",
        height=380,
        margin={"l": 24, "r": 24, "t": 58, "b": 48},
        font={"family": "Malgun Gothic, Arial, sans-serif"},
    )
    return fig


def show_table(title: str, dataframe: pd.DataFrame, height: int = 360) -> None:
    st.subheader(title)
    if dataframe.empty:
        st.info("표시할 데이터가 없습니다.")
        return
    display = dataframe.copy()
    for column in display.columns:
        if pd.api.types.is_datetime64_any_dtype(display[column]):
            display[column] = display[column].dt.strftime("%Y-%m-%d").fillna("")
    st.dataframe(display, use_container_width=True, height=height, hide_index=True)


def quality_to_dataframe(quality: dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame([{"항목": key, "값": value} for key, value in quality.items()])
