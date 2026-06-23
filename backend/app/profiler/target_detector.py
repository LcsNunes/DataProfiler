from __future__ import annotations

from typing import Any

import polars as pl

from backend.app.profiler.utils import is_numeric_dtype, sample_non_null_strings, top_values


TARGET_NAME_HINTS = (
    "target",
    "label",
    "classe",
    "class",
    "status",
    "resultado",
    "result",
    "churn",
    "fraude",
    "fraud",
    "aprovado",
    "inadimplente",
    "default",
)

STRONG_TARGET_NAMES = {
    "target",
    "label",
    "classe",
    "class",
    "resultado",
    "result",
    "churn",
    "fraude",
    "fraud",
    "aprovado",
    "inadimplente",
    "default",
}


def _score_target_candidate(column: dict[str, Any], index: int, total_columns: int) -> float:
    name = column["name"].lower()
    semantic = column["semantic_type"]
    unique_count = column["unique_count"]
    unique_rate = column["unique_rate"]
    score = 0.0

    if name in STRONG_TARGET_NAMES:
        score += 9
    elif name in TARGET_NAME_HINTS:
        score += 5
    elif any(hint in name for hint in TARGET_NAME_HINTS):
        score += 4
    if semantic in {"boolean", "categorical"} and 2 <= unique_count <= 20:
        score += 2
    if semantic == "numeric" and unique_count <= 20 and unique_rate < 0.5:
        score += 1.5
    if index == total_columns - 1:
        score += 0.5
    if column.get("possible_sensitive"):
        score -= 1
    if unique_rate > 0.8:
        score -= 3
    if unique_count <= 1:
        score -= 2
    return score


def _problem_type(series: pl.Series, column: dict[str, Any]) -> str:
    semantic = column["semantic_type"]
    unique_count = column["unique_count"]
    if semantic in {"text", "long_text"}:
        values = sample_non_null_strings(series, 200)
        avg_len = sum(len(value) for value in values) / len(values) if values else 0
        return "text" if avg_len > 60 else "classification"
    if is_numeric_dtype(series.dtype) and unique_count > max(20, series.len() * 0.05):
        return "regression"
    if unique_count == 2:
        return "binary_classification"
    if unique_count > 2:
        return "multiclass_classification"
    return "unknown"


def detect_target(df: pl.DataFrame, schema: dict[str, Any]) -> dict[str, Any]:
    if not df.columns:
        return {"detected": False, "column": None, "warning": "Dataset has no columns."}

    scored = [
        (_score_target_candidate(column, index, len(schema["columns"])), column)
        for index, column in enumerate(schema["columns"])
    ]
    scored.sort(key=lambda item: item[0], reverse=True)
    best_score, best = scored[0]

    if best_score < 2.5:
        return {
            "detected": False,
            "column": None,
            "warning": "No reliable target column detected. Define the modeling objective before supervised training.",
            "candidates": [{"column": col["name"], "score": round(score, 2)} for score, col in scored[:5]],
        }

    series = df[best["name"]]
    distribution = top_values(series, 30)
    non_null_count = max(series.len() - series.null_count(), 1)
    majority = distribution[0]["count"] if distribution else 0
    majority_pct = round((majority / non_null_count) * 100, 2)
    minority = distribution[-1]["count"] if distribution else 0
    minority_pct = round((minority / non_null_count) * 100, 2)
    problem_type = _problem_type(series, best)
    imbalanced = problem_type in {"binary_classification", "multiclass_classification"} and majority_pct >= 75

    return {
        "detected": True,
        "column": best["name"],
        "score": round(best_score, 2),
        "problem_type": problem_type,
        "distribution": distribution,
        "majority_class_pct": majority_pct,
        "minority_class_pct": minority_pct,
        "imbalanced": imbalanced,
        "warning": "Target appears imbalanced." if imbalanced else None,
        "candidates": [{"column": col["name"], "score": round(score, 2)} for score, col in scored[:5]],
    }
