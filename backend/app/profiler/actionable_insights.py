from __future__ import annotations

from typing import Any

import polars as pl

from backend.app.profiler.utils import json_safe


def analysis_context(business_objective: str | None = None) -> dict[str, Any]:
    objective = (business_objective or "").strip()
    objective_lower = objective.lower()
    return {
        "business_objective": objective or None,
        "objective_signals": {
            "mentions_natural_language": any(
                token in objective_lower
                for token in ("pergunta", "linguagem natural", "chat", "consulta", "sql", "dashboard")
            ),
            "mentions_prediction": any(
                token in objective_lower
                for token in ("prever", "predizer", "classificar", "regressao", "regression", "forecast")
            ),
            "mentions_risk_or_fraud": any(token in objective_lower for token in ("fraude", "risco", "inadimpl", "churn")),
        },
    }


def _score_label(score: int) -> str:
    if score >= 80:
        return "ready"
    if score >= 55:
        return "needs_review"
    return "not_ready"


def _score_label_pt(label: str | None) -> str:
    return {
        "ready": "pronto",
        "needs_review": "requer revisão",
        "not_ready": "não pronto",
    }.get(label or "", label or "não avaliado")


def _format_int(value: Any) -> str:
    try:
        return f"{int(value):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "0"


def _problem_label(problem_type: str) -> str:
    return {
        "missing_values": "valores ausentes",
        "empty_strings": "strings vazias",
        "whitespace_only_strings": "strings só com espaços",
        "constant_column": "colunas constantes",
        "near_constant_column": "colunas quase constantes",
        "high_cardinality": "alta cardinalidade",
        "possible_id": "possível identificador",
        "possible_primary_key": "possível chave primária",
        "invalid_dates": "datas inválidas",
        "inconsistent_values": "valores inconsistentes",
        "numeric_outliers": "outliers numéricos",
        "mixed_types": "mistura de tipos",
        "possible_encoding_issue": "possível problema de encoding",
    }.get(problem_type, problem_type.replace("_", " "))


def _top_problem_types(problems: list[dict[str, Any]], limit: int = 3) -> list[str]:
    counts: dict[str, int] = {}
    for problem in problems:
        problem_type = str(problem.get("type", "unknown"))
        counts[problem_type] = counts.get(problem_type, 0) + 1
    return [item[0] for item in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:limit]]


def build_readiness_scores(
    summary: dict[str, Any],
    schema: dict[str, Any],
    quality: dict[str, Any],
    target: dict[str, Any],
    relationships: dict[str, Any] | None = None,
) -> dict[str, Any]:
    problems = quality.get("problems", [])
    warning_count = sum(1 for problem in problems if problem.get("severity") == "warning")
    info_count = len(problems) - warning_count
    high_cardinality = sum(1 for problem in problems if problem.get("type") == "high_cardinality")
    sensitive = sum(1 for column in schema.get("columns", []) if column.get("possible_sensitive"))
    null_penalty = min(float(summary.get("null_pct", 0)) * 1.2, 30)
    duplicate_penalty = min(float(summary.get("duplicate_pct", 0)) * 1.5, 20)
    problem_penalty = min(warning_count * 3 + info_count * 1.2, 30)
    sensitive_penalty = min(sensitive * 4, 16)

    data_quality = max(0, round(100 - null_penalty - duplicate_penalty - problem_penalty - sensitive_penalty))

    modeling = data_quality
    if target.get("detected"):
        modeling += 12
    else:
        modeling -= 25
    if target.get("imbalanced"):
        modeling -= 10
    modeling -= min(high_cardinality * 2, 10)
    modeling = max(0, min(100, round(modeling)))

    join_readiness: int | None = None
    if relationships is not None:
        join_readiness = 35
        if relationships.get("common_columns"):
            join_readiness += 25
        if relationships.get("possible_joins"):
            join_readiness += 25
        if relationships.get("compatible_schema_groups"):
            join_readiness += 10
        join_readiness = min(100, join_readiness)

    return {
        "data_quality_score": data_quality,
        "data_quality_label": _score_label(data_quality),
        "modeling_readiness_score": modeling,
        "modeling_readiness_label": _score_label(modeling),
        "join_readiness_score": join_readiness,
        "join_readiness_label": _score_label(join_readiness) if join_readiness is not None else None,
        "drivers": {
            "warning_count": warning_count,
            "problem_count": len(problems),
            "top_problem_types": _top_problem_types(problems),
            "has_target": bool(target.get("detected")),
            "target_imbalanced": bool(target.get("imbalanced")),
            "sensitive_column_count": sensitive,
        },
    }


def build_column_actions(
    schema: dict[str, Any],
    quality: dict[str, Any],
    target: dict[str, Any],
    limit: int = 80,
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    target_column = target.get("column")
    checks_by_column = quality.get("columns", {})

    for column in schema.get("columns", [])[:limit]:
        name = column["name"]
        checks = checks_by_column.get(name, {})
        recommended_action = "keep"
        role = "feature_candidate"
        reasons: list[str] = []
        strategies: list[str] = []

        if name == target_column:
            recommended_action = "validate_target"
            role = "target_candidate"
            reasons.append("Possível coluna target detectada.")
            strategies.append("Confirme esse target com a área de negócio antes de modelagem supervisionada.")
        elif checks.get("possible_primary_key") or checks.get("possible_id"):
            recommended_action = "use_as_key"
            role = "join_or_identifier"
            reasons.append("A coluna parece ser identificador ou chave.")
            strategies.append("Use para joins, deduplicação ou rastreabilidade; evite uso preditivo direto.")
        elif checks.get("constant"):
            recommended_action = "drop_from_modeling"
            reasons.append("A coluna é constante.")
            strategies.append("Remova da modelagem, exceto se for metadado útil.")
        elif column.get("possible_sensitive"):
            recommended_action = "mask_or_exclude"
            role = "sensitive_candidate"
            reasons.append("A coluna pode conter dados sensíveis.")
            strategies.append("Mascare, aplique hash ou remova antes de compartilhamento externo ou modelagem.")

        if checks.get("null_count"):
            reasons.append(f"{checks.get('null_pct', 0)}% de valores ausentes.")
            strategies.append("Decida entre imputação, flag de nulo, filtro de linhas ou correção na origem.")
            if recommended_action == "keep":
                recommended_action = "treat_missing_values"
        if checks.get("high_cardinality"):
            reasons.append("Alta cardinalidade detectada.")
            strategies.append("Evite one-hot encoding cego; considere agrupamento, hashing ou target encoding.")
            if recommended_action == "keep":
                recommended_action = "validate_cardinality"
        if checks.get("outliers"):
            reasons.append("Outliers numéricos detectados.")
            strategies.append("Inspecione extremos; considere modelos robustos, transformação log, winsorização ou flag de outlier.")
        if checks.get("mixed_types"):
            reasons.append("Mistura de tipos detectada.")
            strategies.append("Defina o tipo oficial e corrija valores fora do tipo esperado.")
            if recommended_action == "keep":
                recommended_action = "fix_type_consistency"
        if checks.get("invalid_dates"):
            reasons.append("Datas inválidas detectadas.")
            strategies.append("Padronize o formato antes de criar features temporais ou cortes treino/teste por tempo.")
            if recommended_action == "keep":
                recommended_action = "fix_dates"

        semantic_type = column.get("semantic_type")
        if semantic_type == "categorical" and recommended_action == "keep":
            strategies.append("Codifique categóricas com método definido pela cardinalidade e pelo modelo escolhido.")
        if semantic_type in {"text", "long_text"} and recommended_action == "keep":
            strategies.append("Considere limpeza textual, embeddings ou TF-IDF conforme o objetivo.")
        if semantic_type == "date" and recommended_action == "keep":
            strategies.append("Crie features derivadas de data, como mês, recência e tempo decorrido.")

        actions.append(
            {
                "column": name,
                "semantic_type": semantic_type,
                "recommended_action": recommended_action,
                "role": role,
                "priority": "high" if recommended_action not in {"keep"} else "normal",
                "reasons": reasons or ["Nenhum problema relevante detectado nesta coluna."],
                "strategies": strategies or ["Mantenha como feature candidata e valide com o objetivo da modelagem."],
            }
        )

    actions.sort(key=lambda item: 0 if item["priority"] == "high" else 1)
    return actions


def build_smart_preview(df: pl.DataFrame, quality: dict[str, Any], row_limit: int = 8) -> dict[str, Any]:
    issue_examples: list[dict[str, Any]] = []

    for column, checks in list(quality.get("columns", {}).items())[:80]:
        series = df[column] if column in df.columns else None
        if series is None:
            continue
        if checks.get("null_count"):
            issue_examples.append(
                {
                    "column": column,
                    "type": "missing_values",
                    "examples": [{"row_index": index, "value": None} for index, value in enumerate(series.head(100).to_list()) if value is None][:5],
                }
            )
        if checks.get("empty_strings") or checks.get("whitespace_strings"):
            values = series.cast(pl.Utf8, strict=False).head(100).to_list()
            issue_examples.append(
                {
                    "column": column,
                    "type": "blank_strings",
                    "examples": [
                        {"row_index": index, "value": value}
                        for index, value in enumerate(values)
                        if value is not None and str(value).strip() == ""
                    ][:5],
                }
            )
        if checks.get("outliers"):
            bounds = checks["outliers"]
            values = series.cast(pl.Float64, strict=False).drop_nulls().head(500).to_list()
            issue_examples.append(
                {
                    "column": column,
                    "type": "numeric_outliers",
                    "examples": [
                        {"value": value}
                        for value in values
                        if value < bounds["lower_bound"] or value > bounds["upper_bound"]
                    ][:5],
                }
            )

    return {
        "sample_rows": json_safe(df.head(row_limit).to_dicts()),
        "issue_examples": [item for item in issue_examples if item["examples"]][:30],
    }


def build_executive_summary(
    summary: dict[str, Any],
    schema: dict[str, Any],
    quality: dict[str, Any],
    target: dict[str, Any],
    recommendation: dict[str, Any],
    readiness: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    top_problem_types = readiness["drivers"].get("top_problem_types", [])
    has_target = target.get("detected")
    objective = context.get("business_objective")
    verdict = "Pode iniciar análise exploratória e preparar um baseline simples."
    if readiness["modeling_readiness_label"] == "not_ready":
        verdict = "Não modele ainda; resolva qualidade, objetivo ou target primeiro."
    elif readiness["modeling_readiness_label"] == "needs_review":
        verdict = "Pode explorar, mas valide problemas principais antes de treinar modelo."

    headline = f"{_format_int(summary.get('row_count', 0))} linhas · {_format_int(summary.get('column_count', 0))} colunas"
    if summary.get("dataset_count"):
        headline = f"{_format_int(summary.get('dataset_count'))} bases · {_format_int(summary.get('row_count', 0))} linhas totais"

    top_findings = [
        f"Qualidade dos dados: {readiness['data_quality_score']}/100 ({_score_label_pt(readiness['data_quality_label'])}).",
        f"Prontidão para modelagem: {readiness['modeling_readiness_score']}/100 ({_score_label_pt(readiness['modeling_readiness_label'])}).",
        f"Target provável: {target.get('column') if has_target else 'não detectado'}.",
    ]
    if top_problem_types:
        top_findings.append("Problemas mais frequentes: " + ", ".join(_problem_label(item) for item in top_problem_types) + ".")
    if objective:
        top_findings.append(f"Objetivo informado: {objective}.")

    immediate_actions = []
    if not has_target:
        immediate_actions.append("Definir ou confirmar objetivo/target antes de modelagem supervisionada.")
    if quality.get("problems"):
        immediate_actions.append("Tratar os alertas de maior prioridade na tabela de ações por coluna.")
    immediate_actions.extend(recommendation.get("next_steps", [])[:3])

    return {
        "headline": headline,
        "verdict": verdict,
        "top_findings": top_findings,
        "immediate_actions": immediate_actions[:6],
        "recommended_approach": recommendation.get("recommended_approach"),
    }


def build_table_map(datasets: list[dict[str, Any]], relationships: dict[str, Any]) -> dict[str, Any]:
    nodes = [
        {
            "id": dataset["dataset_name"],
            "label": dataset["dataset_name"],
            "row_count": dataset["summary"].get("row_count", 0),
            "column_count": dataset["summary"].get("column_count", 0),
            "target": dataset.get("target", {}).get("column"),
        }
        for dataset in datasets
    ]
    edges = []
    for pair in relationships.get("schema_overlap", []):
        if not pair.get("shared_columns"):
            continue
        edges.append(
            {
                "source": pair["left"],
                "target": pair["right"],
                "shared_columns": pair["shared_columns"],
                "overlap_pct": pair["overlap_pct"],
                "relationship_hint": "possible_join" if any(
                    join["column"] in pair["shared_columns"] for join in relationships.get("possible_joins", [])
                ) else "shared_schema",
            }
        )
    return {"nodes": nodes, "edges": edges}
