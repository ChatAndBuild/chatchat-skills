#!/usr/bin/env python3
"""Stateful local workflow runner for creatiads agent-native MCP plans.

The runner never calls MCP. It advances every local step it can, then stops at
the MCP boundary with a concrete pending task list for the agent/subagents.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from build_mcp_pull_plan import PLANNER_VERSION, build_plan_fingerprint
    from account_profile_cache import cached_user_type_label, load_account_profile_cache
    from backend_router import route_run
    from build_mcp_task_plan import build_capability_plan, write_plan
    from classify_user_type import build_user_type_report
    from metric_confirmation import build_metric_confirmation, maybe_write_confirmed_cache
    from metric_probe import recommend_metric_preset
    from normalize_mcp_source import normalize_file
    from plan_subagent_execution import write_subagent_execution_plan
    from tiktok_app_landing_evidence import collect_app_landing_evidence
    from validate_pull_state import validate
    from utils import STATUS_OK, write_json
except ImportError:  # pragma: no cover
    from .build_mcp_pull_plan import PLANNER_VERSION, build_plan_fingerprint
    from .account_profile_cache import cached_user_type_label, load_account_profile_cache
    from .backend_router import route_run
    from .build_mcp_task_plan import build_capability_plan, write_plan
    from .classify_user_type import build_user_type_report
    from .metric_confirmation import build_metric_confirmation, maybe_write_confirmed_cache
    from .metric_probe import recommend_metric_preset
    from .normalize_mcp_source import normalize_file
    from .plan_subagent_execution import write_subagent_execution_plan
    from .tiktok_app_landing_evidence import collect_app_landing_evidence
    from .validate_pull_state import validate
    from .utils import STATUS_OK, write_json


SCRIPT_DIR = Path(__file__).resolve().parent
PHASE_ORDER = [
    "bootstrap",
    "classification",
    "local_classification",
    "preset",
    "report_data",
    "enrichment",
    "analysis",
    "audit",
]
METRIC_CONFIRMATION_REQUIRED_CAPABILITIES = {
    "full_report",
    "performance_diagnosis",
    "creative_diagnosis",
    "audience_diagnosis",
    "activity_changelog",
    "bottleneck_diagnosis",
    "budget_recommendation",
    "landing_app_paths",
}


class StalePlanError(RuntimeError):
    def __init__(self, *, expected: dict[str, Any], found: dict[str, Any] | None) -> None:
        self.expected = expected
        self.found = found or {}
        super().__init__(
            "Existing pull_plan.json does not match requested workflow inputs. "
            "Use --refresh-plan to regenerate it."
        )


def _load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _load_tasks(run_dir: Path) -> list[dict[str, Any]]:
    path = run_dir / "mcp_tasks.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _source_path(run_dir: Path, source_id: str) -> Path:
    return run_dir / "sources" / f"{source_id}.json"


def _source_exists(run_dir: Path, source_id: str) -> bool:
    return _source_path(run_dir, source_id).exists() or (run_dir / f"{source_id}.json").exists()


def _source_status(run_dir: Path, source_id: str) -> str:
    data = _load_json(_source_path(run_dir, source_id), None)
    if data is None:
        data = _load_json(run_dir / f"{source_id}.json", None)
    if not isinstance(data, dict):
        return "missing"
    return str(data.get("status") or STATUS_OK)


def _task_source_id(task: dict[str, Any]) -> str:
    output = str(task.get("output_source") or task.get("output") or "")
    return Path(output).stem if output else str(task.get("id") or "")


def _deps_satisfied(run_dir: Path, task: dict[str, Any]) -> bool:
    return all(_source_exists(run_dir, dep) for dep in task.get("depends_on") or [])


def ensure_plan(
    *,
    run_dir: Path,
    capability: str,
    advertiser_id: str,
    start_date: str,
    end_date: str,
    previous_start_date: str | None,
    previous_end_date: str | None,
    depth: str,
    bc_id: str = "",
    refresh_plan: bool = False,
) -> dict[str, Any]:
    depth = "fast" if depth == "quick" else depth
    if not refresh_plan and (run_dir / "pull_plan.json").exists() and (run_dir / "mcp_tasks.jsonl").exists():
        summary = _load_json(run_dir / "summary.json", {}) or {}
        plan = _load_json(run_dir / "pull_plan.json", {}) or {}
        found_fingerprint = (
            summary.get("plan_fingerprint")
            if isinstance(summary, dict)
            else None
        ) or (
            plan.get("plan_fingerprint")
            if isinstance(plan, dict)
            else None
        )
        found_user_type = ""
        found_account_cache_mode = ""
        if isinstance(found_fingerprint, dict):
            found_user_type = str(found_fingerprint.get("user_type") or "")
            found_account_cache_mode = str(found_fingerprint.get("account_cache_mode") or "")
        else:
            account_cache = load_account_profile_cache(advertiser_id)
            found_user_type = cached_user_type_label(account_cache)
            found_account_cache_mode = "user_type_account_cache" if account_cache else ""
        expected_fingerprint = build_plan_fingerprint(
            capability=capability,
            advertiser_id=advertiser_id,
            start_date=start_date,
            end_date=end_date,
            previous_start_date=previous_start_date,
            previous_end_date=previous_end_date,
            depth=depth,
            bc_id=bc_id,
            user_type=found_user_type,
            account_cache_mode=found_account_cache_mode,
        )
        if not isinstance(found_fingerprint, dict) or found_fingerprint.get("hash") != expected_fingerprint.get("hash"):
            raise StalePlanError(expected=expected_fingerprint, found=found_fingerprint if isinstance(found_fingerprint, dict) else {})
        return summary

    account_cache = load_account_profile_cache(advertiser_id)
    cached_user_type = cached_user_type_label(account_cache)
    plan = build_capability_plan(
        capability=capability,
        advertiser_id=advertiser_id,
        start_date=start_date,
        end_date=end_date,
        previous_start_date=previous_start_date,
        previous_end_date=previous_end_date,
        depth=depth,
        bc_id=bc_id,
        use_cached_user_type=bool(account_cache),
        cached_user_type=cached_user_type,
    )
    return write_plan(run_dir, plan)


def ensure_routing(run_dir: Path) -> dict[str, Any]:
    routing = route_run(run_dir)
    write_json(run_dir / "backend_routing.json", routing)
    backend_counts = routing.get("backend_counts") if isinstance(routing.get("backend_counts"), dict) else {}
    if routing.get("backend") == "mcp_subagent_executor" or backend_counts.get("mcp_subagent_executor", 0) > 0:
        write_subagent_execution_plan(run_dir)
    return routing


def normalize_available_raw(run_dir: Path) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for task in _load_tasks(run_dir):
        if task.get("l0_or_l1") == "local":
            continue
        output_source = run_dir / str(task.get("output_source") or "")
        output_raw = run_dir / str(task.get("output_raw") or "")
        if output_source.exists() or not output_raw.exists():
            continue
        result = normalize_file(
            output_raw,
            output_source,
            tool=str(task.get("tool") or ""),
            phase=str(task.get("phase") or ""),
            depends_on=task.get("depends_on") or [],
            params=task.get("params") if isinstance(task.get("params"), dict) else None,
            attempts=task.get("attempts") if isinstance(task.get("attempts"), list) else None,
            backend=str(task.get("preferred_backend") or ""),
            auth_status="",
        )
        normalized.append({
            "task_id": task.get("id"),
            "output_source": str(output_source),
            "status": result.get("status"),
            "row_count": result.get("row_count"),
        })
    return normalized


def derive_bootstrap_aliases(run_dir: Path) -> list[str]:
    """Derive account bootstrap sources from the single MCP readiness probe."""
    mcp_ready = _load_json(_source_path(run_dir, "mcp_ready"), None)
    if not isinstance(mcp_ready, dict):
        return []
    status = str(mcp_ready.get("status") or STATUS_OK)
    if status not in {STATUS_OK, "supported_empty"}:
        return []

    written: list[str] = []
    now = datetime.now(timezone.utc).isoformat()
    for target in ("current_account", "advertiser_info"):
        target_path = _source_path(run_dir, target)
        if target_path.exists():
            continue
        alias = dict(mcp_ready)
        metadata = dict(alias.get("metadata") or {})
        metadata.update({
            "derived_from": "mcp_ready",
            "derivation": "bootstrap_alias",
            "generated_at": now,
        })
        alias.update({
            "phase": "bootstrap",
            "status": status,
            "metadata": metadata,
        })
        write_json(target_path, alias)
        written.append(target)
    return written


def _read_source(run_dir: Path, name: str) -> dict[str, Any]:
    data = _load_json(_source_path(run_dir, name), None)
    if isinstance(data, dict):
        return data
    data = _load_json(run_dir / f"{name}.json", None)
    return data if isinstance(data, dict) else {"status": "not_queried", "rows": []}


def _rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows = source.get("rows")
    return rows if isinstance(rows, list) else []


def _write_cached_account_profile_sources(
    *,
    run_dir: Path,
    advertiser_id: str,
    cache: dict[str, Any],
    generated_at: str,
) -> list[str]:
    written: list[str] = []
    user_type = cache.get("user_type") if isinstance(cache.get("user_type"), dict) else {}
    metric_preset = cache.get("metric_preset") if isinstance(cache.get("metric_preset"), dict) else {}
    if not user_type:
        return written

    evidence = {
        "status": STATUS_OK,
        "phase": "local_classification",
        "generated_at": generated_at,
        "source": "account_cache",
        "advertiser_id": advertiser_id,
        "cache_schema_version": cache.get("schema_version"),
        "cache_generated_at": cache.get("generated_at"),
        "cache_expires_at": cache.get("expires_at"),
        "evidence_hash": cache.get("evidence_hash"),
        "evidence_summary": cache.get("evidence_summary") or {},
        "rows": [],
    }
    if not _source_exists(run_dir, "user_type_evidence"):
        write_json(_source_path(run_dir, "user_type_evidence"), evidence)
        written.append("user_type_evidence")

    user_type_source = {
        **user_type,
        "status": user_type.get("status") or STATUS_OK,
        "phase": "local_classification",
        "generated_at": generated_at,
        "source": "account_cache",
        "advertiser_id": advertiser_id,
        "cache_generated_at": cache.get("generated_at"),
        "cache_expires_at": cache.get("expires_at"),
        "evidence_hash": cache.get("evidence_hash"),
    }
    if not _source_exists(run_dir, "user_type"):
        write_json(_source_path(run_dir, "user_type"), user_type_source)
        write_json(run_dir / "user_type.json", user_type_source)
        written.append("user_type")

    if metric_preset and not _source_exists(run_dir, "metric_preset"):
        preset_source = {
            **metric_preset,
            "status": metric_preset.get("status") or STATUS_OK,
            "phase": "preset",
            "generated_at": generated_at,
            "source": "account_cache",
            "advertiser_id": advertiser_id,
            "cache_generated_at": cache.get("generated_at"),
            "cache_expires_at": cache.get("expires_at"),
        }
        write_json(_source_path(run_dir, "metric_preset"), preset_source)
        write_json(run_dir / "metric_preset.json", preset_source)
        written.append("metric_preset")

    return written


def run_local_gate_tasks(
    *,
    run_dir: Path,
    advertiser_id: str,
    start_date: str,
    end_date: str,
) -> list[str]:
    """Build local classification/preset artifacts that unblock report pulls."""
    written: list[str] = []
    now = datetime.now(timezone.utc).isoformat()

    account_cache = load_account_profile_cache(advertiser_id)
    if account_cache and _source_exists(run_dir, "mcp_ready"):
        written.extend(_write_cached_account_profile_sources(
            run_dir=run_dir,
            advertiser_id=advertiser_id,
            cache=account_cache,
            generated_at=now,
        ))
        if _source_exists(run_dir, "user_type") and not _source_exists(run_dir, "metric_preset"):
            user_type = _read_source(run_dir, "user_type")
            top_type = user_type.get("top_type") or ((user_type.get("top_types") or [{}])[0].get("type")) or "代理商/多类型"
            derived = user_type.get("derived_user_type") or top_type
            preset = recommend_metric_preset(
                top_type,
                profile="vertical",
                derived_user_type=derived,
                w2a=bool(user_type.get("w2a_evidence")),
                shop=bool(user_type.get("catalog_rows") or user_type.get("shop_rows")),
                source_user_type=user_type,
            )
            preset_source = {
                **preset,
                "phase": "preset",
                "generated_at": now,
                "source": "account_cache_derived",
                "cache_generated_at": account_cache.get("generated_at"),
            }
            write_json(_source_path(run_dir, "metric_preset"), preset_source)
            write_json(run_dir / "metric_preset.json", preset_source)
            written.append("metric_preset")
        if _source_exists(run_dir, "user_type") and _source_exists(run_dir, "metric_preset"):
            return written

    classification_sources_ready = all(
        _source_exists(run_dir, name)
        for name in (
            "current_account",
            "classification_campaigns",
            "classification_adgroups",
            "classification_ads",
            "classification_ad_v2_insights",
        )
    )
    if not classification_sources_ready:
        return written

    if not _source_exists(run_dir, "user_type_evidence"):
        evidence = collect_app_landing_evidence(
            current_ad_rows=_rows(_read_source(run_dir, "classification_ads")),
            current_ad_v2_rows=_rows(_read_source(run_dir, "classification_ad_v2_insights")),
            current_campaign_rows=_rows(_read_source(run_dir, "classification_campaigns")),
            advertiser_info=_read_source(run_dir, "advertiser_info"),
            app_list=_read_source(run_dir, "app_list"),
            catalog_list=_read_source(run_dir, "catalog_list"),
            shop_list=_read_source(run_dir, "shop_list"),
            smart_plus_details=_read_source(run_dir, "smart_plus_ads"),
        ).to_dict()
        evidence.update({"status": STATUS_OK, "phase": "local_classification", "generated_at": now})
        write_json(_source_path(run_dir, "user_type_evidence"), evidence)
        written.append("user_type_evidence")

    if not _source_exists(run_dir, "user_type"):
        evidence = _read_source(run_dir, "user_type_evidence")
        user_type = build_user_type_report(
            advertiser_id=advertiser_id,
            start_date=start_date,
            end_date=end_date,
            account_rows=_rows(_read_source(run_dir, "current_account")),
            campaign_rows=_rows(_read_source(run_dir, "classification_campaigns")),
            adgroup_rows=_rows(_read_source(run_dir, "classification_adgroups")),
            ad_rows=_rows(_read_source(run_dir, "classification_ads")),
            smart_plus_rows=evidence.get("smart_plus_rows") or _rows(_read_source(run_dir, "smart_plus_ads")),
            landing_rows=evidence.get("landing_rows") or [],
            app_rows=evidence.get("app_rows") or [],
            catalog_rows=evidence.get("catalog_rows") or evidence.get("catalog_evidence") or [],
            shop_rows=evidence.get("shop_rows") or evidence.get("shop_evidence") or [],
            skipped_app_url_rows=evidence.get("skipped_app_url_rows") or [],
            scraped_content=evidence.get("scraped_content") or [],
            errors=evidence.get("errors") or [],
        )
        user_type_source = {**user_type, "phase": "local_classification", "generated_at": now}
        write_json(_source_path(run_dir, "user_type"), user_type_source)
        write_json(run_dir / "user_type.json", user_type)
        written.append("user_type")

    if _source_exists(run_dir, "user_type") and not _source_exists(run_dir, "metric_preset"):
        user_type = _read_source(run_dir, "user_type")
        top_type = user_type.get("top_type") or ((user_type.get("top_types") or [{}])[0].get("type")) or "代理商/多类型"
        derived = user_type.get("derived_user_type") or top_type
        preset = recommend_metric_preset(
            top_type,
            profile="vertical",
            derived_user_type=derived,
            w2a=bool(user_type.get("w2a_evidence")),
            shop=bool(user_type.get("catalog_rows") or user_type.get("shop_rows")),
            source_user_type=user_type,
        )
        preset_source = {**preset, "phase": "preset", "generated_at": now}
        write_json(_source_path(run_dir, "metric_preset"), preset_source)
        write_json(run_dir / "metric_preset.json", preset)
        written.append("metric_preset")

    return written


def ensure_metric_confirmation_gate(
    *,
    run_dir: Path,
    advertiser_id: str,
    capability: str,
) -> dict[str, Any] | None:
    if capability not in METRIC_CONFIRMATION_REQUIRED_CAPABILITIES:
        return None
    if not _source_exists(run_dir, "user_type") or not _source_exists(run_dir, "metric_preset"):
        return None
    user_type = _read_source(run_dir, "user_type")
    preset = _read_source(run_dir, "metric_preset")
    confirmation_path = run_dir / "metric_confirmation.json"
    confirmation = _load_json(confirmation_path, None)
    if not isinstance(confirmation, dict):
        confirmation = build_metric_confirmation(user_type, preset)
        if preset.get("source") == "account_cache":
            confirmation.update({
                "status": "confirmed_from_account_cache",
                "confirmed": True,
                "cache_write_allowed": False,
                "final_metric_preset": preset,
                "instruction_zh": "已复用近期账户垂类指标缓存；如需调整，请更新 metric_confirmation.json 后重新验证。",
                "instruction_en": "Recent account vertical metric cache was reused. To adjust it, update metric_confirmation.json and verify again.",
            })
        write_json(confirmation_path, confirmation)
        return confirmation
    if confirmation.get("cache_write_allowed") and isinstance(confirmation.get("final_metric_preset"), dict):
        maybe_write_confirmed_cache(
            advertiser_id=advertiser_id,
            user_type=user_type,
            metric_preset=confirmation["final_metric_preset"],
            confirmation=confirmation,
            evidence=_read_source(run_dir, "user_type_evidence"),
            planner_version=PLANNER_VERSION,
        )
    return confirmation


def pending_mcp_tasks(run_dir: Path, *, ready_only: bool = True, required_only: bool = True) -> list[dict[str, Any]]:
    pending = _all_pending_mcp_tasks(run_dir, ready_only=ready_only, required_only=required_only)
    if not pending:
        return []
    min_phase = min(PHASE_ORDER.index(str(t.get("phase"))) if str(t.get("phase")) in PHASE_ORDER else 999 for t in pending)
    return [task for task in pending if (PHASE_ORDER.index(str(task.get("phase"))) if str(task.get("phase")) in PHASE_ORDER else 999) == min_phase]


def _all_pending_mcp_tasks(run_dir: Path, *, ready_only: bool = True, required_only: bool = True) -> list[dict[str, Any]]:
    pending: list[dict[str, Any]] = []
    for task in _load_tasks(run_dir):
        if task.get("l0_or_l1") == "local":
            continue
        if required_only and not task.get("required"):
            continue
        source_id = _task_source_id(task)
        if _source_exists(run_dir, source_id):
            continue
        if ready_only and not _deps_satisfied(run_dir, task):
            continue
        pending.append(task)
    return pending


def _mcp_namespace_state(run_dir: Path, pending: list[dict[str, Any]]) -> dict[str, Any]:
    probe = next((task for task in _load_tasks(run_dir) if task.get("onboard_check")), None)
    if not probe:
        return {"status": "not_configured"}
    source_id = _task_source_id(probe)
    source = _read_source(run_dir, source_id)
    namespace = probe.get("expected_tool_namespace") or probe.get("mcp_namespace") or "tiktok-mcp"
    if source.get("status") in {"mcp_namespace_unavailable", "structured_unavailable"}:
        return {
            "status": "unavailable",
            "namespace": namespace,
            "probe_task": probe.get("id"),
            "message": source.get("message") or "TikTok MCP namespace is unavailable in the main session.",
        }
    if _source_exists(run_dir, source_id):
        return {"status": "available", "namespace": namespace, "probe_task": probe.get("id")}
    if any(task.get("id") == probe.get("id") for task in pending):
        return {
            "status": "awaiting_probe",
            "namespace": namespace,
            "probe_task": probe.get("id"),
            "message": "Run the onboard MCP namespace probe before starting classification/report pulls.",
        }
    return {"status": "blocked", "namespace": namespace, "probe_task": probe.get("id")}


PREVIEW_BLOCKING_OPTIONAL_IDS = {
    "ad_details_for_enrichment",
    "creative_preview_images",
    "creative_preview_videos",
    "creative_preview_spark_posts",
    "creative_preview_catalog_products",
    "creative_preview_catalog_sets",
}
PREVIEW_IMAGE_REF_FIELDS = {"image_id", "image_ids", "image_material_id", "web_uri"}
PREVIEW_VIDEO_REF_FIELDS = {"video_id", "video_ids", "video_material_id"}
PREVIEW_SPARK_REF_FIELDS = {"item_id", "item_ids", "tiktok_item_id", "spark_post_id", "anchor_id"}
PREVIEW_CATALOG_REF_FIELDS = {
    "catalog_id", "catalog_ids", "product_id", "product_ids", "item_group_id",
    "item_group_ids", "sku_id", "sku_ids", "product_set_id", "product_set_ids", "set_id",
}
PREVIEW_CATALOG_ID_FIELDS = {"catalog_id", "catalog_ids"}
PREVIEW_PRODUCT_REF_FIELDS = {
    "product_id", "product_ids", "item_group_id", "item_group_ids",
    "sku_id", "sku_ids", "product_set_id", "product_set_ids", "set_id",
}


def _collect_nested_values(payload: Any, keys: set[str]) -> list[str]:
    values: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in keys:
                if isinstance(value, list):
                    values.extend(str(item) for item in value if item)
                elif value:
                    values.append(str(value))
            values.extend(_collect_nested_values(value, keys))
    elif isinstance(payload, list):
        for item in payload:
            values.extend(_collect_nested_values(item, keys))
    return values


def _preview_reference_counts(run_dir: Path) -> dict[str, int]:
    detail_rows: list[dict[str, Any]] = []
    for source_id in ("ad_details_for_enrichment", "ad_structure", "smart_plus_ads"):
        detail_rows.extend(_rows(_read_source(run_dir, source_id)))
    catalog_ids = set(_collect_nested_values(detail_rows, PREVIEW_CATALOG_ID_FIELDS))
    product_refs = set(_collect_nested_values(detail_rows, PREVIEW_PRODUCT_REF_FIELDS))
    catalog_ref_count = len(catalog_ids) if catalog_ids and product_refs else 0
    return {
        "creative_preview_images": len(set(_collect_nested_values(detail_rows, PREVIEW_IMAGE_REF_FIELDS))),
        "creative_preview_videos": len(set(_collect_nested_values(detail_rows, PREVIEW_VIDEO_REF_FIELDS))),
        "creative_preview_spark_posts": len(set(_collect_nested_values(detail_rows, PREVIEW_SPARK_REF_FIELDS))),
        "creative_preview_catalog_products": catalog_ref_count,
        "creative_preview_catalog_sets": catalog_ref_count,
    }


def _blocking_optional_tasks(run_dir: Path, optional_pending: list[dict[str, Any]], *, depth: str) -> list[dict[str, Any]]:
    """Return optional MCP tasks that must finish before a formal report is complete."""
    if depth not in {"standard", "full", "deep"}:
        return []
    planned_ids = {str(task.get("id") or "") for task in _load_tasks(run_dir)}
    if "creative_previews" not in planned_ids:
        return []
    ref_counts = _preview_reference_counts(run_dir)
    blocking: list[dict[str, Any]] = []
    for task in optional_pending:
        task_id = str(task.get("id") or "")
        if task_id not in PREVIEW_BLOCKING_OPTIONAL_IDS:
            continue
        if task_id == "ad_details_for_enrichment":
            blocking.append(task)
            continue
        if ref_counts.get(task_id, 0) > 0:
            blocking.append(task)
    return blocking


def _nonlocal_required_complete(run_dir: Path) -> bool:
    for task in _load_tasks(run_dir):
        if not task.get("required") or task.get("l0_or_l1") == "local":
            continue
        source_id = _task_source_id(task)
        if not _source_exists(run_dir, source_id):
            return False
        if _source_status(run_dir, source_id) in {"not_queried", "permission_denied", "auth_required"}:
            return False
    return True


def maybe_run_report(
    *,
    run_dir: Path,
    advertiser_id: str,
    period: str,
    depth: str,
    start_date: str,
    end_date: str,
    previous_start_date: str | None,
    previous_end_date: str | None,
    enabled: bool,
) -> dict[str, Any] | None:
    depth = "fast" if depth == "quick" else depth
    if not enabled or not _nonlocal_required_complete(run_dir):
        return None
    cmd = [
        "python3",
        str(SCRIPT_DIR / "run_report.py"),
        "--data-dir",
        str(run_dir),
        "--depth",
        depth,
        "--advertiser-id",
        advertiser_id,
        "--period",
        period,
        "--since",
        start_date,
        "--until",
        end_date,
        "--quiet",
    ]
    if previous_start_date and previous_end_date:
        cmd.extend(["--previous-since", previous_start_date, "--previous-until", previous_end_date])
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return {
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-2000:],
        "stderr_tail": proc.stderr[-2000:],
    }


def advance_workflow(
    *,
    run_dir: Path,
    capability: str,
    advertiser_id: str,
    start_date: str,
    end_date: str,
    previous_start_date: str | None = None,
    previous_end_date: str | None = None,
    period: str = "custom",
    depth: str = "standard",
    bc_id: str = "",
    run_report_when_ready: bool = True,
    refresh_plan: bool = False,
) -> dict[str, Any]:
    depth = "fast" if depth == "quick" else depth
    try:
        summary = ensure_plan(
            run_dir=run_dir,
            capability=capability,
            advertiser_id=advertiser_id,
            start_date=start_date,
            end_date=end_date,
            previous_start_date=previous_start_date,
            previous_end_date=previous_end_date,
            depth=depth,
            bc_id=bc_id,
            refresh_plan=refresh_plan,
        )
    except StalePlanError as exc:
        result = {
            "stage": "blocked",
            "reason": "stale_plan",
            "message": str(exc),
            "run_dir": str(run_dir),
            "expected_plan_fingerprint": exc.expected,
            "found_plan_fingerprint": exc.found,
            "pending_mcp_task_count": 0,
            "pending_mcp_tasks": [],
            "audit_required_passed": False,
        }
        write_json(run_dir / "workflow_state.json", result)
        return result
    routing = ensure_routing(run_dir)
    normalized = normalize_available_raw(run_dir)
    bootstrap_derived = derive_bootstrap_aliases(run_dir)
    local_written = run_local_gate_tasks(
        run_dir=run_dir,
        advertiser_id=advertiser_id,
        start_date=start_date,
        end_date=end_date,
    )
    metric_confirmation = ensure_metric_confirmation_gate(
        run_dir=run_dir,
        advertiser_id=advertiser_id,
        capability=capability,
    )
    validation = validate(run_dir)
    report_result = maybe_run_report(
        run_dir=run_dir,
        advertiser_id=advertiser_id,
        period=period,
        depth=depth,
        start_date=start_date,
        end_date=end_date,
        previous_start_date=previous_start_date,
        previous_end_date=previous_end_date,
        enabled=run_report_when_ready,
    )
    if report_result is not None:
        validation = validate(run_dir)

    pending = pending_mcp_tasks(run_dir, ready_only=True, required_only=True)
    namespace_state = _mcp_namespace_state(run_dir, pending)
    optional_pending = _all_pending_mcp_tasks(run_dir, ready_only=True, required_only=False)
    optional_pending = [task for task in optional_pending if not task.get("required")]
    blocking_optional = _blocking_optional_tasks(run_dir, optional_pending, depth=depth)
    subagent_plan = _load_json(run_dir / "subagent_execution_plan.json", {}) or {}
    task_prompt_files: dict[str, str] = {}
    if isinstance(subagent_plan, dict):
        for shard in subagent_plan.get("shards") or []:
            if not isinstance(shard, dict):
                continue
            prompt_file = str(shard.get("prompt_file") or "")
            for task_id in shard.get("tasks") or []:
                task_prompt_files[str(task_id)] = prompt_file
    audit = _load_json(run_dir / "report_audit.json", {}) or {}
    if namespace_state.get("status") == "unavailable":
        stage = "mcp_namespace_unavailable"
    elif namespace_state.get("status") == "awaiting_probe" and pending:
        stage = "awaiting_mcp_namespace"
    elif metric_confirmation and not metric_confirmation.get("confirmed") and not metric_confirmation.get("cache_write_allowed"):
        stage = "awaiting_metric_confirmation"
    elif blocking_optional:
        stage = "awaiting_optional_mcp"
    elif audit.get("required_passed"):
        stage = "complete"
    elif pending:
        stage = "awaiting_mcp"
    elif report_result is not None and report_result.get("returncode") != 0:
        stage = "blocked"
    elif _nonlocal_required_complete(run_dir):
        stage = "ready_for_report"
    else:
        stage = "blocked"

    pending_compact = [
        {
            "id": task.get("id"),
            "phase": task.get("phase"),
            "tool": task.get("tool"),
            "l0_or_l1": task.get("l0_or_l1"),
            "l1_tool_name": task.get("l1_tool_name"),
            "output_raw": task.get("output_raw"),
            "output_source": task.get("output_source"),
            "preferred_backend": task.get("preferred_backend"),
            "expected_tool_namespace": task.get("expected_tool_namespace"),
            "mcp_namespace": task.get("mcp_namespace"),
            "onboard_check": task.get("onboard_check"),
            "namespace_fail_fast": task.get("namespace_fail_fast"),
            "metric_source_policy": task.get("metric_source_policy"),
            "subagent_prompt_file": task_prompt_files.get(str(task.get("id") or "")),
            "params": task.get("params"),
        }
        for task in pending
    ]
    blocking_optional_compact = [
        {
            "id": task.get("id"),
            "phase": task.get("phase"),
            "tool": task.get("tool"),
            "l0_or_l1": task.get("l0_or_l1"),
            "l1_tool_name": task.get("l1_tool_name"),
            "output_raw": task.get("output_raw"),
            "output_source": task.get("output_source"),
            "preferred_backend": task.get("preferred_backend"),
            "subagent_prompt_file": task_prompt_files.get(str(task.get("id") or "")),
            "params": task.get("params"),
        }
        for task in blocking_optional
    ]
    write_json(run_dir / "pending_mcp_tasks.json", pending_compact)

    result = {
        "stage": stage,
        "run_dir": str(run_dir),
        "summary": summary,
        "routing": routing,
        "normalized": normalized,
        "bootstrap_derived": bootstrap_derived,
        "local_written": local_written,
        "validation": validation,
        "metric_confirmation": metric_confirmation,
        "mcp_namespace_state": namespace_state,
        "report_result": report_result,
        "pending_mcp_task_count": len(pending_compact),
        "optional_pending_mcp_task_count": len(optional_pending),
        "blocking_optional_mcp_task_count": len(blocking_optional_compact),
        "blocking_optional_mcp_tasks": blocking_optional_compact,
        "pending_mcp_tasks_path": str(run_dir / "pending_mcp_tasks.json"),
        "metric_confirmation_path": str(run_dir / "metric_confirmation.json") if metric_confirmation else None,
        "subagent_recovery_command": subagent_plan.get("recovery_command") if isinstance(subagent_plan, dict) else None,
        "pending_mcp_tasks": pending_compact,
        "audit_required_passed": bool(audit.get("required_passed")),
    }
    write_json(run_dir / "workflow_state.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Advance a creatiads workflow without calling MCP.")
    parser.add_argument("--capability", default="full_report")
    parser.add_argument("--advertiser-id", required=True)
    parser.add_argument("--since", "--start-date", dest="start_date", required=True)
    parser.add_argument("--until", "--end-date", dest="end_date", required=True)
    parser.add_argument("--previous-since", "--previous-start-date", dest="previous_start_date")
    parser.add_argument("--previous-until", "--previous-end-date", dest="previous_end_date")
    parser.add_argument("--period", choices=["daily", "weekly", "custom"], default="custom")
    parser.add_argument("--depth", choices=["quick", "fast", "standard", "full", "deep"], default="standard")
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--bc-id", default="")
    parser.add_argument("--no-report", action="store_true", help="Do not run run_report.py even when sources are complete.")
    parser.add_argument("--refresh-plan", action="store_true", help="Regenerate pull_plan.json and mcp_tasks.jsonl even if a plan already exists.")
    parser.add_argument("--quiet", action="store_true", help="Print a compact workflow summary instead of full pending task details.")
    args = parser.parse_args()

    result = advance_workflow(
        run_dir=args.run_dir,
        capability=args.capability,
        advertiser_id=args.advertiser_id,
        start_date=args.start_date,
        end_date=args.end_date,
        previous_start_date=args.previous_start_date,
        previous_end_date=args.previous_end_date,
        period=args.period,
        depth=args.depth,
        bc_id=args.bc_id,
        run_report_when_ready=not args.no_report,
        refresh_plan=args.refresh_plan,
    )
    if args.quiet:
        compact = {
            "stage": result.get("stage"),
            "run_dir": result.get("run_dir"),
            "pending_mcp_task_count": result.get("pending_mcp_task_count"),
            "optional_pending_mcp_task_count": result.get("optional_pending_mcp_task_count"),
            "mcp_namespace_status": (result.get("mcp_namespace_state") or {}).get("status"),
            "audit_required_passed": result.get("audit_required_passed"),
            "report_result": result.get("report_result"),
        }
        print(json.dumps(compact, ensure_ascii=False))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("stage") in {"awaiting_mcp_namespace", "awaiting_mcp", "ready_for_report", "complete"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
