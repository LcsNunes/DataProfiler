from __future__ import annotations

import re
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


SENSITIVE_KEY_PARTS = (
    "api_key",
    "apikey",
    "token",
    "secret",
    "password",
    "passwd",
    "authorization",
    "auth",
    "credential",
    "bearer",
)


def is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(part in normalized for part in SENSITIVE_KEY_PARTS)


def mask_value(value: Any) -> str:
    text = "" if value is None else str(value)
    if not text:
        return "***"
    if len(text) <= 8:
        return "***"
    return f"{text[:2]}***{text[-2:]}"


def sanitize_for_output(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: mask_value(val) if is_sensitive_key(str(key)) else sanitize_for_output(val)
            for key, val in value.items()
        }
    if isinstance(value, list):
        return [sanitize_for_output(item) for item in value]
    return value


def sanitize_connection_string(connection_string: str) -> str:
    try:
        parts = urlsplit(connection_string)
    except ValueError:
        return re.sub(r"://([^:/@]+):([^@]+)@", r"://\1:***@", connection_string)

    if "@" not in parts.netloc or ":" not in parts.netloc.split("@", 1)[0]:
        return connection_string

    credentials, host = parts.netloc.rsplit("@", 1)
    username = credentials.split(":", 1)[0]
    safe_netloc = f"{username}:***@{host}"
    return urlunsplit((parts.scheme, safe_netloc, parts.path, parts.query, parts.fragment))


def sanitize_url(url: str) -> str:
    try:
        parts = urlsplit(str(url))
    except ValueError:
        return redact_text(str(url))
    safe_query = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        safe_query.append((key, mask_value(value) if is_sensitive_key(key) else value))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(safe_query), parts.fragment))


def redact_text(text: str) -> str:
    patterns = [
        r"(?i)(authorization:\s*bearer\s+)[^\s,;]+",
        r"(?i)(api[_-]?key['\"]?\s*[:=]\s*['\"]?)[^'\"\s,;]+",
        r"(?i)(password['\"]?\s*[:=]\s*['\"]?)[^'\"\s,;]+",
        r"(?i)(token['\"]?\s*[:=]\s*['\"]?)[^'\"\s,;]+",
    ]
    redacted = text
    for pattern in patterns:
        redacted = re.sub(pattern, r"\1***", redacted)
    redacted = re.sub(r"://([^:/@\s]+):([^@\s]+)@", r"://\1:***@", redacted)
    return redacted


def public_error(message: str) -> str:
    return redact_text(message)
