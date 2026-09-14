"""Read-only web previews using the report generation payload."""
from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from as_report.report_pdf import render_pdf_report

SLIDE_TITLES = (
    "A/S 현황 리포트", "목차", "A/S 종합 현황", "월별 접수 및 처리 추이",
    "고객사·업무유형별 접수 현황", "설비·부품별 접수 현황",
    "긴급방문 접수 현황", "일반방문 접수 현황", "원격 지원 접수 현황",
    "부품 수리·클레임 접수 현황", "VOC 및 기타 접수 현황",
)


def build_slide_preview(payload: dict[str, Any], index: int) -> dict[str, Any]:
    if not 0 <= index < len(SLIDE_TITLES):
        raise ValueError("Invalid slide index")
    slide: dict[str, Any] = {
        "title": SLIDE_TITLES[index], "number": index + 1,
        "metrics": [], "panels": [], "lines": [], "description": "", "details": [],
    }

    def panel(title: str, rows: list, label: str, value: str = "접수 건수", unit: str = "건") -> dict:
        return {"title": title, "rows": rows, "label": label, "value": value, "unit": unit}

    if index == 1:
        slide["lines"] = list(SLIDE_TITLES[2:])
    elif index == 2:
        slide.update(metrics=payload["kpis"], lines=payload["narrative"])
    elif index == 3:
        slide["panels"] = [
            panel("월별 접수 건수", payload["monthly"], "기간_연월"),
            panel("월별 처리 완료율", payload["monthly_completion"], "기간_연월", "처리완료율", "%"),
        ]
    elif index == 4:
        slide["panels"] = [
            panel("접수 건수 상위 10개 고객사", payload["customers"], "고객사"),
            panel("업무유형별 접수 건수", payload["work_types"], "업무유형구분"),
        ]
    elif index == 5:
        slide["panels"] = [
            panel("대분류별 접수 건수", payload["categories"], "대분류"),
            panel("접수 건수 상위 10개 고장부품", payload["parts"], "소분류 (고장부품)"),
        ]
    elif 6 <= index <= 9:
        key = ("emergency", "general", "remote", "claim")[index - 6]
        detail = payload["work_type_details"][key]
        slide["metrics"] = detail["kpis"]
        slide["panels"] = [
            panel("월별 접수 건수", detail["monthly"], "기간_연월"),
            panel("제조사별 접수 건수", payload["manufacturers"], "제조사") if key == "claim"
            else panel("주요 고객사", detail["customers"], "고객사"),
        ]
    elif index == 10:
        details = [payload["work_type_details"][key] for key in ("voc", "other")]
        slide.update(description=payload["other_description"], details=details)
        slide["panels"] = [panel(f"{detail['label']} 주요 고객사", detail["customers"], "고객사") for detail in details]
    return slide


def render_slide_preview(payload: dict[str, Any], index: int) -> str:
    root = Path(__file__).parent
    environment = Environment(loader=FileSystemLoader(root / "templates"), autoescape=select_autoescape(["html"]))
    logo = base64.b64encode((root / "resources" / "company_logo.png").read_bytes()).decode("ascii")
    return environment.get_template("report_slide_preview.html").render(
        report=payload, slide=build_slide_preview(payload, index), logo=logo,
    )


def render_document_preview(payload: dict[str, Any]) -> str:
    # Only screen CSS is appended; export HTML and its print rules remain untouched.
    screen_style = """<style>
    @media screen {
      body { background:#e9edef; padding:16px; }
      .page { background:white; width:min(100%, 794px); margin:0 auto 20px;
              padding:32px; min-height:900px; border:1px solid #dce3e1; }
      @media (max-width:540px) {
        body { padding:6px; } .page { padding:18px; min-height:0; }
        .grid { grid-template-columns:1fr; gap:18px; }
        .metrics { grid-template-columns:repeat(2,minmax(0,1fr)); }
        h1 { font-size:22px; } .running { flex-wrap:wrap; }
        .barrow { grid-template-columns:minmax(0,1fr) 70px 30px; }
      }
    }
    </style>"""
    return render_pdf_report(payload).replace("</head>", screen_style + "</head>", 1)
