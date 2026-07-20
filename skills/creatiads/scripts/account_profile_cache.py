#!/usr/bin/env python3
"""Account-level cache for TikTok user type and metric preset decisions."""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

DEFAULT_TTL_DAYS = 14
CACHE_SCHEMA_VERSION = "2026-06-01-account-profile-v1"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_dt(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def cache_root() -> Path:
    override = os.environ.get("CREATIADS_ACCOUNT_CACHE_ROOT")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".codex" / "creatiads" / "cache" / "tiktok_accounts"


def account_cache_dir(advertiser_id: str, *, root: Path | None = None) -> Path:
    safe_id = "".join(ch for ch in str(advertiser_id) if ch.isalnum() or ch in {"_", "-"}).strip()
    if not safe_id:
        safe_id = hashlib.sha256(str(advertiser_id).encode("utf-8")).hexdigest()[:16]
    return (root or cache_root()) / safe_id


def account_cache_path(advertiser_id: str, *, root: Path | None = None) -> Path:
    return account_cache_dir(advertiser_id, root=root) / "profile.json"


def evidence_hash(evidence: dict[str, Any] | None) -> str:
    if not evidence:
        return ""
    summary = {
        key: evidence.get(key)
        for key in (
            "app_count",
            "catalog_count",
            "shop_count",
            "smart_plus_count",
            "landing_count",
            "errors",
        )
        if key in evidence
    }
    if not summary:
        summary = {
            "app_rows": len(evidence.get("app_rows") or []),
            "catalog_rows": len(evidence.get("catalog_rows") or evidence.get("catalog_evidence") or []),
            "shop_rows": len(evidence.get("shop_rows") or evidence.get("shop_evidence") or []),
            "smart_plus_rows": len(evidence.get("smart_plus_rows") or []),
        }
    raw = json.dumps(summary, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def load_account_profile_cache(
    advertiser_id: str,
    *,
    root: Path | None = None,
    now: datetime | None = None,
    max_age_days: int = DEFAULT_TTL_DAYS,
) -> dict[str, Any] | None:
    path = account_cache_path(advertiser_id, root=root)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    if str(payload.get("advertiser_id") or "") != str(advertiser_id):
        return None
    generated_at = _parse_dt(payload.get("generated_at"))
    expires_at = _parse_dt(payload.get("expires_at"))
    current = now or _utcnow()
    if expires_at and current > expires_at:
        return None
    if generated_at and max_age_days > 0 and current - generated_at > timedelta(days=max_age_days):
        return None
    if not isinstance(payload.get("user_type"), dict):
        return None
    return payload


def write_account_profile_cache(
    advertiser_id: str,
    *,
    user_type: dict[str, Any],
    metric_preset: dict[str, Any] | None = None,
    evidence: dict[str, Any] | None = None,
    planner_version: str = "",
    root: Path | None = None,
    ttl_days: int = DEFAULT_TTL_DAYS,
    now: datetime | None = None,
) -> dict[str, Any]:
    current = now or _utcnow()
    path = account_cache_path(advertiser_id, root=root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": CACHE_SCHEMA_VERSION,
        "platform": "tiktok",
        "advertiser_id": str(advertiser_id),
        "generated_at": current.isoformat(),
        "expires_at": (current + timedelta(days=ttl_days)).isoformat(),
        "ttl_days": ttl_days,
        "planner_version": planner_version,
        "source": "classification",
        "user_type": user_type,
        "metric_preset": metric_preset or {},
        "evidence_hash": evidence_hash(evidence),
        "evidence_summary": {
            "app_rows": len((evidence or {}).get("app_rows") or []),
            "catalog_rows": len((evidence or {}).get("catalog_rows") or (evidence or {}).get("catalog_evidence") or []),
            "shop_rows": len((evidence or {}).get("shop_rows") or (evidence or {}).get("shop_evidence") or []),
            "smart_plus_rows": len((evidence or {}).get("smart_plus_rows") or []),
            "errors": (evidence or {}).get("errors") or [],
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def cached_user_type_label(cache: dict[str, Any] | None) -> str:
    if not isinstance(cache, dict):
        return ""
    user_type = cache.get("user_type")
    if not isinstance(user_type, dict):
        return ""
    return str(
        user_type.get("derived_user_type")
        or user_type.get("top_type")
        or ((user_type.get("top_types") or [{}])[0].get("type"))
        or ""
    )
