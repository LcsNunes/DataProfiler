from __future__ import annotations

import re
import warnings
from statistics import mean
from typing import Any

import pandas as pd
import polars as pl

from backend.app.profiler.utils import (
    dtype_name,
    is_bool_dtype,
    is_date_dtype,
    is_numeric_dtype,
    is_string_dtype,
    json_safe,
    sample_non_null_strings,
    top_values,
    unique_count,
)


SENSITIVE_NAME_PATTERNS = (
    "cpf",
    "cnpj",
    "ssn",
    "email",
    "e-mail",
    "phone",
    "telefone",
    "celular",
    "nome",
    "name",
    "address",
    "endereco",
    "senha",
    "password",
    "token",
    "secret",
    "api_key",
    "cartao",
    "credit_card",
)


def _string_date_ratio(values: list[str]) -> float:
    if not values:
        return 0.0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        parsed = pd.to_datetime(values, errors="coerce", utc=False)
    valid = int(parsed.notna().sum())
    return valid / len(values)


def _boolean_like_ratio(values: list[str]) -> float:
    if not values:
        return 0.0
    accepted = {"true", "false", "yes", "no", "sim", "nao", "não", "0", "1", "y", "n"}
    return sum(value.strip().lower() in accepted for value in values) / len(values)


def _semantic_type(column: str, series: pl.Series, dtype: pl.DataType, row_count: int) -> str:
    if is_bool_dtype(dtype):
        return "boolean"
    if is_date_dtype(dtype):
        return "date"
    if is_numeric_dtype(dtype):
        return "numeric"
    if not is_string_dtype(dtype):
        return "categorical"

    values = sample_non_null_strings(series, 1000)
    if _boolean_like_ratio(values) >= 0.95:
        return "boolean"
    if _string_date_ratio(values) >= 0.8:
        return "date"

    non_empty = [value for value in values if value.strip()]
    avg_len = mean([len(value) for value in non_empty]) if non_empty else 0
    uniq = unique_count(series)
    unique_rate = uniq / row_count if row_count else 0
    if avg_len > 60:
        return "long_text"
    if avg_len > 24 or unique_rate > 0.5:
        return "text"
    return "categorical"


def _looks_sensitive(column: str, values: list[str]) -> bool:
    lower = column.lower()
    if any(pattern in lower for pattern in SENSITIVE_NAME_PATTERNS):
        return True
    sample = " ".join(values[:100])
    email = re.search(r"[\w.\-+]+@[\w.\-]+\.\w+", sample)
    cpf = re.search(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b", sample)
    return bool(email or cpf)


def analyze_schema(df: pl.DataFrame) -> dict[str, Any]:
    row_count = df.height
    columns: list[dict[str, Any]] = []
    type_counts: dict[str, int] = {}

    for column, dtype in zip(df.columns, df.dtypes):
        series = df[column]
        null_count = int(series.null_count())
        non_null = row_count - null_count
        uniq = unique_count(series)
        semantic = _semantic_type(column, series, dtype, row_count)
        values = sample_non_null_strings(series, 200)
        sensitive = _looks_sensitive(column, values)
        unique_rate = uniq / row_count if row_count else 0.0

        problems: list[str] = []
        if null_count:
            problems.append("missing_values")
        if uniq <= 1 and row_count:
            problems.append("constant")
        if unique_rate > 0.9 and row_count > 5:
            problems.append("high_cardinality")
        if sensitive:
            problems.append("possible_sensitive_field")

        type_counts[semantic] = type_counts.get(semantic, 0) + 1
        columns.append(
            {
                "name": column,
                "dtype": dtype_name(dtype),
                "semantic_type": semantic,
                "null_count": null_count,
                "null_pct": round((null_count / row_count) * 100, 2) if row_count else 0.0,
                "non_null_count": non_null,
                "unique_count": uniq,
                "unique_rate": round(unique_rate, 4),
                "sample_values": [json_safe(value) for value in series.drop_nulls().head(5).to_list()],
                "top_values": top_values(series, 5),
                "possible_sensitive": sensitive,
                "problems": problems,
            }
        )

    return {
        "columns": columns,
        "type_counts": type_counts,
        "type_percentages": {
            key: round((count / len(df.columns)) * 100, 2) if df.columns else 0.0
            for key, count in type_counts.items()
        },
    }
