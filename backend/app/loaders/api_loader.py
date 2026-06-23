from __future__ import annotations

import ipaddress
import socket
import time
from typing import Any
from urllib.parse import urljoin, urlsplit

import requests
from requests.auth import HTTPBasicAuth

from backend.app.core.config import settings
from backend.app.core.security import sanitize_for_output, sanitize_url
from backend.app.loaders.base import DataLoadResult
from backend.app.loaders.json_normalizer import extract_records, flatten_records, get_by_path
from backend.app.models.schemas import ApiSourceRequest


def _validate_external_url(url: str, *, base_url: str | None = None) -> None:
    parts = urlsplit(str(url))
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        raise ValueError("Only http/https API URLs with a host are allowed.")
    if base_url:
        base = urlsplit(str(base_url))
        if parts.hostname != base.hostname:
            raise ValueError("Paginated next_url must stay on the original host.")
    if settings.allow_private_api_hosts:
        return
    try:
        addresses = socket.getaddrinfo(parts.hostname, parts.port or (443 if parts.scheme == "https" else 80), proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise ValueError("Could not resolve API host.") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
            raise ValueError("API host resolves to a private or unsafe network address.")


def _build_request(config: ApiSourceRequest) -> tuple[dict[str, str], dict[str, Any], Any]:
    headers = dict(config.headers)
    params = dict(config.params)
    auth = None

    if config.auth.type == "api_key" and config.auth.api_key_name and config.auth.api_key_value:
        if config.auth.api_key_location == "header":
            headers[config.auth.api_key_name] = config.auth.api_key_value
        else:
            params[config.auth.api_key_name] = config.auth.api_key_value
    elif config.auth.type == "bearer" and config.auth.bearer_token:
        headers["Authorization"] = f"Bearer {config.auth.bearer_token}"
    elif config.auth.type == "basic" and config.auth.basic_username and config.auth.basic_password:
        auth = HTTPBasicAuth(config.auth.basic_username, config.auth.basic_password)

    return headers, params, auth


def _request_json(config: ApiSourceRequest, url: str, params: dict[str, Any]) -> Any:
    _validate_external_url(url, base_url=config.url)
    headers, base_params, auth = _build_request(config)
    request_params = {**base_params, **params}
    last_error: Exception | None = None

    for attempt in range(config.retries + 1):
        try:
            response = requests.request(
                method=config.method,
                url=url,
                headers=headers,
                params=request_params,
                json=config.body if config.method == "POST" else None,
                timeout=config.timeout,
                auth=auth,
                allow_redirects=False,
            )
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            last_error = exc
            if attempt < config.retries:
                time.sleep(0.4 * (attempt + 1))

    raise RuntimeError(f"API request failed after retries for {sanitize_url(url)}") from last_error


def _collect_paginated(config: ApiSourceRequest) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    pagination = config.pagination

    if pagination.type == "none":
        payload = _request_json(config, config.url, {})
        return extract_records(payload, config.data_path)

    if pagination.type == "page_limit":
        for index in range(pagination.max_pages):
            page = pagination.start_page + index
            payload = _request_json(
                config,
                config.url,
                {pagination.page_param: page, pagination.limit_param: pagination.limit},
            )
            page_records = extract_records(payload, config.data_path)
            records.extend(page_records)
            if len(page_records) < pagination.limit:
                break
        return records

    if pagination.type == "offset_limit":
        offset = pagination.start_offset
        for _ in range(pagination.max_pages):
            payload = _request_json(
                config,
                config.url,
                {pagination.offset_param: offset, pagination.limit_param: pagination.limit},
            )
            page_records = extract_records(payload, config.data_path)
            records.extend(page_records)
            if len(page_records) < pagination.limit:
                break
            offset += pagination.limit
        return records

    if pagination.type == "next_url":
        next_url = config.url
        for _ in range(pagination.max_pages):
            payload = _request_json(config, next_url, {})
            page_records = extract_records(payload, config.data_path)
            records.extend(page_records)
            raw_next = get_by_path(payload, pagination.next_url_path or "next")
            if not raw_next:
                break
            next_url = urljoin(next_url, str(raw_next))
        return records

    next_token: str | None = None
    for _ in range(pagination.max_pages):
        params = {}
        if next_token:
            params[pagination.next_token_param] = next_token
        payload = _request_json(config, config.url, params)
        page_records = extract_records(payload, config.data_path)
        records.extend(page_records)
        next_token = get_by_path(payload, pagination.next_token_path or "next_token")
        if not next_token:
            break
    return records


def load_api(config: ApiSourceRequest) -> DataLoadResult:
    _validate_external_url(config.url)
    records = _collect_paginated(config)
    df = flatten_records(records)
    safe_config = sanitize_for_output(config.model_dump())
    safe_config["url"] = sanitize_url(config.url)
    return DataLoadResult(
        dataframe=df,
        source={
            "type": "api",
            "url": sanitize_url(config.url),
            "method": config.method,
            "config": safe_config,
        },
        metadata={"records_loaded": len(records), "data_path": config.data_path},
    )


def preview_api(config: ApiSourceRequest, limit: int = 5) -> dict[str, Any]:
    limited = config.model_copy(deep=True)
    limited.pagination.max_pages = 1
    limited.pagination.limit = min(limited.pagination.limit, max(limit, 1))
    loaded = load_api(limited)
    return {
        "columns": loaded.dataframe.columns,
        "rows": loaded.dataframe.head(limit).to_dicts(),
        "source": loaded.source,
    }
