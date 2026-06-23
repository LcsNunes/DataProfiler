import polars as pl

from backend.app.profiler.schema_analyzer import analyze_schema
from backend.app.profiler.target_detector import detect_target


def test_detects_named_binary_target():
    df = pl.DataFrame({"age": [20, 30, 40, 50], "churn": ["no", "no", "no", "yes"]})

    target = detect_target(df, analyze_schema(df))

    assert target["detected"] is True
    assert target["column"] == "churn"
    assert target["problem_type"] == "binary_classification"
    assert target["imbalanced"] is True

