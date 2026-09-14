from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


def render_pdf_report(payload: dict[str, Any]) -> str:
    """Render a static print document from the same aggregates as the PPT."""
    environment = Environment(
        loader=FileSystemLoader(Path(__file__).parent / "templates"),
        autoescape=select_autoescape(["html"]),
    )
    months = payload.get("monthly_status", [])
    month_pages = [months[index:index + 12] for index in range(0, len(months), 12)] or [[]]
    details = list(payload["work_type_details"].values())
    detail_pages = [details[index:index + 3] for index in range(0, len(details), 3)]
    return environment.get_template("report_pdf.html").render(
        report=payload, month_pages=month_pages, detail_pages=detail_pages,
    )
