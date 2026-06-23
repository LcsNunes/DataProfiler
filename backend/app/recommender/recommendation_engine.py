from __future__ import annotations

from typing import Any

from backend.app.recommender.catalog_loader import load_catalog
from backend.app.recommender.rules import derive_signals


FIELDS_TO_MERGE = ("suggested_models", "why", "risks", "next_steps", "not_recommended", "required_preprocessing")


def _matches(rule: dict[str, Any], signals: dict[str, bool]) -> bool:
    return all(signals.get(item, False) for item in rule.get("match", [])) and not any(
        signals.get(item, False) for item in rule.get("exclude", [])
    )


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def build_recommendation(
    source: dict[str, Any],
    summary: dict[str, Any],
    schema: dict[str, Any],
    quality: dict[str, Any],
    statistics: dict[str, Any],
    target: dict[str, Any],
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    signals = derive_signals(source, summary, schema, quality, statistics, target, context)
    catalog = load_catalog()
    matched = [rule for rule in catalog.get("rules", []) if _matches(rule, signals)]
    matched.sort(key=lambda item: item.get("priority", 0), reverse=True)

    if not matched:
        matched = [catalog["default"]]

    primary = matched[0]
    recommendation = {
        "recommended_approach": primary["recommended_approach"],
        "suggested_models": [],
        "confidence": primary.get("confidence", "medium"),
        "why": [],
        "risks": [],
        "next_steps": [],
        "not_recommended": [],
        "required_preprocessing": [],
        "matched_rules": [rule.get("id") for rule in matched if rule.get("id")],
        "signals": signals,
    }

    for rule in matched[:4]:
        for field in FIELDS_TO_MERGE:
            recommendation[field].extend(rule.get(field, []))

    for field in FIELDS_TO_MERGE:
        recommendation[field] = _unique(recommendation[field])

    if signals.get("sensitive_data"):
        recommendation["risks"] = _unique(
            recommendation["risks"]
            + ["Existem possíveis campos sensíveis; evite enviar dados brutos para serviços externos sem anonimização."]
        )
        recommendation["next_steps"] = _unique(
            recommendation["next_steps"] + ["Validar política de privacidade, mascaramento e retenção antes de modelar."]
        )

    return recommendation
