from __future__ import annotations

from typing import Any

import polars as pl

from backend.app.profiler.utils import (
    is_numeric_dtype,
    json_safe,
    safe_float,
    top_values,
    unique_count,
)


def _numeric_stats(series: pl.Series) -> dict[str, Any]:
    numeric = series.cast(pl.Float64, strict=False).drop_nulls()
    if not len(numeric):
        return {}
    try:
        skew = safe_float(numeric.skew())
    except Exception:
        skew = None
    return {
        "count": len(numeric),
        "mean": safe_float(numeric.mean()),
        "median": safe_float(numeric.median()),
        "min": safe_float(numeric.min()),
        "max": safe_float(numeric.max()),
        "std": safe_float(numeric.std()),
        "q1": safe_float(numeric.quantile(0.25)),
        "q3": safe_float(numeric.quantile(0.75)),
        "skew": skew,
    }


def analyze_statistics(df: pl.DataFrame, schema: dict[str, Any]) -> dict[str, Any]:
    numeric: dict[str, Any] = {}
    categorical: dict[str, Any] = {}
    profile_by_name = {column["name"]: column for column in schema["columns"]}
    row_count = df.height

    for column in df.columns:
        series = df[column]
        profile = profile_by_name[column]
        if is_numeric_dtype(series.dtype):
            numeric[column] = _numeric_stats(series)
        elif profile["semantic_type"] in {"categorical", "boolean", "text", "long_text"}:
            uniq = unique_count(series)
            categorical[column] = {
                "unique_count": uniq,
                "unique_rate": round((uniq / row_count), 4) if row_count else 0.0,
                "top_values": top_values(series, 10),
                "sample_values": [json_safe(value) for value in series.drop_nulls().head(5).to_list()],
            }

    return {"numeric": numeric, "categorical": categorical}

