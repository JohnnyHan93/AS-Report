from __future__ import annotations

DATE_COLUMN = "접수일"
ID_COLUMN = "*ID"
DOWNTIME_COLUMN = "라인 중단 시간 (분)"
PART_REPAIR_WORK_TYPE = "A/S대응(부품수리/클레임처리)"

MISSING_MARKERS = {"", "선택안함", "--", "#NAME?", "기타", "nan", "None", "NaN", "<NA>"}
ERROR_MARKERS = {"#NAME?"}
DETAIL_REQUIRED_MARKERS = {"기타"}

BASE_REVIEW_FIELDS = [
    "고객사",
    "BOOTH",
    "LINE",
    "공정",
    "로보트 NO",
    "로보트 기종",
    "고장원인",
    DOWNTIME_COLUMN,
    "설치년도",
    "대분류",
    "중분류",
    "소분류 (고장부품)",
]
CONDITIONAL_FIELDS = ["유/무상", "제조사"]
TRACE_COLUMNS = [ID_COLUMN, DATE_COLUMN, "업무유형", "접수사원", "접수 내용 (요약)", "처리내용/진행상황 (요약)"]

QUALITY_COLUMNS = [
    "대상구분_정제",
    "고객사_정제",
    "위치상태_정제",
    "로보트대상수_정제",
    "로봇기종_정제",
    "분류상태_정제",
    "조건부입력_제외필드",
    "보완필요필드",
    "보완방법",
    "보완난이도",
    "보완필요여부",
    "보완우선순위",
    "보완메모",
    "추천검색방법",
    "접수내용_요약검색어",
]

MANUAL_REVIEW_COLUMNS = [
    "추천 검색방법",
    DATE_COLUMN,
    "고객사",
    "업무유형",
    "접수사원",
    ID_COLUMN,
    "보완 필요 필드",
    "보완 판단 사유",
    "우선순위",
    "접수내용 요약 검색어",
    "참고용 원본ID",
]

TARGET_TYPES = [
    "단일로보트",
    "다중로보트",
    "라인전체",
    "시스템_현장기기_주변장치",
    "부품수리_클레임_설치_시운전_개선",
    "고객문의_VOC",
    "기타_교육_테스트_미확정",
    "미확정",
]
