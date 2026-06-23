from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes_health import router as health_router
from backend.app.api.routes_profile import router as profile_router
from backend.app.api.routes_reports import router as reports_router
from backend.app.api.routes_sources import router as sources_router
from backend.app.core.config import settings
from backend.app.core.logging import configure_logging


configure_logging()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Automatic data profiling, data-quality diagnostics and model recommendation API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(profile_router)
app.include_router(reports_router)
app.include_router(sources_router)

