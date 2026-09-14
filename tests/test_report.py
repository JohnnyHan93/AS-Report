from __future__ import annotations

from argparse import Namespace
import json
import re

from as_report.cli import build_parser, generate_report
from as_report.report_html import COMPARISON_COLOR_MAP, comparison_chart_frame
from conftest import sample_dataframe


def _chart_blocks(html: str) -> list[str]:
    blocks: list[str] = []
    marker = '<div class="chart-slot"'
    index = 0
    while True:
        start = html.find(marker, index)
        if start == -1:
            return blocks
        position = html.find(">", start) + 1
        depth = 1
        while depth > 0 and position < len(html):
            next_open = html.find("<div", position)
            next_close = html.find("</div>", position)
            if next_close == -1:
                break
            if next_open != -1 and next_open < next_close:
                depth += 1
                position = next_open + 4
            else:
                depth -= 1
                position = next_close + 6
        blocks.append(html[start:position])
        index = position


def _plotly_trace_payloads(html: str) -> list[list[object]]:
    payloads: list[list[object]] = []
    decoder = json.JSONDecoder()
    index = 0
    while True:
        call_start = html.find("Plotly.newPlot(", index)
        if call_start == -1:
            return payloads
        data_start = html.find("[", call_start)
        if data_start == -1:
            index = call_start + 1
            continue
        try:
            payload, offset = decoder.raw_decode(html[data_start:])
        except json.JSONDecodeError:
            index = call_start + 1
            continue
        if isinstance(payload, list):
            payloads.append(payload)
        index = data_start + offset


def _strings_from_json(value: object):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from _strings_from_json(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _strings_from_json(nested)


def _chart_slots_are_visible_or_explained(html: str) -> bool:
    return all(
        ("plotly-graph-div" in block and "Plotly.newPlot" in block)
        or "empty-state" in block
        or "empty-chart" in block
        or "no-data" in block
        for block in _chart_blocks(html)
    )


def _plotly_div_ids(html: str) -> list[str]:
    return re.findall(r'<div id="([^"]+)" class="plotly-graph-div"', html)


def _plotly_newplot_targets(html: str) -> list[str]:
    return re.findall(r'Plotly\.newPlot\(\s*"([^"]+)"', html)


def _detail_blocks(html: str) -> list[str]:
    return re.findall(r'<details class="detail-table-block"[^>]*>.*?</details>', html, re.DOTALL)


def _detail_opening_tags(html: str) -> list[str]:
    return re.findall(r'<details class="detail-table-block"[^>]*>', html)


def _detail_block_by_summary(html: str, summary: str) -> str:
    match = re.search(
        rf'<details class="detail-table-block"[^>]*>\s*<summary>{re.escape(summary)}</summary>.*?</details>',
        html,
        re.DOTALL,
    )
    assert match is not None
    return match.group(0)


def _visible_body_text(html: str) -> str:
    body_match = re.search(r"<body[^>]*>(.*?)</body>", html, re.DOTALL | re.IGNORECASE)
    body = body_match.group(1) if body_match else html
    body = re.sub(r"<script\b[^>]*>.*?</script>", "", body, flags=re.DOTALL | re.IGNORECASE)
    body = re.sub(r"<style\b[^>]*>.*?</style>", "", body, flags=re.DOTALL | re.IGNORECASE)
    return re.sub(r"<[^>]+>", " ", body)


def test_cli_accepts_only_explicit_raw_input_for_data_sources() -> None:
    parser = build_parser()
    destinations = {action.dest for action in parser._actions}

    assert "input" in destinations
    assert next(action for action in parser._actions if action.dest == "input").required is True
    assert "input_set" not in destinations
    assert "customer_master" not in destinations
    assert "failure_master" not in destinations
    assert "gate_b_validation" not in destinations


def test_empty_period_report_files_are_created(tmp_path):
    input_path = tmp_path / "issues.csv"
    output_dir = tmp_path / "reports"
    sample_dataframe().to_csv(input_path, index=False, encoding="utf-8-sig")

    result = generate_report(
        Namespace(
            input=str(input_path),
            period="custom",
            year=None,
            half=None,
            quarter=None,
            start="2023-01-01",
            end="2023-12-31",
            output=str(output_dir),
        )
    )

    html = result.html_path.read_text(encoding="utf-8")

    assert result.total_count == 0
    assert result.html_path.exists()
    assert result.excel_path.exists()
    assert "분석 대상 기간에 접수된 이슈가 없습니다." in html
    assert "empty-state" in html
    assert _chart_slots_are_visible_or_explained(html)


def test_main_html_keeps_raw_quality_compact(tmp_path):
    input_path = tmp_path / "issues.csv"
    output_dir = tmp_path / "reports"
    source = sample_dataframe()
    source.loc[source["*ID"].isin([1, 2]), ["접수 내용 (요약)", "처리내용/진행상황 (요약)"]] = ""
    source.to_csv(input_path, index=False, encoding="utf-8-sig")

    result = generate_report(
        Namespace(
            input=str(input_path),
            period="year",
            year=2025,
            half=None,
            quarter=None,
            start=None,
            end=None,
            output=str(output_dir),
        )
    )

    html = result.html_path.read_text(encoding="utf-8")
    visible_text = _visible_body_text(html)

    assert "AS_REPORT_LAYOUT_VERSION: AS17_BRIEFING" in html
    assert "리포트 레이아웃</strong>: AS17_BRIEFING" in html
    assert "보고 기간 기준</strong>: 접수일" in html
    assert "A/S 운영 브리핑" in visible_text
    assert "생성일시" in visible_text
    assert "Raw 원본" in visible_text
    assert "분석 입력" in visible_text
    assert "04. ES_ 이슈사항 보고 단일 Raw" in visible_text
    assert "Master 기준" not in visible_text
    assert "승인 입력 세트 Gate B 검증" not in html
    assert "로보트 기종별 등록 설치대수 기준 대당 AS 접수건수" not in html
    assert "핵심 브리핑" in html
    assert "기간 변동" in html
    assert "집중 발생 영역" in html
    assert "라인 영향" in html
    assert "반복 검토 후보" in html
    assert "상세 확인 Appendix" in html
    assert "접수 흐름" in visible_text
    assert "보고 기준" in visible_text
    assert "집중 영역" in visible_text
    assert "반복 검토" in visible_text
    assert "후보 순위" in visible_text
    assert "상세 확인" in visible_text
    assert "Raw 데이터 품질 상태" in html
    assert "상세 Raw 품질 검증 결과는 별도 Raw 데이터 품질 Markdown/Excel/CSV 산출물을 참조하십시오." in html
    assert "보완 필요" in visible_text
    assert "WARNING" not in visible_text
    assert "PASS" not in visible_text
    assert "BLOCKED" not in visible_text
    assert "BOOTH 미입력 건수" not in html
    assert "LINE 미입력 건수" not in html
    assert "공정 미입력 건수" not in html
    assert "고장원인 미입력 건수" not in html
    assert "선택안함 정리 건수" not in html
    assert "주요 보완 필요 필드 TOP 5" not in html
    assert "수동 보완 우선 항목 TOP 10" not in html
    assert "본 보고서는 입력 데이터에서 계산 가능한 사실만 요약하며, 원인 추정이나 개선 효과를 임의로 작성하지 않습니다." not in html
    assert "라인 중단 시간은 입력 건 기준 참고값" in html
    assert "월별 라인 중단 시간" in html
    assert "고객사별 라인 중단 시간 TOP 10" in html
    assert "전체 Excel 기준" in html
    assert html.count('class="plotly-graph-div"') >= 3

    assert "PDF 저장 안내" not in html
    assert "Ctrl+P" not in html
    assert "용지는 A4" not in html
    assert "배경 그래픽 인쇄" not in html
    assert "<h2>Executive Summary</h2>" not in html
    assert "Executive Summary" not in html
    assert "메인 대시보드" not in html
    assert "KPI Detail" not in html
    assert "차트 코멘트" not in html
    assert "비교 코멘트" not in html
    assert "반복 후보 코멘트" not in html
    assert "반복 이슈 후보" not in html
    assert "A/S Operation Briefing" not in visible_text
    assert "Reception Trend" not in visible_text
    assert "Safe Notes" not in visible_text
    assert "Customer Impact" not in visible_text
    assert "Report layout" not in visible_text
    assert "Generated at" not in visible_text
    assert "Raw source" not in visible_text
    assert "Master source" not in visible_text
    assert "Report period basis" not in visible_text
    assert "라인 중단 입력값" in visible_text
    assert "고장률" not in html
    assert "MTTR" not in html
    assert "고질불량" not in html
    assert "원인으로 판단" not in html
    assert "노후화로 인해" not in html
    assert "관리 미흡" not in html
    assert "개선 효과" not in html
    assert "효과 보장" not in html
    assert "비용 절감" not in html
    assert "생산손실 확정" not in html
    assert "metric-card" in html
    assert "analysis-card" in html
    assert "chart-slot" in html
    assert "insight-note" in html
    assert "metric-card--blue" in html
    assert "metric-card--green" in html
    assert "metric-card--amber" in html

    appendix = html.split("<h2>상세 확인 Appendix</h2>", 1)[1]
    assert "접수일 누락 건수" not in appendix
    assert "대분류 미입력 건수" not in appendix
    assert "라인 중단 시간(입력 건 기준)" in appendix
    detail_blocks = _detail_blocks(appendix)
    detail_opening_tags = _detail_opening_tags(appendix)
    required_summaries = [
        "세부 지표 상세 보기",
        "기간 비교 상세 표 보기",
        "반복 검토 후보 상세 표 보기",
        "고객사 상세 표 보기",
        "설비/장비 상세 표 보기",
        "월별 및 업무유형 상세 표 보기",
        "상세 이슈 목록 보기",
        "미완료 이슈 상세 표 보기",
        "Raw 품질 상세 보기",
    ]
    assert len(detail_blocks) >= len(required_summaries)
    for summary in required_summaries:
        assert f"<summary>{summary}</summary>" in appendix
    assert all(" open" not in tag for tag in detail_opening_tags)
    assert all(
        any(marker in block for marker in ["data-table", "metric-card", "issue-table-wrap", "empty-table", "empty-state", "no-data"])
        for block in detail_blocks
    )
    assert "appendix-comparison" in appendix
    assert "appendix-customer-top10" in appendix
    assert "appendix-equipment-top10" in appendix
    assert "appendix-open-issues" in appendix
    assert "appendix-raw-quality" in appendix
    downtime_issue_block = _detail_block_by_summary(appendix, "상세 이슈 목록 보기")
    open_issue_block = _detail_block_by_summary(appendix, "미완료 이슈 상세 표 보기")
    for block in [downtime_issue_block, open_issue_block]:
        assert "<th>접수내용</th>" in block
        assert "<th>조치이력</th>" in block
        assert "<th>처리상태</th>" in block
        assert 'class="full-text-col"><div class="issue-text-full">미입력</div></td>' in block
        assert 'class="full-text-col"><div class="issue-text-full">' in block
    assert _chart_slots_are_visible_or_explained(html)

    div_ids = _plotly_div_ids(html)
    newplot_targets = _plotly_newplot_targets(html)
    assert len(div_ids) == len(set(div_ids))
    assert len(newplot_targets) == len(set(newplot_targets))
    assert set(newplot_targets) <= set(div_ids)

    forbidden_trace_colors = {"#000001", "#000000", "black"}
    trace_strings = {
        value.lower()
        for payload in _plotly_trace_payloads(html)
        for trace in payload
        for value in _strings_from_json(trace)
    }
    assert trace_strings.isdisjoint(forbidden_trace_colors)
    assert {"#2563eb", "#16a34a", "#475569"} <= trace_strings


def test_comparison_chart_orders_previous_before_current():
    import pandas as pd

    dataframe = pd.DataFrame(
        [
            {
                "항목": "총 접수 건수",
                "현재 기간 값": 10,
                "전년 동기 값": 7,
                "직전 기간 값": "-",
            }
        ]
    )

    chart_frame, value_columns = comparison_chart_frame(dataframe)

    assert value_columns == ["전년 동기 값", "직전 기간 값", "현재 기간 값"]
    assert chart_frame["비교 기준"].cat.categories.tolist() == value_columns
    assert COMPARISON_COLOR_MAP["현재 기간 값"] == "#2563eb"
    assert COMPARISON_COLOR_MAP["전년 동기 값"] == "#475569"
    assert COMPARISON_COLOR_MAP["직전 기간 값"] == "#f59e0b"
