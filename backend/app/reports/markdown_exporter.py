from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def export_markdown(report: dict[str, Any]) -> str:
    report_path = Path(report["report_path"])
    md_path = report_path.with_name("report.md")
    summary = report.get("summary", {})
    target = report.get("target", {})
    recommendation = report.get("recommendation", {})
    executive = report.get("executive_summary", {})
    readiness = report.get("readiness", {})
    column_actions = report.get("column_actions", [])[:12]
    cleaning_plan = report.get("cleaning_plan", {})
    problems = report.get("problems", [])[:20]
    datasets = report.get("datasets", [])
    relationships = report.get("relationships", {})

    lines = [
        f"# Data Profiler AI Report `{report['id']}`",
        "",
        f"- Created at: `{report['created_at']}`",
        f"- Source type: `{report.get('source', {}).get('type', 'unknown')}`",
        f"- Rows: `{summary.get('row_count', 0)}`",
        f"- Columns: `{summary.get('column_count', 0)}`",
        f"- Datasets: `{summary.get('dataset_count', 1)}`",
        f"- Common columns: `{summary.get('common_column_count', 0)}`",
        f"- Relationship candidates: `{summary.get('relationship_candidate_count', 0)}`",
        f"- Null cells: `{summary.get('null_cells', 0)}`",
        f"- Duplicate rows: `{summary.get('duplicate_rows', 0)}`",
        f"- Likely target: `{target.get('column') or 'not detected'}`",
        "",
        "## Executive Summary",
        "",
        f"**Headline:** {executive.get('headline', 'n/a')}",
        f"**Verdict:** {executive.get('verdict', 'n/a')}",
        f"**Data quality score:** {readiness.get('data_quality_score', 'n/a')}",
        f"**Modeling readiness score:** {readiness.get('modeling_readiness_score', 'n/a')}",
        "",
        "### Immediate Actions",
        "",
        *[f"- {item}" for item in executive.get("immediate_actions", [])],
        "",
        "## Recommendation",
        "",
        f"**Approach:** {recommendation.get('recommended_approach', 'n/a')}",
        f"**Confidence:** {recommendation.get('confidence', 'n/a')}",
        "",
        "### Why",
        "",
        *[f"- {item}" for item in recommendation.get("why", [])],
        "",
        "### Risks",
        "",
        *[f"- {item}" for item in recommendation.get("risks", [])],
        "",
        "### Next Steps",
        "",
        *[f"- {item}" for item in recommendation.get("next_steps", [])],
        "",
        "## Main Problems",
        "",
        *[f"- `{item.get('column')}`: {item.get('type')} ({item.get('severity')})" for item in problems],
        "",
        "## Column Actions",
        "",
        *[
            f"- `{item.get('column')}`: {item.get('recommended_action')} - {' '.join(item.get('strategies', [])[:1])}"
            for item in column_actions
        ],
        "",
        "## Cleaning Plan",
        "",
        *[f"- [ ] {item}" for item in cleaning_plan.get("checklist", [])],
    ]
    if datasets:
        lines.extend(
            [
                "",
                "## Datasets",
                "",
                *[
                    f"- `{dataset.get('dataset_name')}`: {dataset.get('summary', {}).get('row_count', 0)} rows, {dataset.get('summary', {}).get('column_count', 0)} columns"
                    for dataset in datasets
                ],
                "",
                "## Relationship Candidates",
                "",
                *[
                    f"- `{item.get('column')}` appears in {len(item.get('datasets', []))} datasets"
                    for item in relationships.get("possible_joins", [])[:20]
                ],
            ]
        )
    cleaning_md_path = report_path.with_name("cleaning_plan.md")
    cleaning_py_path = report_path.with_name("cleaning_plan.py")
    cleaning_lines = [
        f"# Cleaning Plan `{report['id']}`",
        "",
        "## Checklist",
        "",
        *[f"- [ ] {item}" for item in cleaning_plan.get("checklist", [])],
        "",
        "## Notes",
        "",
        *[f"- {item}" for item in cleaning_plan.get("notes", [])],
    ]
    cleaning_md_path.write_text("\n".join(cleaning_lines), encoding="utf-8")
    cleaning_py_path.write_text(cleaning_plan.get("polars_script", "# Cleaning plan unavailable.\n"), encoding="utf-8")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    report["markdown_path"] = str(md_path)
    report["cleaning_plan_path"] = str(cleaning_md_path)
    report["cleaning_script_path"] = str(cleaning_py_path)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(md_path)
