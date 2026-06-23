from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pandas as pd
import polars as pl


DEFAULT_DATA_PATHS = ("data", "items", "results", "response.items", "response.data")


def get_by_path(payload: Any, path: str | None) -> Any:
    if not path:
        return payload
    current = payload
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def _looks_like_records(value: Any) -> bool:
    if not isinstance(value, list):
        return False
    first_non_null = next((item for item in value if item is not None), None)
    return first_non_null is None or isinstance(first_non_null, dict)


def extract_records(payload: Any, data_path: str | None = None) -> list[dict[str, Any]]:
    selected = get_by_path(payload, data_path) if data_path else None
    if selected is None and isinstance(payload, dict):
        for path in DEFAULT_DATA_PATHS:
            selected = get_by_path(payload, path)
            if _looks_like_records(selected):
                break
    if selected is None:
        selected = payload

    if isinstance(selected, dict):
        return [selected]
    if isinstance(selected, list):
        if not selected:
            return []
        if _looks_like_records(selected):
            return [item for item in selected if isinstance(item, dict)]
        return [{"value": item} for item in selected]
    return [{"value": selected}]


def flatten_records(records: Iterable[dict[str, Any]]) -> pl.DataFrame:
    records_list = list(records)
    if not records_list:
        return pl.DataFrame()
    normalized = pd.json_normalize(records_list, sep=".")
    return pl.from_pandas(normalized)


def normalize_json_payload(payload: Any, data_path: str | None = None) -> pl.DataFrame:
    return flatten_records(extract_records(payload, data_path))
