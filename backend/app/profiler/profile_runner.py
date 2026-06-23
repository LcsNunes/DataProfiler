from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from backend.app.core.security import sanitize_for_output
from backend.app.loaders.base import DataLoadResult
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


def build_profile_payload(loaded: DataLoadResult) -> dict[str, Any]:
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
    )

    return {
        "id": "",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "report_type": "single_dataset",
        "source": sanitize_for_output(loaded.source),
        "summary": summary,
        "schema": schema,
        "quality": quality,
        "statistics": statistics,
        "target": target,
        "problems": _enrich_problems(quality["problems"]),
        "charts": charts,
        "recommendation": recommendation,
    }


def run_profile(loaded: DataLoadResult) -> dict[str, Any]:
    report = build_profile_payload(loaded)
    report = json_safe(report)
    saved = save_report(report)
    export_markdown(saved)
    return saved
