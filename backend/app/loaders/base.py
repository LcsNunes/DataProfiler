from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import polars as pl


@dataclass
class DataLoadResult:
    dataframe: pl.DataFrame
    source: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

