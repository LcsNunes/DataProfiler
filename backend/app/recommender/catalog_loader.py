from __future__ import annotations

from functools import lru_cache
from typing import Any

import yaml

from backend.app.core.config import settings


@lru_cache(maxsize=1)
def load_catalog() -> dict[str, Any]:
    with settings.model_catalog_path.open("r", encoding="utf-8") as fp:
        return yaml.safe_load(fp)

