from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.app.core.security import sanitize_for_output
from backend.app.loaders.base import DataLoadResult
from backend.app.profiler.actionable_insights import (
    analysis_context,
    build_cleaning_plan,
    build_column_actions,
    build_executive_summary,
    build_readiness_scores,
    build_table_map,
)
from backend.app.profiler.issue_catalog import explain_problem
from backend.app.profiler.profile_runner import build_profile_payload
from backend.app.profiler.utils import json_safe
from backend.app.recommender.recommendation_engine import build_recommendation
from backend.app.reports.markdown_exporter import export_markdown
from backend.app.reports.report_store import save_report


def _dataset_name(loaded: DataLoadResult, index: int) -> str:
    source = loaded.source
    name = source.get("name") or source.get("table") or source.get("url") or f"dataset_{index + 1}"
    return Path(str(name)).stem if source.get("type") == "file" else str(name)


def _combine_type_counts(datasets: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for dataset in datasets:
        for key, value in dataset["schema"].get("type_counts", {}).items():
            counts[key] = counts.get(key, 0) + int(value)
    return counts


def _aggregate_schema(datasets: list[dict[str, Any]]) -> dict[str, Any]:
    columns: list[dict[str, Any]] = []
    for dataset in datasets:
        dataset_name = dataset["dataset_name"]
        for column in dataset["schema"].get("columns", []):
            enriched = dict(column)
            enriched["dataset"] = dataset_name
            enriched["original_name"] = column["name"]
            enriched["name"] = f"{dataset_name}.{column['name']}"
            columns.append(enriched)

    type_counts = _combine_type_counts(datasets)
    total = sum(type_counts.values())
    return {
        "columns": columns,
        "type_counts": type_counts,
        "type_percentages": {
            key: round((value / total) * 100, 2) if total else 0.0
            for key, value in type_counts.items()
        },
    }


def _aggregate_quality(datasets: list[dict[str, Any]]) -> dict[str, Any]:
    problems: list[dict[str, Any]] = []
    columns: dict[str, Any] = {}
    duplicate_rows = 0
    rows_fully_empty = 0

    for dataset in datasets:
        dataset_name = dataset["dataset_name"]
        quality = dataset.get("quality", {})
        duplicate_rows += int(quality.get("duplicate_rows", 0))
        rows_fully_empty += int(quality.get("rows_fully_empty", 0))
        for column, checks in quality.get("columns", {}).items():
            columns[f"{dataset_name}.{column}"] = checks
        for problem in dataset.get("problems", []):
            enriched = dict(problem)
            enriched["dataset"] = dataset_name
            enriched["original_column"] = problem.get("column")
            enriched["column"] = f"{dataset_name}.{problem.get('column')}"
            explanation = explain_problem(str(problem.get("type")))
            if explanation:
                enriched["explanation"] = explanation
            problems.append(enriched)

    row_count = sum(int(dataset["summary"].get("row_count", 0)) for dataset in datasets)
    return {
        "duplicate_rows": duplicate_rows,
        "duplicate_pct": round((duplicate_rows / row_count) * 100, 2) if row_count else 0.0,
        "rows_fully_empty": rows_fully_empty,
        "columns": columns,
        "problems": problems,
    }


def _relationships(datasets: list[dict[str, Any]]) -> dict[str, Any]:
    by_column: dict[str, list[dict[str, Any]]] = defaultdict(list)
    signatures: dict[str, list[str]] = defaultdict(list)

    for dataset in datasets:
        dataset_name = dataset["dataset_name"]
        column_names = []
        quality_columns = dataset.get("quality", {}).get("columns", {})
        for column in dataset["schema"].get("columns", []):
            original = column["name"]
            normalized = original.lower().strip()
            column_names.append(normalized)
            checks = quality_columns.get(original, {})
            by_column[normalized].append(
                {
                    "dataset": dataset_name,
                    "column": original,
                    "semantic_type": column.get("semantic_type"),
                    "unique_rate": column.get("unique_rate"),
                    "possible_id": bool(checks.get("possible_id")),
                    "possible_primary_key": bool(checks.get("possible_primary_key")),
                }
            )
        signatures["|".join(sorted(column_names))].append(dataset_name)

    common_columns = [
        {"column": column, "datasets": refs}
        for column, refs in sorted(by_column.items())
        if len(refs) > 1
    ]
    possible_joins = [
        item
        for item in common_columns
        if any(ref["possible_id"] or ref["possible_primary_key"] for ref in item["datasets"])
    ]

    overlap_pairs: list[dict[str, Any]] = []
    for left_index, left in enumerate(datasets):
        left_cols = {column["name"].lower().strip() for column in left["schema"].get("columns", [])}
        for right in datasets[left_index + 1 :]:
            right_cols = {column["name"].lower().strip() for column in right["schema"].get("columns", [])}
            union = left_cols | right_cols
            intersection = left_cols & right_cols
            overlap_pairs.append(
                {
                    "left": left["dataset_name"],
                    "right": right["dataset_name"],
                    "shared_columns": sorted(intersection),
                    "overlap_pct": round((len(intersection) / len(union)) * 100, 2) if union else 0.0,
                }
            )

    compatible_schema_groups = [
        {"datasets": names, "column_count": len(signature.split("|")) if signature else 0}
        for signature, names in signatures.items()
        if len(names) > 1
    ]

    return {
        "common_columns": common_columns,
        "possible_joins": possible_joins,
        "schema_overlap": sorted(overlap_pairs, key=lambda item: item["overlap_pct"], reverse=True),
        "compatible_schema_groups": compatible_schema_groups,
    }


def _multi_charts(datasets: list[dict[str, Any]], relationships: dict[str, Any]) -> list[dict[str, Any]]:
    labels = [dataset["dataset_name"] for dataset in datasets]
    rows = [dataset["summary"].get("row_count", 0) for dataset in datasets]
    null_pct = [dataset["summary"].get("null_pct", 0) for dataset in datasets]
    problem_counts = [len(dataset.get("problems", [])) for dataset in datasets]

    def bar(chart_id: str, title: str, values: list[float], color: str) -> dict[str, Any]:
        return {
            "id": chart_id,
            "title": title,
            "kind": "bar",
            "description": "Comparativo entre bases analisadas.",
            "option": {
                "tooltip": {"trigger": "axis"},
                "grid": {"left": 56, "right": 24, "bottom": 72, "top": 36},
                "xAxis": {"type": "category", "data": labels, "axisLabel": {"rotate": 25}},
                "yAxis": {"type": "value"},
                "series": [{"type": "bar", "data": values, "itemStyle": {"color": color}}],
            },
        }

    charts = [
        bar("multi_rows_by_dataset", "Linhas por base", rows, "#3d6b64"),
        bar("multi_null_pct_by_dataset", "Percentual de nulos por base", null_pct, "#c0764f"),
        bar("multi_problem_count_by_dataset", "Alertas por base", problem_counts, "#8e4f3e"),
    ]

    if relationships["common_columns"]:
        charts.append(
            {
                "id": "multi_common_columns",
                "title": "Colunas compartilhadas",
                "kind": "bar",
                "description": "Colunas presentes em mais de uma base.",
                "option": {
                    "tooltip": {"trigger": "axis"},
                    "grid": {"left": 56, "right": 24, "bottom": 72, "top": 36},
                    "xAxis": {
                        "type": "category",
                        "data": [item["column"] for item in relationships["common_columns"][:20]],
                        "axisLabel": {"rotate": 35},
                    },
                    "yAxis": {"type": "value"},
                    "series": [
                        {
                            "type": "bar",
                            "data": [len(item["datasets"]) for item in relationships["common_columns"][:20]],
                            "itemStyle": {"color": "#2f5f8f"},
                        }
                    ],
                },
            }
        )
    return charts


def _aggregate_target(datasets: list[dict[str, Any]]) -> dict[str, Any]:
    targets = []
    for dataset in datasets:
        target = dataset.get("target", {})
        if target.get("detected"):
            enriched = dict(target)
            enriched["dataset"] = dataset["dataset_name"]
            enriched["qualified_column"] = f"{dataset['dataset_name']}.{target.get('column')}"
            targets.append(enriched)

    return {
        "detected": bool(targets),
        "column": targets[0]["qualified_column"] if targets else None,
        "targets_by_dataset": targets,
        "warning": None if targets else "No reliable target detected across datasets.",
    }


def _summary(datasets: list[dict[str, Any]], relationships: dict[str, Any]) -> dict[str, Any]:
    total_cells = sum(int(dataset["summary"].get("total_cells", 0)) for dataset in datasets)
    null_cells = sum(int(dataset["summary"].get("null_cells", 0)) for dataset in datasets)
    memory_bytes = sum(int(dataset["summary"].get("estimated_memory_bytes", 0)) for dataset in datasets)
    row_count = sum(int(dataset["summary"].get("row_count", 0)) for dataset in datasets)
    duplicate_rows = sum(int(dataset["summary"].get("duplicate_rows", 0)) for dataset in datasets)
    return {
        "dataset_count": len(datasets),
        "row_count": row_count,
        "column_count": sum(int(dataset["summary"].get("column_count", 0)) for dataset in datasets),
        "total_cells": total_cells,
        "null_cells": null_cells,
        "null_pct": round((null_cells / total_cells) * 100, 2) if total_cells else 0.0,
        "duplicate_rows": duplicate_rows,
        "duplicate_pct": round((duplicate_rows / row_count) * 100, 2) if row_count else 0.0,
        "rows_fully_empty": sum(int(dataset["summary"].get("rows_fully_empty", 0)) for dataset in datasets),
        "estimated_memory_bytes": memory_bytes,
        "estimated_memory_mb": round(memory_bytes / (1024 * 1024), 3) if memory_bytes else 0.0,
        "common_column_count": len(relationships["common_columns"]),
        "relationship_candidate_count": len(relationships["possible_joins"]),
        "compatible_schema_group_count": len(relationships["compatible_schema_groups"]),
    }


def _multi_dataset_insights(datasets: list[dict[str, Any]], relationships: dict[str, Any]) -> dict[str, Any]:
    target_datasets = [
        dataset for dataset in datasets if dataset.get("target", {}).get("detected")
    ]
    suggested_primary = max(target_datasets or datasets, key=lambda item: int(item["summary"].get("row_count", 0)))

    dataset_roles = []
    for dataset in datasets:
        rows = int(dataset["summary"].get("row_count", 0))
        columns = int(dataset["summary"].get("column_count", 0))
        has_target = bool(dataset.get("target", {}).get("detected"))
        key_count = sum(
            1
            for checks in dataset.get("quality", {}).get("columns", {}).values()
            if checks.get("possible_primary_key") or checks.get("possible_id")
        )
        if dataset["dataset_name"] == suggested_primary["dataset_name"]:
            role = "primary_candidate"
            reason = "Possui target detectado ou maior volume de registros para iniciar a análise."
        elif key_count and rows <= int(suggested_primary["summary"].get("row_count", 0)):
            role = "dimension_candidate"
            reason = "Possui possíveis chaves e menor volume, indicando tabela de dimensão ou cadastro."
        else:
            role = "fact_or_event_candidate"
            reason = "Pode representar eventos/fatos ou tabela complementar; valide granularidade antes do join."
        dataset_roles.append(
            {
                "dataset": dataset["dataset_name"],
                "role": role,
                "reason": reason,
                "row_count": rows,
                "column_count": columns,
                "has_target": has_target,
                "candidate_key_count": key_count,
            }
        )

    join_plan = []
    for pair in relationships.get("schema_overlap", [])[:12]:
        shared_columns = pair.get("shared_columns", [])
        possible_key_columns = [
            item["column"]
            for item in relationships.get("possible_joins", [])
            if item["column"] in shared_columns
        ]
        if possible_key_columns:
            risk = "medium"
            advice = "Validar unicidade e cardinalidade antes de executar join."
        elif shared_columns:
            risk = "high"
            advice = "Colunas comuns existem, mas nenhuma parece chave confiável; risco de duplicar linhas."
        else:
            risk = "low"
            advice = "Sem coluna compartilhada detectada; relacionamento não deve ser assumido."
        join_plan.append(
            {
                "left": pair["left"],
                "right": pair["right"],
                "shared_columns": shared_columns,
                "candidate_keys": possible_key_columns,
                "overlap_pct": pair.get("overlap_pct", 0),
                "risk": risk,
                "advice": advice,
            }
        )

    warnings = []
    if not relationships.get("possible_joins"):
        warnings.append("Nenhuma chave compartilhada confiável foi detectada automaticamente.")
    if len(datasets) > 1 and not relationships.get("common_columns"):
        warnings.append("As bases não compartilham nomes de colunas; pode ser necessário mapear chaves manualmente.")

    return {
        "suggested_primary_dataset": suggested_primary["dataset_name"],
        "dataset_roles": dataset_roles,
        "join_plan": join_plan,
        "warnings": warnings,
    }


def run_multi_profile(loaded_items: list[DataLoadResult], business_objective: str | None = None) -> dict[str, Any]:
    if len(loaded_items) < 2:
        raise ValueError("Multi-dataset profiling requires at least two datasets.")

    context = analysis_context(business_objective)
    datasets = []
    name_counts: dict[str, int] = {}
    for index, loaded in enumerate(loaded_items):
        dataset = build_profile_payload(loaded, business_objective=business_objective)
        base_name = _dataset_name(loaded, index)
        name_counts[base_name] = name_counts.get(base_name, 0) + 1
        dataset_name = base_name if name_counts[base_name] == 1 else f"{base_name}_{name_counts[base_name]}"
        dataset["dataset_id"] = f"dataset_{index + 1}"
        dataset["dataset_name"] = dataset_name
        datasets.append(dataset)

    relationships = _relationships(datasets)
    multi_dataset_insights = _multi_dataset_insights(datasets, relationships)
    schema = _aggregate_schema(datasets)
    quality = _aggregate_quality(datasets)
    target = _aggregate_target(datasets)
    summary = _summary(datasets, relationships)
    charts = _multi_charts(datasets, relationships)
    source = {
        "type": "multi_file",
        "dataset_count": len(datasets),
        "sources": [sanitize_for_output(dataset.get("source", {})) for dataset in datasets],
    }
    summary["detected_types"] = schema["type_counts"]
    summary["type_percentages"] = schema["type_percentages"]

    recommendation = build_recommendation(
        source=source,
        summary=summary,
        schema=schema,
        quality=quality,
        statistics={},
        target=target,
        context=context,
    )
    readiness = build_readiness_scores(summary, schema, quality, target, relationships)
    column_actions = build_column_actions(schema, quality, target, limit=120)
    cleaning_plan = build_cleaning_plan(column_actions)
    table_map = build_table_map(datasets, relationships)
    executive_summary = build_executive_summary(
        summary=summary,
        schema=schema,
        quality=quality,
        target=target,
        recommendation=recommendation,
        readiness=readiness,
        context=context,
    )

    report = json_safe(
        {
            "id": "",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "report_type": "multi_dataset",
            "source": source,
            "analysis_context": context,
            "executive_summary": executive_summary,
            "readiness": readiness,
            "column_actions": column_actions,
            "cleaning_plan": cleaning_plan,
            "smart_preview": {"sample_rows": [], "issue_examples": []},
            "summary": summary,
            "schema": schema,
            "quality": quality,
            "statistics": {},
            "target": target,
            "problems": quality["problems"],
            "charts": charts,
            "recommendation": recommendation,
            "datasets": datasets,
            "relationships": relationships,
            "multi_dataset_insights": multi_dataset_insights,
            "table_map": table_map,
        }
    )
    saved = save_report(report)
    export_markdown(saved)
    return saved
