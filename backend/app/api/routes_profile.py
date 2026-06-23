from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.app.core.config import settings
from backend.app.core.security import public_error
from backend.app.loaders.api_loader import load_api
from backend.app.loaders.file_loader import is_supported_file_name, load_file
from backend.app.loaders.sql_loader import load_sql
from backend.app.models.schemas import ApiSourceRequest, FilePathRequest, FilePathsRequest, SqlSourceRequest
from backend.app.profiler.multi_profile_runner import run_multi_profile
from backend.app.profiler.profile_runner import run_profile

router = APIRouter(prefix="/profile", tags=["profile"])


def _public_exception(exc: Exception) -> HTTPException:
    return HTTPException(status_code=400, detail=public_error(str(exc)))


def _save_upload(file: UploadFile) -> Path:
    safe_name = Path(file.filename or "upload").name
    if not is_supported_file_name(safe_name):
        raise ValueError("Unsupported upload file extension.")
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    destination = settings.upload_dir / f"{uuid4().hex[:8]}_{safe_name}"
    bytes_written = 0
    with destination.open("wb") as fp:
        while chunk := file.file.read(1024 * 1024):
            bytes_written += len(chunk)
            if bytes_written > settings.max_upload_bytes:
                fp.close()
                destination.unlink(missing_ok=True)
                raise ValueError(f"Upload exceeds maximum size of {settings.max_upload_bytes} bytes.")
            fp.write(chunk)
    return destination


@router.post("/file-path")
def profile_file_path(request: FilePathRequest) -> dict:
    try:
        return run_profile(
            load_file(request.path, enforce_allowed_roots=True, include_path=False),
            business_objective=request.business_objective,
        )
    except Exception as exc:
        raise _public_exception(exc) from exc


@router.post("/file-paths")
def profile_file_paths(request: FilePathsRequest) -> dict:
    try:
        loaded_items = [load_file(path, enforce_allowed_roots=True, include_path=False) for path in request.paths]
        return run_multi_profile(loaded_items, business_objective=request.business_objective)
    except Exception as exc:
        raise _public_exception(exc) from exc


@router.post("/upload")
def profile_upload(file: UploadFile = File(...), business_objective: str | None = Form(default=None)) -> dict:
    try:
        destination = _save_upload(file)
        loaded = load_file(str(destination), include_path=False)
        loaded.source["name"] = Path(file.filename or destination.name).name
        loaded.metadata["original_file_name"] = loaded.source["name"]
        return run_profile(loaded, business_objective=business_objective)
    except Exception as exc:
        raise _public_exception(exc) from exc


@router.post("/upload-multiple")
def profile_upload_multiple(
    files: list[UploadFile] = File(...),
    business_objective: str | None = Form(default=None),
) -> dict:
    try:
        if len(files) < 2:
            raise ValueError("Upload at least two files for multi-dataset analysis.")
        loaded_items = []
        for file in files:
            safe_name = Path(file.filename or "upload").name
            destination = _save_upload(file)
            loaded = load_file(str(destination), include_path=False)
            loaded.source["name"] = safe_name
            loaded.metadata["original_file_name"] = safe_name
            loaded_items.append(loaded)
        return run_multi_profile(loaded_items, business_objective=business_objective)
    except Exception as exc:
        raise _public_exception(exc) from exc


@router.post("/api")
def profile_api(request: ApiSourceRequest) -> dict:
    try:
        return run_profile(load_api(request), business_objective=request.business_objective)
    except Exception as exc:
        raise _public_exception(exc) from exc


@router.post("/sql")
def profile_sql(request: SqlSourceRequest) -> dict:
    try:
        return run_profile(load_sql(request), business_objective=request.business_objective)
    except Exception as exc:
        raise _public_exception(exc) from exc
