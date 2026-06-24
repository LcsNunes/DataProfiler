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
    target_impact = 12 if target.get("detected") else -25
    if target.get("detected"):
        modeling += 12
    else:
        modeling -= 25
    imbalance_penalty = 10 if target.get("imbalanced") else 0
    if target.get("imbalanced"):
        modeling -= 10
    cardinality_penalty = min(high_cardinality * 2, 10)
    modeling -= cardinality_penalty
    modeling = max(0, min(100, round(modeling)))

    join_readiness: int | None = None
    join_explanation: list[dict[str, Any]] = []
    if relationships is not None:
        join_readiness = 35
        join_explanation.append({"label": "Base inicial para análise multi-base", "impact": 35})
        if relationships.get("common_columns"):
            join_readiness += 25
            join_explanation.append({"label": "Existem colunas compartilhadas entre bases", "impact": 25})
        else:
            join_explanation.append({"label": "Nenhuma coluna compartilhada detectada", "impact": 0})
        if relationships.get("possible_joins"):
            join_readiness += 25
            join_explanation.append({"label": "Foram encontradas chaves candidatas para join", "impact": 25})
        else:
            join_explanation.append({"label": "Nenhuma chave candidata confiável foi detectada", "impact": 0})
        if relationships.get("compatible_schema_groups"):
            join_readiness += 10
            join_explanation.append({"label": "Há grupos com schemas compatíveis", "impact": 10})
        join_readiness = min(100, join_readiness)

    return {
        "data_quality_score": data_quality,
        "data_quality_label": _score_label(data_quality),
        "modeling_readiness_score": modeling,
        "modeling_readiness_label": _score_label(modeling),
        "join_readiness_score": join_readiness,
        "join_readiness_label": _score_label(join_readiness) if join_readiness is not None else None,
        "score_explanations": {
            "data_quality": [
                {"label": "Base inicial", "impact": 100},
                {"label": f"Nulos na base ({summary.get('null_pct', 0)}%)", "impact": -round(null_penalty, 1)},
                {"label": f"Linhas duplicadas ({summary.get('duplicate_pct', 0)}%)", "impact": -round(duplicate_penalty, 1)},
                {"label": f"Alertas de qualidade ({len(problems)})", "impact": -round(problem_penalty, 1)},
                {"label": f"Campos sensíveis candidatos ({sensitive})", "impact": -round(sensitive_penalty, 1)},
            ],
            "modeling": [
                {"label": "Score de qualidade dos dados", "impact": data_quality},
                {
                    "label": "Target detectado" if target.get("detected") else "Target não detectado",
                    "impact": target_impact,
                },
                {"label": "Target desbalanceado", "impact": -imbalance_penalty},
                {"label": f"Alta cardinalidade em {high_cardinality} coluna(s)", "impact": -cardinality_penalty},
            ],
            "joins": join_explanation,
        },
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


def build_cleaning_plan(column_actions: list[dict[str, Any]]) -> dict[str, Any]:
    high_priority = [action for action in column_actions if action.get("priority") == "high"]
    missing_columns = [action["column"] for action in column_actions if action.get("recommended_action") == "treat_missing_values"]
    drop_columns = [action["column"] for action in column_actions if action.get("recommended_action") == "drop_from_modeling"]
    key_columns = [action["column"] for action in column_actions if action.get("recommended_action") == "use_as_key"]
    sensitive_columns = [action["column"] for action in column_actions if action.get("recommended_action") == "mask_or_exclude"]

    checklist = [
        "Criar cópia da base original antes de qualquer transformação.",
        "Converter strings vazias e espaços em branco para nulo.",
        "Validar target e remover identificadores da lista de features diretas.",
    ]
    if missing_columns:
        checklist.append(f"Definir estratégia de nulos para {len(missing_columns)} coluna(s).")
    if drop_columns:
        checklist.append(f"Remover ou justificar {len(drop_columns)} coluna(s) constante(s) ou sem valor analítico.")
    if sensitive_columns:
        checklist.append(f"Mascarar, hashear ou excluir {len(sensitive_columns)} campo(s) sensível(is).")
    if key_columns:
        checklist.append(f"Separar {len(key_columns)} chave(s)/ID(s) para joins, auditoria ou deduplicação.")

    polars_lines = [
        "import polars as pl",
        "",
        "# Substitua pelo carregamento real da sua base.",
        "# df = pl.read_csv('sua_base.csv')",
        "",
        "# 1) Padronizar textos vazios como nulos.",
        "text_columns = [column for column, dtype in df.schema.items() if dtype == pl.Utf8]",
        "df = df.with_columns([",
        "    pl.when(pl.col(column).str.strip_chars() == '')",
        "    .then(None)",
        "    .otherwise(pl.col(column))",
        "    .alias(column)",
        "    for column in text_columns",
        "])",
    ]
    if drop_columns:
        polars_lines.extend(["", "# 2) Remover colunas sem utilidade analítica clara.", f"df = df.drop({drop_columns!r}, strict=False)"])
    if sensitive_columns:
        polars_lines.extend(
            [
                "",
                "# 3) Remover ou mascarar campos sensíveis antes de compartilhar/modelar.",
                f"sensitive_columns = {sensitive_columns!r}",
                "df_model = df.drop(sensitive_columns, strict=False)",
            ]
        )
    if missing_columns:
        polars_lines.extend(
            [
                "",
                "# 4) Exemplo conservador: criar flags de nulo para colunas com valores ausentes.",
                f"missing_columns = {missing_columns!r}",
                "df = df.with_columns([pl.col(column).is_null().alias(f'{column}__is_null') for column in missing_columns if column in df.columns])",
            ]
        )

    return {
        "checklist": checklist,
        "high_priority_actions": high_priority[:20],
        "polars_script": "\n".join(polars_lines) + "\n",
        "notes": [
            "O script é um ponto de partida e deve ser revisado antes de uso em produção.",
            "Não impute valores automaticamente sem validar o significado do nulo.",
            "IDs e chaves devem ser usados para relacionamento/deduplicação, não como feature direta por padrão.",
        ],
    }


def build_data_dictionary(
    df: pl.DataFrame | None,
    schema: dict[str, Any],
    quality: dict[str, Any],
    target: dict[str, Any],
    column_actions: list[dict[str, Any]],
    limit: int = 120,
) -> list[dict[str, Any]]:
    actions_by_column = {action["column"]: action for action in column_actions}
    target_column = target.get("column")
    dictionary: list[dict[str, Any]] = []

    for column in schema.get("columns", [])[:limit]:
        name = column["name"]
        checks = quality.get("columns", {}).get(name, {})
        action = actions_by_column.get(name, {})
        role = action.get("role", "feature_candidate")
        if name == target_column:
            role = "target_candidate"
        elif checks.get("possible_primary_key") or checks.get("possible_id"):
            role = "join_or_identifier"
        elif column.get("possible_sensitive"):
            role = "sensitive_candidate"

        examples: list[Any] = []
        if df is not None and name in df.columns:
            examples = [
                value
                for value in df[name].drop_nulls().head(5).to_list()
                if str(value).strip() != ""
            ][:5]

        dictionary.append(
            {
                "column": name,
                "dataset": column.get("dataset"),
                "dtype": column.get("dtype"),
                "semantic_type": column.get("semantic_type"),
                "role": role,
                "recommended_action": action.get("recommended_action", "keep"),
                "null_pct": column.get("null_pct", 0),
                "unique_count": column.get("unique_count", 0),
                "unique_rate": column.get("unique_rate", 0),
                "possible_sensitive": bool(column.get("possible_sensitive")),
                "problems": column.get("problems", []),
                "example_values": json_safe(examples),
                "notes": action.get("strategies", [])[:2],
            }
        )

    return dictionary


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
    decision_status = "ready_for_baseline"
    decision_title = "Pode preparar baseline"
    decision_reason = "A base tem sinais suficientes para uma primeira exploração e baseline controlado."
    if readiness["modeling_readiness_label"] == "not_ready":
        verdict = "Não modele ainda; resolva qualidade, objetivo ou target primeiro."
        decision_status = "blocked"
        decision_title = "Não modelar ainda"
        decision_reason = "A prontidão para modelagem está baixa; valide qualidade, target ou objetivo antes de treinar."
    elif readiness["modeling_readiness_label"] == "needs_review":
        verdict = "Pode explorar, mas valide problemas principais antes de treinar modelo."
        decision_status = "needs_validation"
        decision_title = "Explorar antes de modelar"
        decision_reason = "Há sinais úteis, mas os principais alertas precisam ser tratados ou aceitos conscientemente."

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
    risk_summary = (
        recommendation.get("risks", [None])[0]
        or "Sem risco crítico específico identificado pelas regras atuais; valide as hipóteses com a área de negócio."
    )

    return {
        "headline": headline,
        "verdict": verdict,
        "decision": {
            "status": decision_status,
            "title": decision_title,
            "reason": decision_reason,
        },
        "top_findings": top_findings,
        "immediate_actions": immediate_actions[:6],
        "primary_action": immediate_actions[0] if immediate_actions else "Revisar resumo e validar objetivo analítico.",
        "risk_summary": risk_summary,
        "top_problem_types": [_problem_label(item) for item in top_problem_types],
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
