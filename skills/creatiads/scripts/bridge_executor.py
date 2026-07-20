#!/usr/bin/env python3
"""Bridge Executor v1 — read-only batch execution backend for creatiads.

Coordinates batch MCP task execution for full/deep reports, enrichment,
and multi-page data pulls. The agent makes all MCP calls; this executor
provides the plan, validation, result recording, and normalization.

Key constraints:
  - Read-only: no Create/Update/Status/Delete MCP tasks.
  - No token handling: never reads or stores OAuth tokens.
  - All raw responses written to raw/*.json.
  - After execution, normalize_mcp_source.py converts raw -> sources.

Usage:
  # Generate batch execution plan:
  python3 creatiads/scripts/bridge_executor.py plan --run-dir <dir>

  # Record a task's raw result:
  python3 creatiads/scripts/bridge_executor.py record \\
    --run-dir <dir> --task-id current_ads --raw-file raw/current_ads_page1.json

  # Merge pages for a multi-page task:
  python3 creatiads/scripts/bridge_executor.py merge \\
    --run-dir <dir> --task-id current_ads

  # Normalize all raw outputs:
  python3 creatiads/scripts/bridge_executor.py normalize-all --run-dir <dir>

  # Check auth status:
  python3 creatiads/scripts/bridge_executor.py auth-check --run-dir <dir>
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from normalize_mcp_source import normalize, merge_pages
    from utils import (
        STATUS_OK, STATUS_DEGRADED, STATUS_PARTIAL,
        STATUS_SUPPORTED_EMPTY, STATUS_UNSUPPORTED,
        STATUS_PERMISSION_DENIED,
        write_json,
    )
except ImportError:
    from .normalize_mcp_source import normalize, merge_pages
    from .utils import (
        STATUS_OK, STATUS_DEGRADED, STATUS_PARTIAL,
        STATUS_SUPPORTED_EMPTY, STATUS_UNSUPPORTED,
        STATUS_PERMISSION_DENIED,
        write_json,
    )

# ── Bridge-supported tools ──────────────────────────────────────────────

BRIDGE_L0_TOOLS: set[str] = {
    "report_integrated_get",
    "advertiser_info_get",
    "smart_plus_ad_get",
    "app_list_get",
    "smart_plus_campaign_get",
    "smart_plus_adgroup_get",
}

BRIDGE_L1_TOOLS: set[str] = {
    "ad_get",
    "adgroup_get",
    "campaign_get",
    "file_image_ad_info_get",
    "file_video_ad_info_get",
    "tt_video_list_get",
    "changelog_task_create",
    "changelog_task_check",
    "changelog_task_download",
}

# ── Auth state ──────────────────────────────────────────────────────────

AUTH_STATE_PATH = "bridge_auth_state.json"


def read_auth_state(run_dir: Path) -> dict[str, Any]:
    path = run_dir / AUTH_STATE_PATH
    if not path.exists():
        return {
            "auth_status": "auth_required",
            "auth_provider": "disabled_auth",
            "last_checked_at": datetime.now(timezone.utc).isoformat(),
        }
    return json.loads(path.read_text(encoding="utf-8"))


def write_auth_state(run_dir: Path, state: dict[str, Any]) -> None:
    state["last_checked_at"] = datetime.now(timezone.utc).isoformat()
    path = run_dir / AUTH_STATE_PATH
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


# ── Task plan ───────────────────────────────────────────────────────────

def load_tasks(run_dir: Path) -> list[dict[str, Any]]:
    tasks_path = run_dir / "mcp_tasks.jsonl"
    if not tasks_path.exists():
        return []
    tasks: list[dict[str, Any]] = []
    for line in tasks_path.read_text(encoding="utf-8").strip().split("\n"):
        if line.strip():
            tasks.append(json.loads(line))
    return tasks


def bridge_eligible(task: dict[str, Any]) -> bool:
    """Check if a task is eligible for bridge execution."""
    tool = str(task.get("tool") or "")
    l0_or_l1 = str(task.get("l0_or_l1") or "")

    if tool.startswith("local:"):
        return False

    if l0_or_l1 == "l0" and tool not in BRIDGE_L0_TOOLS:
        return False

    if l0_or_l1 == "l1":
        l1_tool = str(task.get("l1_tool_name") or "")
        if l1_tool not in BRIDGE_L1_TOOLS:
            return False

    return True


def plan_bridge_execution(run_dir: Path) -> dict[str, Any]:
    """Generate a batch execution plan for bridge-assigned tasks.

    Reads mcp_tasks.jsonl, filters to bridge_executor tasks,
    orders by phase and dependency, and returns the execution plan.
    """
    tasks = load_tasks(run_dir)
    if not tasks:
        return {"error": "mcp_tasks.jsonl not found or empty", "tasks": []}

    # Filter to bridge-assigned tasks
    bridge_tasks = [
        t for t in tasks
        if t.get("preferred_backend") == "bridge_executor" and bridge_eligible(t)
    ]

    # Verify all bridge tasks are read-only
    for t in bridge_tasks:
        tool = str(t.get("tool") or "")
        if any(verb in tool for verb in ("Update", "Delete", "Status")):
            return {
                "error": f"task {t.get('id')} tool '{tool}' is a write operation — bridge v1 is read-only",
                "tasks": [],
            }

    # Sort by phase order, then by dependencies
    phase_order = {
        "bootstrap": 0, "classification": 1, "local_classification": 2,
        "preset": 3, "report_data": 4, "enrichment": 5,
        "analysis": 6, "audit": 7,
    }

    bridge_tasks.sort(key=lambda t: (
        phase_order.get(str(t.get("phase") or ""), 99),
        t.get("order", 999),
    ))

    now = datetime.now(timezone.utc).isoformat()
    return {
        "generated_at": now,
        "execution_backend": "bridge_executor",
        "auth_status": read_auth_state(run_dir).get("auth_status", "disabled_auth"),
        "task_count": len(bridge_tasks),
        "tasks": bridge_tasks,
    }


# ── Result recording ────────────────────────────────────────────────────

def record_raw_result(
    run_dir: Path,
    task_id: str,
    raw_data: Any,
    *,
    page_index: int = 0,
    attempts: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Record a raw MCP response for a bridge task.

    For single-page tasks, writes to raw/{task_id}.json.
    For multi-page tasks, writes to raw/{task_id}_page{N}.json.
    """
    raw_dir = run_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    if page_index > 0:
        raw_path = raw_dir / f"{task_id}_page{page_index}.json"
    else:
        raw_path = raw_dir / f"{task_id}.json"

    # Parse raw_data if string
    if isinstance(raw_data, str):
        try:
            raw_data = json.loads(raw_data)
        except (json.JSONDecodeError, TypeError):
            pass

    payload: dict[str, Any] = {
        "task_id": task_id,
        "backend": "bridge_executor",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "page_index": page_index,
        "attempts": attempts or [],
        "raw_response": raw_data,
    }
    write_json(raw_path, payload)
    return {"task_id": task_id, "raw_path": str(raw_path), "page_index": page_index}


def merge_task_pages(
    run_dir: Path,
    task_id: str,
    *,
    tool: str = "",
    phase: str = "",
    depends_on: list[str] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Merge multi-page raw results into a single normalized source."""
    raw_dir = run_dir / "raw"
    sources_dir = run_dir / "sources"
    sources_dir.mkdir(parents=True, exist_ok=True)

    # Find all page files
    page_files = sorted(raw_dir.glob(f"{task_id}_page*.json"))
    if not page_files:
        main_file = raw_dir / f"{task_id}.json"
        if main_file.exists():
            page_files = [main_file]
        else:
            return {"error": f"no raw files for task {task_id}", "task_id": task_id}

    # Load and normalize each page
    pages: list[dict[str, Any]] = []
    for pf in page_files:
        raw_payload = json.loads(pf.read_text(encoding="utf-8"))
        raw_response = raw_payload.get("raw_response", raw_payload)
        attempts = raw_payload.get("attempts", [])
        normalized = normalize(
            raw_response,
            tool=tool,
            phase=phase,
            depends_on=depends_on,
            params=params,
            attempts=attempts,
        )
        pages.append(normalized)

    # Merge and write
    merged = merge_pages(pages, tool=tool, phase=phase, depends_on=depends_on)
    merged["backend"] = "bridge_executor"
    merged["auth_status"] = read_auth_state(run_dir).get("auth_status", "disabled_auth")

    output_path = sources_dir / f"{task_id}.json"
    write_json(output_path, merged)
    return {"task_id": task_id, "output": str(output_path), "row_count": merged["row_count"], "status": merged["status"]}


def normalize_single(
    run_dir: Path,
    task_id: str,
    *,
    tool: str = "",
    phase: str = "",
    depends_on: list[str] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize a single-page raw result."""
    raw_dir = run_dir / "raw"
    raw_path = raw_dir / f"{task_id}.json"
    sources_dir = run_dir / "sources"
    sources_dir.mkdir(parents=True, exist_ok=True)

    if not raw_path.exists():
        return {"error": f"raw file not found: {raw_path}", "task_id": task_id}

    raw_payload = json.loads(raw_path.read_text(encoding="utf-8"))
    raw_response = raw_payload.get("raw_response", raw_payload)
    attempts = raw_payload.get("attempts", [])
    normalized = normalize(
        raw_response,
        tool=tool,
        phase=phase,
        depends_on=depends_on,
        params=params,
        attempts=attempts,
    )
    normalized["backend"] = "bridge_executor"
    normalized["auth_status"] = read_auth_state(run_dir).get("auth_status", "disabled_auth")

    output_path = sources_dir / f"{task_id}.json"
    write_json(output_path, normalized)
    return {"task_id": task_id, "output": str(output_path), "row_count": normalized["row_count"], "status": normalized["status"]}


def normalize_all(run_dir: Path) -> dict[str, Any]:
    """Normalize all bridge raw outputs to sources.

    Reads mcp_tasks.jsonl, finds all bridge tasks, normalizes each.
    """
    tasks = load_tasks(run_dir)
    results: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    for task in tasks:
        task_id = str(task.get("id") or "")
        if task.get("preferred_backend") != "bridge_executor":
            continue
        if not bridge_eligible(task):
            continue

        tool = str(task.get("tool") or "")
        phase = str(task.get("phase") or "")
        depends_on = task.get("depends_on", [])
        params = task.get("params", {})
        pagination = task.get("pagination") or {}
        is_paginated = pagination.get("mode") == "paginated"

        raw_dir = run_dir / "raw"
        has_multi = any(raw_dir.glob(f"{task_id}_page*.json"))

        try:
            if is_paginated and has_multi:
                result = merge_task_pages(
                    run_dir, task_id,
                    tool=tool, phase=phase,
                    depends_on=depends_on, params=params,
                )
            else:
                result = normalize_single(
                    run_dir, task_id,
                    tool=tool, phase=phase,
                    depends_on=depends_on, params=params,
                )
            results.append(result)
        except Exception as exc:
            failures.append({"task_id": task_id, "error": str(exc)})

    return {
        "normalized": len(results),
        "failed": len(failures),
        "results": results,
        "failures": failures,
    }


# ── Auth management ─────────────────────────────────────────────────────

def set_auth_state(run_dir: Path, status: str, provider: str = "disabled_auth") -> dict[str, Any]:
    """Set the bridge auth state without storing tokens.

    Valid statuses: ok, auth_required, expired, permission_denied.
    Valid providers: managed_bridge_oauth, external_mcp_proxy, disabled_auth.
    """
    valid_statuses = {"ok", "auth_required", "expired", "permission_denied"}
    valid_providers = {"managed_bridge_oauth", "external_mcp_proxy", "disabled_auth"}

    if status not in valid_statuses:
        return {"error": f"invalid auth_status: {status}", "valid": list(valid_statuses)}
    if provider not in valid_providers:
        return {"error": f"invalid auth_provider: {provider}", "valid": list(valid_providers)}

    state = {
        "auth_status": status,
        "auth_provider": provider,
    }
    write_auth_state(run_dir, state)
    return state


# ── Execution metadata ──────────────────────────────────────────────────

def update_manifest(run_dir: Path, execution_result: dict[str, Any]) -> None:
    """Update manifest.json with bridge execution metadata."""
    manifest_path = run_dir / "manifest.json"
    manifest: dict[str, Any] = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    manifest["execution_backend"] = "bridge_executor"
    manifest["bridge_execution"] = {
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "normalized": execution_result.get("normalized", 0),
        "failed": execution_result.get("failed", 0),
    }
    manifest["auth_status"] = read_auth_state(run_dir).get("auth_status", "disabled_auth")

    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


# ── CLI ─────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bridge Executor v1 — read-only batch execution backend for creatiads."
    )
    sub = parser.add_subparsers(dest="command")

    # plan
    plan_p = sub.add_parser("plan", help="Generate bridge batch execution plan")
    plan_p.add_argument("--run-dir", required=True, type=Path)

    # record
    record_p = sub.add_parser("record", help="Record a raw MCP result for a bridge task")
    record_p.add_argument("--run-dir", required=True, type=Path)
    record_p.add_argument("--task-id", required=True)
    record_p.add_argument("--raw-file", required=True, type=Path, help="Path to raw MCP response JSON")
    record_p.add_argument("--page-index", type=int, default=0)
    record_p.add_argument("--attempts-file", type=Path, help="JSON file with retry attempts")

    # merge
    merge_p = sub.add_parser("merge", help="Merge multi-page raw results")
    merge_p.add_argument("--run-dir", required=True, type=Path)
    merge_p.add_argument("--task-id", required=True)
    merge_p.add_argument("--tool", default="")
    merge_p.add_argument("--phase", default="")
    merge_p.add_argument("--depends-on", nargs="*", default=[])
    merge_p.add_argument("--params-file", type=Path)

    # normalize-all
    norm_p = sub.add_parser("normalize-all", help="Normalize all bridge raw outputs")
    norm_p.add_argument("--run-dir", required=True, type=Path)

    # auth-check
    auth_p = sub.add_parser("auth-check", help="Check bridge auth status")
    auth_p.add_argument("--run-dir", required=True, type=Path)

    # auth-set
    auth_set_p = sub.add_parser("auth-set", help="Set bridge auth state")
    auth_set_p.add_argument("--run-dir", required=True, type=Path)
    auth_set_p.add_argument("--status", required=True, choices=["ok", "auth_required", "expired", "permission_denied"])
    auth_set_p.add_argument("--provider", default="disabled_auth", choices=["managed_bridge_oauth", "external_mcp_proxy", "disabled_auth"])

    args = parser.parse_args()

    if args.command == "plan":
        result = plan_bridge_execution(args.run_dir)
        out_path = args.run_dir / "bridge_execution_plan.json"
        write_json(out_path, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if "error" in result else 0

    elif args.command == "record":
        raw_data = json.loads(args.raw_file.read_text(encoding="utf-8"))
        attempts = None
        if args.attempts_file and args.attempts_file.exists():
            attempts = json.loads(args.attempts_file.read_text(encoding="utf-8"))
            if not isinstance(attempts, list):
                attempts = [attempts]
        result = record_raw_result(args.run_dir, args.task_id, raw_data, page_index=args.page_index, attempts=attempts)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    elif args.command == "merge":
        params = None
        if args.params_file and args.params_file.exists():
            params = json.loads(args.params_file.read_text(encoding="utf-8"))
        result = merge_task_pages(
            args.run_dir, args.task_id,
            tool=args.tool, phase=args.phase,
            depends_on=args.depends_on, params=params,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if "error" in result else 0

    elif args.command == "normalize-all":
        result = normalize_all(args.run_dir)
        update_manifest(args.run_dir, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    elif args.command == "auth-check":
        state = read_auth_state(args.run_dir)
        print(json.dumps(state, ensure_ascii=False, indent=2))
        return 0

    elif args.command == "auth-set":
        result = set_auth_state(args.run_dir, args.status, args.provider)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if "error" in result else 0

    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
