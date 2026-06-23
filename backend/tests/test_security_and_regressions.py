from pathlib import Path

import polars as pl
import pytest

from backend.app.loaders.api_loader import load_api
from backend.app.loaders.base import DataLoadResult
from backend.app.loaders.file_loader import load_file, validate_allowed_file_path
from backend.app.loaders.json_normalizer import normalize_json_payload
from backend.app.loaders.sql_loader import _query_from_config
from backend.app.models.schemas import ApiSourceRequest, SqlSourceRequest
from backend.app.profiler.multi_profile_runner import run_multi_profile
from backend.app.profiler.quality_checks import run_quality_checks
from backend.app.profiler.schema_analyzer import analyze_schema
from backend.app.reports.report_store import get_report


def test_csv_fallback_preserves_invalid_value_after_inference_window(tmp_path: Path):
    path = tmp_path / "late_invalid.csv"
    rows = ["id,value"] + [f"{index},{index}" for index in range(1001)] + ["1002,oops"]
    path.write_text("\n".join(rows), encoding="utf-8")

    loaded = load_file(str(path))

    assert loaded.metadata["csv_fallback"] is True
    assert loaded.dataframe["value"].tail(1).item() == "oops"


def test_json_normalizer_uses_first_non_null_record():
    df = normalize_json_payload({"data": [None, {"id": 1, "name": "Ana"}]})

    assert df.height == 1
    assert df["id"].item() == 1


def test_multi_profile_calculates_duplicate_pct():
    first = pl.DataFrame({"id": [1, 1], "target": ["yes", "yes"]})
    second = pl.DataFrame({"id": [2, 3], "value": [10, 20]})

    report = run_multi_profile(
        [
            DataLoadResult(first, {"type": "file", "name": "first.csv"}),
            DataLoadResult(second, {"type": "file", "name": "second.csv"}),
        ]
    )

    assert report["summary"]["duplicate_rows"] > 0
    assert report["summary"]["duplicate_pct"] > 0
    assert report["quality"]["duplicate_pct"] > 0


def test_quality_severity_does_not_leak_between_problem_types():
    df = pl.DataFrame({"event_date": ["bad", "Bad ", "2024-01-01", "bad", "Bad ", "bad"]})
    quality = run_quality_checks(df, analyze_schema(df))
    severities = {problem["type"]: problem["severity"] for problem in quality["problems"]}

    assert severities["invalid_dates"] == "warning"
    assert severities["inconsistent_values"] == "info"


def test_api_loader_blocks_loopback_hosts_without_network_call():
    request = ApiSourceRequest(url="http://localhost:8000/private")

    with pytest.raises(ValueError, match="private|unsafe"):
        load_api(request)


def test_http_file_path_guard_blocks_paths_outside_allowed_roots(tmp_path: Path):
    path = tmp_path / "outside.csv"
    path.write_text("id\n1\n", encoding="utf-8")

    with pytest.raises(PermissionError):
        validate_allowed_file_path(str(path))


def test_sql_loader_rejects_mutating_query():
    request = SqlSourceRequest(connection_string="sqlite:///example.db", query="DROP TABLE customers")

    with pytest.raises(ValueError, match="read-only"):
        _query_from_config(request)


def test_invalid_report_id_is_not_resolved():
    assert get_report("..") is None
