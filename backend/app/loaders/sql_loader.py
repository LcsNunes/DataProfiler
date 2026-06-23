from __future__ import annotations

import re

import pandas as pd
import polars as pl
from sqlalchemy import create_engine, text

from backend.app.core.security import redact_text, sanitize_connection_string
from backend.app.loaders.base import DataLoadResult
from backend.app.models.schemas import SqlSourceRequest


SAFE_TABLE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_\.]*$")
READ_ONLY_QUERY_RE = re.compile(r"^\s*(select|with)\b", re.IGNORECASE | re.DOTALL)
MUTATING_SQL_RE = re.compile(
    r"\b(insert|update|delete|drop|alter|create|truncate|merge|grant|revoke|call|execute|attach|detach|pragma)\b",
    re.IGNORECASE,
)


def _validate_read_only_query(query: str) -> None:
    normalized = query.strip().rstrip(";")
    if not READ_ONLY_QUERY_RE.match(normalized) or MUTATING_SQL_RE.search(normalized):
        raise ValueError("Only read-only SELECT/WITH SQL queries are allowed.")


def _query_from_config(config: SqlSourceRequest) -> str:
    limit = config.limit or 5000
    if config.query:
        _validate_read_only_query(config.query)
        return f"SELECT * FROM ({config.query.strip().rstrip(';')}) AS data_profiler_source LIMIT {limit}"
    if not config.table or not SAFE_TABLE_RE.match(config.table):
        raise ValueError("Unsafe or invalid table name.")
    return f"SELECT * FROM {config.table} LIMIT {limit}"


def load_sql(config: SqlSourceRequest) -> DataLoadResult:
    engine = create_engine(config.connection_string)
    query = _query_from_config(config)
    with engine.connect() as connection:
        pdf = pd.read_sql_query(text(query), connection)
    df = pl.from_pandas(pdf)
    return DataLoadResult(
        dataframe=df,
        source={
            "type": "sql",
            "connection_string": sanitize_connection_string(config.connection_string),
            "table": config.table,
            "query": redact_text(config.query) if config.query else None,
            "limit": config.limit,
        },
        metadata={"query_executed": redact_text(query), "rows_loaded": df.height},
    )
