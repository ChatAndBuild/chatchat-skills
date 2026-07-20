#!/usr/bin/env python3
"""Plan agent-native MCP subagent shards for creatiads task execution.

This script does not call MCP and does not execute any task. It converts the
planner's mcp_tasks.jsonl into deterministic shard files that a main agent can
hand to subagents. Subagents then perform the native MCP calls, write raw
responses to the planned files, normalize sources, and return compact status.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


NATIVE_BACKEND = "native_agent_mcp"
SUBAGENT_BACKEND = "mcp_subagent_executor"
LEGACY_BRIDGE_BACKEND = "bridge_executor"
SUBAGENT_BACKEND_ALIASES = {SUBAGENT_BACKEND, LEGACY_BRIDGE_BACKEND}

RETURN_CONTRACT = {
    "type": "compact_status",
    "fields": ["shard_id", "status", "sources", "row_counts", "degraded_sources", "errors"],
    "raw_payload_in_chat": False,
    "direct_to_file": True,
    "chat_response_max_bytes": 0,
}

SUBAGENT_PROMPT_TEMPLATE = """You are a Creatiads TikTok MCP subexecutor.

Run dir: {run_dir}
Shard id: {shard_id}
Task file: {task_file}
Script dir: {script_dir}

Execute only the tasks listed in the shard file. Use TikTok MCP tools only.
Do not use Motata data, direct HTTP, curl, or local mocks.

Formal KPI/report/audience/ad_v2/metric-probe rows must call direct
TikTok MCP report_integrated_get only; never use tool_execute for those
sources. Non-report enrichment may use direct L0 tools first, then L1
tool_execute only when the shard task explicitly allows L1 or the direct
tool is unavailable.

Write every raw MCP response to the exact output_raw path under the run dir
as soon as that tool call completes. Before calling the next MCP task, verify
that the raw file exists and has non-zero size. If you cannot write or verify a
raw file within one step, stop the shard immediately and return the missing
source ID; do not keep calling additional sources.

For creative preview tasks with placeholder params, first run:

python3 {script_dir}/prepare_preview_mcp_calls.py --run-dir {run_dir} --advertiser-id <advertiser_id> --source-id <task_id>

Then execute the returned concrete TikTok MCP call(s). For image/video batches,
split and retry smaller batches when a mixed batch hits permission errors, and
persist successful rows instead of dropping the whole source. For Spark posts,
use item_types=["VIDEO","CAROUSEL"], page/page_size, and exact keyword lookups
for item IDs; do not use legacy item_type/count params.

Return compact status only: source IDs, output paths, row counts, degraded
sources, and errors. Do not paste raw MCP payloads into chat.

If a large MCP response is clipped before you can write it, say which source
IDs were successfully called and which raw files are missing; the main
session will recover them from mcp_tool_call_end.
"""

OPTIONAL_FIRST_REPORT_DEFER_TASK_PREFIXES = (
    "creative_preview_",
    "ad_details_for_enrichment",
    "activity_targeted_",
    "activity_daily_",
    "targeted_creative_retention_raw",
    "landing_pages_report",
    "campaign_structure",
    "adgroup_structure",
    "ad_structure",
)

SHARD_ORDER = {
    "classification_seed": 10,
    "metric_probe": 20,
    "smart_plus": 29,
    "formal_totals": 30,
    "formal_campaigns": 31,
    "formal_adgroups": 32,
    "formal_ads": 33,
    "audience": 40,
    "audience_country": 41,
    "audience_age_gender": 42,
    "audience_placement": 43,
    "audience_device": 44,
    "creative": 50,
    "activity_changelog_required": 60,
    "activity_targeted_optional": 61,
    "activity_daily_optional": 62,
    "landing_app": 70,
    "structure": 80,
}


def _load_tasks(run_dir: Path) -> list[dict[str, Any]]:
    path = run_dir / "mcp_tasks.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"{path} not found")
    tasks: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            tasks.append(json.loads(line))
    return tasks


def _is_shardable_mcp_task(task: dict[str, Any]) -> bool:
    return (
        task.get("l0_or_l1") != "local"
        and task.get("preferred_backend") in SUBAGENT_BACKEND_ALIASES
    )


def _default_shard_key(task: dict[str, Any]) -> str:
    task_id = str(task.get("id") or "")
    phase = str(task.get("phase") or "")
    if phase in {"bootstrap", "classification"}:
        return "classification_seed"
    if task_id == "metric_probe_results":
        return "metric_probe"
    if phase == "report_data" and task_id in {"current_advertiser_insights", "previous_advertiser_insights"}:
        return "formal_totals"
    if phase == "report_data" and task_id in {"current_campaigns", "previous_campaigns"}:
        return "formal_campaigns"
    if phase == "report_data" and task_id in {"current_adgroups", "previous_adgroups"}:
        return "formal_adgroups"
    if phase == "report_data" and task_id in {"current_ads", "previous_ads", "current_ad_v2_insights"}:
        return "formal_ads"
    if task_id.startswith("audience_"):
        return task_id
    if task_id.startswith(("creative_", "targeted_creative", "ad_details")):
        return "creative"
    if task_id == "activity_changelog":
        return "activity_changelog_required"
    if task_id.startswith("activity_targeted_"):
        return "activity_targeted_optional"
    if task_id.startswith("activity_daily_"):
        return "activity_daily_optional"
    if task_id == "smart_plus_ads":
        return "smart_plus"
    if task_id.startswith("landing_"):
        return "landing_app"
    return phase or "general"


def _role_for_shard(shard_key: str) -> str:
    return {
        "classification_seed": "classification_seed_collector",
        "metric_probe": "metric_probe_worker",
        "formal_totals": "formal_report_source_worker",
        "formal_campaigns": "formal_report_source_worker",
        "formal_adgroups": "formal_report_source_worker",
        "formal_ads": "formal_report_source_worker",
        "audience": "audience_enrichment_worker",
        "audience_country": "audience_enrichment_worker",
        "audience_age_gender": "audience_enrichment_worker",
        "audience_placement": "audience_enrichment_worker",
        "audience_device": "audience_enrichment_worker",
        "creative": "creative_enrichment_worker",
        "structure": "structure_enrichment_worker",
        "activity_changelog_required": "activity_changelog_worker",
        "activity_targeted_optional": "activity_enrichment_worker",
        "activity_daily_optional": "activity_enrichment_worker",
        "landing_app": "landing_app_worker",
        "smart_plus": "smart_plus_enrichment_worker",
    }.get(shard_key, f"{shard_key}_worker")


def build_subagent_execution_plan(run_dir: Path) -> dict[str, Any]:
    tasks = _load_tasks(run_dir)
    subagent_tasks = [task for task in tasks if _is_shardable_mcp_task(task)]
    script_dir = Path(__file__).resolve().parent

    source_owner: dict[str, str] = {}
    duplicate_outputs: list[dict[str, str]] = []
    for task in subagent_tasks:
        output_source = str(task.get("output_source") or "")
        task_id = str(task.get("id") or "")
        if not output_source:
            continue
        prior = source_owner.get(output_source)
        if prior and prior != task_id:
            duplicate_outputs.append({
                "output_source": output_source,
                "first_task_id": prior,
                "duplicate_task_id": task_id,
            })
        source_owner[output_source] = task_id

    if duplicate_outputs:
        return {
            "passed": False,
            "error": "duplicate output_source ownership",
            "duplicate_outputs": duplicate_outputs,
            "shards": [],
        }

    grouped: dict[str, list[dict[str, Any]]] = {}
    for task in subagent_tasks:
        shard_key = str(task.get("shard_key") or _default_shard_key(task))
        task.setdefault("shard_execution_backend", SUBAGENT_BACKEND)
        task.setdefault("shard_key", shard_key)
        task.setdefault("subagent_role", _role_for_shard(shard_key))
        task.setdefault("return_contract", RETURN_CONTRACT)
        grouped.setdefault(shard_key, []).append(task)

    shards: list[dict[str, Any]] = []
    subagent_dir = run_dir / "subagent_tasks"
    prompt_dir = run_dir / "subagent_prompts"
    subagent_dir.mkdir(parents=True, exist_ok=True)
    prompt_dir.mkdir(parents=True, exist_ok=True)

    for shard_key, shard_tasks in sorted(grouped.items(), key=lambda item: (SHARD_ORDER.get(item[0], 999), item[0])):
        shard_tasks.sort(key=lambda task: int(task.get("order") or 9999))
        shard_id = f"{SHARD_ORDER.get(shard_key, 999):03d}_{shard_key}"
        required_task_count = sum(1 for task in shard_tasks if task.get("required"))
        optional_task_count = len(shard_tasks) - required_task_count
        all_tasks_deferred_optional = required_task_count == 0 and all(
            str(task.get("id") or "").startswith(OPTIONAL_FIRST_REPORT_DEFER_TASK_PREFIXES)
            for task in shard_tasks
        )
        execution_stage = "optional_after_first_report" if all_tasks_deferred_optional else "blocking_before_report"
        shard_path = subagent_dir / f"{shard_id}.jsonl"
        shard_path.write_text(
            "\n".join(json.dumps(task, ensure_ascii=False, sort_keys=True) for task in shard_tasks) + "\n",
            encoding="utf-8",
        )
        prompt_path = prompt_dir / f"{shard_id}.md"
        prompt_path.write_text(
            SUBAGENT_PROMPT_TEMPLATE.format(
                run_dir=str(run_dir),
                shard_id=shard_id,
                task_file=str(shard_path),
                script_dir=str(script_dir),
            ),
            encoding="utf-8",
        )
        shards.append({
            "shard_id": shard_id,
            "shard_key": shard_key,
            "subagent_role": shard_tasks[0].get("subagent_role") or _role_for_shard(shard_key),
            "parallel_group": shard_tasks[0].get("parallel_group") or shard_key,
            "max_concurrency": int(shard_tasks[0].get("max_concurrency") or 1),
            "execution_mode": shard_tasks[0].get("execution_mode") or "parallel_after_dependencies",
            "task_count": len(shard_tasks),
            "required_task_count": required_task_count,
            "optional_task_count": optional_task_count,
            "execution_stage": execution_stage,
            "blocking": execution_stage == "blocking_before_report",
            "tasks": [task.get("id") for task in shard_tasks],
            "task_file": str(shard_path),
            "prompt_file": str(prompt_path),
            "outputs": [task.get("output_source") for task in shard_tasks if task.get("output_source")],
            "return_contract": RETURN_CONTRACT,
        })

    parallel_groups: dict[str, dict[str, Any]] = {}
    for shard in shards:
        group = str(shard.get("parallel_group") or shard.get("shard_key") or "general")
        current = parallel_groups.setdefault(group, {"shards": [], "max_concurrency": shard.get("max_concurrency") or 1})
        current["shards"].append(shard["shard_id"])
        current["max_concurrency"] = max(int(current.get("max_concurrency") or 1), int(shard.get("max_concurrency") or 1))

    return {
        "passed": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "execution_backend": SUBAGENT_BACKEND,
        "task_count": len(subagent_tasks),
        "shard_count": len(shards),
        "blocking_shards": [shard["shard_id"] for shard in shards if shard.get("blocking")],
        "optional_after_first_report_shards": [shard["shard_id"] for shard in shards if not shard.get("blocking")],
        "shards": shards,
        "parallel_groups": parallel_groups,
        "execution_protocol": [
            "Main agent first spawns only blocking_before_report shards, respecting parallel_group max_concurrency.",
            "optional_after_first_report shards are preview/activity enhancement work; run them only after the first audited report exists or when the user explicitly asks for preview repair/enrichment.",
            "Subagents execute only tasks listed in their shard file.",
            "Subagents write output_raw exactly as specified immediately after each MCP call and verify the file before the next MCP call.",
            "Subagents return compact status only; raw MCP payloads stay on disk.",
            "After each completed or timed-out subagent wave, run recover_subagent_mcp_payloads.py before scheduling the next wave or report audit.",
            "If a large response is clipped, treat the subagent MCP call as recoverable when request_id exists; recover from the session log instead of rerunning the platform call.",
        ],
        "recovery_command": (
            f"python3 {script_dir / 'recover_subagent_mcp_payloads.py'} "
            f"--run-dir {run_dir}"
        ),
    }


def write_subagent_execution_plan(run_dir: Path) -> dict[str, Any]:
    plan = build_subagent_execution_plan(run_dir)
    (run_dir / "subagent_execution_plan.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    template = {
        "shard_id": "",
        "status": "pending",
        "sources": [],
        "row_counts": {},
        "degraded_sources": [],
        "errors": [],
    }
    (run_dir / "subagent_status_template.json").write_text(
        json.dumps(template, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return plan


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan mcp_subagent_executor shards from mcp_tasks.jsonl.")
    parser.add_argument("--run-dir", required=True, type=Path)
    args = parser.parse_args()

    result = write_subagent_execution_plan(args.run_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
