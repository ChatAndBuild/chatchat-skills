#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


SECRET_PATTERNS = [
    re.compile(r"access[_-]?token", re.I),
    re.compile(r"authorization\s*[:=]", re.I),
    re.compile(r"bearer\s+[A-Za-z0-9._~+/=-]{16,}", re.I),
    re.compile(r"x-api-key\s*[:=]", re.I),
    re.compile(r"oauth.*callback.*(code|state|secret)", re.I),
    re.compile(r"ticket=[A-Za-z0-9%._~+/=-]{16,}", re.I),
    # MCP session metadata — must never appear in sources
    re.compile(r"mcp.*session.*(token|secret|key)", re.I),
    re.compile(r"session.*metadata", re.I),
    re.compile(r"mcpSessionToken", re.I),
    re.compile(r"Mcp-Session-Id", re.I),
]

SUBAGENT_BACKEND = "mcp_subagent_executor"
LEGACY_BRIDGE_BACKEND = "bridge_executor"
EXECUTOR_BACKEND_ALIASES = {SUBAGENT_BACKEND, LEGACY_BRIDGE_BACKEND}
LEAN_KPI_KEYS = {"spend", "impressions", "clicks", "conversion"}
ADVERTISER_VALUE_KPI_KEYS = {
    "total_purchase",
    "total_purchase_value",
    "total_active_pay_roas",
    "complete_payment",
    "complete_payment_roas",
    "value_per_complete_payment",
    "onsite_total_purchase",
    "onsite_total_purchase_value",
    "onsite_purchases_roas",
    "shop_total_purchase_by_order_submission",
    "shop_gross_revenue_by_order_submission",
}

REQUIRED_HTML_MARKERS = [
    "Scope:",
    "Data Quality",
]

CURRENT_SOURCE_HINTS = (
    "current_account",
    "current_advertiser",
    "current_campaign",
    "current_adgroup",
    "current_adset",
    "current_ads",
    "current_ad_",
)

PREVIOUS_SOURCE_HINTS = (
    "previous_advertiser",
    "previous_account",
    "previous_campaign",
    "previous_adgroup",
    "previous_adset",
    "previous_ads",
    "comparison",
)

PREVIEW_COVERAGE_STATUSES = {
    "with_preview",
    "inline_image",
    "action_url_only",
    "spark_post_url",
}

PREVIEW_EVIDENCE_FIELDS = {
    "preview_image_url",
    "preview_action_url",
    "thumbnail_url",
    "cover_url",
    "image_url",
    "video_url",
    "playable_url",
    "preview_url",
    "permalink_url",
    "spark_post_url",
}


def load_json(path: Path) -> tuple[bool, Any | str]:
    try:
        return True, json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, str(exc)


def count_rows(data: Any) -> int:
    if isinstance(data, list):
        return len(data)
    if not isinstance(data, dict):
        return 1 if data else 0
    for key in ("rows", "segments", "data", "items", "list", "accounts"):
        value = data.get(key)
        if isinstance(value, list):
            return len(value)
        if isinstance(value, dict):
            nested = value.get("rows") or value.get("list") or value.get("items")
            if isinstance(nested, list):
                return len(nested)
    if isinstance(data.get("sections"), dict):
        total = 0
        for section in data["sections"].values():
            if isinstance(section, dict):
                rows = section.get("rows") or section.get("segments") or []
            else:
                rows = section
            if isinstance(rows, list):
                total += len(rows)
        return total
    return 1 if data else 0


def metric_keys(data: Any) -> set[str]:
    rows: list[Any] = []
    if isinstance(data, dict):
        for key in ("rows", "data", "items", "list"):
            value = data.get(key)
            if isinstance(value, list):
                rows = value
                break
            if isinstance(value, dict):
                nested = value.get("rows") or value.get("list") or value.get("items")
                if isinstance(nested, list):
                    rows = nested
                    break
    elif isinstance(data, list):
        rows = data
    keys: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        metrics = row.get("metrics")
        if isinstance(metrics, dict):
            keys.update(str(key) for key in metrics)
        for key, value in row.items():
            if key not in {"dimensions", "metrics"} and not isinstance(value, (dict, list)):
                keys.add(str(key))
    return keys


def scan_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def display_path(path: Path, *, base: Path | None = None) -> str:
    """Return a stable artifact path for reports and committed fixtures."""
    try:
        if base is not None:
            return str(path.resolve().relative_to(base.resolve()))
    except Exception:
        pass
    return path.name if path.is_absolute() else str(path)


def secret_hits(text: str) -> list[str]:
    return [pattern.pattern for pattern in SECRET_PATTERNS if pattern.search(text)]


def read_manifest(run_dir: Path) -> tuple[bool, dict[str, Any] | str]:
    manifest = run_dir / "manifest.json"
    if not manifest.exists():
        return False, "manifest.json missing"
    ok, payload = load_json(manifest)
    if not ok:
        return False, payload
    if not isinstance(payload, dict):
        return False, "manifest.json is not an object"
    return True, payload


def as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def rel_exists(run_dir: Path, raw_path: Any) -> bool:
    if not isinstance(raw_path, str) or not raw_path.strip():
        return False
    path = Path(raw_path)
    if path.is_absolute():
        return path.exists()
    return (run_dir / path).exists()


def manifest_contract_audit(run_dir: Path, manifest: dict[str, Any] | None) -> dict[str, Any]:
    if not manifest:
        return {
            "checked": False,
            "passed": False,
            "missing_fields": ["manifest"],
            "missing_source_files": [],
            "pending_source_files": [],
            "message": "manifest unavailable",
        }

    field_groups = {
        "platform": ["platform"],
        "account_or_advertiser_id": ["account_or_advertiser_id", "advertiser_id", "account_id", "ad_account_id"],
        "period": ["period"],
        "depth": ["depth"],
        "date_window": ["since", "until", "periods"],
        "mcp_servers": ["mcp_servers", "mcp_server", "server_name"],
        "tools_used": ["tools_used", "mcp_tools_called"],
        "coverage": ["coverage"],
        "source_files": ["source_files", "files"],
        "validation_status": ["validation_status", "validation_summary"],
    }
    source_entries = []
    for key in ("source_files", "files"):
        source_entries.extend(as_list(manifest.get(key)))

    missing_fields = []
    for canonical, aliases in field_groups.items():
        has_value = any(alias in manifest and manifest.get(alias) not in (None, "", []) for alias in aliases)
        if canonical == "validation_status" and not has_value:
            has_value = (run_dir / "validation_summary.json").exists() or "validation_summary.json" in source_entries
        if not has_value:
            missing_fields.append(canonical)

    missing_source_files = []
    pending_source_files = []
    for entry in source_entries:
        if not isinstance(entry, str):
            continue
        if rel_exists(run_dir, entry):
            continue
        if Path(entry).name == "report_audit.json":
            pending_source_files.append(entry)
            continue
        missing_source_files.append(entry)

    coverage = manifest.get("coverage", {})
    coverage_ok = isinstance(coverage, dict)
    return {
        "checked": True,
        "passed": not missing_fields and not missing_source_files and coverage_ok,
        "missing_fields": missing_fields,
        "missing_source_files": missing_source_files,
        "pending_source_files": pending_source_files,
        "coverage_is_object": coverage_ok,
        "message": None
        if not missing_fields and not missing_source_files and coverage_ok
        else "manifest is missing required report contract fields or declared source files",
    }


def extract_section(html: str, section_id: str) -> str:
    marker = f'id="{section_id}"'
    idx = html.find(marker)
    if idx < 0:
        return ""
    start = html.rfind("<div", 0, idx)
    if start < 0:
        start = idx
    next_section = html.find('<div class="section"', idx + len(marker))
    if next_section < 0:
        return html[start:]
    return html[start:next_section]


def preview_html_embedding_audit(run_dir: Path, html: str) -> dict[str, Any]:
    source_path = run_dir / "sources" / "creative_previews.json"
    if not source_path.exists():
        return {"checked": False, "passed": True, "message": "creative_previews.json missing; skipped HTML embedding audit"}
    ok, payload = load_json(source_path)
    if not ok or not isinstance(payload, dict):
        return {"checked": True, "passed": False, "message": "creative_previews.json invalid"}
    rows = payload.get("rows") or []
    image_fields = {"preview_image_url", "image_url", "thumbnail_url", "cover_url"}
    action_fields = {"preview_action_url", "preview_url", "video_url", "playable_url", "spark_post_url"}
    needs_img = any(isinstance(row, dict) and any(row.get(field) for field in image_fields) for row in rows)
    needs_link = any(isinstance(row, dict) and any(row.get(field) for field in action_fields) for row in rows)
    section = extract_section(html, "creative-preview")
    has_img = "<img" in section.lower()
    has_link = "<a " in section.lower() and "href=" in section.lower()
    failures = []
    if needs_img and not has_img:
        failures.append("creative preview image URLs exist but no <img> is embedded in HTML")
    if needs_link and not has_link:
        failures.append("creative preview action URLs exist but no <a href> is embedded in HTML")
    return {
        "checked": True,
        "passed": not failures,
        "needs_img": needs_img,
        "has_img": has_img,
        "needs_link": needs_link,
        "has_link": has_link,
        "message": "; ".join(failures) if failures else None,
    }


def json_row_count(path: Path) -> int:
    ok, payload = load_json(path)
    return count_rows(payload) if ok else 0


def source_row_audit(run_dir: Path, manifest: dict[str, Any] | None) -> dict[str, Any]:
    source_paths = sorted(run_dir.glob("*.json")) + sorted((run_dir / "sources").glob("*.json"))
    current = [
        path
        for path in source_paths
        if any(hint in path.name for hint in CURRENT_SOURCE_HINTS)
    ]
    previous = [
        path
        for path in source_paths
        if any(hint in path.name for hint in PREVIOUS_SOURCE_HINTS)
    ]
    current_rows = sum(json_row_count(path) for path in current)
    previous_rows = sum(json_row_count(path) for path in previous)

    period = str((manifest or {}).get("period", "")).lower()
    comparison_eligible = (manifest or {}).get("comparison_eligible")
    if comparison_eligible is None:
        comparison_eligible = period in {"daily", "weekly"} and bool(previous)

    return {
        "checked": True,
        "passed": current_rows > 0 and (not comparison_eligible or previous_rows > 0),
        "current_sources": [str(path) for path in current],
        "previous_sources": [str(path) for path in previous],
        "current_rows": current_rows,
        "previous_rows": previous_rows,
        "comparison_eligible": bool(comparison_eligible),
        "message": None
        if current_rows > 0 and (not comparison_eligible or previous_rows > 0)
        else "current rows or required comparison rows are missing",
    }


def user_type_audit(run_dir: Path, html_path: Path) -> dict[str, Any]:
    candidates = [run_dir / "user_type.json", run_dir / "sources" / "user_type.json"]
    user_type_path = next((path for path in candidates if path.exists()), None)
    analysis_path = run_dir / "analysis_brief.json"
    ordering_violation = False
    checked_ordering = False
    if user_type_path:
        later_paths = [path for path in (analysis_path, html_path) if path.exists()]
        if later_paths:
            checked_ordering = True
            ordering_violation = any(user_type_path.stat().st_mtime > path.stat().st_mtime + 1 for path in later_paths)
    return {
        "checked": True,
        "passed": user_type_path is not None and not ordering_violation,
        "user_type_path": str(user_type_path) if user_type_path else None,
        "checked_ordering": checked_ordering,
        "ordering_violation": ordering_violation,
        "message": None
        if user_type_path is not None and not ordering_violation
        else "user_type.json is missing or appears newer than analysis/report artifacts",
    }


def user_type_hash(user_type_payload: dict[str, Any] | None) -> str | None:
    if not user_type_payload:
        return None
    top = (user_type_payload.get("top_types") or [{}])[0] if isinstance(user_type_payload.get("top_types"), list) else {}
    payload = {
        "top_type": user_type_payload.get("top_type") or top.get("type"),
        "top_index": top.get("index"),
        "derived_user_type": user_type_payload.get("derived_user_type"),
        "w2a_evidence": bool(user_type_payload.get("w2a_evidence")),
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _parse_dt(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def metric_preset_audit(run_dir: Path, html_path: Path) -> dict[str, Any]:
    user_path = next((path for path in (run_dir / "user_type.json", run_dir / "sources" / "user_type.json") if path.exists()), None)
    preset_path = next((path for path in (run_dir / "metric_preset.json", run_dir / "sources" / "metric_preset.json") if path.exists()), None)
    if not user_path or not preset_path:
        return {
            "checked": True,
            "passed": False,
            "user_type_path": str(user_path) if user_path else None,
            "metric_preset_path": str(preset_path) if preset_path else None,
            "message": "user_type.json or metric_preset.json is missing",
        }
    user_ok, user_payload = load_json(user_path)
    preset_ok, preset_payload = load_json(preset_path)
    if not user_ok or not preset_ok or not isinstance(user_payload, dict) or not isinstance(preset_payload, dict):
        return {
            "checked": True,
            "passed": False,
            "user_type_path": str(user_path),
            "metric_preset_path": str(preset_path),
            "message": "user_type.json or metric_preset.json is invalid",
        }
    top_type = user_payload.get("top_type") or ((user_payload.get("top_types") or [{}])[0].get("type"))
    derived = user_payload.get("derived_user_type") or top_type
    expected_hash = user_type_hash(user_payload)
    actual_hash = preset_payload.get("source_user_type_hash")
    mismatch = []
    if preset_payload.get("user_type") != top_type:
        mismatch.append("preset user_type does not match user_type top type")
    if preset_payload.get("derived_user_type") != derived:
        mismatch.append("preset derived_user_type does not match user_type derived type")
    if actual_hash and actual_hash != expected_hash:
        mismatch.append("preset source_user_type_hash does not match user_type.json")
    ordering_violation = False
    later_paths = [path for path in (html_path, run_dir / "analysis_brief.json") if path.exists()]
    if later_paths:
        ordering_violation = any(preset_path.stat().st_mtime > path.stat().st_mtime + 1 for path in later_paths)
    return {
        "checked": True,
        "passed": not mismatch and not ordering_violation,
        "user_type_path": str(user_path),
        "metric_preset_path": str(preset_path),
        "expected_hash": expected_hash,
        "actual_hash": actual_hash,
        "ordering_violation": ordering_violation,
        "message": "; ".join(mismatch) if mismatch else ("metric_preset.json appears newer than analysis/report artifacts" if ordering_violation else None),
    }


def mcp_phase_order_audit(run_dir: Path) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    phase_times: dict[str, list[tuple[str, datetime]]] = {"classification": [], "preset": [], "report_data": [], "enrichment": []}
    for path in sorted((run_dir / "sources").glob("*.json")):
        ok, payload = load_json(path)
        if not ok or not isinstance(payload, dict):
            continue
        phase = payload.get("phase")
        if phase not in phase_times:
            continue
        generated = _parse_dt(payload.get("generated_at"))
        if generated is None:
            failures.append({"file": path.name, "reason": f"phase {phase} source missing generated_at"})
            continue
        phase_times[phase].append((path.name, generated))

    preset_times = phase_times["preset"]
    if not preset_times:
        failures.append({"file": "metric_preset.json", "reason": "no preset phase source found"})
    else:
        first_preset = min(ts for _, ts in preset_times)
        for phase in ("report_data", "enrichment"):
            for file_name, ts in phase_times[phase]:
                if ts < first_preset:
                    failures.append({"file": file_name, "reason": f"{phase} generated before metric_preset"})
    return {
        "checked": True,
        "passed": not failures,
        "failures": failures,
        "phase_counts": {phase: len(items) for phase, items in phase_times.items()},
        "message": None if not failures else "MCP source phase ordering is invalid",
    }


def html_has_any(html: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, html, re.I) for pattern in patterns)


def preview_evidence_audit(run_dir: Path) -> dict[str, Any]:
    source_path = run_dir / "sources" / "creative_previews.json"
    if not source_path.exists():
        return {
            "checked": False,
            "passed": True,
            "rows_checked": 0,
            "invalid_rows": [],
            "message": "creative_previews.json missing; skipped preview evidence audit",
        }

    ok, payload = load_json(source_path)
    if not ok:
        return {
            "checked": True,
            "passed": False,
            "rows_checked": 0,
            "invalid_rows": [{"error": payload}],
            "message": "creative_previews.json is invalid",
        }

    rows = payload.get("rows", []) if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        return {
            "checked": True,
            "passed": False,
            "rows_checked": 0,
            "invalid_rows": [{"error": "creative preview rows are not a list"}],
            "message": "creative_previews rows must be a list",
        }

    invalid_rows = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        status = str(row.get("preview_status", "")).strip()
        if status not in PREVIEW_COVERAGE_STATUSES:
            continue
        has_evidence = any(row.get(field) for field in PREVIEW_EVIDENCE_FIELDS)
        if row.get("preview_action") == "reference_only" and status in {"with_preview", "inline_image", "action_url_only"}:
            has_evidence = False
        if not has_evidence:
            invalid_rows.append(
                {
                    "index": index,
                    "ad_id": row.get("ad_id"),
                    "preview_status": status,
                    "reason": "preview coverage status requires a concrete URL or image evidence field",
                }
            )

    return {
        "checked": True,
        "passed": not invalid_rows,
        "rows_checked": len(rows),
        "invalid_rows": invalid_rows,
        "message": None if not invalid_rows else "preview rows counted as coverage without URL/image evidence",
    }


def preview_coverage_depth_audit(run_dir: Path, manifest: dict[str, Any] | None) -> dict[str, Any]:
    depth = str((manifest or {}).get("depth", "")).lower()
    if depth not in {"standard", "full", "deep"}:
        return {"checked": True, "passed": True, "message": None}
    source_path = run_dir / "sources" / "creative_previews.json"
    if not source_path.exists():
        return {"checked": True, "passed": False, "message": "creative_previews.json missing for formal report depth"}
    ok, payload = load_json(source_path)
    if not ok or not isinstance(payload, dict):
        return {"checked": True, "passed": False, "message": "creative_previews.json invalid"}
    coverage = payload.get("coverage") if isinstance(payload.get("coverage"), dict) else {}
    total = int(coverage.get("total") or count_rows(payload) or 0)
    with_preview = int(coverage.get("with_preview") or 0)
    rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
    inline_image_count = sum(
        1
        for row in rows
        if isinstance(row, dict)
        and any(row.get(field) for field in ("preview_image_url", "image_url", "thumbnail_url", "cover_url", "video_cover_url"))
    )
    explicit_unavailable = payload.get("status") in {"permission_denied", "rate_limited", "structured_unavailable", "unsupported"}
    passed = total == 0 or inline_image_count > 0 or explicit_unavailable
    return {
        "checked": True,
        "passed": passed,
        "depth": depth,
        "total": total,
        "with_preview": with_preview,
        "inline_image_count": inline_image_count,
        "status": payload.get("status"),
        "message": None if passed else f"{depth} report has {total} creative preview rows but zero inline creative images",
    }


def activity_factor_join_audit(run_dir: Path, manifest: dict[str, Any] | None) -> dict[str, Any]:
    depth = str((manifest or {}).get("depth", "")).lower()
    if depth not in {"full", "deep"}:
        return {"checked": True, "passed": True, "message": None}
    path = run_dir / "sources" / "activity_factors.json"
    if not path.exists():
        return {"checked": True, "passed": False, "message": "activity_factors.json missing for full/deep report"}
    ok, payload = load_json(path)
    if not ok or not isinstance(payload, dict):
        return {"checked": True, "passed": False, "message": "activity_factors.json invalid"}
    factors = payload.get("factors") or []
    activities_path = run_dir / "sources" / "activities.json"
    activity_rows = json_row_count(activities_path) if activities_path.exists() else 0
    if activity_rows == 0:
        return {"checked": True, "passed": True, "activity_rows": 0, "message": None}
    matched = (payload.get("summary") or {}).get("matched_factor_count")
    if matched is None:
        matched = sum(1 for item in factors if isinstance(item, dict) and item.get("matched_kpi"))
    passed = bool(factors) and int(matched or 0) > 0
    return {
        "checked": True,
        "passed": passed,
        "activity_rows": activity_rows,
        "factor_count": len(factors) if isinstance(factors, list) else 0,
        "matched_factor_count": int(matched or 0),
        "message": None if passed else "activity_factors lacks object-level KPI joins",
    }


def validation_summary_audit(run_dir: Path, manifest: dict[str, Any] | None) -> dict[str, Any]:
    summary_path = run_dir / "validation_summary.json"
    ok, payload = load_json(summary_path) if summary_path.exists() else (False, "validation_summary.json missing")
    if not ok or not isinstance(payload, dict):
        return {
            "checked": False,
            "passed": False,
            "not_queried_sources": [],
            "missing_required_sources": [],
            "message": payload,
        }

    not_queried = payload.get("not_queried_sources", [])
    if not isinstance(not_queried, list):
        not_queried = ["not_queried_sources is not a list"]

    platform = str((manifest or {}).get("platform", "")).lower()
    depth = str((manifest or {}).get("depth", "")).lower()

    required_sources = []
    if platform == "tiktok":
        if depth in {"standard", "full", "deep"}:
            required_sources = [
                "sources/current_advertiser_insights.json",
                "sources/previous_advertiser_insights.json",
                "sources/audience_country.json",
                "sources/landing_app_paths.json",
                "sources/creative_previews.json",
            ]
        if depth in {"full", "deep"}:
            required_sources.extend([
                "sources/audience_age_gender.json",
                "sources/audience_placement.json",
                "sources/audience_device.json",
                "sources/activities.json",
                "sources/creative_retention.json",
                "sources/metric_probe.json",
                "sources/metric_probe_results.json",
            ])
        if depth == "deep":
            required_sources.extend([
                "sources/bottleneck_diagnosis.json",
            ])

    missing = []
    for name in required_sources:
        if (run_dir / name).exists():
            continue
        # metric_probe can be satisfied by either metric_probe.json or metric_probe_results.json
        if name in {"sources/metric_probe.json", "sources/metric_probe_results.json"}:
            other = "sources/metric_probe_results.json" if name == "sources/metric_probe.json" else "sources/metric_probe.json"
            if (run_dir / other).exists():
                continue
        missing.append(name)
    return {
        "checked": True,
        "passed": not not_queried and not missing,
        "not_queried_sources": not_queried,
        "missing_required_sources": missing,
        "message": None if not not_queried and not missing else "required report sources are missing or still not_queried",
    }


VALID_STATUSES = {
    "ok", "supported_empty", "unsupported", "not_queried",
    "permission_denied", "rate_limited", "degraded", "partial",
    "structured_unavailable", "not_applicable",
}

NO_DATA_STATUSES = {
    "supported_empty", "not_queried", "not_applicable",
    "unsupported", "permission_denied", "rate_limited",
    "structured_unavailable", "partial", "degraded",
}

CONTENT_KEYS = {
    "rows", "data", "items", "payload", "sections", "accounts",
    "list", "segments", "results", "metrics", "unresolved", "server",
    "tools_available", "taxonomy", "preset", "groups",
    "coverage", "landing_rows", "app_rows", "smart_plus_rows",
    "calls",
    # Keys used by specific source files written in data-dir mode
    "raw_csv", "summary", "bottleneck_labels", "findings",
    "primary_label", "probes", "note",
}


def any_content(data: dict[str, Any]) -> bool:
    """True if the dict has at least one recognized content-bearing key (empty values count)."""
    for key in CONTENT_KEYS:
        value = data.get(key)
        if value is not None:
            return True
    return False


def source_shape_validation_audit(run_dir: Path) -> dict[str, Any]:
    sources_dir = run_dir / "sources"
    if not sources_dir.exists():
        return {"checked": False, "passed": True, "message": "sources/ directory missing; skipped shape validation"}

    failures: list[dict[str, Any]] = []
    json_paths = sorted(sources_dir.glob("*.json"))
    if not json_paths:
        return {"checked": True, "passed": True, "files_scanned": 0, "failures": []}

    for path in json_paths:
        ok, payload = load_json(path)
        fname = path.name
        if not ok:
            failures.append({"file": fname, "error": f"invalid JSON: {payload}"})
            continue

        if isinstance(payload, list):
            if not payload:
                failures.append({"file": fname, "error": "top-level list is empty; expected dict with status"})
            continue

        if not isinstance(payload, dict):
            failures.append({"file": fname, "error": f"top-level is {type(payload).__name__}; expected dict or list"})
            continue

        status = payload.get("status")
        if status is None:
            # Files without a 'status' field are derived outputs (user_type.json,
            # metric_preset.json), not agent-written sources. Skip them.
            continue

        if status not in VALID_STATUSES:
            failures.append({"file": fname, "error": f"unrecognized status '{status}'"})
            continue

        if status == "ok" and not any_content(payload):
            failures.append({"file": fname, "error": f"status is 'ok' but no recognized content keys {CONTENT_KEYS} found with non-empty value"})

        if status not in NO_DATA_STATUSES and status != "ok" and not any_content(payload):
            failures.append({"file": fname, "error": f"status is '{status}' (not a no-data status) but no content found"})

        page_info = payload.get("page_info")
        # Classification sources are top-N samples by design — skip pagination checks
        if status == "ok" and isinstance(page_info, dict) and not fname.startswith("classification_"):
            total_number = page_info.get("total_number")
            total_page = page_info.get("total_page")
            row_count = payload.get("row_count")
            actual_rows = count_rows(payload)
            try:
                total_number_i = int(total_number)
            except Exception:
                total_number_i = None
            try:
                total_page_i = int(total_page)
            except Exception:
                total_page_i = None
            try:
                row_count_i = int(row_count)
            except Exception:
                row_count_i = actual_rows
            if total_number_i is not None and total_number_i > row_count_i:
                failures.append({
                    "file": fname,
                    "error": f"paginated source is incomplete: row_count={row_count_i}, total_number={total_number_i}",
                })
            elif total_page_i is not None and total_page_i > 1 and actual_rows <= row_count_i:
                failures.append({
                    "file": fname,
                    "error": f"paginated source has total_page={total_page_i}; all pages must be merged before report generation",
                })

    return {
        "checked": True,
        "passed": not failures,
        "files_scanned": len(json_paths),
        "failures": [f"{f['file']}: {f['error']}" for f in failures],
        "message": None if not failures else f"{len(failures)} source file(s) have invalid shape",
    }


def pull_plan_completed_audit(run_dir: Path) -> dict[str, Any]:
    """Check that pull_plan.json exists and all required steps are completed."""
    plan_path = run_dir / "pull_plan.json"
    if not plan_path.exists():
        return {
            "checked": True,
            "passed": False,
            "message": "pull_plan.json is missing",
        }
    ok, plan = load_json(plan_path)
    if not ok or not isinstance(plan, dict):
        return {
            "checked": True,
            "passed": False,
            "message": "pull_plan.json is invalid",
        }
    steps = plan.get("steps") or []
    required_steps = [s for s in steps if s.get("required")]
    missing_steps: list[str] = []
    sources_dir = run_dir / "sources"
    for step in required_steps:
        step_id = step.get("id", "")
        output = step.get("output", "")
        source_name = Path(output).stem if output else step_id
        path = sources_dir / f"{source_name}.json"
        if not path.exists():
            alt = run_dir / f"{source_name}.json"
            if not alt.exists():
                missing_steps.append(step_id)
    return {
        "checked": True,
        "passed": not missing_steps,
        "required_step_count": len(required_steps),
        "missing_steps": missing_steps,
        "message": None if not missing_steps else f"{len(missing_steps)} required pull plan steps have no output file",
    }


def formal_sources_complete_audit(run_dir: Path, manifest: dict[str, Any] | None) -> dict[str, Any]:
    """Verify all formal report sources exist with complete pagination."""
    depth = str((manifest or {}).get("depth", "standard")).lower()
    formal_sources = [
        "current_advertiser_insights",
        "current_campaigns",
        "current_adgroups",
        "current_ads",
    ]
    if depth in {"standard", "full", "deep"}:
        formal_sources.extend([
            "previous_advertiser_insights",
            "previous_campaigns",
            "previous_adgroups",
            "previous_ads",
        ])
    if depth in {"full", "deep"}:
        formal_sources.extend([
            "audience_country",
            "audience_age_gender",
            "audience_placement",
            "audience_device",
        ])

    sources_dir = run_dir / "sources"
    failures: list[dict[str, Any]] = []
    for name in formal_sources:
        path = sources_dir / f"{name}.json"
        if not path.exists():
            alt = run_dir / f"{name}.json"
            if alt.exists():
                path = alt
            else:
                failures.append({"source": name, "reason": "file missing"})
                continue
        ok, payload = load_json(path)
        if not ok or not isinstance(payload, dict):
            failures.append({"source": name, "reason": "invalid JSON"})
            continue
        status = payload.get("status")
        if status not in {"ok", "partial"}:
            continue
        page_info = payload.get("page_info") or {}
        try:
            tn = int(page_info.get("total_number", 0))
        except (TypeError, ValueError):
            tn = 0
        rc = payload.get("row_count", 0)
        if tn > rc:
            failures.append({"source": name, "reason": f"pagination incomplete: row_count={rc}, total_number={tn}"})
        tp = page_info.get("total_page", 1)
        try:
            tp_i = int(tp)
        except (TypeError, ValueError):
            tp_i = 1
        merged = (payload.get("merged_page_info") or {}).get("merged")
        if tp_i > 1 and not merged:
            failures.append({"source": name, "reason": f"multi-page not merged: total_page={tp_i}"})

    return {
        "checked": True,
        "passed": not failures,
        "sources_checked": len(formal_sources),
        "failures": failures,
        "message": None if not failures else f"{len(failures)} formal sources incomplete",
    }


def advertiser_totals_present_audit(run_dir: Path) -> dict[str, Any]:
    """Verify advertiser-level KPI anchor sources have exactly 1 row."""
    anchors = ["current_advertiser_insights", "previous_advertiser_insights"]
    failures: list[dict[str, Any]] = []
    sources_dir = run_dir / "sources"
    for name in anchors:
        path = sources_dir / f"{name}.json"
        if not path.exists():
            alt = run_dir / f"{name}.json"
            if alt.exists():
                path = alt
            else:
                failures.append({"source": name, "reason": "file missing"})
                continue
        ok, payload = load_json(path)
        if not ok or not isinstance(payload, dict):
            failures.append({"source": name, "reason": "invalid JSON"})
            continue
        if payload.get("status") != "ok":
            continue
        rc = payload.get("row_count")
        if rc is None:
            rc = count_rows(payload)
        if rc != 1:
            failures.append({"source": name, "reason": f"expected 1 row, got {rc}"})
            continue
        keys = metric_keys(payload)
        if keys and not (keys & ADVERTISER_VALUE_KPI_KEYS):
            explicit_fallback = any(
                payload.get(key)
                for key in (
                    "attempts",
                    "fallback_reason",
                    "metric_fallback_reason",
                    "degradation_reason",
                    "unsupported_metrics",
                )
            )
            if keys <= LEAN_KPI_KEYS and not explicit_fallback:
                failures.append({
                    "source": name,
                    "reason": "advertiser KPI anchor is lean-only without explicit fallback attempts/reason",
                })
            elif not explicit_fallback:
                failures.append({
                    "source": name,
                    "reason": "advertiser KPI anchor is missing value metrics without explicit fallback attempts/reason",
                })
    return {
        "checked": True,
        "passed": not failures,
        "failures": failures,
        "message": None if not failures else "advertiser-level KPI anchor sources have wrong row count",
    }


def agent_sample_not_used_as_formal_audit(run_dir: Path) -> dict[str, Any]:
    """Check that classification sources are not used as formal report sources.

    Classification sources (top-N samples) and formal report sources (full paginated pools)
    must be distinct.  If current_campaigns.json has the same row_count as
    classification_campaigns.json and total_number > row_count, it's evidence that the
    agent used its sample as formal data.
    """
    sources_dir = run_dir / "sources"
    pairs = [
        ("classification_campaigns", "current_campaigns"),
        ("classification_adgroups", "current_adgroups"),
        ("classification_ads", "current_ads"),
    ]
    failures: list[dict[str, Any]] = []
    for class_name, formal_name in pairs:
        class_path = sources_dir / f"{class_name}.json"
        formal_path = sources_dir / f"{formal_name}.json"
        if not class_path.exists() or not formal_path.exists():
            continue
        class_ok, class_data = load_json(class_path)
        formal_ok, formal_data = load_json(formal_path)
        if not class_ok or not formal_ok:
            continue
        if not isinstance(class_data, dict) or not isinstance(formal_data, dict):
            continue
        class_rows = class_data.get("row_count", 0)
        formal_rows = formal_data.get("row_count", 0)
        formal_pi = formal_data.get("page_info") or {}
        try:
            formal_tn = int(formal_pi.get("total_number", 0))
        except (TypeError, ValueError):
            formal_tn = 0
        if class_rows > 0 and class_rows == formal_rows and formal_tn > formal_rows:
            failures.append({
                "classification": class_name,
                "formal": formal_name,
                "reason": f"formal source has same row_count ({formal_rows}) as classification but total_number={formal_tn} — agent may have used sample as formal data",
            })
    return {
        "checked": True,
        "passed": not failures,
        "failures": failures,
        "message": None if not failures else "classification samples may have been used as formal report sources",
    }


def audience_placement_retry_audit(run_dir: Path) -> dict[str, Any]:
    """Check audience_placement is ok or has retry attempts if unsupported."""
    sources_dir = run_dir / "sources"
    path = sources_dir / "audience_placement.json"
    if not path.exists():
        alt = run_dir / "audience_placement.json"
        if alt.exists():
            path = alt
        else:
            return {"checked": False, "passed": True, "message": "audience_placement.json not present; skipped"}
    ok, payload = load_json(path)
    if not ok or not isinstance(payload, dict):
        return {"checked": True, "passed": False, "message": "audience_placement.json is invalid"}
    status = payload.get("status")
    if status == "unsupported":
        attempts = payload.get("attempts")
        if not attempts or (isinstance(attempts, list) and len(attempts) == 0):
            return {
                "checked": True,
                "passed": False,
                "message": "audience_placement is unsupported but has no retry attempts",
            }
    return {"checked": True, "passed": True, "message": None}


def unsupported_sources_have_attempts_audit(run_dir: Path) -> dict[str, Any]:
    """Check that every source with status=unsupported has non-empty attempts."""
    sources_dir = run_dir / "sources"
    if not sources_dir.exists():
        return {"checked": False, "passed": True, "message": "sources/ missing; skipped"}
    failures: list[str] = []
    for path in sorted(sources_dir.glob("*.json")):
        ok, payload = load_json(path)
        if not ok or not isinstance(payload, dict):
            continue
        if payload.get("status") != "unsupported":
            continue
        attempts = payload.get("attempts")
        if not attempts or (isinstance(attempts, list) and len(attempts) == 0):
            failures.append(path.name)
    return {
        "checked": True,
        "passed": not failures,
        "unsupported_without_attempts": failures,
        "message": None if not failures else f"{len(failures)} unsupported source(s) have no retry attempts",
    }


def bridge_execution_audit(run_dir: Path) -> dict[str, Any]:
    """Audit agent-native executor-specific concerns.

    Checks:
      - Executor auth failures are not masked as ok status.
      - Executor sources have backend field set correctly.
      - Fallback entries in manifest have corresponding source attempts.
      - No MCP session metadata in executor-produced sources.
    """
    sources_dir = run_dir / "sources"
    if not sources_dir.exists():
        return {"checked": False, "passed": True, "message": "sources/ missing; skipped bridge audit"}

    auth_swallowed: list[str] = []
    missing_backend: list[str] = []
    session_meta_hits: list[str] = []

    for path in sorted(sources_dir.glob("*.json")):
        ok, payload = load_json(path)
        if not ok or not isinstance(payload, dict):
            continue

        backend = payload.get("backend", "")
        auth_status = payload.get("auth_status", "")
        status = payload.get("status", "")

        # Executor auth failure must not be masked as ok
        if backend in EXECUTOR_BACKEND_ALIASES and auth_status in {"auth_required", "permission_denied"}:
            if status == "ok":
                auth_swallowed.append(path.name)

        # Executor sources should have backend field
        if status == "ok" and not backend:
            text = path.read_text(encoding="utf-8", errors="replace")
            if any(hint in text.lower() for hint in ("subagent", "bridge", "batch", "executor")):
                missing_backend.append(path.name)

        # Check for MCP session metadata in any source
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in SECRET_PATTERNS[-4:]:  # MCP session patterns
            if pattern.search(text):
                session_meta_hits.append({"file": path.name, "pattern": pattern.pattern})
                break

    # Check manifest for fallback consistency
    manifest_path = run_dir / "manifest.json"
    fallback_mismatch: list[str] = []
    if manifest_path.exists():
        ok, manifest = load_json(manifest_path)
        if ok and isinstance(manifest, dict):
            fallbacks = manifest.get("backend_fallbacks") or []
            for fb in fallbacks:
                fb_task_id = fb.get("task_id", "")
                source_path = sources_dir / f"{fb_task_id}.json"
                if source_path.exists():
                    ok_s, source = load_json(source_path)
                    if ok_s and isinstance(source, dict):
                        attempts = source.get("attempts", [])
                        if not attempts or (isinstance(attempts, list) and len(attempts) == 0):
                            fallback_mismatch.append(fb_task_id)

    passed = (
        not auth_swallowed
        and not session_meta_hits
        and not fallback_mismatch
    )

    return {
        "checked": True,
        "passed": passed,
        "auth_failures_swallowed": auth_swallowed,
        "sources_missing_backend": missing_backend,
        "session_metadata_hits": session_meta_hits,
        "fallback_attempts_missing": fallback_mismatch,
        "message": None if passed else (
            f"executor audit failed: "
            + (f"{len(auth_swallowed)} auth failures swallowed; " if auth_swallowed else "")
            + (f"{len(session_meta_hits)} session metadata hits; " if session_meta_hits else "")
            + (f"{len(fallback_mismatch)} fallbacks without attempts" if fallback_mismatch else "")
        ).strip().rstrip(";"),
    }


def audit(run_dir: Path, html_path: Path) -> dict[str, Any]:
    html_exists = html_path.exists()
    html = scan_text(html_path) if html_exists else ""
    manifest_ok, manifest_payload = read_manifest(run_dir)
    sources_dir = run_dir / "sources"
    json_files = sorted(run_dir.glob("*.json")) + sorted(sources_dir.glob("*.json"))
    seen: set[Path] = set()
    json_results = []
    for file_path in json_files:
        if file_path in seen:
            continue
        seen.add(file_path)
        ok, payload = load_json(file_path)
        json_results.append(
            {
                "file": str(file_path),
                "valid_json": ok,
                "row_count": count_rows(payload) if ok else 0,
                "error": None if ok else payload,
            }
        )

    all_artifact_text = html
    for file_path in seen:
        if file_path.name == "report_audit.json":
            continue
        all_artifact_text += "\n" + scan_text(file_path)

    manifest_audit = manifest_contract_audit(
        run_dir,
        manifest_payload if manifest_ok and isinstance(manifest_payload, dict) else None,
    )
    source_rows = source_row_audit(
        run_dir,
        manifest_payload if manifest_ok and isinstance(manifest_payload, dict) else None,
    )
    user_type = user_type_audit(run_dir, html_path)
    preview_audit = preview_evidence_audit(run_dir)
    preview_coverage_audit = preview_coverage_depth_audit(
        run_dir,
        manifest_payload if manifest_ok and isinstance(manifest_payload, dict) else None,
    )
    preview_html_audit = preview_html_embedding_audit(run_dir, html)
    validation_audit = validation_summary_audit(
        run_dir,
        manifest_payload if manifest_ok and isinstance(manifest_payload, dict) else None,
    )
    source_shape_audit = source_shape_validation_audit(run_dir)
    metric_preset = metric_preset_audit(run_dir, html_path)
    phase_order = mcp_phase_order_audit(run_dir)
    pull_plan_audit = pull_plan_completed_audit(run_dir)
    formal_sources_audit = formal_sources_complete_audit(
        run_dir,
        manifest_payload if manifest_ok and isinstance(manifest_payload, dict) else None,
    )
    advertiser_totals_audit = advertiser_totals_present_audit(run_dir)
    agent_sample_audit = agent_sample_not_used_as_formal_audit(run_dir)
    audience_placement_retry = audience_placement_retry_audit(run_dir)
    unsupported_attempts_audit = unsupported_sources_have_attempts_audit(run_dir)
    bridge_audit = bridge_execution_audit(run_dir)
    activity_join_audit = activity_factor_join_audit(
        run_dir,
        manifest_payload if manifest_ok and isinstance(manifest_payload, dict) else None,
    )

    checks = {
        "html_exists": html_exists,
        "manifest_valid": manifest_ok,
        "manifest_contract_valid": manifest_audit["passed"],
        "json_files_valid": all(item["valid_json"] for item in json_results),
        "source_directory_exists": sources_dir.exists(),
        "source_files_declared_or_covered": manifest_audit["passed"],
        "source_rows_present": source_rows["passed"],
        "user_type_present_and_first": user_type["passed"],
        "metric_preset_present_and_first": metric_preset["passed"],
        "metric_preset_matches_user_type": metric_preset["passed"],
        "mcp_phase_order_valid": phase_order["passed"],
        "has_scope": "Scope:" in html or "范围" in html,
        "has_user_type_or_classification": html_has_any(
            html,
            [r"user\s*type", r"classification", r"用户类型", r"分类"],
        ),
        "has_coverage_context": html_has_any(
            html,
            [r"coverage", r"覆盖", r"full\s*\|", r"partial", r"degraded", r"数据质量"],
        ),
        "has_data_quality": any(marker in html for marker in REQUIRED_HTML_MARKERS) or "数据质量" in html,
        "html_contains_metric_context": html_has_any(
            html,
            [r"Metric Context", r"metric preset", r"Metric groups", r"指标"],
        ),
        "has_kpi": "KPI" in html or "Spend" in html or "花费" in html,
        "has_summary_or_findings": html_has_any(
            html,
            [r"executive", r"summary", r"key findings", r"findings", r"摘要", r"结论"],
        ),
        "has_drivers_or_findings": html_has_any(
            html,
            [r"drivers?", r"findings?", r"原因", r"驱动", r"诊断"],
        ),
        "has_next_actions": "Next" in html or "行动" in html or "建议" in html,
        "has_url_wrapping_css": "overflow-wrap:anywhere" in html and "word-break:break-word" in html,
        "has_preview_contract": ("<th>Preview</th>" in html and "preview-action" in html) or "preview_status" in html or "Unavailable" in html,
        "preview_evidence_consistent": preview_audit["passed"],
        "preview_coverage_present": preview_coverage_audit["passed"],
        "preview_html_embedded": preview_html_audit["passed"],
        "validation_summary_consistent": validation_audit["passed"],
        "source_shapes_valid": source_shape_audit["passed"],
        "no_secret_patterns": not secret_hits(all_artifact_text),
        "pull_plan_completed": pull_plan_audit["passed"],
        "formal_sources_complete": formal_sources_audit["passed"],
        "advertiser_totals_present": advertiser_totals_audit["passed"],
        "agent_sample_not_used_as_formal": agent_sample_audit["passed"],
        "audience_placement_retry_or_ok": audience_placement_retry["passed"],
        "unsupported_sources_have_attempts": unsupported_attempts_audit["passed"],
        "bridge_execution_valid": bridge_audit["passed"],
        "subagent_execution_valid": bridge_audit["passed"],
        "activity_factors_join_kpi": activity_join_audit["passed"],
    }
    required = [
        "html_exists",
        "manifest_valid",
        "manifest_contract_valid",
        "json_files_valid",
        "source_directory_exists",
        "source_rows_present",
        "user_type_present_and_first",
        "metric_preset_present_and_first",
        "metric_preset_matches_user_type",
        "mcp_phase_order_valid",
        "has_scope",
        "has_user_type_or_classification",
        "has_coverage_context",
        "has_data_quality",
        "html_contains_metric_context",
        "has_kpi",
        "has_summary_or_findings",
        "has_drivers_or_findings",
        "has_next_actions",
        "has_url_wrapping_css",
        "preview_evidence_consistent",
        "preview_coverage_present",
        "preview_html_embedded",
        "validation_summary_consistent",
        "source_shapes_valid",
        "no_secret_patterns",
        "pull_plan_completed",
        "formal_sources_complete",
        "advertiser_totals_present",
        "agent_sample_not_used_as_formal",
        "audience_placement_retry_or_ok",
        "unsupported_sources_have_attempts",
        "bridge_execution_valid",
        "subagent_execution_valid",
        "activity_factors_join_kpi",
    ]
    return {
        "html": display_path(html_path, base=run_dir),
        "run_dir": display_path(run_dir),
        "checks": checks,
        "required_passed": all(checks[name] for name in required),
        "json_files": json_results,
        "manifest_error": None if manifest_ok else manifest_payload,
        "manifest_contract_audit": manifest_audit,
        "source_row_audit": source_rows,
        "user_type_audit": user_type,
        "preview_evidence_audit": preview_audit,
        "preview_coverage_depth_audit": preview_coverage_audit,
        "preview_html_embedding_audit": preview_html_audit,
        "validation_summary_audit": validation_audit,
        "source_shape_validation_audit": source_shape_audit,
        "metric_preset_audit": metric_preset,
        "mcp_phase_order_audit": phase_order,
        "pull_plan_completed_audit": pull_plan_audit,
        "formal_sources_complete_audit": formal_sources_audit,
        "advertiser_totals_present_audit": advertiser_totals_audit,
        "agent_sample_not_used_as_formal_audit": agent_sample_audit,
        "audience_placement_retry_audit": audience_placement_retry,
        "unsupported_sources_have_attempts_audit": unsupported_attempts_audit,
        "bridge_execution_audit": bridge_audit,
        "activity_factor_join_audit": activity_join_audit,
        "secret_patterns_found": secret_hits(all_artifact_text),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a Creatiads HTML report run directory.")
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--html", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    html_path = args.html or args.run_dir / "report.html"
    result = audit(args.run_dir, html_path)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text)
    return 0 if result["required_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
