from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_name: str = "Data Profiler AI"
    app_version: str = "0.1.0"
    cors_origins: list[str] = None  # type: ignore[assignment]

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[3]

    @property
    def reports_dir(self) -> Path:
        return self.project_root / "reports"

    @property
    def upload_dir(self) -> Path:
        return self.project_root / "backend" / "uploads"

    @property
    def allowed_file_roots(self) -> list[Path]:
        raw = os.getenv("DATA_PROFILER_ALLOWED_PATHS")
        if not raw:
            return [self.project_root]
        return [Path(item).expanduser().resolve() for item in raw.split(os.pathsep) if item.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return int(os.getenv("DATA_PROFILER_MAX_UPLOAD_BYTES", str(50 * 1024 * 1024)))

    @property
    def allow_private_api_hosts(self) -> bool:
        return os.getenv("DATA_PROFILER_ALLOW_PRIVATE_API_HOSTS", "false").lower() in {"1", "true", "yes"}

    @property
    def model_catalog_path(self) -> Path:
        return self.project_root / "backend" / "config" / "model_catalog.yaml"


settings = Settings(cors_origins=["http://localhost:3000", "http://127.0.0.1:3000"])
