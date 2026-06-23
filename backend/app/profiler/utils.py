from __future__ import annotations

import math
from collections import Counter
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import polars as pl


NUMERIC_DTYPES = {
    pl.Int8,
    pl.Int16,
    pl.Int32,
    pl.Int64,
    pl.UInt8,
    pl.UInt16,
    pl.UInt32,
    pl.UInt64,
    pl.Float32,
    pl.Float64,
}
DATE_DTYPES = {pl.Date, pl.Datetime, pl.Time}
BOOLEAN_DTYPES = {pl.Boolean}
STRING_DTYPES = {pl.Utf8, pl.String}


def dtype_name(dtype: pl.DataType) -> str:
    return str(dtype)


def is_numeric_dtype(dtype: pl.DataType) -> bool:
    return dtype in NUMERIC_DTYPES


def is_date_dtype(dtype: pl.DataType) -> bool:
    return dtype in DATE_DTYPES or str(dtype).startswith("Datetime")


def is_bool_dtype(dtype: pl.DataType) -> bool:
    return dtype in BOOLEAN_DTYPES


def is_string_dtype(dtype: pl.DataType) -> bool:
    return dtype in STRING_DTYPES or str(dtype) in {"Utf8", "String"}


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_safe(val) for key, val in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [json_safe(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def top_values(series: pl.Series, limit: int = 10) -> list[dict[str, Any]]:
    values = [json_safe(value) for value in series.drop_nulls().head(50_000).to_list()]
    counts = Counter(str(value) for value in values)
    return [{"value": value, "count": count} for value, count in counts.most_common(limit)]


def sample_non_null_strings(series: pl.Series, limit: int = 1000) -> list[str]:
    casted = series.cast(pl.Utf8, strict=False).drop_nulls().head(limit).to_list()
    return [str(value) for value in casted if value is not None]


def unique_count(series: pl.Series) -> int:
    try:
        return int(series.n_unique())
    except Exception:
        return len(set(series.drop_nulls().head(50_000).to_list()))

