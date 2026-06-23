from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import pandas as pd
import polars as pl
from charset_normalizer import from_bytes

from backend.app.core.config import settings
from backend.app.loaders.base import DataLoadResult
from backend.app.loaders.json_normalizer import normalize_json_payload


SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".json", ".parquet"}


def is_supported_file_name(filename: str) -> bool:
    return Path(filename).suffix.lower() in SUPPORTED_EXTENSIONS


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def validate_allowed_file_path(path: str) -> Path:
    resolved = _resolve_path(path)
    allowed_roots = settings.allowed_file_roots
    if not any(_is_relative_to(resolved, root) for root in allowed_roots):
        raise PermissionError("File path is outside allowed roots. Configure DATA_PROFILER_ALLOWED_PATHS.")
    return resolved


def _resolve_path(path: str) -> Path:
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if resolved.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file extension: {resolved.suffix}")
    return resolved


def _detect_encoding(path: Path) -> str:
    sample = path.read_bytes()[:200_000]
    best = from_bytes(sample).best()
    return best.encoding if best and best.encoding else "utf-8"


def _detect_separator(path: Path, encoding: str) -> str:
    sample = path.read_text(encoding=encoding, errors="replace")[:20_000]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        return dialect.delimiter
    except csv.Error:
        candidates = [",", ";", "\t", "|"]
        first_lines = sample.splitlines()[:20]
        return max(candidates, key=lambda sep: sum(line.count(sep) for line in first_lines))


def _read_csv(path: Path) -> tuple[pl.DataFrame, dict[str, Any]]:
    encoding = _detect_encoding(path)
    separator = _detect_separator(path, encoding)
    try:
        df = pl.read_csv(
            path,
            separator=separator,
            encoding=encoding,
            infer_schema_length=1000,
            ignore_errors=False,
            try_parse_dates=True,
        )
        return df, {"encoding": encoding, "separator": separator, "csv_fallback": False}
    except Exception as exc:
        # Fallback keeps raw values instead of silently coercing invalid rows to nulls.
        pdf = pd.read_csv(path, sep=separator, encoding=encoding, engine="python", dtype=str, keep_default_na=False)
        df = pl.from_pandas(pdf)
        return df, {"encoding": encoding, "separator": separator, "csv_fallback": True, "csv_fallback_reason": exc.__class__.__name__}


def _read_excel(path: Path) -> tuple[pl.DataFrame, dict[str, Any]]:
    xls = pd.ExcelFile(path)
    sheets = xls.sheet_names
    selected_sheet = sheets[0]
    pdf = pd.read_excel(path, sheet_name=selected_sheet)
    return pl.from_pandas(pdf), {"sheet_names": sheets, "selected_sheet": selected_sheet}


def _read_json(path: Path) -> tuple[pl.DataFrame, dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fp:
        payload = json.load(fp)
    df = normalize_json_payload(payload)
    return df, {"json_normalized": True}


def load_file(path: str, *, enforce_allowed_roots: bool = False, include_path: bool = True) -> DataLoadResult:
    resolved = validate_allowed_file_path(path) if enforce_allowed_roots else _resolve_path(path)
    extension = resolved.suffix.lower()
    metadata: dict[str, Any] = {"extension": extension, "file_name": resolved.name}

    if extension == ".csv":
        df, detected = _read_csv(resolved)
        metadata.update(detected)
    elif extension in {".xlsx", ".xls"}:
        df, detected = _read_excel(resolved)
        metadata.update(detected)
    elif extension == ".json":
        df, detected = _read_json(resolved)
        metadata.update(detected)
    else:
        df = pl.read_parquet(resolved)
        metadata.update({"parquet": True})

    return DataLoadResult(
        dataframe=df,
        source={
            "type": "file",
            "path": str(resolved) if include_path else resolved.name,
            "name": resolved.name,
            "extension": extension,
        },
        metadata=metadata,
    )
