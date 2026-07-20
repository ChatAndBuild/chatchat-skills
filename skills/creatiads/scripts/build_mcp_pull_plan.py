#!/usr/bin/env python3
"""Build a machine-readable MCP pull plan for the creatiads agent.

Generates pull_plan.json that tells the agent exactly which TikTok MCP tools
to call, in which order, with which parameters.  The agent executes the plan;
this script owns the decisions about what to pull and when.

Usage:
  python3 creatiads/scripts/build_mcp_pull_plan.py \\
    --advertiser-id 7444033053753835536 \\
    --start-date 2025-12-08 \\
    --end-date 2025-12-14 \\
    --previous-start-date 2025-12-01 \\
    --previous-end-date 2025-12-07 \\
    --depth full \\
    --run-dir runs/7444033053753835536_2025w50_full
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CORE_METRICS = [
    "spend", "impressions", "clicks", "ctr", "cpc", "cpm", "reach", "frequency",
    "conversion", "cost_per_conversion", "conversion_rate_v2", "result",
    "cost_per_result", "result_rate",
]
CORE_METRICS_STR = json.dumps(CORE_METRICS)

VALUE_METRICS = [
    "total_purchase", "total_purchase_value", "total_active_pay_roas",
    "complete_payment", "complete_payment_roas", "value_per_complete_payment",
    "onsite_total_purchase", "onsite_total_purchase_value", "onsite_purchases_roas",
    "shop_total_purchase_by_order_submission", "shop_gross_revenue_by_order_submission",
]

LEAN_METRICS = ["spend", "impressions", "clicks", "conversion"]
CLASSIFICATION_TOP_N = 50
PLANNER_VERSION = "2026-06-01-tiktok-preview-parity"

ADVERTISER_ATTR_METRICS: list[str] = []

CAMPAIGN_ATTR_METRICS = [
    "campaign_name", "objective_type", "campaign_automation_type",
]

CAMPAIGN_STRUCTURE_FIELDS = [
    "campaign_id", "campaign_name", "objective_type",
    "campaign_automation_type", "operation_status", "secondary_status",
]

ADGROUP_STRUCTURE_FIELDS = [
    "adgroup_id", "adgroup_name", "campaign_id", "campaign_name",
    "promotion_type", "promotion_target_type", "app_id", "app_download_url",
    "app_type", "optimization_goal", "billing_event", "operation_status",
    "secondary_status",
]

AD_STRUCTURE_FIELDS = [
    "ad_id", "smart_plus_ad_id", "ad_name", "campaign_id", "campaign_name",
    "campaign_automation_type", "adgroup_id", "adgroup_name",
    "landing_page_url", "landing_page_urls", "creative_type", "ad_text",
    "ad_texts", "call_to_action", "call_to_action_id", "identity_id", "identity_type",
    "identity_authorized_bc_id", "ad_format", "image_mode", "playable_url",
    "profile_image_url", "avatar_icon_web_uri",
    "app_name", "page_id", "video_id", "image_ids", "tracking_pixel_id", "tiktok_item_id",
    "catalog_id", "item_group_ids", "sku_ids", "product_set_id",
]

ADGROUP_ATTR_METRICS = [
    "campaign_id", "campaign_name", "campaign_automation_type",
    "adgroup_name", "promotion_type", "billing_event", "placement_type",
    "adgroup_download_url",
]

AD_ATTR_METRICS = [
    "campaign_id", "campaign_name", "campaign_automation_type", "adgroup_id",
    "adgroup_name", "ad_name", "ad_text", "ad_url",
    "adgroup_download_url", "objective_type", "promotion_type", "tt_app_name",
    "mobile_app_id", "call_to_action",
]

AD_V2_ATTR_METRICS = [
    "smart_plus_ad_id", "campaign_id", "campaign_name",
    "campaign_automation_type", "adgroup_id", "adgroup_name", "ad_name",
    "ad_url", "objective_type", "promotion_type", "tt_app_name",
    "mobile_app_id", "call_to_action",
]

LANDING_METRICS = ["cost_per_landing_page_view"]
KNOWN_UNSUPPORTED_LANDING_METRICS = [
    "landing_page_view",
    "traffic_landing_page_view",
    "click_to_destination_rate",
]

RETENTION_METRICS = [
    "video_play_actions", "video_watched_2s", "video_watched_6s",
    "video_views_p25", "video_views_p50", "video_views_p75", "video_views_p100",
    "average_video_play", "engaged_view", "engaged_view_15s",
]

AUDIENCE_CORE_METRICS = [
    "spend", "impressions", "clicks", "ctr", "cpc", "cpm", "conversion",
    "cost_per_conversion", "result", "cost_per_result",
]

AUDIENCE_VALUE_METRICS = [
    "total_purchase_value", "total_active_pay_roas", "onsite_total_purchase_value",
]

AUDIENCE_METRICS = AUDIENCE_CORE_METRICS + AUDIENCE_VALUE_METRICS

GMV_MAX_ACCOUNT_METRICS = [
    "cost", "orders", "cost_per_order", "gross_revenue", "roi", "net_cost",
]

GMV_MAX_CAMPAIGN_METRICS = [
    "roas_bid", "cost", "net_cost", "orders", "cost_per_order", "gross_revenue", "roi",
]

GMV_MAX_PRODUCT_METRICS = [
    "product_status", "orders", "gross_revenue",
]

GMV_MAX_CREATIVE_METRICS = [
    "creative_delivery_status", "cost", "orders", "cost_per_order", "gross_revenue", "roi",
    "product_impressions", "product_clicks", "product_click_rate", "ad_click_rate",
    "ad_conversion_rate", "ad_video_view_rate_2s", "ad_video_view_rate_6s",
    "ad_video_view_rate_p25", "ad_video_view_rate_p50", "ad_video_view_rate_p75",
    "ad_video_view_rate_p100",
]

GMV_MAX_DURATION_METRICS = [
    "cost", "orders", "cost_per_order", "gross_revenue", "roi", "roas_bid",
]

# ── Phase ordering ──────────────────────────────────────────────────────
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

# ── Per-phase required sources (from plan §1 table) ─────────────────────
PHASE_REQUIRED_SOURCES: dict[str, list[str]] = {
    "bootstrap": ["mcp_ready", "current_account", "advertiser_info"],
    "classification": [
        "classification_campaigns", "classification_adgroups",
        "classification_ads", "classification_ad_v2_insights",
        "app_list", "catalog_list", "shop_list", "smart_plus_ads",
    ],
    "local_classification": ["user_type_evidence", "user_type"],
    "preset": ["metric_preset"],
    "report_data": [
        "current_advertiser_insights", "current_campaigns",
        "current_adgroups", "current_ads", "current_ad_v2_insights",
        "previous_advertiser_insights", "previous_campaigns",
        "previous_adgroups", "previous_ads",
    ],
    "enrichment": [
        "audience_country", "audience_age_gender", "audience_placement",
        "audience_device", "ad_details_for_enrichment",
        "creative_preview_images", "creative_preview_videos", "landing_app_paths",
        "apps", "campaign_structure", "adgroup_structure", "ad_structure",
        "activity_changelog", "activity_targeted_insights",
        "activity_daily_breakdown", "activity_factors",
        "creative_retention", "targeted_creative_retention",
    ],
}

# ── Depth-gated enrichment sources ──────────────────────────────────────
DEPTH_ENRICHMENT: dict[str, list[str]] = {
    "fast": [
        "audience_country", "landing_pages_report", "landing_app_paths",
        "activity_changelog", "activity_targeted_insights",
        "activity_daily_breakdown", "activity_factors",
        "activity_targeted_campaign_insights", "activity_targeted_adgroup_insights",
        "activity_targeted_ad_insights", "activity_daily_campaign_breakdown",
        "activity_daily_adgroup_breakdown", "activity_daily_ad_breakdown",
    ],
    "standard": [
        "audience_country", "audience_age_gender", "audience_placement",
        "landing_pages_report", "landing_app_paths", "creative_previews",
        "creative_retention", "targeted_creative_retention",
        "targeted_creative_retention_raw",
        "apps", "campaign_structure", "adgroup_structure", "ad_structure",
        "activity_changelog", "activity_targeted_insights",
        "activity_daily_breakdown", "activity_factors",
        "activity_targeted_campaign_insights", "activity_targeted_adgroup_insights",
        "activity_targeted_ad_insights", "activity_daily_campaign_breakdown",
        "activity_daily_adgroup_breakdown", "activity_daily_ad_breakdown",
        "ad_details_for_enrichment", "creative_preview_images", "creative_preview_videos",
        "creative_preview_spark_posts", "creative_preview_catalog_products", "creative_preview_catalog_sets",
    ],
    "full": [
        "audience_country", "audience_age_gender", "audience_placement",
        "audience_device", "landing_pages_report", "landing_app_paths",
        "creative_previews", "creative_retention", "targeted_creative_retention",
        "targeted_creative_retention_raw",
        "apps", "campaign_structure", "adgroup_structure", "ad_structure",
        "activity_changelog", "activity_targeted_insights",
        "activity_daily_breakdown", "activity_factors",
        "activity_targeted_campaign_insights", "activity_targeted_adgroup_insights",
        "activity_targeted_ad_insights", "activity_daily_campaign_breakdown",
        "activity_daily_adgroup_breakdown", "activity_daily_ad_breakdown",
        "ad_details_for_enrichment", "creative_preview_images", "creative_preview_videos",
        "creative_preview_spark_posts", "creative_preview_catalog_products", "creative_preview_catalog_sets",
    ],
    "deep": [
        "audience_country", "audience_age_gender", "audience_placement",
        "audience_device", "landing_pages_report", "landing_app_paths",
        "creative_previews", "creative_retention", "targeted_creative_retention",
        "targeted_creative_retention_raw",
        "apps", "campaign_structure", "adgroup_structure", "ad_structure",
        "activity_changelog", "activity_targeted_insights",
        "activity_daily_breakdown", "activity_factors",
        "activity_targeted_campaign_insights", "activity_targeted_adgroup_insights",
        "activity_targeted_ad_insights", "activity_daily_campaign_breakdown",
        "activity_daily_adgroup_breakdown", "activity_daily_ad_breakdown",
        "ad_details_for_enrichment", "creative_preview_images", "creative_preview_videos",
        "creative_preview_spark_posts", "creative_preview_catalog_products", "creative_preview_catalog_sets",
    ],
}

CURRENT_SOURCES_BY_DEPTH: dict[str, set[str]] = {
    "fast": {
        "current_advertiser_insights",
        "current_campaigns",
        "current_adgroups",
        "current_ads",
        "current_ad_v2_insights",
    },
    "standard": {
        "current_advertiser_insights",
        "current_campaigns",
        "current_adgroups",
        "current_ads",
        "current_ad_v2_insights",
    },
    "full": {
        "current_advertiser_insights",
        "current_campaigns",
        "current_adgroups",
        "current_ads",
        "current_ad_v2_insights",
    },
    "deep": {
        "current_advertiser_insights",
        "current_campaigns",
        "current_adgroups",
        "current_ads",
        "current_ad_v2_insights",
    },
}

PREVIOUS_SOURCES_BY_DEPTH: dict[str, set[str]] = {
    "fast": {"previous_advertiser_insights", "previous_campaigns"},
    "standard": {"previous_advertiser_insights", "previous_campaigns", "previous_adgroups", "previous_ads"},
    "full": {"previous_advertiser_insights", "previous_campaigns", "previous_adgroups", "previous_ads"},
    "deep": {"previous_advertiser_insights", "previous_campaigns", "previous_adgroups", "previous_ads"},
}
DEPTH_METRIC_PROBE: set[str] = {"full", "deep"}

DEPTH_INSIGHT_MAX_PAGES: dict[str, int] = {"fast": 1, "standard": 3, "full": 10, "deep": 50}
DEPTH_LANDING_MAX_PAGES: dict[str, int] = {"fast": 3, "standard": 10, "full": 25, "deep": 50}
DEPTH_STRUCTURE_LIMIT: dict[str, int | None] = {"fast": None, "standard": 30, "full": 60, "deep": None}

L1_TOOL_NAMES = {
    "changelog_task_create",
    "changelog_task_check",
    "changelog_task_download",
    "ad_get",
    "adgroup_get",
    "campaign_get",
    "file_image_ad_info_get",
    "file_video_ad_info_get",
    "tt_video_list_get",
    "gmv_max_store_list_get",
    "store_list_get",
    "gmv_max_campaign_get",
    "campaign_gmv_max_info_get",
    "gmv_max_report_get",
    "store_product_get",
    "identity_video_info_get",
    "gmv_max_custom_anchor_video_list_get",
    "gmv_max_video_get",
    "gmv_max_bid_recommend_get",
}

# ── Backend routing ───────────────────────────────────────────────────────
NATIVE_BACKEND = "native_agent_mcp"
SUBAGENT_BACKEND = "mcp_subagent_executor"
LEGACY_BRIDGE_BACKEND = "bridge_executor"

BATCH_CAPABILITIES: set[str] = {
    "full_report",
    "gmv_max_report",
    "audience_diagnosis",
    "creative_diagnosis",
    "landing_app_paths",
    "activity_changelog",
    "bottleneck_diagnosis",
    "performance_diagnosis",
}

NATIVE_CAPABILITIES: set[str] = {
    "account_inventory",
    "user_type",
    "metric_profile",
}


def _route_backend(capability: str, depth: str, is_local: bool) -> dict[str, Any]:
    """Determine the preferred execution backend for a task.

    Local tasks always run natively. Report runs route batch-capable MCP
    tasks to the agent-native subagent executor so daily/weekly reports can
    pull independent shards in parallel at every supported report depth.
    """
    if is_local:
        return {
            "preferred_backend": NATIVE_BACKEND,
            "allow_backend_fallback": False,
            "backend_reason": "local_compute",
        }
    if capability in NATIVE_CAPABILITIES:
        return {
            "preferred_backend": NATIVE_BACKEND,
            "allow_backend_fallback": False,
            "backend_reason": "light_query",
        }
    if capability in BATCH_CAPABILITIES:
        return {
            "preferred_backend": SUBAGENT_BACKEND,
            "allow_backend_fallback": True,
            "backend_reason": "report_parallel" if capability == "full_report" else "batch_enrichment",
        }
    return {
        "preferred_backend": NATIVE_BACKEND,
        "allow_backend_fallback": False,
        "backend_reason": "light_query",
    }


def _capability_for_step(step_id: str) -> str:
    if step_id.startswith("gmv_max_") or "_gmv_max_" in step_id:
        return "gmv_max_report"
    if step_id in {"mcp_ready", "current_account", "advertiser_info"}:
        return "account_inventory"
    if step_id.startswith("classification_") or step_id in {"app_list", "catalog_list", "shop_list", "smart_plus_ads", "user_type_evidence", "user_type"}:
        return "user_type"
    if step_id.startswith("metric_"):
        return "metric_profile"
    if step_id.startswith(("current_", "previous_")):
        return "performance_diagnosis"
    if step_id.startswith("audience_"):
        return "audience_diagnosis"
    if step_id == "apps" or step_id.endswith("_structure"):
        return "performance_diagnosis"
    if step_id.startswith(("creative_", "targeted_creative", "ad_details")):
        return "creative_diagnosis"
    if step_id.startswith("landing_"):
        return "landing_app_paths"
    if step_id.startswith("activity_"):
        return "activity_changelog"
    if step_id.startswith("bottleneck_"):
        return "bottleneck_diagnosis"
    return "full_report"


def _subagent_shard_fields(step: dict[str, Any]) -> dict[str, Any]:
    step_id = str(step.get("id") or "")
    phase = str(step.get("phase") or "")
    tool = str(step.get("tool") or "")
    pagination = step.get("pagination") or {}

    if tool.startswith("local:"):
        shard_key = "local_compute"
        role = "main_agent_local_compute"
        parallel_group = "local_compute"
        max_concurrency = 1
        execution_mode = "local"
    elif step_id == "mcp_ready":
        shard_key = "classification_seed"
        role = "classification_seed_collector"
        parallel_group = "bootstrap_probe"
        max_concurrency = 1
        execution_mode = "sequential"
    elif step_id == "smart_plus_ads":
        shard_key = "smart_plus"
        role = "smart_plus_enrichment_worker"
        parallel_group = "smart_plus_enrichment"
        max_concurrency = 1
        execution_mode = "parallel_after_dependencies"
    elif phase in {"bootstrap", "classification"}:
        shard_key = "classification_seed"
        role = "classification_seed_collector"
        parallel_group = "classification_seed"
        max_concurrency = 4
        execution_mode = "parallel_after_dependencies"
    elif step_id == "metric_probe_results":
        shard_key = "metric_probe"
        role = "metric_probe_worker"
        parallel_group = "metric_probe"
        max_concurrency = 1
        execution_mode = "sequential"
    elif phase == "report_data" and step_id in {"current_advertiser_insights", "previous_advertiser_insights"}:
        shard_key = "formal_totals"
        role = "formal_report_source_worker"
        parallel_group = "report_data_formal"
        max_concurrency = 4
        execution_mode = "parallel_after_dependencies"
    elif phase == "report_data" and step_id in {"current_campaigns", "previous_campaigns"}:
        shard_key = "formal_campaigns"
        role = "formal_report_source_worker"
        parallel_group = "report_data_formal"
        max_concurrency = 4
        execution_mode = "parallel_after_dependencies"
    elif phase == "report_data" and step_id in {"current_adgroups", "previous_adgroups"}:
        shard_key = "formal_adgroups"
        role = "formal_report_source_worker"
        parallel_group = "report_data_formal"
        max_concurrency = 4
        execution_mode = "parallel_after_dependencies"
    elif phase == "report_data" and step_id in {"current_ads", "previous_ads", "current_ad_v2_insights"}:
        shard_key = "formal_ads"
        role = "formal_report_source_worker"
        parallel_group = "report_data_formal"
        max_concurrency = 4
        execution_mode = "parallel_after_dependencies"
    elif step_id.startswith("audience_"):
        shard_key = step_id
        role = "audience_enrichment_worker"
        parallel_group = "audience_breakdowns"
        max_concurrency = 4
        execution_mode = "parallel_after_dependencies"
    elif step_id == "apps" or step_id.endswith("_structure"):
        shard_key = "structure"
        role = "structure_enrichment_worker"
        parallel_group = "structure_enrichment"
        max_concurrency = 3
        execution_mode = "parallel_after_dependencies"
    elif step_id.startswith(("creative_", "targeted_creative", "ad_details")):
        shard_key = "creative"
        role = "creative_enrichment_worker"
        parallel_group = "creative_enrichment"
        max_concurrency = 3
        execution_mode = "parallel_after_dependencies"
    elif step_id == "activity_changelog":
        shard_key = "activity_changelog_required"
        role = "activity_changelog_worker"
        parallel_group = "activity_enrichment"
        max_concurrency = 3
        execution_mode = "parallel_after_dependencies"
    elif step_id.startswith("activity_targeted_"):
        shard_key = "activity_targeted_optional"
        role = "activity_enrichment_worker"
        parallel_group = "activity_enrichment"
        max_concurrency = 3
        execution_mode = "parallel_after_dependencies"
    elif step_id.startswith("activity_daily_"):
        shard_key = "activity_daily_optional"
        role = "activity_enrichment_worker"
        parallel_group = "activity_enrichment"
        max_concurrency = 3
        execution_mode = "parallel_after_dependencies"
    elif step_id.startswith("landing_"):
        shard_key = "landing_app"
        role = "landing_app_worker"
        parallel_group = "landing_app_enrichment"
        max_concurrency = 2
        execution_mode = "parallel_after_dependencies"
    else:
        shard_key = phase or "general"
        role = f"{shard_key}_worker"
        parallel_group = shard_key
        max_concurrency = 2
        execution_mode = "parallel_after_dependencies"

    max_rows_hint = pagination.get("expected_total_max") or pagination.get("page_size") or 0
    direct_to_file = not tool.startswith("local:")
    return {
        "shard_key": shard_key,
        "subagent_role": role,
        "parallel_group": parallel_group,
        "max_concurrency": max_concurrency,
        "execution_mode": execution_mode,
        "max_rows_hint": max_rows_hint,
        "return_contract": {
            "type": "compact_status",
            "fields": ["shard_id", "status", "sources", "row_counts", "degraded_sources", "errors"],
            "raw_payload_in_chat": False,
            "direct_to_file": direct_to_file,
            "chat_response_max_bytes": 0 if direct_to_file else 2000,
        },
    }


def _agent_task_fields(step: dict[str, Any], depth: str = "standard") -> dict[str, Any]:
    tool = str(step.get("tool") or "")
    step_id = str(step.get("id") or "")
    output = str(step.get("output") or f"sources/{step_id}.json")
    is_local = tool.startswith("local:")
    is_l1 = tool in L1_TOOL_NAMES
    capability = step.get("capability") or _capability_for_step(step_id)
    backend = _route_backend(capability, depth, is_local)
    fields = {
        "capability": capability,
        "l0_or_l1": "local" if is_local else ("l1" if is_l1 else "l0"),
        "l1_tool_name": "" if is_local else (tool if is_l1 else ""),
        "output_raw": "" if is_local else f"raw/{step_id}.json",
        "output_source": output,
        "direct_to_file": not is_local,
        "chat_response_max_bytes": 0 if not is_local else 2000,
        "degradation_policy": step.get("degradation_policy") or (
            "required_source_must_be_ok_or_structured_degraded"
            if step.get("required")
            else "optional_source_may_be_degraded"
        ),
        "preferred_backend": backend["preferred_backend"],
        "allow_backend_fallback": backend["allow_backend_fallback"],
        "backend_reason": backend["backend_reason"],
    }
    fields.update(_subagent_shard_fields(step))
    return fields


def enrich_steps_for_agent_tasks(steps: list[dict[str, Any]], depth: str = "standard") -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for step in steps:
        item = dict(step)
        for key, value in _agent_task_fields(item, depth).items():
            item.setdefault(key, value)
        enriched.append(item)
    return enriched


def write_mcp_tasks(run_dir: Path, plan: dict[str, Any]) -> Path:
    tasks_path = run_dir / "mcp_tasks.jsonl"
    lines = []
    for step in plan.get("steps") or []:
        task = {
            key: step.get(key)
            for key in (
                "id", "capability", "phase", "tool", "l0_or_l1", "l1_tool_name",
                "params", "output_raw", "output_source", "depends_on", "required",
                "pagination", "degradation_policy", "retry_ladder", "async_flow",
                "metric_probe_template", "metric_source_policy",
                "mcp_namespace", "expected_tool_namespace", "onboard_check",
                "namespace_fail_fast",
                "order", "preferred_backend", "allow_backend_fallback", "backend_reason",
                "shard_key", "subagent_role", "parallel_group", "max_concurrency",
                "execution_mode", "max_rows_hint", "return_contract", "direct_to_file",
                "chat_response_max_bytes", "compatibility_notes", "note", "source_expansion",
                "gmv_max_report_contract", "gmv_max_enum_policy",
            )
            if key in step
        }
        lines.append(json.dumps(task, ensure_ascii=False, sort_keys=True))
    tasks_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return tasks_path


def _params_hash(params: dict[str, Any]) -> str:
    raw = json.dumps(params, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def build_plan_fingerprint(
    *,
    capability: str,
    advertiser_id: str,
    start_date: str,
    end_date: str,
    previous_start_date: str | None = None,
    previous_end_date: str | None = None,
    depth: str,
    bc_id: str = "",
    user_type: str = "",
    account_cache_mode: str = "",
) -> dict[str, Any]:
    values = {
        "planner_version": PLANNER_VERSION,
        "capability": capability,
        "advertiser_id": advertiser_id,
        "start_date": start_date,
        "end_date": end_date,
        "previous_start_date": previous_start_date or "",
        "previous_end_date": previous_end_date or "",
        "depth": depth,
        "bc_id": bc_id or "",
        "user_type": user_type or "",
        "account_cache_mode": account_cache_mode or "",
    }
    raw = json.dumps(values, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {**values, "hash": hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]}


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _metric_attrs(dimensions: list[str], attributes: list[str]) -> list[str]:
    """TikTok rejects dimension fields when they are repeated in metrics."""
    dimension_set = set(dimensions)
    return [attribute for attribute in attributes if attribute not in dimension_set]


def _main_metrics(attributes: list[str]) -> list[str]:
    return _dedupe(CORE_METRICS + VALUE_METRICS + attributes)


def _metrics_without_value(attributes: list[str]) -> list[str]:
    return _dedupe(CORE_METRICS + attributes)


def _lean_metrics(attributes: list[str] | None = None) -> list[str]:
    return _dedupe(LEAN_METRICS + (attributes or []))


def _main_retry_ladder(dimensions: list[str], attributes: list[str]) -> list[dict[str, Any]]:
    attrs = _metric_attrs(dimensions, attributes)
    return [
        {"dimensions": dimensions, "metrics": _main_metrics(attrs)},
        {"dimensions": dimensions, "metrics": _metrics_without_value(attrs)},
        {"dimensions": dimensions, "metrics": _lean_metrics(attrs)},
        {"dimensions": dimensions, "metrics": _lean_metrics()},
    ]


def _preset_metric_policy(source_id: str, compatibility_profile: str = "standard") -> dict[str, Any]:
    return {
        "metrics_from": "metric_preset.json",
        "user_type_source": "user_type.json",
        "preset_fields": ["recommended_preset.metrics", "metrics"],
        "attribute_source": "smart_plus_enrichment_for_names",
        "compatibility_profile": compatibility_profile,
        "forbid_default_lean": True,
        "fallback_order": [
            "preset_metrics_plus_compatible_attributes",
            "preset_metrics_without_value",
            "core_conversion_plus_compatible_attributes",
            "lean_metrics_last_resort_only",
        ],
        "source_id": source_id,
    }


def _compatible_attrs(source_id: str, attributes: list[str]) -> list[str]:
    """Remove fields known to break formal report pulls for a source.

    Name/object metadata should be filled from Smart+ structure APIs when the
    reporting endpoint rejects the field as a metric for the chosen dimension.
    """
    blocked: dict[str, set[str]] = {
        "current_adgroups": {
            "campaign_id", "campaign_name", "campaign_automation_type",
            "adgroup_name", "promotion_type", "billing_event",
            "placement_type", "adgroup_download_url",
        },
        "previous_adgroups": {
            "campaign_id", "campaign_name", "campaign_automation_type",
            "adgroup_name", "promotion_type", "billing_event",
            "placement_type", "adgroup_download_url",
        },
        "classification_ad_v2_insights": {"smart_plus_ad_id"},
        "current_ad_v2_insights": {"smart_plus_ad_id"},
    }
    denied = blocked.get(source_id, set())
    return [attribute for attribute in attributes if attribute not in denied]


def _report_params(
    advertiser_id: str,
    data_level: str,
    dimensions: list[str],
    metrics: list[str],
    start_date: str,
    end_date: str,
    page_size: int = 1000,
) -> dict[str, Any]:
    return {
        "advertiser_id": advertiser_id,
        "report_type": "BASIC",
        "data_level": data_level,
        "dimensions": dimensions,
        "metrics": metrics,
        "start_date": start_date,
        "end_date": end_date,
        "page": 1,
        "page_size": page_size,
        "order_field": "spend",
        "order_type": "DESC",
    }


def _audience_params(
    advertiser_id: str,
    dimensions: list[str],
    metrics: list[str],
    start_date: str,
    end_date: str,
    page_size: int = 1000,
) -> dict[str, Any]:
    return {
        "advertiser_id": advertiser_id,
        "report_type": "AUDIENCE",
        "data_level": "AUCTION_ADVERTISER",
        "dimensions": dimensions,
        "metrics": metrics,
        "start_date": start_date,
        "end_date": end_date,
        "page": 1,
        "page_size": page_size,
    }


def _gmv_max_report_params(
    advertiser_id: str,
    dimensions: list[str],
    metrics: list[str],
    start_date: str,
    end_date: str,
    *,
    store_ids: list[str] | None = None,
    filtering: dict[str, Any] | None = None,
    page_size: int = 1000,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "advertiser_id": advertiser_id,
        "dimensions": dimensions,
        "metrics": metrics,
        "start_date": start_date,
        "end_date": end_date,
        "enable_total_metrics": True,
        "sort_field": "cost",
        "sort_type": "DESC",
        "page": 1,
        "page_size": page_size,
    }
    if store_ids:
        params["store_ids"] = store_ids
    if filtering:
        params["filtering"] = filtering
    return params


def _gmv_max_report_step(
    *,
    source_id: str,
    advertiser_id: str,
    dimensions: list[str],
    metrics: list[str],
    start_date: str,
    end_date: str,
    depends_on: list[str],
    required: bool = True,
    filtering: dict[str, Any] | None = None,
    note: str = "",
) -> dict[str, Any]:
    return {
        "id": source_id,
        "phase": "gmv_max_report_data",
        "tool": "gmv_max_report_get",
        "required": required,
        "output": f"sources/{source_id}.json",
        "depends_on": depends_on,
        "params": _gmv_max_report_params(
            advertiser_id,
            dimensions,
            metrics,
            start_date,
            end_date,
            store_ids=["__gmv_max_store_ids__"],
            filtering=filtering,
        ),
        "pagination": {"mode": "paginated", "page_size": 1000, "max_pages": 20},
        "gmv_max_report_contract": {
            "report_mode": "gmv_max",
            "enum_policy": "campaign discovery uses PRODUCT_GMV_MAX/LIVE_GMV_MAX; report filtering uses PRODUCT/LIVE.",
            "metrics_are_level_specific": True,
        },
        "note": note,
    }


def _report_step(
    *,
    source_id: str,
    phase: str,
    advertiser_id: str,
    data_level: str,
    dimensions: list[str],
    metrics: list[str],
    start_date: str,
    end_date: str,
    output: str,
    depends_on: list[str],
    required: bool = True,
    pagination: dict[str, Any] | None = None,
    retry_ladder: list[dict[str, Any]] | None = None,
    filtering: dict[str, Any] | None = None,
    note: str | None = None,
    page_size: int = 1000,
    metric_source_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    params = _report_params(advertiser_id, data_level, dimensions, metrics, start_date, end_date, page_size=page_size)
    if filtering:
        params["filtering"] = filtering
    step: dict[str, Any] = {
        "id": source_id,
        "phase": phase,
        "tool": "report_integrated_get",
        "required": required,
        "output": output,
        "depends_on": depends_on,
        "params": params,
        "pagination": pagination or {"mode": "paginated", "page_size": 1000},
    }
    if retry_ladder:
        step["retry_ladder"] = retry_ladder
    if note:
        step["note"] = note
    if metric_source_policy:
        step["metric_source_policy"] = metric_source_policy
    return step


def _audience_step(
    *,
    source_id: str,
    advertiser_id: str,
    candidate_dimensions: list[list[str]],
    start_date: str,
    end_date: str,
    expected_total_max: int,
    metrics: list[str] | None = None,
) -> dict[str, Any]:
    first_dimensions = candidate_dimensions[0]
    metric_set = metrics or AUDIENCE_METRICS
    return {
        "id": source_id,
        "phase": "enrichment",
        "tool": "report_integrated_get",
        "required": True,
        "output": f"sources/{source_id}.json",
        "depends_on": ["metric_preset"],
        "params": _audience_params(advertiser_id, first_dimensions, metric_set, start_date, end_date),
        "pagination": {"mode": "single", "expected_total_max": expected_total_max},
        "retry_ladder": [
            {"dimensions": dimensions, "metrics": metric_set}
            for dimensions in candidate_dimensions
        ] + [
            {"dimensions": first_dimensions, "metrics": AUDIENCE_CORE_METRICS},
            {"dimensions": first_dimensions, "metrics": LEAN_METRICS},
        ],
    }


def build_plan(
    advertiser_id: str,
    start_date: str,
    end_date: str,
    previous_start_date: str | None = None,
    previous_end_date: str | None = None,
    depth: str = "full",
    bc_id: str = "",
    use_cached_user_type: bool = False,
    cached_user_type: str = "",
) -> dict[str, Any]:
    depth = "fast" if depth == "quick" else depth
    run_id = f"{advertiser_id}_{start_date}_{end_date}_{depth}"
    now = datetime.now(timezone.utc).isoformat()
    steps: list[dict[str, Any]] = []
    phase_index: dict[str, int] = {p: i for i, p in enumerate(PHASE_ORDER)}
    insight_max_pages = DEPTH_INSIGHT_MAX_PAGES.get(depth, 3)
    landing_max_pages = DEPTH_LANDING_MAX_PAGES.get(depth, 10)
    classification_required = not use_cached_user_type

    # ── bootstrap ───────────────────────────────────────────────────
    steps.append({
        "id": "mcp_ready",
        "phase": "bootstrap",
        "tool": "advertiser_info_get",
        "required": True,
        "output": "sources/mcp_ready.json",
        "depends_on": [],
        "params": {"advertiser_ids": [advertiser_id]},
        "pagination": {"mode": "single", "expected_total_max": 1},
        "mcp_namespace": "tiktok-mcp",
        "expected_tool_namespace": "tiktok-mcp",
        "onboard_check": {
            "type": "mcp_namespace_probe",
            "fail_fast": True,
            "success_source_derives": ["current_account", "advertiser_info"],
            "unavailable_status": "mcp_namespace_unavailable",
            "message": "Main session must expose the TikTok MCP namespace before report pulls start.",
        },
        "namespace_fail_fast": True,
    })
    steps.append({
        "id": "current_account",
        "phase": "bootstrap",
        "tool": "local:bootstrap_alias.current_account",
        "required": True,
        "output": "sources/current_account.json",
        "depends_on": ["mcp_ready"],
        "params": {"derive_from": "mcp_ready", "fields": ["name", "currency", "timezone", "industry", "status", "country"]},
        "pagination": {"mode": "single", "expected_total_max": 1},
    })
    steps.append({
        "id": "advertiser_info",
        "phase": "bootstrap",
        "tool": "local:bootstrap_alias.advertiser_info",
        "required": True,
        "output": "sources/advertiser_info.json",
        "depends_on": ["mcp_ready"],
        "params": {"derive_from": "mcp_ready"},
        "pagination": {"mode": "single", "expected_total_max": 1},
    })

    # ── classification ──────────────────────────────────────────────
    steps.append(_report_step(
        source_id="classification_campaigns",
        phase="classification",
        advertiser_id=advertiser_id,
        data_level="AUCTION_CAMPAIGN",
        dimensions=["campaign_id"],
        metrics=_lean_metrics(CAMPAIGN_ATTR_METRICS),
        start_date=start_date,
        end_date=end_date,
        output="sources/classification_campaigns.json",
        depends_on=["mcp_ready"],
        required=classification_required,
        retry_ladder=_main_retry_ladder(["campaign_id"], CAMPAIGN_ATTR_METRICS),
        pagination={"mode": "single", "expected_total_max": CLASSIFICATION_TOP_N, "sample": "top_spend"},
        page_size=CLASSIFICATION_TOP_N,
        note="Classification seed only: top spend sample, capped at 50 rows.",
    ))

    steps.append(_report_step(
        source_id="classification_adgroups",
        phase="classification",
        advertiser_id=advertiser_id,
        data_level="AUCTION_ADGROUP",
        dimensions=["adgroup_id"],
        metrics=_lean_metrics(ADGROUP_ATTR_METRICS),
        start_date=start_date,
        end_date=end_date,
        output="sources/classification_adgroups.json",
        depends_on=["mcp_ready"],
        required=classification_required,
        retry_ladder=_main_retry_ladder(["adgroup_id"], ADGROUP_ATTR_METRICS),
        pagination={"mode": "single", "expected_total_max": CLASSIFICATION_TOP_N, "sample": "top_spend"},
        page_size=CLASSIFICATION_TOP_N,
        note="Classification seed only: top spend sample, capped at 50 rows.",
    ))

    steps.append(_report_step(
        source_id="classification_ads",
        phase="classification",
        advertiser_id=advertiser_id,
        data_level="AUCTION_AD",
        dimensions=["ad_id"],
        metrics=_lean_metrics(AD_ATTR_METRICS),
        start_date=start_date,
        end_date=end_date,
        output="sources/classification_ads.json",
        depends_on=["mcp_ready"],
        required=classification_required,
        retry_ladder=_main_retry_ladder(["ad_id"], AD_ATTR_METRICS),
        pagination={"mode": "single", "expected_total_max": CLASSIFICATION_TOP_N, "sample": "top_spend"},
        page_size=CLASSIFICATION_TOP_N,
        note="Classification seed only: top spend sample, capped at 50 rows.",
    ))

    steps.append(_report_step(
        source_id="classification_ad_v2_insights",
        phase="classification",
        advertiser_id=advertiser_id,
        data_level="AUCTION_AD",
        dimensions=["ad_id_v2"],
        metrics=_lean_metrics(_compatible_attrs("classification_ad_v2_insights", AD_V2_ATTR_METRICS)),
        start_date=start_date,
        end_date=end_date,
        output="sources/classification_ad_v2_insights.json",
        depends_on=["mcp_ready"],
        required=classification_required,
        retry_ladder=_main_retry_ladder(["ad_id_v2"], _compatible_attrs("classification_ad_v2_insights", AD_V2_ATTR_METRICS)),
        pagination={"mode": "single", "expected_total_max": CLASSIFICATION_TOP_N, "sample": "top_spend"},
        page_size=CLASSIFICATION_TOP_N,
        note="Classification seed only: top spend sample, capped at 50 rows.",
    ))

    # app_list
    steps.append({
        "id": "app_list",
        "phase": "classification",
        "tool": "app_list_get",
        "required": classification_required,
        "output": "sources/app_list.json",
        "depends_on": ["mcp_ready"],
        "params": {"advertiser_id": advertiser_id},
        "pagination": {"mode": "single", "expected_total_max": 100},
    })

    # catalog_list
    if bc_id:
        steps.append({
            "id": "catalog_list",
            "phase": "classification",
            "tool": "catalog_get",
            "required": classification_required,
            "output": "sources/catalog_list.json",
            "depends_on": ["mcp_ready"],
            "params": {"bc_id": bc_id},
            "pagination": {"mode": "single", "expected_total_max": 100},
        })

    # smart_plus_ads
    steps.append({
        "id": "smart_plus_ads",
        "phase": "classification",
        "tool": "smart_plus_ad_get",
        "required": True,
        "output": "sources/smart_plus_ads.json",
        "depends_on": ["mcp_ready"],
        "params": {"advertiser_id": advertiser_id, "page_size": CLASSIFICATION_TOP_N},
        "pagination": {"mode": "paginated", "page_size": CLASSIFICATION_TOP_N},
        "capability": "landing_app_paths",
        "note": "Report Smart+ enrichment source: pull all Smart+ pages once; user type and landing/app analysis both reuse this source.",
    })

    # ── local_classification ────────────────────────────────────────
    steps.append({
        "id": "user_type_evidence",
        "phase": "local_classification",
        "tool": "local:classify_user_type.build_user_type_report",
        "required": True,
        "output": "sources/user_type_evidence.json",
        "depends_on": (
            ["classification_ads", "classification_ad_v2_insights", "app_list", "catalog_list", "smart_plus_ads"]
            if not use_cached_user_type
            else ["mcp_ready"]
        ),
        "params": {},
        "pagination": {"mode": "single"},
    })
    steps.append({
        "id": "user_type",
        "phase": "local_classification",
        "tool": "local:classify_user_type.build_user_type_report",
        "required": True,
        "output": "user_type.json",
        "depends_on": ["user_type_evidence"] if not use_cached_user_type else ["mcp_ready"],
        "params": {},
        "pagination": {"mode": "single"},
    })

    # ── preset ──────────────────────────────────────────────────────
    steps.append({
        "id": "metric_preset",
        "phase": "preset",
        "tool": "local:metric_probe.recommend_metric_preset",
        "required": True,
        "output": "metric_preset.json",
        "depends_on": ["user_type"],
        "params": {},
        "pagination": {"mode": "single"},
    })

    if depth in DEPTH_METRIC_PROBE:
        steps.append({
            "id": "metric_probe_results",
            "phase": "preset",
            "tool": "report_integrated_get",
            "required": True,
            "output": "sources/metric_probe_results.json",
            "depends_on": ["metric_preset"],
            "params": _report_params(
                advertiser_id,
                "AUCTION_ADVERTISER",
                ["advertiser_id"],
                _dedupe(LEAN_METRICS + ["result"]),
                start_date,
                end_date,
            ),
            "pagination": {"mode": "single"},
            "metric_probe_template": {
                "report_type": "BASIC",
                "data_level": "AUCTION_ADVERTISER",
                "dimensions": ["advertiser_id"],
                "metrics_from": "metric_preset.json groups expanded via metric_probe.BASE_METRICS",
                "user_adjustments_from": "metric_confirmation.json user_adjustments.add_metrics",
                "cache_write_rule": "probe user-added metrics once before writing account profile cache",
                "page": 1,
                "page_size": 1000,
            },
            "retry_ladder": [
                {"dimensions": ["advertiser_id"], "metrics": _dedupe(LEAN_METRICS + ["result"])},
                {"dimensions": ["advertiser_id"], "metrics": LEAN_METRICS},
            ],
            "note": "Run traffic check first, then probe each metric group from metric_preset.json; store grouped raw results.",
        })

    # ── report_data ─────────────────────────────────────────────────
    report_specs = [
        ("current_advertiser_insights", "AUCTION_ADVERTISER", ["advertiser_id"], ADVERTISER_ATTR_METRICS, {"mode": "single", "expected_total_max": 1}),
        ("current_campaigns", "AUCTION_CAMPAIGN", ["campaign_id"], CAMPAIGN_ATTR_METRICS, {"mode": "paginated", "page_size": 1000, "max_pages": insight_max_pages}),
        ("current_adgroups", "AUCTION_ADGROUP", ["adgroup_id"], ADGROUP_ATTR_METRICS, {"mode": "paginated", "page_size": 1000, "max_pages": insight_max_pages}),
        ("current_ads", "AUCTION_AD", ["ad_id"], AD_ATTR_METRICS, {"mode": "paginated", "page_size": 1000, "max_pages": insight_max_pages}),
        ("current_ad_v2_insights", "AUCTION_AD", ["ad_id_v2"], AD_V2_ATTR_METRICS, {"mode": "paginated", "page_size": 1000, "max_pages": insight_max_pages}),
    ]
    allowed_current = CURRENT_SOURCES_BY_DEPTH.get(depth, CURRENT_SOURCES_BY_DEPTH["standard"])
    for source_id, data_level, dimensions, attrs, pagination in report_specs:
        if source_id not in allowed_current:
            continue
        compatible_attrs = _compatible_attrs(source_id, attrs)
        compatibility_profile = (
            "adgroup"
            if source_id == "current_adgroups"
            else ("ad_v2" if source_id == "current_ad_v2_insights" else "standard")
        )
        steps.append(_report_step(
            source_id=source_id,
            phase="report_data",
            advertiser_id=advertiser_id,
            data_level=data_level,
            dimensions=dimensions,
            metrics=_main_metrics(compatible_attrs),
            start_date=start_date,
            end_date=end_date,
            output=f"sources/{source_id}.json",
            depends_on=["metric_preset"],
            pagination=pagination,
            retry_ladder=_main_retry_ladder(dimensions, compatible_attrs),
            metric_source_policy=_preset_metric_policy(source_id, compatibility_profile),
        ))

    if previous_start_date and previous_end_date:
        previous_specs = [
            ("previous_advertiser_insights", "AUCTION_ADVERTISER", ["advertiser_id"], ADVERTISER_ATTR_METRICS, {"mode": "single", "expected_total_max": 1}),
            ("previous_campaigns", "AUCTION_CAMPAIGN", ["campaign_id"], CAMPAIGN_ATTR_METRICS, {"mode": "paginated", "page_size": 1000, "max_pages": insight_max_pages}),
            ("previous_adgroups", "AUCTION_ADGROUP", ["adgroup_id"], ADGROUP_ATTR_METRICS, {"mode": "paginated", "page_size": 1000, "max_pages": insight_max_pages}),
            ("previous_ads", "AUCTION_AD", ["ad_id"], AD_ATTR_METRICS, {"mode": "paginated", "page_size": 1000, "max_pages": insight_max_pages}),
        ]
        allowed_previous = PREVIOUS_SOURCES_BY_DEPTH.get(depth, set())
        for source_id, data_level, dimensions, attrs, pagination in previous_specs:
            if source_id not in allowed_previous:
                continue
            compatible_attrs = _compatible_attrs(source_id, attrs)
            compatibility_profile = "adgroup" if source_id == "previous_adgroups" else "standard"
            steps.append(_report_step(
                source_id=source_id,
                phase="report_data",
                advertiser_id=advertiser_id,
                data_level=data_level,
                dimensions=dimensions,
                metrics=_main_metrics(compatible_attrs),
                start_date=previous_start_date,
                end_date=previous_end_date,
                output=f"sources/{source_id}.json",
                depends_on=["metric_preset"],
                pagination=pagination,
                retry_ladder=_main_retry_ladder(dimensions, compatible_attrs),
                metric_source_policy=_preset_metric_policy(source_id, compatibility_profile),
            ))

    # ── enrichment ──────────────────────────────────────────────────
    enrichment_sources = DEPTH_ENRICHMENT.get(depth, [])

    if "audience_country" in enrichment_sources:
        steps.append(_audience_step(
            source_id="audience_country",
            advertiser_id=advertiser_id,
            candidate_dimensions=[["advertiser_id", "country_code"], ["advertiser_id", "country"]],
            start_date=start_date,
            end_date=end_date,
            expected_total_max=250,
        ))

    if "audience_age_gender" in enrichment_sources:
        steps.append(_audience_step(
            source_id="audience_age_gender",
            advertiser_id=advertiser_id,
            candidate_dimensions=[
                ["advertiser_id", "age", "gender"],
                ["advertiser_id", "age"],
                ["advertiser_id", "gender"],
            ],
            start_date=start_date,
            end_date=end_date,
            expected_total_max=50,
        ))

    if "audience_placement" in enrichment_sources:
        steps.append(_audience_step(
            source_id="audience_placement",
            advertiser_id=advertiser_id,
            candidate_dimensions=[
                ["advertiser_id", "placement"],
                ["advertiser_id", "placement_type"],
                ["advertiser_id", "site_id"],
            ],
            start_date=start_date,
            end_date=end_date,
            expected_total_max=10,
        ))

    if "audience_device" in enrichment_sources:
        steps.append(_audience_step(
            source_id="audience_device",
            advertiser_id=advertiser_id,
            candidate_dimensions=[
                ["advertiser_id", "platform"],
                ["advertiser_id", "device_platform"],
                ["advertiser_id", "device_os"],
                ["advertiser_id", "operating_system"],
            ],
            start_date=start_date,
            end_date=end_date,
            expected_total_max=5,
            metrics=AUDIENCE_CORE_METRICS,
        ))

    if "landing_pages_report" in enrichment_sources:
        landing_metrics = _dedupe(LEAN_METRICS + LANDING_METRICS + AD_ATTR_METRICS)
        landing_step = _report_step(
            source_id="landing_pages_report",
            phase="enrichment",
            advertiser_id=advertiser_id,
            data_level="AUCTION_AD",
            dimensions=["ad_id"],
            metrics=landing_metrics,
            start_date=start_date,
            end_date=end_date,
            output="sources/landing_pages_report.json",
            depends_on=["current_ads"],
            required=False,
            pagination={"mode": "paginated", "page_size": 1000, "max_pages": landing_max_pages},
            retry_ladder=[
                {"dimensions": ["ad_id"], "metrics": landing_metrics},
                {"dimensions": ["ad_id"], "metrics": _lean_metrics(AD_ATTR_METRICS)},
                {"dimensions": ["ad_id"], "metrics": _lean_metrics()},
            ],
            note="Motata parity landing-pages standalone fallback.",
        )
        landing_step["compatibility_notes"] = {
            "known_unsupported_metrics_excluded_by_default": KNOWN_UNSUPPORTED_LANDING_METRICS,
            "reason": "TikTok /report/integrated/get rejected these fields during live W49/W50 compatibility checks.",
        }
        steps.append(landing_step)

    if "targeted_creative_retention_raw" in enrichment_sources:
        retention_with_attrs = _dedupe(RETENTION_METRICS + AD_ATTR_METRICS)
        steps.append(_report_step(
            source_id="targeted_creative_retention_raw",
            phase="enrichment",
            advertiser_id=advertiser_id,
            data_level="AUCTION_AD",
            dimensions=["ad_id"],
            metrics=retention_with_attrs,
            start_date=start_date,
            end_date=end_date,
            output="sources/targeted_creative_retention_raw.json",
            depends_on=["current_ads"],
            required=False,
            retry_ladder=[
                {"dimensions": ["ad_id"], "metrics": retention_with_attrs},
                {"dimensions": ["ad_id"], "metrics": RETENTION_METRICS},
            ],
            note="Motata parity targeted creative retention report.",
        ))

    structure_specs = [
        (
            "campaign_structure",
            "campaign_get",
            "sources/campaign_structure.json",
            "current_campaigns",
            {"campaign_ids": ["__top_campaign_ids__"]},
            CAMPAIGN_STRUCTURE_FIELDS,
        ),
        (
            "adgroup_structure",
            "adgroup_get",
            "sources/adgroup_structure.json",
            "current_adgroups",
            {"adgroup_ids": ["__top_adgroup_ids__"]},
            ADGROUP_STRUCTURE_FIELDS,
        ),
        (
            "ad_structure",
            "ad_get",
            "sources/ad_structure.json",
            "current_ads",
            {"ad_ids": ["__top_ad_ids__"]},
            AD_STRUCTURE_FIELDS,
        ),
    ]
    for source_id, tool, output, dependency, filtering, fields in structure_specs:
        if source_id not in enrichment_sources:
            continue
        structure_limit = DEPTH_STRUCTURE_LIMIT.get(depth)
        params = {
            "advertiser_id": advertiser_id,
            "fields": fields,
            "page": 1,
            "page_size": structure_limit or 1000,
        }
        pagination: dict[str, Any] = (
            {"mode": "paginated", "page_size": 1000, "max_pages": insight_max_pages, "structure_mode": "all"}
            if structure_limit is None
            else {"mode": "single", "expected_total_max": structure_limit, "sample": "top_spend", "structure_mode": "top"}
        )
        if structure_limit is not None:
            params["filtering"] = filtering
        steps.append({
            "id": source_id,
            "phase": "enrichment",
            "tool": tool,
            "required": False,
            "output": output,
            "depends_on": [dependency],
            "params": params,
            "pagination": pagination,
            "note": (
                f"Motata parity top structure pull: expand placeholder IDs from {dependency} top spend rows before execution."
                if structure_limit is not None
                else "Motata parity deep structure pull: paginate all accessible objects."
            ),
        })

    if "activity_changelog" in enrichment_sources:
        activity_start_time = f"{start_date} 00:00:00"
        activity_end_time = f"{end_date} 23:59:59"
        activity_params = {"advertiser_id": advertiser_id,
                           "start_time": activity_start_time,
                           "end_time": activity_end_time,
                           "timezone": "Asia/Shanghai"}
        activity_strategy = "broad_changelog" if depth == "deep" else "targeted_top_objects_changelog"
        if depth != "deep":
            activity_params.update({
                "object_type": "__targeted_activity_object_type__",
                "object_ids": ["__top_activity_object_ids__"],
                "operation_types": ["CREATE", "STATUS", "UPDATE"],
            })
        steps.append({
            "id": "activity_changelog",
            "phase": "enrichment",
            "tool": "changelog_task_create",
            "required": True,
            "output": "sources/activity_changelog.json",
            "depends_on": ["metric_preset"],
            "params": activity_params,
            "pagination": {
                "mode": "single",
                "activity_strategy": activity_strategy,
                "target_count_per_level": 8 if depth == "fast" else (12 if depth == "standard" else 20),
                "max_object_ids_per_task": 20,
            },
            "async_flow": [
                "changelog_task_create",
                "changelog_task_check",
                "changelog_task_download",
            ],
            "note": (
                "Motata parity broad changelog for deep depth."
                if depth == "deep"
                else "Motata parity targeted changelog: execute once per level/batch after expanding top campaign/adgroup/ad object IDs."
            ),
        })

    activity_report_specs = [
        ("activity_targeted_campaign_insights", "AUCTION_CAMPAIGN", ["campaign_id"], CAMPAIGN_ATTR_METRICS, {"campaign_ids": ["__activity_campaign_ids__"]}),
        ("activity_targeted_adgroup_insights", "AUCTION_ADGROUP", ["adgroup_id"], ADGROUP_ATTR_METRICS, {"adgroup_ids": ["__activity_adgroup_ids__"]}),
        ("activity_targeted_ad_insights", "AUCTION_AD", ["ad_id"], AD_ATTR_METRICS, {"ad_ids": ["__activity_ad_ids__"]}),
    ]
    if depth == "fast":
        activity_report_specs = [spec for spec in activity_report_specs if spec[0] != "activity_targeted_adgroup_insights"]
    for source_id, data_level, dimensions, attrs, filtering in activity_report_specs:
        if source_id not in enrichment_sources:
            continue
        steps.append(_report_step(
            source_id=source_id,
            phase="enrichment",
            advertiser_id=advertiser_id,
            data_level=data_level,
            dimensions=dimensions,
            metrics=_main_metrics(attrs),
            start_date=start_date,
            end_date=end_date,
            output=f"sources/{source_id}.json",
            depends_on=["activity_changelog", "metric_preset"],
            required=False,
            filtering=filtering,
            retry_ladder=_main_retry_ladder(dimensions, attrs),
            note="Template report: expand placeholder ID filters from activity_changelog before execution.",
        ))

    activity_daily_specs = [
        ("activity_daily_campaign_breakdown", "AUCTION_CAMPAIGN", ["campaign_id", "stat_time_day"], CAMPAIGN_ATTR_METRICS, {"campaign_ids": ["__activity_campaign_ids__"]}),
        ("activity_daily_adgroup_breakdown", "AUCTION_ADGROUP", ["adgroup_id", "stat_time_day"], ADGROUP_ATTR_METRICS, {"adgroup_ids": ["__activity_adgroup_ids__"]}),
        ("activity_daily_ad_breakdown", "AUCTION_AD", ["ad_id", "stat_time_day"], AD_ATTR_METRICS, {"ad_ids": ["__activity_ad_ids__"]}),
    ]
    if depth == "fast":
        activity_daily_specs = [spec for spec in activity_daily_specs if spec[0] != "activity_daily_adgroup_breakdown"]
    daily_metrics = _dedupe(LEAN_METRICS + ["cost_per_result", "result_rate"])
    for source_id, data_level, dimensions, attrs, filtering in activity_daily_specs:
        if source_id not in enrichment_sources:
            continue
        steps.append(_report_step(
            source_id=source_id,
            phase="enrichment",
            advertiser_id=advertiser_id,
            data_level=data_level,
            dimensions=dimensions,
            metrics=_dedupe(daily_metrics + attrs),
            start_date=start_date,
            end_date=end_date,
            output=f"sources/{source_id}.json",
            depends_on=["activity_changelog", "metric_preset"],
            required=False,
            filtering=filtering,
            retry_ladder=[
                {"dimensions": dimensions, "metrics": _dedupe(daily_metrics + attrs)},
                {"dimensions": dimensions, "metrics": daily_metrics},
                {"dimensions": dimensions, "metrics": LEAN_METRICS},
            ],
            note="Template daily report: expand placeholder ID filters from activity_changelog before execution.",
        ))

    if "ad_details_for_enrichment" in enrichment_sources:
        steps.append({
            "id": "ad_details_for_enrichment",
            "phase": "enrichment",
            "tool": "ad_get",
            "required": False,
            "output": "sources/ad_details_for_enrichment.json",
            "depends_on": ["current_ads"],
            "params": {
                "advertiser_id": advertiser_id,
                "fields": AD_STRUCTURE_FIELDS,
                "filtering": {"ad_ids": ["__top_ad_ids__"]},
                "page": 1,
                "page_size": DEPTH_STRUCTURE_LIMIT.get(depth) or 100,
            },
            "pagination": {
                "mode": "single",
                "expected_total_max": DEPTH_STRUCTURE_LIMIT.get(depth) or 100,
                "sample": "top_spend",
                "structure_mode": "top",
            },
            "note": "Creative preview seed: expand __top_ad_ids__ from current_ads top spend rows before execution.",
        })

    if "creative_preview_images" in enrichment_sources:
        steps.append({
            "id": "creative_preview_images",
            "phase": "enrichment",
            "tool": "file_image_ad_info_get",
            "required": False,
            "output": "sources/creative_preview_images.json",
            "depends_on": ["ad_details_for_enrichment"],
            "params": {"advertiser_id": advertiser_id, "image_ids": ["__image_ids_from_ad_details_for_enrichment__"]},
            "pagination": {"mode": "single", "expected_total_max": 100},
            "note": "Creative preview media: collect unique image_ids from ad_details_for_enrichment rows; batch up to 100 IDs. If TikTok reports insufficient permissions for some images, split and retry smaller batches or single IDs, then mark failed IDs permission_denied instead of dropping all preview media.",
        })

    if "creative_preview_videos" in enrichment_sources:
        steps.append({
            "id": "creative_preview_videos",
            "phase": "enrichment",
            "tool": "file_video_ad_info_get",
            "required": False,
            "output": "sources/creative_preview_videos.json",
            "depends_on": ["ad_details_for_enrichment"],
            "params": {"advertiser_id": advertiser_id, "video_ids": ["__video_ids_from_ad_details_for_enrichment__"]},
            "pagination": {"mode": "single", "expected_total_max": 60},
            "note": "Creative preview media: collect unique video_id values from ad_details_for_enrichment rows; batch up to 60 IDs. If a batch partially fails, split and retry smaller batches or single IDs, then mark failed IDs permission_denied instead of dropping all preview media.",
        })

    if "creative_preview_spark_posts" in enrichment_sources:
        steps.append({
            "id": "creative_preview_spark_posts",
            "phase": "enrichment",
            "tool": "tt_video_list_get",
            "required": False,
            "output": "sources/creative_preview_spark_posts.json",
            "depends_on": ["ad_details_for_enrichment"],
            "params": {
                "advertiser_id": advertiser_id,
                "keyword": "__spark_item_ids_from_ad_details_for_enrichment__",
                "item_types": ["VIDEO", "CAROUSEL"],
                "page": 1,
                "page_size": 50,
            },
            "pagination": {"mode": "per_id_or_paginated", "expected_total_max": 100},
            "note": "Creative preview Spark seed: collect item_id/tiktok_item_id/spark_post_id from ad details. Prefer exact keyword=item_id lookup per ID; if empty, page through authorized Spark posts and match item IDs. Also fetch CAROUSEL item_type when VIDEO returns no match.",
        })

    if "creative_preview_catalog_products" in enrichment_sources:
        steps.append({
            "id": "creative_preview_catalog_products",
            "phase": "enrichment",
            "tool": "catalog_product_get",
            "required": False,
            "output": "sources/creative_preview_catalog_products.json",
            "depends_on": ["smart_plus_ads", "ad_details_for_enrichment"],
            "params": {
                "bc_id": bc_id or "__catalog_authorized_bc_id_from_creative_details__",
                "catalog_id": "__catalog_id_from_creative_details__",
                "product_ids": ["__product_ids_from_creative_details__"],
                "page": 1,
                "page_size": 100,
            },
            "pagination": {"mode": "per_catalog_batch", "expected_total_max": 100},
            "note": "Creative preview catalog seed: group catalog_id/product_ids from Smart+ and ad details, then call catalog_product_get per catalog. If only product_set_id exists, run product set source first.",
        })

    if "creative_preview_catalog_sets" in enrichment_sources:
        steps.append({
            "id": "creative_preview_catalog_sets",
            "phase": "enrichment",
            "tool": "catalog_set_get",
            "required": False,
            "output": "sources/creative_preview_catalog_sets.json",
            "depends_on": ["smart_plus_ads", "ad_details_for_enrichment"],
            "params": {
                "bc_id": bc_id or "__catalog_authorized_bc_id_from_creative_details__",
                "catalog_id": "__catalog_id_from_creative_details__",
                "product_set_id": "__product_set_id_from_creative_details__",
                "return_product_count": False,
            },
            "pagination": {"mode": "per_catalog_or_set", "expected_total_max": 100},
            "note": "Creative preview catalog-set seed: resolve product_set_id metadata for catalog ads; pair with catalog_product_get when product IDs are available.",
        })

    # Derived enrichment steps (local compute, no MCP call)
    derived_enrichment = [
        ("apps", "local:run_report.build_apps_summary",
         ["user_type", "current_campaigns", "current_adgroups", "current_ads"]),
        ("landing_app_paths", "local:landing_app_analyzer.analyze_landing_app_paths",
         ["current_ads", "current_ad_v2_insights", "smart_plus_ads", "landing_pages_report"]),
        ("creative_previews", "local:creative_enrichment.build_creative_previews",
         ["current_ads", "smart_plus_ads", "ad_details_for_enrichment", "creative_preview_images", "creative_preview_videos",
          "creative_preview_spark_posts", "creative_preview_catalog_products", "creative_preview_catalog_sets"]),
        ("creative_retention", "local:creative_enrichment.build_creative_retention",
         ["current_ads"]),
        ("targeted_creative_retention", "local:creative_enrichment.build_creative_retention",
         ["current_ads", "targeted_creative_retention_raw"]),
        ("activity_targeted_insights", "local:activity_analysis.run_activity_analysis",
         ["activity_changelog"]),
        ("activity_daily_breakdown", "local:activity_analysis.run_activity_analysis",
         ["activity_changelog"]),
        ("activity_factors", "local:activity_analysis.run_activity_analysis",
         ["activity_changelog"]),
    ]

    for source_id, tool, deps in derived_enrichment:
        if source_id in enrichment_sources or source_id == "landing_app_paths":
            steps.append({
                "id": source_id,
                "phase": "enrichment",
                "tool": tool,
                "required": source_id in PHASE_REQUIRED_SOURCES.get("enrichment", []),
                "output": f"sources/{source_id}.json",
                "depends_on": deps,
                "params": {},
                "pagination": {"mode": "single"},
            })

    # Preserve append order within each phase. The append order is intentional
    # and follows dependencies; sorting alphabetically can put a child step
    # before the source it depends on.
    steps.sort(key=lambda s: phase_index.get(s["phase"], 99))
    steps = enrich_steps_for_agent_tasks(steps, depth)
    for idx, step in enumerate(steps, start=1):
        step["order"] = idx

    step_ids = {step["id"] for step in steps}
    subagent_count = sum(1 for s in steps if s.get("preferred_backend") == SUBAGENT_BACKEND)
    native_count = sum(1 for s in steps if s.get("preferred_backend") == NATIVE_BACKEND)
    execution_backend = SUBAGENT_BACKEND if subagent_count > 0 else NATIVE_BACKEND

    required_step_ids = {step["id"] for step in steps if step.get("required")}
    plan: dict[str, Any] = {
        "run_id": run_id,
        "advertiser_id": advertiser_id,
        "depth": depth,
        "planner_version": PLANNER_VERSION,
        "account_cache_mode": "user_type_account_cache" if use_cached_user_type else "",
        "cached_user_type": cached_user_type,
        "plan_fingerprint": build_plan_fingerprint(
            capability="full_report",
            advertiser_id=advertiser_id,
            start_date=start_date,
            end_date=end_date,
            previous_start_date=previous_start_date,
            previous_end_date=previous_end_date,
            depth=depth,
            bc_id=bc_id,
            user_type=cached_user_type if use_cached_user_type else "",
            account_cache_mode="user_type_account_cache" if use_cached_user_type else "",
        ),
        "generated_at": now,
        "execution_backend": execution_backend,
        "preferred_backend": execution_backend,
        "backend_reason": "report_parallel" if execution_backend == SUBAGENT_BACKEND else "light_query",
        "backend_fallbacks": [],
        "current_window": {"start_date": start_date, "end_date": end_date},
        "previous_window": (
            {"start_date": previous_start_date, "end_date": previous_end_date}
            if previous_start_date and previous_end_date
            else None
        ),
        "phase_order": PHASE_ORDER,
        "phase_required_sources": {
            phase: [source for source in sources if source in step_ids and source in required_step_ids]
            for phase, sources in PHASE_REQUIRED_SOURCES.items()
            if any(source in step_ids and source in required_step_ids for source in sources)
        },
        "steps": steps,
    }
    return plan


def build_gmv_max_plan(
    advertiser_id: str,
    start_date: str,
    end_date: str,
    previous_start_date: str | None = None,
    previous_end_date: str | None = None,
    depth: str = "standard",
    bc_id: str = "",
) -> dict[str, Any]:
    depth = "standard" if depth in {"quick", "fast"} else depth
    run_id = f"{advertiser_id}_{start_date}_{end_date}_gmv_max_{depth}"
    now = datetime.now(timezone.utc).isoformat()
    gmv_phase_order = [
        "bootstrap",
        "gmv_max_discovery",
        "gmv_max_report_data",
        "gmv_max_enrichment",
        "analysis",
        "audit",
    ]
    phase_index = {phase: idx for idx, phase in enumerate(gmv_phase_order)}
    steps: list[dict[str, Any]] = [
        {
            "id": "mcp_ready",
            "phase": "bootstrap",
            "tool": "advertiser_info_get",
            "required": True,
            "output": "sources/mcp_ready.json",
            "depends_on": [],
            "params": {"advertiser_ids": [advertiser_id]},
            "pagination": {"mode": "single", "expected_total_max": 1},
            "mcp_namespace": "tiktok-mcp",
            "expected_tool_namespace": "tiktok-mcp",
            "namespace_fail_fast": True,
        },
        {
            "id": "current_account",
            "phase": "bootstrap",
            "tool": "local:bootstrap_alias.current_account",
            "required": True,
            "output": "sources/current_account.json",
            "depends_on": ["mcp_ready"],
            "params": {"derive_from": "mcp_ready", "fields": ["name", "currency", "timezone", "industry", "status", "country"]},
            "pagination": {"mode": "single", "expected_total_max": 1},
        },
        {
            "id": "advertiser_info",
            "phase": "bootstrap",
            "tool": "local:bootstrap_alias.advertiser_info",
            "required": True,
            "output": "sources/advertiser_info.json",
            "depends_on": ["mcp_ready"],
            "params": {"derive_from": "mcp_ready"},
            "pagination": {"mode": "single", "expected_total_max": 1},
        },
        {
            "id": "gmv_max_stores",
            "phase": "gmv_max_discovery",
            "tool": "gmv_max_store_list_get",
            "required": True,
            "output": "sources/gmv_max_stores.json",
            "depends_on": ["mcp_ready"],
            "params": {"advertiser_id": advertiser_id, "page": 1, "page_size": 100},
            "pagination": {"mode": "paginated", "page_size": 100, "filter_after": "is_gmv_max_available=true"},
            "note": "Extract store_id, store_authorized_bc_id, and store_name. If no available GMV Max store exists, mark GMV Max coverage unavailable.",
        },
        {
            "id": "gmv_max_campaigns_product",
            "phase": "gmv_max_discovery",
            "tool": "gmv_max_campaign_get",
            "required": True,
            "output": "sources/gmv_max_campaigns_product.json",
            "depends_on": ["gmv_max_stores"],
            "params": {
                "advertiser_id": advertiser_id,
                "store_ids": ["__gmv_max_store_ids__"],
                "gmv_max_promotion_types": ["PRODUCT_GMV_MAX"],
                "page": 1,
                "page_size": 1000,
            },
            "pagination": {"mode": "paginated", "page_size": 1000},
            "gmv_max_enum_policy": {
                "discovery_values": ["PRODUCT_GMV_MAX", "LIVE_GMV_MAX"],
                "report_filter_values": ["PRODUCT", "LIVE"],
            },
        },
        {
            "id": "gmv_max_campaigns_live",
            "phase": "gmv_max_discovery",
            "tool": "gmv_max_campaign_get",
            "required": False,
            "output": "sources/gmv_max_campaigns_live.json",
            "depends_on": ["gmv_max_stores"],
            "params": {
                "advertiser_id": advertiser_id,
                "store_ids": ["__gmv_max_store_ids__"],
                "gmv_max_promotion_types": ["LIVE_GMV_MAX"],
                "page": 1,
                "page_size": 1000,
            },
            "pagination": {"mode": "paginated", "page_size": 1000},
            "note": "Optional unless the user asks for Live GMV Max.",
        },
    ]

    product_filter = {
        "gmv_max_promotion_type": "PRODUCT",
        "campaign_ids": ["__product_gmv_max_campaign_ids__"],
    }
    creative_filter = {
        "gmv_max_promotion_type": "PRODUCT",
        "campaign_ids": ["__product_gmv_max_campaign_ids__"],
        "item_group_ids": ["__item_group_ids_from_current_gmv_max_product__"],
    }
    current_specs = [
        ("current_gmv_max_account", ["advertiser_id"], GMV_MAX_ACCOUNT_METRICS, None),
        ("current_gmv_max_campaign", ["campaign_id"], GMV_MAX_CAMPAIGN_METRICS, product_filter),
        ("current_gmv_max_campaign_day", ["campaign_id", "stat_time_day"], GMV_MAX_CAMPAIGN_METRICS, product_filter),
        ("current_gmv_max_product", ["item_group_id"], GMV_MAX_PRODUCT_METRICS, product_filter),
        ("current_gmv_max_creative", ["campaign_id", "item_group_id", "item_id"], GMV_MAX_CREATIVE_METRICS, creative_filter),
        ("current_gmv_max_duration", ["duration"], GMV_MAX_DURATION_METRICS, product_filter),
    ]
    for source_id, dimensions, metrics, filtering in current_specs:
        steps.append(_gmv_max_report_step(
            source_id=source_id,
            advertiser_id=advertiser_id,
            dimensions=dimensions,
            metrics=metrics,
            start_date=start_date,
            end_date=end_date,
            depends_on=["gmv_max_campaigns_product"],
            filtering=filtering,
            note="Verify gmv_max_report_get schema with tool_get before execution; keep metrics level-specific.",
        ))

    if previous_start_date and previous_end_date:
        previous_specs = [
            ("previous_gmv_max_account", ["advertiser_id"], GMV_MAX_ACCOUNT_METRICS, None),
            ("previous_gmv_max_campaign", ["campaign_id"], GMV_MAX_CAMPAIGN_METRICS, product_filter),
            ("previous_gmv_max_campaign_day", ["campaign_id", "stat_time_day"], GMV_MAX_CAMPAIGN_METRICS, product_filter),
            ("previous_gmv_max_product", ["item_group_id"], GMV_MAX_PRODUCT_METRICS, product_filter),
            ("previous_gmv_max_creative", ["campaign_id", "item_group_id", "item_id"], GMV_MAX_CREATIVE_METRICS, creative_filter),
            ("previous_gmv_max_duration", ["duration"], GMV_MAX_DURATION_METRICS, product_filter),
        ]
        for source_id, dimensions, metrics, filtering in previous_specs:
            steps.append(_gmv_max_report_step(
                source_id=source_id,
                advertiser_id=advertiser_id,
                dimensions=dimensions,
                metrics=metrics,
                start_date=previous_start_date,
                end_date=previous_end_date,
                depends_on=["gmv_max_campaigns_product"],
                filtering=filtering,
                required=source_id in {"previous_gmv_max_account", "previous_gmv_max_campaign", "previous_gmv_max_creative"},
                note="Previous-period GMV Max report for period-over-period comparison.",
            ))

    enrichment_steps = [
        {
            "id": "gmv_max_campaign_item_previews",
            "phase": "gmv_max_enrichment",
            "tool": "campaign_gmv_max_info_get",
            "required": True,
            "output": "sources/gmv_max_campaign_item_previews.json",
            "depends_on": ["gmv_max_campaigns_product", "current_gmv_max_creative"],
            "params": {
                "advertiser_id": advertiser_id,
                "campaign_ids": ["__product_gmv_max_campaign_ids__"],
            },
            "pagination": {"mode": "per_campaign", "expected_total_max": 1000},
            "note": "Preferred preview source: map item_list[] item_id to video_info, preview_url, and identity_info. AUTO_SELECTION may return empty item_list.",
        },
        {
            "id": "gmv_max_store_products",
            "phase": "gmv_max_enrichment",
            "tool": "store_product_get",
            "required": True,
            "output": "sources/gmv_max_store_products.json",
            "depends_on": ["gmv_max_stores", "current_gmv_max_product", "current_gmv_max_creative"],
            "params": {
                "advertiser_id": advertiser_id,
                "bc_id": bc_id or "__store_authorized_bc_id__",
                "store_id": "__gmv_max_store_id__",
                "filtering": {
                    "item_group_ids": ["__item_group_ids_from_current_gmv_max_product_or_creative__"],
                    "ad_creation_eligible": "GMV_MAX",
                },
                "page": 1,
                "page_size": 10,
            },
            "pagination": {"mode": "per_store_item_group_batch", "page_size": 10},
            "note": "Store product identity enrichment. Batch item_group_ids at max 10 per request.",
        },
        {
            "id": "gmv_max_identity_video_info",
            "phase": "gmv_max_enrichment",
            "tool": "identity_video_info_get",
            "required": False,
            "output": "sources/gmv_max_identity_video_info.json",
            "depends_on": ["gmv_max_campaign_item_previews"],
            "params": {
                "advertiser_id": advertiser_id,
                "identity_type": "__identity_type__",
                "identity_id": "__identity_id__",
                "identity_authorized_bc_id": "__identity_authorized_bc_id_if_BC_AUTH_TT__",
                "item_ids": ["__item_ids_grouped_by_identity__"],
            },
            "pagination": {"mode": "per_identity_batch", "page_size": 20},
            "note": "Targeted preview refresh for CUSTOM_SELECTION rows. Group by identity tuple; batch at most 20 item_ids.",
        },
        {
            "id": "gmv_max_custom_anchor_videos",
            "phase": "gmv_max_enrichment",
            "tool": "gmv_max_custom_anchor_video_list_get",
            "required": False,
            "output": "sources/gmv_max_custom_anchor_videos.json",
            "depends_on": ["current_gmv_max_creative"],
            "params": {
                "advertiser_id": advertiser_id,
                "item_ids": ["__top_rendered_item_ids_missing_preview__"],
                "page": 1,
                "page_size": 100,
            },
            "pagination": {"mode": "targeted_optional", "expected_total_max": 100},
            "note": "Optional customized-post fallback. Zero hits are normal and should not degrade the report.",
        },
        {
            "id": "gmv_max_videos",
            "phase": "gmv_max_enrichment",
            "tool": "gmv_max_video_get",
            "required": False,
            "output": "sources/gmv_max_videos.json",
            "depends_on": ["current_gmv_max_creative"],
            "params": {
                "advertiser_id": advertiser_id,
                "keyword": "__top_rendered_item_ids_missing_preview__",
                "custom_posts_eligible": True,
                "page": 1,
                "page_size": 100,
            },
            "pagination": {"mode": "diagnostic_join_only", "expected_total_max": 100},
            "note": "Diagnostic source-pool query only. Do not use rows that cannot join back to report item_id. Do not default need_auth_code_video=true.",
        },
        {
            "id": "gmv_max_html_report",
            "phase": "analysis",
            "tool": "local:gmv_max.generate_html_report",
            "required": True,
            "output": "report.html",
            "depends_on": [
                "current_gmv_max_account",
                "current_gmv_max_campaign",
                "current_gmv_max_product",
                "current_gmv_max_creative",
                "gmv_max_campaign_item_previews",
                "gmv_max_store_products",
            ],
            "params": {"creative_limit": 40, "cache_images": True},
            "pagination": {"mode": "single"},
            "note": "Generate GMV Max HTML with Product / Item Group, Creative / Item Buckets, Product Card aggregate, and Data Quality sections.",
        },
        {
            "id": "gmv_max_report_audit",
            "phase": "audit",
            "tool": "local:gmv_max.audit_html_report",
            "required": True,
            "output": "audit.json",
            "depends_on": ["gmv_max_html_report"],
            "params": {},
            "pagination": {"mode": "single"},
            "note": "Audit GMV Max coverage, enum policy, creative dimensions, preview coverage, local image caching, and secret redaction.",
        },
    ]
    if depth in {"full", "deep"}:
        steps.extend(enrichment_steps)
    else:
        steps.extend([s for s in enrichment_steps if s["id"] not in {"gmv_max_custom_anchor_videos", "gmv_max_videos"}])

    steps.sort(key=lambda s: phase_index.get(s["phase"], 99))
    steps = enrich_steps_for_agent_tasks(steps, depth)
    for idx, step in enumerate(steps, start=1):
        step["order"] = idx

    step_ids = {step["id"] for step in steps}
    required_step_ids = {step["id"] for step in steps if step.get("required")}
    execution_backend = SUBAGENT_BACKEND if any(step.get("preferred_backend") == SUBAGENT_BACKEND for step in steps) else NATIVE_BACKEND
    return {
        "run_id": run_id,
        "advertiser_id": advertiser_id,
        "capability": "gmv_max_report",
        "report_mode": "gmv_max",
        "depth": depth,
        "planner_version": PLANNER_VERSION,
        "plan_fingerprint": build_plan_fingerprint(
            capability="gmv_max_report",
            advertiser_id=advertiser_id,
            start_date=start_date,
            end_date=end_date,
            previous_start_date=previous_start_date,
            previous_end_date=previous_end_date,
            depth=depth,
            bc_id=bc_id,
        ),
        "generated_at": now,
        "execution_backend": execution_backend,
        "preferred_backend": execution_backend,
        "backend_reason": "gmv_max_report_parallel" if execution_backend == SUBAGENT_BACKEND else "light_query",
        "backend_fallbacks": [],
        "current_window": {"start_date": start_date, "end_date": end_date},
        "previous_window": (
            {"start_date": previous_start_date, "end_date": previous_end_date}
            if previous_start_date and previous_end_date
            else None
        ),
        "phase_order": gmv_phase_order,
        "phase_required_sources": {
            phase: [
                step["id"]
                for step in steps
                if step.get("phase") == phase and step.get("id") in step_ids and step.get("id") in required_step_ids
            ]
            for phase in gmv_phase_order
            if any(step.get("phase") == phase and step.get("id") in required_step_ids for step in steps)
        },
        "gmv_max_contract": {
            "primary_data_plane": "gmv_max",
            "regular_auction_sources_required": False,
            "regular_auction_empty_is_not_degraded": True,
            "creative_dimension_contract": ["campaign_id", "item_group_id", "item_id"],
            "product_card_item_id": "-1",
        },
        "steps": steps,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a machine-readable MCP pull plan for creatiads agent execution."
    )
    parser.add_argument("--capability", choices=["full_report", "gmv_max_report"], default="full_report")
    parser.add_argument("--advertiser-id", required=True)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--previous-start-date")
    parser.add_argument("--previous-end-date")
    parser.add_argument("--depth", choices=["quick", "fast", "standard", "full", "deep"], default="full")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--bc-id", default="", help="Business Center ID for catalog access")
    args = parser.parse_args()

    if args.capability == "gmv_max_report":
        plan = build_gmv_max_plan(
            advertiser_id=args.advertiser_id,
            start_date=args.start_date,
            end_date=args.end_date,
            previous_start_date=args.previous_start_date or None,
            previous_end_date=args.previous_end_date or None,
            depth=args.depth,
            bc_id=args.bc_id,
        )
    else:
        plan = build_plan(
            advertiser_id=args.advertiser_id,
            start_date=args.start_date,
            end_date=args.end_date,
            previous_start_date=args.previous_start_date or None,
            previous_end_date=args.previous_end_date or None,
            depth=args.depth,
            bc_id=args.bc_id,
        )

    run_dir = Path(args.run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "raw").mkdir(exist_ok=True)
    (run_dir / "sources").mkdir(exist_ok=True)
    plan_path = run_dir / "pull_plan.json"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    tasks_path = write_mcp_tasks(run_dir, plan)
    backend = plan.get("execution_backend", "native_agent_mcp")
    steps = plan.get("steps", [])
    subagent_count = sum(1 for s in steps if s.get("preferred_backend") == SUBAGENT_BACKEND)
    native_count = sum(1 for s in steps if s.get("preferred_backend") == NATIVE_BACKEND)
    summary = {
        "capability": plan.get("capability", args.capability),
        "advertiser_id": plan.get("advertiser_id"),
        "depth": plan.get("depth"),
        "planner_version": plan.get("planner_version"),
        "plan_fingerprint": plan.get("plan_fingerprint"),
        "execution_backend": backend,
        "preferred_backend": backend,
        "backend_reason": plan.get("backend_reason"),
        "backend_fallbacks": [],
        "current_window": plan.get("current_window"),
        "previous_window": plan.get("previous_window"),
        "step_count": len(steps),
        "mcp_task_count": sum(1 for step in steps if step.get("l0_or_l1") != "local"),
        "local_task_count": sum(1 for step in steps if step.get("l0_or_l1") == "local"),
        "subagent_task_count": subagent_count,
        "bridge_task_count": 0,
        "native_task_count": native_count,
        "pull_plan": str(plan_path),
        "mcp_tasks": str(tasks_path),
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"pull_plan": str(plan_path), "mcp_tasks": str(tasks_path), "step_count": len(plan["steps"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
