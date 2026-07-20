#!/usr/bin/env python3
"""Build agent-native MCP task plans for creatiads capabilities.

This module deliberately does not call MCP. It chooses the exact native-MCP
tasks the agent should execute, writes ``pull_plan.json`` and
``mcp_tasks.jsonl``, and leaves platform I/O to the agent.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from account_profile_cache import cached_user_type_label, load_account_profile_cache
    from build_mcp_pull_plan import PLANNER_VERSION, build_gmv_max_plan, build_plan, build_plan_fingerprint, write_mcp_tasks
except ImportError:  # pragma: no cover
    from .account_profile_cache import cached_user_type_label, load_account_profile_cache
    from .build_mcp_pull_plan import PLANNER_VERSION, build_gmv_max_plan, build_plan, build_plan_fingerprint, write_mcp_tasks


USER_TYPE_CONTEXT_CAPABILITIES: set[str] = {
    "performance_diagnosis",
    "landing_app_paths",
    "creative_diagnosis",
    "audience_diagnosis",
    "activity_changelog",
    "bottleneck_diagnosis",
    "budget_recommendation",
    "metric_profile",
}

CAPABILITY_DEPENDENCIES: dict[str, set[str]] = {
    "account_inventory": {"mcp_ready", "current_account", "advertiser_info", "app_list", "catalog_list"},
    "user_type": {"mcp_ready", "current_account", "advertiser_info", "classification_campaigns", "classification_adgroups", "classification_ads", "classification_ad_v2_insights", "app_list", "catalog_list", "shop_list", "smart_plus_ads", "user_type_evidence", "user_type"},
    "metric_profile": {"user_type", "metric_preset", "metric_probe_results"},
    "performance_diagnosis": {"metric_preset", "current_advertiser_insights", "current_campaigns", "current_adgroups", "current_ads", "current_ad_v2_insights", "previous_advertiser_insights", "previous_campaigns", "previous_adgroups", "previous_ads"},
    "landing_app_paths": {"current_ads", "current_ad_v2_insights", "smart_plus_ads", "ad_details_for_enrichment", "landing_pages_report", "landing_app_paths"},
    "creative_diagnosis": {"current_ads", "smart_plus_ads", "ad_details_for_enrichment", "creative_preview_images", "creative_preview_videos", "creative_preview_spark_posts", "creative_preview_catalog_products", "creative_preview_catalog_sets", "creative_previews", "creative_retention", "targeted_creative_retention_raw", "targeted_creative_retention"},
    "audience_diagnosis": {"metric_preset", "audience_country", "audience_age_gender", "audience_placement", "audience_device"},
    "activity_changelog": {"metric_preset", "activity_changelog", "activity_targeted_campaign_insights", "activity_targeted_adgroup_insights", "activity_targeted_ad_insights", "activity_daily_campaign_breakdown", "activity_daily_adgroup_breakdown", "activity_daily_ad_breakdown", "activity_targeted_insights", "activity_daily_breakdown", "activity_factors"},
    "bottleneck_diagnosis": {"current_account", "advertiser_info", "metric_preset", "current_campaigns", "current_adgroups", "current_ads", "activity_changelog", "bottleneck_diagnosis"},
    "budget_recommendation": {"user_type", "metric_preset", "current_campaigns", "current_adgroups", "current_ads", "budget_recommendation"},
    "preflight_validate": {"mcp_ready", "current_account", "advertiser_info", "preflight_validate"},
    "staged_operations": {"mcp_ready", "current_account", "staged_operations"},
    "gmv_max_report": set(),
    "full_report": set(),
}

LOCAL_ONLY_STEPS: dict[str, dict[str, Any]] = {
    "bottleneck_diagnosis": {
        "id": "bottleneck_diagnosis",
        "capability": "bottleneck_diagnosis",
        "phase": "analysis",
        "tool": "local:validation_rebuild.diagnose_bottlenecks",
        "l0_or_l1": "local",
        "l1_tool_name": "",
        "params": {},
        "output": "sources/bottleneck_diagnosis.json",
        "output_raw": "",
        "output_source": "sources/bottleneck_diagnosis.json",
        "depends_on": ["current_account", "current_campaigns", "current_adgroups", "current_ads"],
        "required": True,
        "pagination": {"mode": "single"},
        "degradation_policy": "local_diagnosis_must_record_available_evidence",
    },
    "budget_recommendation": {
        "id": "budget_recommendation",
        "capability": "budget_recommendation",
        "phase": "analysis",
        "tool": "local:validation_rebuild.diagnose_bottlenecks",
        "l0_or_l1": "local",
        "l1_tool_name": "",
        "params": {},
        "output": "sources/staged_budget_plan.json",
        "output_raw": "",
        "output_source": "sources/staged_budget_plan.json",
        "depends_on": ["metric_preset", "current_campaigns", "current_adgroups", "current_ads"],
        "required": True,
        "pagination": {"mode": "single"},
        "degradation_policy": "approval_gated_plan_only",
    },
    "preflight_validate": {
        "id": "preflight_validate",
        "capability": "preflight_validate",
        "phase": "analysis",
        "tool": "local:validation_rebuild.validate_promoted_object",
        "l0_or_l1": "local",
        "l1_tool_name": "",
        "params": {},
        "output": "sources/preflight_validate.json",
        "output_raw": "",
        "output_source": "sources/preflight_validate.json",
        "depends_on": ["current_account"],
        "required": True,
        "pagination": {"mode": "single"},
        "degradation_policy": "read_only_go_no_go",
    },
    "staged_operations": {
        "id": "staged_operations",
        "capability": "staged_operations",
        "phase": "analysis",
        "tool": "local:staged_operations",
        "l0_or_l1": "local",
        "l1_tool_name": "",
        "params": {"approval_required": True},
        "output": "sources/staged_operations.json",
        "output_raw": "",
        "output_source": "sources/staged_operations.json",
        "depends_on": ["current_account"],
        "required": True,
        "pagination": {"mode": "single"},
        "degradation_policy": "no_live_mutation_without_user_approval",
    },
}


def _closure(step_by_id: dict[str, dict[str, Any]], selected: set[str]) -> set[str]:
    changed = True
    result = set(selected)
    while changed:
        changed = False
        for step_id in list(result):
            step = step_by_id.get(step_id) or LOCAL_ONLY_STEPS.get(step_id)
            if not step:
                continue
            for dep in step.get("depends_on") or []:
                if dep in step_by_id and dep not in result:
                    result.add(dep)
                    changed = True
    return result


def build_capability_plan(
    *,
    capability: str,
    advertiser_id: str,
    start_date: str,
    end_date: str,
    previous_start_date: str | None = None,
    previous_end_date: str | None = None,
    depth: str = "standard",
    bc_id: str = "",
    use_cached_user_type: bool = False,
    cached_user_type: str = "",
) -> dict[str, Any]:
    depth = "fast" if depth == "quick" else depth
    if capability not in CAPABILITY_DEPENDENCIES:
        raise ValueError(f"Unknown capability: {capability}")

    if capability == "gmv_max_report":
        return build_gmv_max_plan(
            advertiser_id=advertiser_id,
            start_date=start_date,
            end_date=end_date,
            previous_start_date=previous_start_date,
            previous_end_date=previous_end_date,
            depth=depth,
            bc_id=bc_id,
        )

    base_depth = depth if capability in {"full_report", "audience_diagnosis", "creative_diagnosis", "activity_changelog"} else ("full" if depth in {"full", "deep"} else "standard")
    if capability in USER_TYPE_CONTEXT_CAPABILITIES:
        # Every substantive diagnosis needs a vertical lens. If a recent
        # account profile cache exists, build_plan marks classification seed
        # steps optional and local gates hydrate user_type/metric_preset from
        # cache, avoiding repeated vertical classification.
        capability_deps = set(CAPABILITY_DEPENDENCIES[capability])
        capability_deps.update({"user_type", "metric_preset"})
    else:
        capability_deps = set(CAPABILITY_DEPENDENCIES[capability])
    base = build_plan(
        advertiser_id=advertiser_id,
        start_date=start_date,
        end_date=end_date,
        previous_start_date=previous_start_date,
        previous_end_date=previous_end_date,
        depth=base_depth,
        bc_id=bc_id,
        use_cached_user_type=use_cached_user_type,
        cached_user_type=cached_user_type,
    )
    if capability == "full_report":
        base["capability"] = "full_report"
        return base

    step_by_id = {step["id"]: step for step in base.get("steps") or []}
    wanted = _closure(step_by_id, capability_deps)
    steps = [step for step in base.get("steps") or [] if step.get("id") in wanted]
    if capability in LOCAL_ONLY_STEPS and capability not in {step.get("id") for step in steps}:
        steps.append(dict(LOCAL_ONLY_STEPS[capability]))

    for order, step in enumerate(steps, start=1):
        step["order"] = order
        step["capability"] = step.get("capability") or capability
        if capability in USER_TYPE_CONTEXT_CAPABILITIES:
            step["analysis_context"] = {
                "requires_user_type": True,
                "metrics_from": "metric_preset.json",
                "account_cache_mode": "user_type_account_cache" if use_cached_user_type else "",
                "cached_user_type": cached_user_type if use_cached_user_type else "",
            }
            if step.get("id") in {"current_ads", "current_ad_v2_insights", "targeted_creative_retention_raw", "creative_retention", "targeted_creative_retention"}:
                step["vertical_metric_lens"] = {
                    "metrics_from": "metric_preset.json",
                    "reason": "creative and ad analysis must interpret performance using the cached or freshly classified account vertical.",
                }

    execution_backend = (
        "mcp_subagent_executor"
        if any(step.get("preferred_backend") == "mcp_subagent_executor" for step in steps)
        else "native_agent_mcp"
    )

    phase_required_sources: dict[str, list[str]] = {}
    required_ids = {step["id"] for step in steps if step.get("required")}
    for phase in base.get("phase_order") or []:
        phase_sources = [
            step["id"]
            for step in steps
            if step.get("phase") == phase and step.get("id") in required_ids
        ]
        if phase_sources:
            phase_required_sources[phase] = phase_sources

    return {
        **base,
        "run_id": f"{advertiser_id}_{start_date}_{end_date}_{capability}_{depth}",
        "capability": capability,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "depth": depth,
        "planner_version": PLANNER_VERSION,
        "plan_fingerprint": build_plan_fingerprint(
            capability=capability,
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
        "account_cache_mode": "user_type_account_cache" if use_cached_user_type else "",
        "cached_user_type": cached_user_type,
        "execution_backend": execution_backend,
        "preferred_backend": execution_backend,
        "backend_reason": "batch_enrichment" if execution_backend == "mcp_subagent_executor" else "light_query",
        "backend_fallbacks": [],
        "phase_required_sources": phase_required_sources,
        "steps": steps,
    }


def write_plan(run_dir: Path, plan: dict[str, Any]) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "raw").mkdir(exist_ok=True)
    (run_dir / "sources").mkdir(exist_ok=True)
    plan_path = run_dir / "pull_plan.json"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    tasks_path = write_mcp_tasks(run_dir, plan)
    steps = plan.get("steps") or []
    summary = {
        "capability": plan.get("capability", "full_report"),
        "advertiser_id": plan.get("advertiser_id"),
        "depth": plan.get("depth"),
        "planner_version": plan.get("planner_version"),
        "plan_fingerprint": plan.get("plan_fingerprint"),
        "execution_backend": plan.get("execution_backend"),
        "preferred_backend": plan.get("preferred_backend"),
        "backend_reason": plan.get("backend_reason"),
        "backend_fallbacks": plan.get("backend_fallbacks", []),
        "current_window": plan.get("current_window"),
        "previous_window": plan.get("previous_window"),
        "step_count": len(steps),
        "mcp_task_count": sum(1 for step in steps if step.get("l0_or_l1") != "local"),
        "local_task_count": sum(1 for step in steps if step.get("l0_or_l1") == "local"),
        "subagent_task_count": sum(1 for step in steps if step.get("preferred_backend") == "mcp_subagent_executor"),
        "native_task_count": sum(1 for step in steps if step.get("preferred_backend") == "native_agent_mcp"),
        "pull_plan": str(plan_path),
        "mcp_tasks": str(tasks_path),
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an agent-native MCP task plan for a creatiads capability.")
    parser.add_argument("--capability", choices=sorted(CAPABILITY_DEPENDENCIES), default="full_report")
    parser.add_argument("--advertiser-id", required=True)
    parser.add_argument("--since", "--start-date", dest="start_date", required=True)
    parser.add_argument("--until", "--end-date", dest="end_date", required=True)
    parser.add_argument("--previous-since", "--previous-start-date", dest="previous_start_date")
    parser.add_argument("--previous-until", "--previous-end-date", dest="previous_end_date")
    parser.add_argument("--depth", choices=["quick", "fast", "standard", "full", "deep"], default="standard")
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--bc-id", default="")
    parser.add_argument("--ignore-account-cache", action="store_true", help="Force fresh user-type classification instead of reusing the recent account profile cache.")
    args = parser.parse_args()
    account_cache = None if args.ignore_account_cache else load_account_profile_cache(args.advertiser_id)
    cached_user_type = cached_user_type_label(account_cache)

    plan = build_capability_plan(
        capability=args.capability,
        advertiser_id=args.advertiser_id,
        start_date=args.start_date,
        end_date=args.end_date,
        previous_start_date=args.previous_start_date,
        previous_end_date=args.previous_end_date,
        depth=args.depth,
        bc_id=args.bc_id,
        use_cached_user_type=bool(account_cache),
        cached_user_type=cached_user_type,
    )
    print(json.dumps(write_plan(args.run_dir, plan), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
