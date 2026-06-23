from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from backend.app.loaders.api_loader import load_api
from backend.app.loaders.file_loader import load_file
from backend.app.loaders.sql_loader import load_sql
from backend.app.models.schemas import ApiSourceRequest, SqlSourceRequest
from backend.app.profiler.multi_profile_runner import run_multi_profile
from backend.app.profiler.profile_runner import run_profile


def _read_json_config(path: str) -> dict:
    with Path(path).expanduser().resolve().open("r", encoding="utf-8") as fp:
        return json.load(fp)


def _print_report_summary(report: dict) -> None:
    summary = report.get("summary", {})
    target = report.get("target", {})
    recommendation = report.get("recommendation", {})
    readiness = report.get("readiness", {})
    print("\nData Profiler AI")
    print("----------------")
    print(f"Report ID: {report['id']}")
    print(f"Rows: {summary.get('row_count', 0)}")
    print(f"Columns: {summary.get('column_count', 0)}")
    if summary.get("dataset_count"):
        print(f"Datasets: {summary.get('dataset_count')}")
        print(f"Common columns: {summary.get('common_column_count', 0)}")
        print(f"Relationship candidates: {summary.get('relationship_candidate_count', 0)}")
    print(f"Duplicate rows: {summary.get('duplicate_rows', 0)}")
    print(f"Null cells: {summary.get('null_cells', 0)}")
    print(f"Likely target: {target.get('column') or 'not detected'}")
    print(f"Recommendation: {recommendation.get('recommended_approach', 'n/a')}")
    print(f"Confidence: {recommendation.get('confidence', 'n/a')}")
    if readiness:
        print(f"Data quality score: {readiness.get('data_quality_score', 'n/a')}")
        print(f"Modeling readiness score: {readiness.get('modeling_readiness_score', 'n/a')}")
    print(f"Saved report: {report.get('report_path')}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run automatic data profiling without the frontend.")
    parser.add_argument("--path", help="Local CSV, XLSX, JSON or Parquet path.")
    parser.add_argument("--paths", nargs="+", help="Multiple local data files to analyze together.")
    parser.add_argument("--api-config", help="JSON config file for an external API source.")
    parser.add_argument("--sql-config", help="JSON config file for a SQL source.")
    parser.add_argument("--objective", help="Optional business objective to guide deterministic recommendations.")
    args = parser.parse_args()

    selected = [bool(args.path), bool(args.paths), bool(args.api_config), bool(args.sql_config)]
    if sum(selected) != 1:
        parser.error("Use exactly one of --path, --paths, --api-config or --sql-config.")

    if args.path:
        loaded = load_file(args.path)
        report = run_profile(loaded, business_objective=args.objective)
    elif args.paths:
        if len(args.paths) < 2:
            parser.error("--paths requires at least two files.")
        report = run_multi_profile([load_file(path) for path in args.paths], business_objective=args.objective)
    elif args.api_config:
        config = ApiSourceRequest(**_read_json_config(args.api_config))
        loaded = load_api(config)
        report = run_profile(loaded, business_objective=args.objective or config.business_objective)
    else:
        config = SqlSourceRequest(**_read_json_config(args.sql_config))
        loaded = load_sql(config)
        report = run_profile(loaded, business_objective=args.objective or config.business_objective)
    _print_report_summary(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
