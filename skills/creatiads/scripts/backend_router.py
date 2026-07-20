#!/usr/bin/env python3
"""Unified backend routing layer for creatiads dual-backend architecture.

Routes execution to native_agent_mcp or mcp_subagent_executor based on
capability, depth, task count, and estimated payload size.

Usage:
  python3 creatiads/scripts/backend_router.py \\
    --run-dir runs/7444033053753835536_2025w50_full \\
    --task-id current_ads
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

# ── Default routing rules ───────────────────────────────────────────────

NATIVE_BACKEND = "native_agent_mcp"
SUBAGENT_BACKEND = "mcp_subagent_executor"
LEGACY_BRIDGE_BACKEND = "bridge_executor"
BATCH_BACKEND_ALIASES = {SUBAGENT_BACKEND, LEGACY_BRIDGE_BACKEND}

BATCH_CAPABILITIES: set[str] = {
    "full_report",
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


def normalize_backend(value: str) -> str:
    """Return the canonical backend name while accepting legacy plans."""
    if value == LEGACY_BRIDGE_BACKEND:
        return SUBAGENT_BACKEND
    return value or NATIVE_BACKEND


def route_task(
    task: dict[str, Any],
    *,
    depth: str = "standard",
    estimated_rows: int = 0,
) -> dict[str, Any]:
    """Determine the execution backend for a single task.

    Returns a routing decision dict with backend, reason, and fallback info.
    """
    capability = str(task.get("capability") or "")
    tool = str(task.get("tool") or "")
    is_local = tool.startswith("local:")
    preferred = str(task.get("preferred_backend") or "")

    if is_local:
        return {
            "backend": NATIVE_BACKEND,
            "reason": "local_compute",
            "allow_fallback": False,
        }

    # Honor explicit preferred_backend from planner
    if preferred:
        return {
            "backend": normalize_backend(preferred),
            "reason": task.get("backend_reason", "planner_specified"),
            "allow_fallback": bool(task.get("allow_backend_fallback", False)),
        }

    # Route by capability
    if capability in NATIVE_CAPABILITIES:
        return {
            "backend": NATIVE_BACKEND,
            "reason": "light_query",
            "allow_fallback": False,
        }

    if capability in BATCH_CAPABILITIES:
        return {
            "backend": SUBAGENT_BACKEND,
            "reason": "report_parallel" if capability == "full_report" else "batch_enrichment",
            "allow_fallback": True,
        }

    # Estimated payload gating: single-page small results stay native
    if estimated_rows > 0 and estimated_rows <= 20:
        return {
            "backend": NATIVE_BACKEND,
            "reason": "light_query",
            "allow_fallback": False,
        }

    return {
        "backend": NATIVE_BACKEND,
        "reason": "light_query",
        "allow_fallback": False,
    }


def route_phase(
    tasks: list[dict[str, Any]],
    *,
    phase: str,
    depth: str = "standard",
) -> dict[str, Any]:
    """Determine the backend for an entire phase.

    Returns the consensus backend. All tasks in a phase must use
    the same backend per the contract.
    """
    phase_tasks = [t for t in tasks if t.get("phase") == phase]
    if not phase_tasks:
        return {"backend": NATIVE_BACKEND, "reason": "empty_phase"}

    backends: dict[str, int] = {}
    for t in phase_tasks:
        decision = route_task(t, depth=depth)
        backend = decision["backend"]
        backends[backend] = backends.get(backend, 0) + 1

    chosen = max(backends, key=lambda k: backends[k])
    return {
        "backend": chosen,
        "reason": "phase_consensus",
        "backends": backends,
    }


def route_run(run_dir: Path) -> dict[str, Any]:
    """Route all tasks in a run and produce a backend assignment plan.

    Reads pull_plan.json, assigns backends per task, and determines
    whether the run is native-led or subagent-led.
    """
    plan_path = run_dir / "pull_plan.json"
    if not plan_path.exists():
        return {
            "backend": "native_agent_mcp",
            "reason": "no_plan",
            "assignments": {},
        }

    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    steps: list[dict[str, Any]] = plan.get("steps") or []
    depth = str(plan.get("depth", "standard"))

    assignments: dict[str, dict[str, Any]] = {}
    backend_counts: dict[str, int] = {}

    for step in steps:
        task_id = step.get("id", "")
        decision = route_task(step, depth=depth)
        assignments[task_id] = decision
        backend_counts[decision["backend"]] = backend_counts.get(decision["backend"], 0) + 1

    run_backend = SUBAGENT_BACKEND if backend_counts.get(SUBAGENT_BACKEND, 0) else NATIVE_BACKEND

    return {
        "backend": run_backend,
        "reason": "subagent_task_present" if run_backend == SUBAGENT_BACKEND else "native_only",
        "backend_counts": backend_counts,
        "assignments": assignments,
    }


def fallback_task(task_id: str, run_dir: Path) -> dict[str, Any]:
    """Record a backend fallback for a single task.

    Only allowed from mcp_subagent_executor/legacy bridge_executor to native_agent_mcp.
    Updates manifest.json with the fallback record.
    """
    manifest_path = run_dir / "manifest.json"
    manifest: dict[str, Any] = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    fallbacks: list[dict[str, Any]] = manifest.get("backend_fallbacks", [])
    fallbacks.append({
        "task_id": task_id,
        "from_backend": SUBAGENT_BACKEND,
        "to_backend": NATIVE_BACKEND,
        "reason": "subagent_executor_unavailable",
    })
    manifest["backend_fallbacks"] = fallbacks

    # Update source attempts if source exists
    sources_dir = run_dir / "sources"
    source_path = sources_dir / f"{task_id}.json"
    if source_path.exists():
        source = json.loads(source_path.read_text(encoding="utf-8"))
        attempts = source.get("attempts", [])
        if isinstance(attempts, list):
            attempts.append({
                "backend": SUBAGENT_BACKEND,
                "status": "fallback_to_native",
                "reason": "subagent_executor_unavailable",
            })
            source["attempts"] = attempts
            source_path.write_text(json.dumps(source, ensure_ascii=False, indent=2), encoding="utf-8")

    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"task_id": task_id, "fallback": f"{SUBAGENT_BACKEND} -> {NATIVE_BACKEND}"}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Route creatiads tasks between native_agent_mcp and mcp_subagent_executor."
    )
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--task-id", help="Route a specific task")
    parser.add_argument("--phase", help="Route an entire phase")
    parser.add_argument("--fallback", action="store_true", help="Record a fallback for --task-id")
    args = parser.parse_args()

    if args.fallback and args.task_id:
        result = fallback_task(args.task_id, args.run_dir)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.task_id:
        plan_path = args.run_dir / "pull_plan.json"
        if plan_path.exists():
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            depth = plan.get("depth", "standard")
            for step in plan.get("steps") or []:
                if step.get("id") == args.task_id:
                    result = route_task(step, depth=depth)
                    print(json.dumps(result, ensure_ascii=False, indent=2))
                    return 0
        print(json.dumps({"error": f"task {args.task_id} not found"}, ensure_ascii=False))
        return 1

    if args.phase:
        plan_path = args.run_dir / "pull_plan.json"
        if plan_path.exists():
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            depth = plan.get("depth", "standard")
            result = route_phase(plan.get("steps") or [], phase=args.phase, depth=depth)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        print(json.dumps({"error": "pull_plan.json not found"}, ensure_ascii=False))
        return 1

    # Default: route entire run
    result = route_run(args.run_dir)
    out_path = args.run_dir / "backend_routing.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
