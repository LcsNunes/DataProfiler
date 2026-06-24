from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from backend.app.core.security import sanitize_for_output
from backend.app.loaders.base import DataLoadResult
from backend.app.profiler.actionable_insights import (
    analysis_context,
    build_cleaning_plan,
    build_column_actions,
    build_executive_summary,
    build_readiness_scores,
    build_smart_preview,
)
from backend.app.profiler.chart_builder import build_charts
from backend.app.profiler.issue_catalog import explain_problem
from backend.app.profiler.quality_checks import run_quality_checks
from backend.app.profiler.schema_analyzer import analyze_schema
from backend.app.profiler.statistics import analyze_statistics
from backend.app.profiler.target_detector import detect_target
from backend.app.profiler.utils import json_safe
from backend.app.recommender.recommendation_engine import build_recommendation
from backend.app.reports.markdown_exporter import export_markdown
from backend.app.reports.report_store import save_report


def _summary(loaded: DataLoadResult, schema: dict[str, Any], quality: dict[str, Any]) -> dict[str, Any]:
    df = loaded.dataframe
    null_cells = sum(column["null_count"] for column in schema["columns"])
    total_cells = df.height * len(df.columns)
    try:
        memory_bytes = int(df.estimated_size())
    except Exception:
        memory_bytes = 0
    return {
        "row_count": df.height,
        "column_count": len(df.columns),
        "total_cells": total_cells,
        "null_cells": null_cells,
        "null_pct": round((null_cells / total_cells) * 100, 2) if total_cells else 0.0,
        "duplicate_rows": quality["duplicate_rows"],
        "duplicate_pct": quality["duplicate_pct"],
        "rows_fully_empty": quality["rows_fully_empty"],
        "estimated_memory_bytes": memory_bytes,
        "estimated_memory_mb": round(memory_bytes / (1024 * 1024), 3) if memory_bytes else 0.0,
        "detected_types": schema["type_counts"],
        "type_percentages": schema["type_percentages"],
        "source_metadata": sanitize_for_output(loaded.metadata),
    }


def _enrich_problems(problems: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched = []
    for problem in problems:
        item = dict(problem)
        explanation = explain_problem(str(problem.get("type")))
        if explanation:
            item["explanation"] = explanation
        enriched.append(item)
    return enriched


def build_profile_payload(loaded: DataLoadResult, business_objective: str | None = None) -> dict[str, Any]:
    context = analysis_context(business_objective)
    schema = analyze_schema(loaded.dataframe)
    quality = run_quality_checks(loaded.dataframe, schema)
    statistics = analyze_statistics(loaded.dataframe, schema)
    target = detect_target(loaded.dataframe, schema)
    charts = build_charts(loaded.dataframe, schema, quality, statistics, target)
    summary = _summary(loaded, schema, quality)
    recommendation = build_recommendation(
        source=loaded.source,
        summary=summary,
        schema=schema,
        quality=quality,
        statistics=statistics,
        target=target,
        context=context,
    )
    readiness = build_readiness_scores(summary, schema, quality, target)
    column_actions = build_column_actions(schema, quality, target)
    cleaning_plan = build_cleaning_plan(column_actions)
    smart_preview = build_smart_preview(loaded.dataframe, quality)
    executive_summary = build_executive_summary(
        summary=summary,
        schema=schema,
        quality=quality,
        target=target,
        recommendation=recommendation,
        readiness=readiness,
        context=context,
    )

    return {
        "id": "",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "report_type": "single_dataset",
        "source": sanitize_for_output(loaded.source),
        "analysis_context": context,
        "executive_summary": executive_summary,
        "readiness": readiness,
        "column_actions": column_actions,
        "cleaning_plan": cleaning_plan,
        "smart_preview": smart_preview,
        "summary": summary,
        "schema": schema,
        "quality": quality,
        "statistics": statistics,
        "target": target,
        "problems": _enrich_problems(quality["problems"]),
        "charts": charts,
        "recommendation": recommendation,
    }


def run_profile(loaded: DataLoadResult, business_objective: str | None = None) -> dict[str, Any]:
    report = build_profile_payload(loaded, business_objective=business_objective)
    report = json_safe(report)
    saved = save_report(report)
    export_markdown(saved)
    return saved
