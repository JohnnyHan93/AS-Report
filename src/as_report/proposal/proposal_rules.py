from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InspectionRule:
    rule_id: str
    inspection_item: str
    applicability_group: str
    keywords: tuple[str, ...]


INSPECTION_RULES = [
    InspectionRule(
        "remote_maintenance",
        "유지보수 계약/원격지원 관리 후보",
        "software_remote_support",
        ("system s/w", "s/w", "job", "모니터링 시스템", "monitoring system", "monitoring", "원격지원", "remote"),
    ),
    InspectionRule(
        "controller_control",
        "컨트롤러/제어부 점검 후보",
        "controller_control",
        ("controller", "컨트롤러", "cpu", "os", "통신", "communication", "제어부", "제어"),
    ),
    InspectionRule(
        "paint_applicator_electrical",
        "도장기/Applicator/전장 점검 후보",
        "paint_applicator_electrical",
        ("fgp", "pcs", "applicator", "어플리케이터", "drive", "pump", "펌프", "도장기", "전장"),
    ),
    InspectionRule(
        "brake_check",
        "브레이크 점검",
        "robot_mechanical",
        ("brake", "브레이크", "brake release", "axis drop", "축 처짐", "holding", "홀딩"),
    ),
    InspectionRule(
        "wrist_axis_clearance",
        "손목축 유격 점검",
        "robot_mechanical",
        ("wrist", "손목", "r축", "b축", "t축", "backlash", "유격", "abnormal vibration", "진동"),
    ),
    InspectionRule(
        "torque_waveform",
        "로봇 토크파형 측정",
        "robot_axis_torque",
        ("robot torque", "로봇 토크", "로보트 토크", "axis", "축", "encoder", "엔코더", "collision", "충돌", "torque", "토크", "servo", "서보", "motor", "모터"),
    ),
    InspectionRule(
        "encoder_cable",
        "엔코더/케이블 점검",
        "robot_cable",
        ("1325", "케이블", "cable"),
    ),
    InspectionRule(
        "reducer_drive",
        "감속기/구동부 점검",
        "robot_mechanical",
        ("reducer", "감속기", "gear", "기어", "abnormal noise", "이음", "소음"),
    ),
    InspectionRule(
        "axis_precision",
        "축별 정밀점검",
        "robot_axis_precision",
        ("robot stop", "로봇 정지", "로보트 정지", "axis", "축", "alarm", "알람"),
    ),
]


PROPOSAL_DISCLAIMER = (
    "본 자료는 입력 데이터와 master 매칭 결과를 기반으로 한 제안 후보입니다.\n"
    "고장 원인 확정, 예방 효과 보장, 비용 절감 효과를 의미하지 않습니다.\n"
    "고객 제안 전 담당자 검토가 필요합니다.\n"
    "원본 Raw CSV와 master CSV는 수정하지 않았습니다."
)
