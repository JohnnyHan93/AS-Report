from __future__ import annotations

from as_report.reporting.display_formatters import (
    evaluate_repeat_condition_quality,
    format_count,
    format_minutes,
    format_percent,
    format_repeat_condition_display,
)


def test_format_repeat_condition_display_removes_field_names() -> None:
    assert format_repeat_condition_display("고객사=HMMME / 대분류=도장기 / 중분류=EVO") == "HMMME 도장기 EVO"
    assert format_repeat_condition_display("BOOTH=상도 / LINE=1 Line / 공정=Clear-Exterior / 대분류=로보트") == "상도 1 Line Clear-Exterior 로보트"
    assert format_repeat_condition_display("로보트 기종=GP25 / 소분류 (고장부품)=OS카드") == "GP25 OS카드"
    assert format_repeat_condition_display("대분류=로보트") == "로보트"


def test_repeat_condition_quality_flags_missing_values() -> None:
    assert evaluate_repeat_condition_quality("고객사=HMMME / 대분류=도장기 / 중분류=EVO") == "normal"
    assert evaluate_repeat_condition_quality("고객사=HMMME / 대분류=미입력 / 중분류=EVO") == "low_confidence"
    assert evaluate_repeat_condition_quality("BOOTH=미입력 / LINE=미입력 / 공정=미입력 / 대분류=도장기") == "data_quality_issue"
    assert evaluate_repeat_condition_quality("고객사=HMMME / 중분류=기타 (확인필요) / 소분류 (고장부품)=Reducer") == "low_confidence"


def test_unit_formatters() -> None:
    assert format_count(42) == "42건"
    assert format_minutes(90.0) == "90분"
    assert format_minutes(18.5) == "18.5분"
    assert format_percent(42.9) == "42.9%"
