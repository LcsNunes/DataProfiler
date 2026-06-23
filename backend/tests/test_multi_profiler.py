import polars as pl

from backend.app.loaders.base import DataLoadResult
from backend.app.profiler.multi_profile_runner import run_multi_profile


def test_run_multi_profile_detects_common_columns_and_saves_report():
    customers = pl.DataFrame(
        {
            "customer_id": [1, 2, 3],
            "name": ["Ana", "Bruno", "Carla"],
            "churn": ["no", "no", "yes"],
        }
    )
    orders = pl.DataFrame(
        {
            "order_id": [10, 11, 12],
            "customer_id": [1, 1, 2],
            "amount": [100.0, 50.0, 75.0],
        }
    )

    report = run_multi_profile(
        [
            DataLoadResult(customers, {"type": "file", "name": "customers.csv"}),
            DataLoadResult(orders, {"type": "file", "name": "orders.csv"}),
        ]
    )

    assert report["report_type"] == "multi_dataset"
    assert report["summary"]["dataset_count"] == 2
    assert report["summary"]["common_column_count"] >= 1
    assert report["relationships"]["common_columns"][0]["column"] == "customer_id"
    assert report["recommendation"]["matched_rules"][0] == "multi_dataset_relationship_analysis"
    assert report["readiness"]["join_readiness_score"] is not None
    assert report["table_map"]["nodes"]
    assert report["table_map"]["edges"]
