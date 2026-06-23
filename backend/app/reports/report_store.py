from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any

from backend.app.core.config import settings

REPORT_ID_RE = re.compile(r"^[a-f0-9]{12}$")


def _report_dir(report_id: str) -> Path:
    if not REPORT_ID_RE.match(report_id):
        raise ValueError("Invalid report id.")
    directory = (settings.reports_dir / report_id).resolve()
    root = settings.reports_dir.resolve()
    try:
        directory.relative_to(root)
    except ValueError as exc:
        raise ValueError("Invalid report path.") from exc
    return directory


def save_report(report: dict[str, Any]) -> dict[str, Any]:
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    report_id = uuid.uuid4().hex[:12]
    report["id"] = report_id
    directory = _report_dir(report_id)
    directory.mkdir(parents=True, exist_ok=True)
    report_path = directory / "report.json"
    report["report_path"] = str(report_path)
    with report_path.open("w", encoding="utf-8") as fp:
        json.dump(report, fp, ensure_ascii=False, indent=2)
    return report


def get_report(report_id: str) -> dict[str, Any] | None:
    try:
        path = _report_dir(report_id) / "report.json"
    except ValueError:
        return None
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def list_reports() -> list[dict[str, Any]]:
    if not settings.reports_dir.exists():
        return []
    reports: list[dict[str, Any]] = []
    for path in settings.reports_dir.glob("*/report.json"):
        try:
            with path.open("r", encoding="utf-8") as fp:
                report = json.load(fp)
            reports.append(
                {
                    "id": report["id"],
                    "created_at": report["created_at"],
                    "source": report.get("source", {}),
                    "summary": report.get("summary", {}),
                    "recommendation": report.get("recommendation", {}),
                }
            )
        except Exception:
            continue
    return sorted(reports, key=lambda item: item["created_at"], reverse=True)
