import polars as pl

from backend.app.loaders.base import DataLoadResult
from backend.app.profiler.profile_runner import run_profile


def test_run_profile_generates_core_sections():
    df = pl.DataFrame(
        {
            "id": [1, 2, 3, 3],
            "status": ["ok", "ok", "fail", "fail"],
            "target": ["yes", "no", "no", "no"],
            "value": [10.0, None, 30.0, 30.0],
        }
    )

    report = run_profile(DataLoadResult(df, {"type": "test"}))

    assert report["id"]
    assert report["summary"]["row_count"] == 4
    assert report["target"]["column"] == "target"
    assert report["recommendation"]["recommended_approach"]
    assert report["charts"]
    assert any(problem.get("explanation") for problem in report["problems"])
    assert report["executive_summary"]["verdict"]
    assert report["readiness"]["data_quality_score"] >= 0
    assert report["column_actions"]
    assert "sample_rows" in report["smart_preview"]
