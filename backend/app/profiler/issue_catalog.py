from __future__ import annotations

from functools import lru_cache
from typing import Any

import yaml

from backend.app.core.config import settings


@lru_cache(maxsize=1)
def load_issue_catalog() -> dict[str, Any]:
    path = settings.project_root / "backend" / "config" / "quality_issue_catalog.yaml"
    with path.open("r", encoding="utf-8") as fp:
        payload = yaml.safe_load(fp)
    return payload.get("issues", {})


def explain_problem(problem_type: str) -> dict[str, Any] | None:
    explanation = load_issue_catalog().get(problem_type)
    if not explanation:
        return None
    return {"type": problem_type, **explanation}

