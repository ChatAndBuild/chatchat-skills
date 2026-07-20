#!/usr/bin/env python3
"""Finalize a Creatiads MCP-backed run after native TikTok MCP calls.

This script does not call MCP. It automates the slow manual loop:
recover completed MCP payloads from Codex session logs, normalize any new raw
files, advance the workflow/report/audit, and write a compact timing summary.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from recover_subagent_mcp_payloads import recover
    from workflow_runner import advance_workflow
    from utils import write_json
except ImportError:  # pragma: no cover
    from .recover_subagent_mcp_payloads import recover
    from .workflow_runner import advance_workflow
    from .utils import write_json


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _upsert_timing(run_dir: Path, entry: dict[str, Any]) -> None:
    path = run_dir / "step_timings.json"
    data = _load_json(path, [])
    if not isinstance(data, list):
        data = []
    by_step = {str(item.get("step")): item for item in data if isinstance(item, dict)}
    by_step[str(entry["step"])] = entry
    order = [str(item.get("step")) for item in data if isinstance(item, dict)]
    if str(entry["step"]) not in order:
        order.append(str(entry["step"]))
    write_json(path, [by_step[step] for step in order if step in by_step])


def _time_call(step: str, phase: str, tool: str, timing_run_dir: Path, fn, *args, **kwargs):
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    duration = round(time.perf_counter() - start, 4)
    status = "ok"
    if isinstance(result, dict):
        if result.get("stage") == "blocked" or result.get("returncode") not in (None, 0):
            status = "blocked"
    _upsert_timing(timing_run_dir, {
        "step": step,
        "phase": phase,
        "tool": tool,
        "duration_seconds": duration,
        "status": status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    })
    return result, duration


def build_timing_summary(run_dir: Path) -> dict[str, Any]:
    timings = _load_json(run_dir / "step_timings.json", [])
    if not isinstance(timings, list):
        timings = []
    rows = [row for row in timings if isinstance(row, dict)]
    phase_call_sums: dict[str, float] = defaultdict(float)
    for row in rows:
        phase_call_sums[str(row.get("phase") or "unknown")] += float(row.get("duration_seconds") or 0)

    slowest = sorted(rows, key=lambda row: float(row.get("duration_seconds") or 0), reverse=True)[:12]
    batch_wall: dict[str, float] = {}
    for row in rows:
        if not str(row.get("step") or "").endswith("_parallel_batch"):
            continue
        phase = str(row.get("phase") or "unknown")
        batch_wall[phase] = max(batch_wall.get(phase, 0.0), float(row.get("duration_seconds") or 0))
    critical_path_estimate = 0.0
    for row in rows:
        step = str(row.get("step") or "")
        phase = str(row.get("phase") or "unknown")
        if step.endswith("_parallel_batch"):
            continue
        if phase in batch_wall and float(row.get("duration_seconds") or 0) <= batch_wall[phase]:
            continue
        critical_path_estimate += float(row.get("duration_seconds") or 0)
    critical_path_estimate += sum(batch_wall.values())

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "timing_file": str(run_dir / "step_timings.json"),
        "step_count": len(rows),
        "phase_call_sums": {key: round(value, 4) for key, value in sorted(phase_call_sums.items())},
        "critical_path_estimate_seconds": round(critical_path_estimate, 4),
        "slowest_steps": [
            {
                "step": row.get("step"),
                "phase": row.get("phase"),
                "tool": row.get("tool"),
                "duration_seconds": row.get("duration_seconds"),
                "status": row.get("status"),
            }
            for row in slowest
        ],
    }
    write_json(run_dir / "timing_summary.json", summary)
    return summary


def finalize_run(
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
    sessions_dir: Path = Path(os.path.expanduser("~/.codex/sessions")),
    lookback_hours: float = 12,
    max_passes: int = 3,
    force_recover: bool = False,
) -> dict[str, Any]:
    passes: list[dict[str, Any]] = []
    state: dict[str, Any] = {}
    for index in range(1, max_passes + 1):
        recovered, recover_duration = _time_call(
            f"finalize_recover_pass_{index}",
            "recovery",
            "recover_subagent_mcp_payloads",
            run_dir,
            recover,
            run_dir=run_dir,
            sessions_dir=sessions_dir,
            lookback_hours=lookback_hours,
            force=force_recover,
        )
        state, advance_duration = _time_call(
            f"finalize_advance_pass_{index}",
            "local_compute",
            "workflow_runner.advance_workflow",
            run_dir,
            advance_workflow,
            run_dir=run_dir,
            capability=capability,
            advertiser_id=advertiser_id,
            start_date=start_date,
            end_date=end_date,
            previous_start_date=previous_start_date,
            previous_end_date=previous_end_date,
            period=period,
            depth=depth,
            bc_id=bc_id,
        )
        pass_summary = {
            "pass": index,
            "recovered_count": recovered.get("recovered_count") if isinstance(recovered, dict) else None,
            "missing_task_ids": recovered.get("missing_task_ids") if isinstance(recovered, dict) else [],
            "recover_duration_seconds": recover_duration,
            "advance_duration_seconds": advance_duration,
            "stage": state.get("stage"),
            "pending_mcp_task_count": state.get("pending_mcp_task_count"),
            "audit_required_passed": state.get("audit_required_passed"),
        }
        passes.append(pass_summary)
        if state.get("stage") == "complete":
            break
        if not pass_summary["recovered_count"]:
            break

    timing_summary = build_timing_summary(run_dir)
    result = {
        "run_dir": str(run_dir),
        "stage": state.get("stage"),
        "passes": passes,
        "timing_summary": timing_summary,
        "report_result": state.get("report_result"),
        "pending_mcp_tasks_path": state.get("pending_mcp_tasks_path"),
    }
    write_json(run_dir / "finalize_summary.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Recover, advance, audit, and summarize a Creatiads MCP-backed run without calling MCP.")
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--capability", default="full_report")
    parser.add_argument("--advertiser-id", required=True)
    parser.add_argument("--since", "--start-date", dest="start_date", required=True)
    parser.add_argument("--until", "--end-date", dest="end_date", required=True)
    parser.add_argument("--previous-since", "--previous-start-date", dest="previous_start_date")
    parser.add_argument("--previous-until", "--previous-end-date", dest="previous_end_date")
    parser.add_argument("--period", choices=["daily", "weekly", "custom"], default="custom")
    parser.add_argument("--depth", choices=["quick", "fast", "standard", "full", "deep"], default="standard")
    parser.add_argument("--bc-id", default="")
    parser.add_argument("--sessions-dir", type=Path, default=Path(os.path.expanduser("~/.codex/sessions")))
    parser.add_argument("--lookback-hours", type=float, default=12)
    parser.add_argument("--max-passes", type=int, default=3)
    parser.add_argument("--force-recover", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    result = finalize_run(
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
        sessions_dir=args.sessions_dir,
        lookback_hours=args.lookback_hours,
        max_passes=args.max_passes,
        force_recover=args.force_recover,
    )
    print(json.dumps(result if not args.quiet else {
        "stage": result.get("stage"),
        "run_dir": result.get("run_dir"),
        "passes": result.get("passes"),
        "critical_path_estimate_seconds": (result.get("timing_summary") or {}).get("critical_path_estimate_seconds"),
        "report_result": result.get("report_result"),
    }, ensure_ascii=False, indent=None if args.quiet else 2))
    return 0 if result.get("stage") in {"complete", "awaiting_mcp", "awaiting_mcp_namespace"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
