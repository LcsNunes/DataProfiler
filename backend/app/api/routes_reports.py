from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.app.profiler.issue_catalog import load_issue_catalog
from backend.app.reports.report_store import get_report, list_reports

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("")
def reports() -> list[dict]:
    return list_reports()


@router.get("/problem-catalog")
def problem_catalog() -> dict:
    return load_issue_catalog()


@router.get("/{report_id}")
def report_detail(report_id: str) -> dict:
    report = get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/{report_id}/metrics")
def report_metrics(report_id: str) -> dict:
    report = report_detail(report_id)
    return report.get("summary", {})


@router.get("/{report_id}/problems")
def report_problems(report_id: str) -> list[dict]:
    report = report_detail(report_id)
    return report.get("problems", [])


@router.get("/{report_id}/charts")
def report_charts(report_id: str) -> list[dict]:
    report = report_detail(report_id)
    return report.get("charts", [])


@router.get("/{report_id}/recommendation")
def report_recommendation(report_id: str) -> dict:
    report = report_detail(report_id)
    return report.get("recommendation", {})


@router.get("/{report_id}/recommendation/explanation")
def report_recommendation_explanation(report_id: str) -> dict:
    recommendation = report_recommendation(report_id)
    parts = []
    if recommendation.get("why"):
        parts.append("Justificativa: " + " ".join(recommendation["why"]))
    if recommendation.get("risks"):
        parts.append("Riscos: " + " ".join(recommendation["risks"]))
    if recommendation.get("next_steps"):
        parts.append("Próximos passos: " + " ".join(recommendation["next_steps"]))
    return {"text": "\n".join(parts)}
