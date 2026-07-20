#!/usr/bin/env python3
"""Shared utilities for creatiads scripts.

Contains status constants, error classification, JSON I/O helpers, and
data extraction utilities — the functions that every script used to import
from the now-deleted mcp_tools.py bridge.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

# ── Status constants ──────────────────────────────────────────

STATUS_OK = "ok"
STATUS_STRUCTURED_UNAVAILABLE = "structured_unavailable"
STATUS_UNSUPPORTED = "unsupported"
STATUS_PERMISSION_DENIED = "permission_denied"
STATUS_RATE_LIMITED = "rate_limited"
STATUS_PARTIAL = "partial"
STATUS_SUPPORTED_EMPTY = "supported_empty"
STATUS_DEGRADED = "degraded"
STATUS_NOT_QUERIED = "not_queried"

SECRET_RE = re.compile(
    r"(?i)(access[_-]?token|authorization|bearer|oauth|client_secret|refresh_token|api_key|ticket)"
)


def classify_error(message: str) -> str:
    text = message.lower()
    if any(token in text for token in ("permission", "unauthorized", "forbidden", "scope", "access denied")):
        return STATUS_PERMISSION_DENIED
    if any(token in text for token in ("rate limit", "too many", "429", "throttle")):
        return STATUS_RATE_LIMITED
    if any(token in text for token in ("unsupported", "invalid field", "invalid metric", "not support")):
        return STATUS_UNSUPPORTED
    return STATUS_DEGRADED


# ── Data utilities ────────────────────────────────────────────

def extract_rows(payload: Any) -> list[dict[str, Any]]:
    """Extract rows from common MCP response shapes."""
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in (
        "rows",
        "list",
        "items",
        "data",
        "ads",
        "campaigns",
        "adgroups",
        "apps",
        "image_infos",
        "video_infos",
    ):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            nested = extract_rows(value)
            if nested:
                return nested
    return []


def chunked(values: Iterable[Any], size: int) -> list[list[Any]]:
    if size <= 0:
        raise ValueError("chunk size must be positive")
    batch: list[Any] = []
    batches: list[list[Any]] = []
    for value in values:
        batch.append(value)
        if len(batch) >= size:
            batches.append(batch)
            batch = []
    if batch:
        batches.append(batch)
    return batches


# ── Serialization ─────────────────────────────────────────────

def sanitize_payload(value: Any) -> Any:
    if isinstance(value, dict):
        clean: dict[str, Any] = {}
        for key, child in value.items():
            if SECRET_RE.search(str(key)):
                clean[key] = "<redacted>"
            else:
                clean[key] = sanitize_payload(child)
        return clean
    if isinstance(value, list):
        return [sanitize_payload(item) for item in value]
    if isinstance(value, str) and SECRET_RE.search(value):
        return "<redacted>"
    return value


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(sanitize_payload(payload), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
