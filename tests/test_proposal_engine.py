from __future__ import annotations

import pandas as pd

from as_report.proposal import build_proposal_candidates, export_proposal_outputs


def _as_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "접수일": pd.Timestamp("2026-06-01"),
                "고객사": "A",
                "BOOTH": "상도",
                "LINE": "1 Line",
                "공정": "도장",
                "로보트 NO": "R1",
                "로보트 기종": "GP25",
                "설치년도": "2021",
                "대분류": "로보트",
                "중분류": "구동부",
                "소분류 (고장부품)": "감속기",
                "고장원인": "감속기 소음",
                "접수 내용 (요약)": "R1 감속기 abnormal noise",
            }
        ]
    )


def _robot_master() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "*ID": "M1",
                "설치연도(Installation year)": "2021",
                "고객사(Customer)": "A",
                "공장(plant)": "1공장",
                "BOOTH": "상도",
                "LINE": "1 Line",
                "Robot No": "R1",
                "본체(Manifold)": "GP25",
                "컨트롤러(Controller)": "YRC1000",
                "공정-대분류 (major category)": "도장",
                "공정-중분류 (middle category)": "상도",
            },
            {
                "*ID": "M2",
                "설치연도(Installation year)": "2021",
                "고객사(Customer)": "B",
                "공장(plant)": "2공장",
                "BOOTH": "상도",
                "LINE": "2 Line",
                "Robot No": "R2",
                "본체(Manifold)": "GP25",
                "컨트롤러(Controller)": "YRC1000",
                "공정-대분류 (major category)": "도장",
                "공정-중분류 (middle category)": "상도",
            },
        ]
    )


def _failure_master() -> pd.DataFrame:
    return pd.DataFrame([{"*ID": "P1", "품명": "감속기", "중분류": "구동부", "대분류": "로보트", "검색용": "감속기", "제조사": "Maker"}])


def test_proposal_engine_builds_preview_without_mutating_sources() -> None:
    as_df = _as_df()
    robot_master = _robot_master()
    failure_master = _failure_master()
    original_as = as_df.copy(deep=True)
    original_master = robot_master.copy(deep=True)

    result = build_proposal_candidates(as_df, robot_master, failure_master, analysis_period="2026-01-01 ~ 2026-12-31", current_year=2026)

    pd.testing.assert_frame_equal(as_df, original_as)
    pd.testing.assert_frame_equal(robot_master, original_master)
    assert not result.preventive_candidates.empty
    assert result.preventive_candidates.iloc[0]["inspection_item"] == "감속기/구동부 점검"
    assert bool(result.preventive_candidates.iloc[0]["top_candidate"]) is True
    assert not result.horizontal_candidates.empty
    assert result.horizontal_candidates.iloc[0]["proposal_type"] == "horizontal_deployment_candidate"
    assert result.horizontal_candidates.iloc[0]["top_candidate_level"] == "High"
    assert result.summary["horizontal_top_candidate_count"] == 1


def test_horizontal_candidate_skips_age_based_when_source_install_year_missing() -> None:
    as_df = _as_df()
    as_df.loc[0, "설치년도"] = ""

    result = build_proposal_candidates(as_df, _robot_master(), _failure_master(), current_year=2026)

    assert not result.preventive_candidates.empty
    assert result.horizontal_candidates.empty


def test_proposal_exporter_writes_disclaimer(tmp_path) -> None:
    result = build_proposal_candidates(_as_df(), _robot_master(), _failure_master(), analysis_period="2026", current_year=2026)

    paths = export_proposal_outputs(result, tmp_path, timestamp="20260630_120000")

    summary = paths["proposal_candidate_summary"].read_text(encoding="utf-8")
    assert "본 자료는 입력 데이터와 master 매칭 결과를 기반으로 한 제안 후보입니다." in summary
    assert paths["preventive_maintenance_candidates"].exists()
    assert paths["horizontal_deployment_candidates"].exists()
    assert paths["proposal_top_candidates"].exists()
    assert paths["proposal_customer_summary"].exists()
    refined = paths["proposal_candidate_summary_refined"].read_text(encoding="utf-8")
    assert "preventive all candidate count" in refined
    assert "horizontal TOP candidate count" in refined
    assert "고객 제안 전 담당자 검토가 필요합니다." in refined


def test_proposal_rules_route_non_robot_items_away_from_torque_waveform() -> None:
    as_df = pd.DataFrame(
        [
            {**_as_df().iloc[0].to_dict(), "소분류 (고장부품)": "FGP", "고장원인": "FGP pump drive", "접수 내용 (요약)": "Applicator pump drive error"},
            {**_as_df().iloc[0].to_dict(), "소분류 (고장부품)": "CPU", "고장원인": "Controller CPU 통신", "접수 내용 (요약)": "Controller OS communication fault"},
            {**_as_df().iloc[0].to_dict(), "소분류 (고장부품)": "JOB", "고장원인": "System S/W JOB", "접수 내용 (요약)": "모니터링 시스템 JOB 원격지원 필요"},
            {**_as_df().iloc[0].to_dict(), "소분류 (고장부품)": "축", "고장원인": "Axis torque collision", "접수 내용 (요약)": "Robot torque waveform check"},
        ]
    )

    result = build_proposal_candidates(as_df, _robot_master(), _failure_master(), current_year=2026)
    items = result.preventive_candidates["inspection_item"].tolist()

    assert "도장기/Applicator/전장 점검 후보" in items
    assert "컨트롤러/제어부 점검 후보" in items
    assert "유지보수 계약/원격지원 관리 후보" in items
    assert "로봇 토크파형 측정" in items
