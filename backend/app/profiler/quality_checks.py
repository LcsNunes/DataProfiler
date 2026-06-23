from __future__ import annotations

import re
import warnings
from collections import Counter
from typing import Any

import pandas as pd
import polars as pl

from backend.app.profiler.utils import (
    is_numeric_dtype,
    is_string_dtype,
    sample_non_null_strings,
    safe_float,
    unique_count,
)


def _string_counts(series: pl.Series) -> tuple[int, int]:
    if not is_string_dtype(series.dtype):
        return 0, 0
    casted = series.cast(pl.Utf8, strict=False)
    empty = int((casted.fill_null("").str.len_chars() == 0).sum())
    whitespace = int(((casted.fill_null("").str.len_chars() > 0) & (casted.fill_null("").str.strip_chars().str.len_chars() == 0)).sum())
    return empty, whitespace


def _is_possible_id(column: str, row_count: int, null_count: int, uniq: int, semantic_type: str) -> bool:
    lower = column.lower()
    high_unique = row_count > 0 and uniq / row_count > 0.9
    name_hint = lower == "id" or lower.endswith("_id") or lower.endswith("id") or "codigo" in lower or "uuid" in lower
    return null_count == 0 and high_unique and (name_hint or semantic_type in {"numeric", "text", "categorical"})


def _detect_mixed_types(series: pl.Series) -> dict[str, Any] | None:
    if not is_string_dtype(series.dtype):
        return None
    values = [value.strip() for value in sample_non_null_strings(series, 1000) if value.strip()]
    if len(values) < 10:
        return None

    buckets: Counter[str] = Counter()
    for value in values:
        if safe_float(value) is not None:
            buckets["numeric_like"] += 1
        elif value.lower() in {"true", "false", "yes", "no", "sim", "nao", "não", "0", "1"}:
            buckets["boolean_like"] += 1
        else:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                parsed_date = pd.to_datetime([value], errors="coerce")
            if not pd.isna(parsed_date)[0]:
                buckets["date_like"] += 1
            else:
                buckets["text_like"] += 1

    meaningful = {key: count for key, count in buckets.items() if count / len(values) >= 0.1}
    if len(meaningful) > 1:
        return {"counts": dict(meaningful), "sample_size": len(values)}
    return None


def _detect_invalid_dates(column: str, series: pl.Series) -> dict[str, Any] | None:
    lower = column.lower()
    if not any(token in lower for token in ("date", "data", "dt_", "_dt", "created", "updated")):
        return None
    values = [value.strip() for value in sample_non_null_strings(series, 1000) if value.strip()]
    if not values:
        return None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        parsed = pd.to_datetime(values, errors="coerce", utc=False)
    invalid = int(parsed.isna().sum())
    invalid_pct = invalid / len(values)
    if invalid_pct >= 0.05:
        return {"invalid_count_sample": invalid, "sample_size": len(values), "invalid_pct_sample": round(invalid_pct * 100, 2)}
    return None


def _detect_outliers(series: pl.Series) -> dict[str, Any] | None:
    if not is_numeric_dtype(series.dtype):
        return None
    numeric = series.cast(pl.Float64, strict=False).drop_nulls()
    if len(numeric) < 8:
        return None
    q1 = numeric.quantile(0.25)
    q3 = numeric.quantile(0.75)
    if q1 is None or q3 is None:
        return None
    iqr = q3 - q1
    if iqr == 0:
        return None
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    count = int(((numeric < lower) | (numeric > upper)).sum())
    if not count:
        return None
    return {
        "count": count,
        "pct": round((count / len(numeric)) * 100, 2),
        "lower_bound": round(float(lower), 4),
        "upper_bound": round(float(upper), 4),
    }


def _detect_inconsistent_values(series: pl.Series) -> dict[str, Any] | None:
    if not is_string_dtype(series.dtype):
        return None
    values = sample_non_null_strings(series, 5000)
    if len(values) < 5:
        return None
    raw_unique = len(set(values))
    normalized_unique = len(set(re.sub(r"\s+", " ", value.strip().lower()) for value in values))
    if raw_unique > normalized_unique:
        return {"raw_unique_sample": raw_unique, "normalized_unique_sample": normalized_unique}
    return None


def rows_fully_empty(df: pl.DataFrame) -> int:
    if not df.columns:
        return 0
    expressions = []
    for column in df.columns:
        expressions.append(
            pl.col(column).is_null()
            | (pl.col(column).cast(pl.Utf8, strict=False).fill_null("").str.strip_chars().str.len_chars() == 0)
        )
    return int(df.select(pl.all_horizontal(expressions).sum()).item())


def run_quality_checks(df: pl.DataFrame, schema: dict[str, Any]) -> dict[str, Any]:
    row_count = df.height
    duplicate_rows = int(df.is_duplicated().sum()) if row_count else 0
    column_profiles = {column["name"]: column for column in schema["columns"]}
    columns: dict[str, Any] = {}
    problems: list[dict[str, Any]] = []

    for column in df.columns:
        series = df[column]
        profile = column_profiles[column]
        null_count = int(series.null_count())
        empty_count, whitespace_count = _string_counts(series)
        uniq = int(profile["unique_count"])
        unique_rate = uniq / row_count if row_count else 0.0
        values = series.drop_nulls().head(50_000).to_list()
        top_ratio = 0.0
        if values:
            top_ratio = Counter(str(value) for value in values).most_common(1)[0][1] / len(values)

        checks = {
            "null_count": null_count,
            "null_pct": round((null_count / row_count) * 100, 2) if row_count else 0.0,
            "empty_strings": empty_count,
            "whitespace_strings": whitespace_count,
            "constant": row_count > 0 and uniq <= 1,
            "near_constant": row_count > 0 and uniq > 1 and top_ratio >= 0.95,
            "high_cardinality": row_count > 10 and unique_rate >= 0.75 and profile["semantic_type"] not in {"numeric", "date"},
            "possible_id": _is_possible_id(column, row_count, null_count, uniq, profile["semantic_type"]),
            "possible_primary_key": row_count > 0 and null_count == 0 and uniq == row_count,
            "invalid_dates": _detect_invalid_dates(column, series),
            "inconsistent_values": _detect_inconsistent_values(series),
            "outliers": _detect_outliers(series),
            "mixed_types": _detect_mixed_types(series),
            "encoding_issue_hint": any("\ufffd" in value for value in sample_non_null_strings(series, 200)),
        }
        columns[column] = checks

        warning_labels = {"missing_values", "mixed_types", "invalid_dates", "possible_encoding_issue"}
        for key, label in [
            ("null_count", "missing_values"),
            ("empty_strings", "empty_strings"),
            ("whitespace_strings", "whitespace_only_strings"),
            ("constant", "constant_column"),
            ("near_constant", "near_constant_column"),
            ("high_cardinality", "high_cardinality"),
            ("possible_id", "possible_id"),
            ("possible_primary_key", "possible_primary_key"),
            ("invalid_dates", "invalid_dates"),
            ("inconsistent_values", "inconsistent_values"),
            ("outliers", "numeric_outliers"),
            ("mixed_types", "mixed_types"),
            ("encoding_issue_hint", "possible_encoding_issue"),
        ]:
            value = checks.get(key)
            active = bool(value)
            if key in {"null_count", "empty_strings", "whitespace_strings"}:
                active = int(value or 0) > 0
            if active:
                severity = "warning" if label in warning_labels else "info"
                problems.append({"column": column, "type": label, "severity": severity, "details": value})

    return {
        "duplicate_rows": duplicate_rows,
        "duplicate_pct": round((duplicate_rows / row_count) * 100, 2) if row_count else 0.0,
        "rows_fully_empty": rows_fully_empty(df),
        "columns": columns,
        "problems": problems,
    }
