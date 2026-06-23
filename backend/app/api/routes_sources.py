from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.app.core.security import public_error
from backend.app.loaders.api_loader import preview_api
from backend.app.models.schemas import ApiSourceRequest

router = APIRouter(prefix="/sources", tags=["sources"])


@router.post("/api/test")
def test_api_source(request: ApiSourceRequest) -> dict:
    try:
        return preview_api(request)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=public_error(str(exc))) from exc
