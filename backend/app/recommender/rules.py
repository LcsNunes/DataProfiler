from __future__ import annotations

from typing import Any


def derive_signals(
    source: dict[str, Any],
    summary: dict[str, Any],
    schema: dict[str, Any],
    quality: dict[str, Any],
    statistics: dict[str, Any],
    target: dict[str, Any],
) -> dict[str, bool]:
    row_count = summary.get("row_count", 0)
    column_count = summary.get("column_count", 0)
    type_counts = schema.get("type_counts", {})
    max_null_pct = max([column.get("null_pct", 0) for column in schema.get("columns", [])] or [0])
    avg_null_pct = summary.get("null_pct", 0)
    categorical_cols = type_counts.get("categorical", 0) + type_counts.get("boolean", 0)
    text_cols = type_counts.get("text", 0)
    long_text_cols = type_counts.get("long_text", 0)
    sensitive = any(column.get("possible_sensitive") for column in schema.get("columns", []))
    source_type = source.get("type")
    dataset_count = summary.get("dataset_count", 1)

    return {
        "multi_dataset": source_type == "multi_file" or dataset_count > 1,
        "has_relationship_candidates": summary.get("relationship_candidate_count", 0) > 0,
        "tabular": column_count > 0 and (type_counts.get("numeric", 0) + categorical_cols) >= max(1, column_count // 2),
        "small_dataset": row_count <= 100_000,
        "large_dataset": row_count > 100_000,
        "clean": max_null_pct < 10 and summary.get("duplicate_pct", 0) < 5 and len(quality.get("problems", [])) <= max(3, column_count),
        "many_nulls_or_inconsistencies": max_null_pct >= 20 or avg_null_pct >= 10 or any(p["type"] in {"mixed_types", "invalid_dates"} for p in quality.get("problems", [])),
        "has_target": bool(target.get("detected")),
        "no_target": not bool(target.get("detected")),
        "target_imbalanced": bool(target.get("imbalanced")),
        "many_categorical": column_count > 0 and categorical_cols / column_count >= 0.35,
        "short_text": text_cols > 0,
        "long_text": long_text_cols > 0,
        "api_source": source_type == "api",
        "sql_source": source_type == "sql",
        "large_sql": source_type == "sql" and row_count >= 50_000,
        "json_or_documental": source_type == "api" and (text_cols + long_text_cols > 0),
        "sensitive_data": sensitive,
        "natural_language_questions": False,
    }
