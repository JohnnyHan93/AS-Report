from __future__ import annotations

from pathlib import Path

from as_report.loader import LoadedData, load_input

CUSTOMER_ROBOT_REQUIRED_COLUMNS = [
    "*ID",
    "설치연도(Installation year)",
    "고객사(Customer)",
    "위치(Location)",
    "공장(plant)",
    "BOOTH",
    "LINE",
    "ZONE",
    "Robot No",
    "공정-대분류 (major category)",
    "공정-중분류 (middle category)",
    "컨트롤러(Controller)",
]


def load_customer_robot_master(path: str | Path) -> LoadedData:
    """Load the customer robot master CSV without modifying it."""
    return load_input(path, required_columns=CUSTOMER_ROBOT_REQUIRED_COLUMNS)
