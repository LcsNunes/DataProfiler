from __future__ import annotations

import math
from typing import Any

import pandas as pd
import polars as pl


def _bar_option(labels: list[str], values: list[float], *, color: str = "#3d6b64") -> dict[str, Any]:
    return {
        "tooltip": {"trigger": "axis"},
        "grid": {"left": 56, "right": 24, "bottom": 72, "top": 36},
        "xAxis": {"type": "category", "data": labels, "axisLabel": {"rotate": 35}},
        "yAxis": {"type": "value"},
        "series": [{"type": "bar", "data": values, "itemStyle": {"color": color}}],
    }


def _pie_option(data: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "tooltip": {"trigger": "item"},
        "legend": {"bottom": 0},
        "series": [
            {
                "type": "pie",
                "radius": ["42%", "70%"],
                "avoidLabelOverlap": True,
                "data": data,
            }
        ],
    }


def _histogram(values: list[float], bins: int = 12) -> tuple[list[str], list[int]]:
    if not values:
        return [], []
    minimum = min(values)
    maximum = max(values)
    if minimum == maximum:
        return [str(round(minimum, 2))], [len(values)]
    step = (maximum - minimum) / bins
    counts = [0] * bins
    for value in values:
        index = min(int((value - minimum) / step), bins - 1)
        counts[index] += 1
    labels = [f"{minimum + i * step:.2f}-{minimum + (i + 1) * step:.2f}" for i in range(bins)]
    return labels, counts


def build_charts(
    df: pl.DataFrame,
    schema: dict[str, Any],
    quality: dict[str, Any],
    statistics: dict[str, Any],
    target: dict[str, Any],
) -> list[dict[str, Any]]:
    charts: list[dict[str, Any]] = []

    type_data = [{"name": key, "value": value} for key, value in schema["type_counts"].items()]
    charts.append(
        {
            "id": "column_type_distribution",
            "title": "Distribuição de tipos de colunas",
            "kind": "pie",
            "description": "Percentual de colunas por tipo semântico detectado.",
            "option": _pie_option(type_data),
        }
    )

    null_columns = sorted(schema["columns"], key=lambda item: item["null_pct"], reverse=True)[:20]
    charts.append(
        {
            "id": "nulls_by_column",
            "title": "Percentual de nulos por coluna",
            "kind": "bar",
            "description": "Top colunas com maior proporção de valores ausentes.",
            "option": _bar_option([item["name"] for item in null_columns], [item["null_pct"] for item in null_columns], color="#c0764f"),
        }
    )

    problem_counts: dict[str, int] = {}
    for problem in quality["problems"]:
        problem_counts[problem["column"]] = problem_counts.get(problem["column"], 0) + 1
    top_problem_columns = sorted(problem_counts.items(), key=lambda item: item[1], reverse=True)[:15]
    charts.append(
        {
            "id": "top_problem_columns",
            "title": "Colunas com mais alertas",
            "kind": "bar",
            "description": "Quantidade de problemas detectados por coluna.",
            "option": _bar_option([item[0] for item in top_problem_columns], [item[1] for item in top_problem_columns], color="#8e4f3e"),
        }
    )

    if target.get("detected") and target.get("distribution"):
        charts.append(
            {
                "id": "target_distribution",
                "title": f"Distribuição do target: {target['column']}",
                "kind": "bar",
                "description": "Distribuição dos valores da possível coluna alvo.",
                "option": _bar_option(
                    [str(item["value"]) for item in target["distribution"]],
                    [item["count"] for item in target["distribution"]],
                    color="#2f5f8f",
                ),
            }
        )

    for column in list(statistics["numeric"].keys())[:3]:
        values = df[column].cast(pl.Float64, strict=False).drop_nulls().head(50_000).to_list()
        finite_values = [float(value) for value in values if value is not None and math.isfinite(float(value))]
        labels, counts = _histogram(finite_values)
        charts.append(
            {
                "id": f"histogram_{column}",
                "title": f"Histograma: {column}",
                "kind": "histogram",
                "description": "Distribuição aproximada dos valores numéricos.",
                "option": _bar_option(labels, counts, color="#3b766f"),
            }
        )

    for column, stats in list(statistics["categorical"].items())[:3]:
        top = stats.get("top_values", [])[:12]
        charts.append(
            {
                "id": f"category_top_{column}",
                "title": f"Top valores: {column}",
                "kind": "bar",
                "description": "Valores categóricos mais frequentes.",
                "option": _bar_option([str(item["value"]) for item in top], [item["count"] for item in top], color="#725c2f"),
            }
        )

    numeric_columns = list(statistics["numeric"].keys())[:10]
    if len(numeric_columns) >= 2:
        pdf = df.select(numeric_columns).to_pandas()
        corr = pdf.corr(numeric_only=True).fillna(0)
        data = [
            [x, y, round(float(corr.iloc[y, x]), 4)]
            for y in range(len(corr.index))
            for x in range(len(corr.columns))
        ]
        charts.append(
            {
                "id": "correlation_matrix",
                "title": "Matriz de correlação",
                "kind": "heatmap",
                "description": "Correlação de Pearson para colunas numéricas selecionadas.",
                "option": {
                    "tooltip": {"position": "top"},
                    "grid": {"height": "62%", "top": "10%"},
                    "xAxis": {"type": "category", "data": list(corr.columns), "splitArea": {"show": True}},
                    "yAxis": {"type": "category", "data": list(corr.index), "splitArea": {"show": True}},
                    "visualMap": {"min": -1, "max": 1, "calculable": True, "orient": "horizontal", "left": "center", "bottom": "0%"},
                    "series": [{"type": "heatmap", "data": data, "label": {"show": False}}],
                },
            }
        )

    outlier_items = [
        (column, checks["outliers"]["count"])
        for column, checks in quality["columns"].items()
        if checks.get("outliers")
    ]
    if outlier_items:
        charts.append(
            {
                "id": "numeric_outliers",
                "title": "Outliers numéricos",
                "kind": "bar",
                "description": "Quantidade de outliers estimados por regra IQR.",
                "option": _bar_option([item[0] for item in outlier_items], [item[1] for item in outlier_items], color="#a54f43"),
            }
        )

    return charts
