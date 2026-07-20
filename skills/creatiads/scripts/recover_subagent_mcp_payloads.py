#!/usr/bin/env python3
"""Recover raw MCP payloads from Codex subagent session logs.

Subagents can successfully call TikTok MCP but fail to persist large tool
responses. This utility scans session JSONL files for `mcp_tool_call_end`
events, matches them back to `mcp_tasks.jsonl`, and writes the exact MCP
content payload into the planned `raw/*.json` files.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    from normalize_mcp_source import normalize
except ImportError:  # pragma: no cover
    from .normalize_mcp_source import normalize


def _load_tasks(run_dir: Path) -> list[dict[str, Any]]:
    path = run_dir / "mcp_tasks.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"{path} not found")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _stable(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _is_placeholder(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("__") and value.endswith("__")


def _wildcard_match(expected: Any, actual: Any) -> bool:
    """Match planned task params where runtime placeholders were expanded.

    Subagent plans intentionally contain placeholders such as ``__top_ad_ids__``.
    The actual MCP call contains the resolved IDs, so exact JSON matching would
    miss valid tool responses. Placeholder strings match any non-empty runtime
    value; lists containing a single placeholder match any non-empty list.
    """
    if _is_placeholder(expected):
        return actual not in (None, "", [])
    if isinstance(expected, list):
        if len(expected) == 1 and _is_placeholder(expected[0]):
            return isinstance(actual, list) and len(actual) > 0
        if not isinstance(actual, list) or len(expected) != len(actual):
            return False
        return all(_wildcard_match(e, a) for e, a in zip(expected, actual))
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        for key, value in expected.items():
            if key not in actual or not _wildcard_match(value, actual.get(key)):
                return False
        return True
    return expected == actual


def _candidate_args(task: dict[str, Any]) -> list[dict[str, Any]]:
    params = task.get("params") if isinstance(task.get("params"), dict) else {}
    candidates = [dict(params)]
    for retry in task.get("retry_ladder") or []:
        if not isinstance(retry, dict):
            continue
        retry_params = dict(params)
        retry_params.update({key: value for key, value in retry.items() if key in {"dimensions", "metrics", "report_type", "data_level"}})
        candidates.append(retry_params)
    return candidates


def _tool_execute_candidate_args(task: dict[str, Any]) -> list[dict[str, Any]]:
    """Build dispatcher-shaped candidates for L1 tool_execute calls.

    L1 TikTok MCP calls are logged as tool_execute with
    {"tool_name": "...", "params": {...}} rather than the logical tool name in
    mcp_tasks.jsonl. Async changelog flows persist the final download response,
    so also allow matching the last async step by advertiser_id.
    """
    params = task.get("params") if isinstance(task.get("params"), dict) else {}
    tool_names: list[str] = []
    for key in ("l1_tool_name", "tool"):
        value = str(task.get(key) or "")
        if value and value not in tool_names:
            tool_names.append(value)
    candidates = [{"tool_name": tool_name, "params": dict(params)} for tool_name in tool_names]

    async_flow = task.get("async_flow")
    if isinstance(async_flow, list) and async_flow:
        final_tool = str(async_flow[-1] or "")
        advertiser_id = params.get("advertiser_id")
        if final_tool and advertiser_id:
            candidates.append({"tool_name": final_tool, "params": {"advertiser_id": advertiser_id}})
    return candidates


def _task_keys(task: dict[str, Any]) -> list[str]:
    tool = str(task.get("tool") or "")
    keys = [f"{tool} {_stable(args)}" for args in _candidate_args(task)]
    if task.get("l0_or_l1") == "l1" or task.get("async_flow"):
        keys.extend(f"tool_execute {_stable(args)}" for args in _tool_execute_candidate_args(task))
    return keys


def _matches_with_placeholders(task: dict[str, Any], tool: str, invocation_args: dict[str, Any]) -> bool:
    if tool == str(task.get("tool") or ""):
        return any(_wildcard_match(args, invocation_args) for args in _candidate_args(task))
    if tool == "tool_execute" and (task.get("l0_or_l1") == "l1" or task.get("async_flow")):
        return any(_wildcard_match(args, invocation_args) for args in _tool_execute_candidate_args(task))
    return False


def _session_files(sessions_dir: Path, lookback_hours: float, agent_ids: list[str]) -> list[Path]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    files: list[Path] = []
    for path in sessions_dir.rglob("*.jsonl"):
        if agent_ids and not any(agent_id in path.name for agent_id in agent_ids):
            continue
        try:
            mtime = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        except OSError:
            continue
        if mtime >= cutoff:
            files.append(path)
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)


def _default_min_event_time(run_dir: Path) -> datetime | None:
    """Use run creation/planning time as the recovery lower bound.

    Codex session logs can contain older MCP calls with identical task IDs and
    parameters. Without a per-run lower bound, recovery may resurrect stale raw
    payloads from previous reports. The plan file is written at run creation and
    is stable enough to act as the first acceptable MCP event timestamp.
    """
    candidates = [run_dir / "pull_plan.json", run_dir / "workflow_state.json", run_dir]
    mtimes: list[float] = []
    for path in candidates:
        try:
            mtimes.append(path.stat().st_mtime)
        except OSError:
            continue
    if not mtimes:
        return None
    return datetime.fromtimestamp(min(mtimes), timezone.utc)


def _parse_event_time(event: dict[str, Any]) -> datetime | None:
    value = event.get("timestamp")
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _extract_raw_content(event_payload: dict[str, Any]) -> Any:
    result = event_payload.get("result")
    if isinstance(result, dict):
        ok = result.get("Ok")
        if isinstance(ok, dict) and "content" in ok:
            return ok["content"]
    return result if result is not None else event_payload


def _is_mergeable_task(task: dict[str, Any]) -> bool:
    task_id = str(task.get("id") or "")
    pagination = task.get("pagination") if isinstance(task.get("pagination"), dict) else {}
    mode = str(pagination.get("mode") or "")
    if task_id.startswith("creative_preview_"):
        return True
    return mode in {"per_id_or_paginated", "per_catalog_batch", "per_catalog_or_set", "batched", "split_retry"}


def _merged_raw_payload(task: dict[str, Any], raws: list[Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    attempts: list[dict[str, Any]] = []
    seen_rows: set[str] = set()
    statuses: set[str] = set()
    for raw in raws:
        normalized = normalize(
            raw,
            tool=str(task.get("tool") or ""),
            phase=str(task.get("phase") or ""),
            depends_on=task.get("depends_on") or [],
            params=task.get("params") if isinstance(task.get("params"), dict) else None,
            backend=str(task.get("preferred_backend") or ""),
        )
        statuses.add(str(normalized.get("status") or ""))
        attempts.append({
            "status": normalized.get("status"),
            "row_count": normalized.get("row_count"),
            "error": normalized.get("error"),
        })
        for row in normalized.get("rows") or []:
            if not isinstance(row, dict):
                continue
            key = json.dumps(row, ensure_ascii=False, sort_keys=True, default=str)
            if key in seen_rows:
                continue
            seen_rows.add(key)
            rows.append(row)
    status = "ok" if rows else ("supported_empty" if statuses <= {"supported_empty", "ok", ""} else "partial")
    return {
        "status": status,
        "rows": rows,
        "row_count": len(rows),
        "recovery_merged": True,
        "merged_raw_count": len(raws),
        "attempts": attempts,
    }


def recover(
    *,
    run_dir: Path,
    sessions_dir: Path,
    lookback_hours: float = 12,
    agent_ids: list[str] | None = None,
    task_ids: set[str] | None = None,
    force: bool = False,
    min_event_time: datetime | None = None,
) -> dict[str, Any]:
    tasks = _load_tasks(run_dir)
    if min_event_time is None:
        min_event_time = _default_min_event_time(run_dir)
    wanted: dict[str, dict[str, Any]] = {}
    for task in tasks:
        task_id = str(task.get("id") or "")
        if task.get("l0_or_l1") == "local" or not task.get("output_raw"):
            continue
        if task_ids and task_id not in task_ids:
            continue
        output_raw = run_dir / str(task.get("output_raw"))
        if output_raw.exists() and not force:
            continue
        for key in _task_keys(task):
            wanted[key] = task

    recovered: dict[str, dict[str, Any]] = {}
    mergeable_raws: dict[str, list[dict[str, Any]]] = {}
    task_by_id: dict[str, dict[str, Any]] = {}
    scanned_files = 0
    for session_path in _session_files(sessions_dir, lookback_hours, agent_ids or []):
        if not wanted:
            break
        scanned_files += 1
        try:
            lines = session_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in reversed(lines):
            if "mcp_tool_call_end" not in line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            event_time = _parse_event_time(event)
            if min_event_time and event_time and event_time < min_event_time:
                continue
            payload = event.get("payload") if isinstance(event, dict) else None
            if not isinstance(payload, dict) or payload.get("type") != "mcp_tool_call_end":
                continue
            invocation = payload.get("invocation")
            if not isinstance(invocation, dict):
                continue
            invocation_args = invocation.get("arguments") or {}
            key = f"{invocation.get('tool') or ''} {_stable(invocation_args)}"
            task = wanted.get(key)
            if not task and invocation.get("tool") == "tool_execute" and isinstance(invocation_args, dict):
                params = invocation_args.get("params")
                if isinstance(params, dict) and "task_id" in params:
                    relaxed = dict(params)
                    relaxed.pop("task_id", None)
                    relaxed_key = f"tool_execute {_stable({'tool_name': invocation_args.get('tool_name'), 'params': relaxed})}"
                    task = wanted.get(relaxed_key)
            if not task:
                for candidate in list({id(item): item for item in wanted.values()}.values()):
                    if _matches_with_placeholders(candidate, str(invocation.get("tool") or ""), invocation_args):
                        task = candidate
                        break
            if not task:
                continue
            task_id = str(task.get("id") or "")
            task_by_id[task_id] = task
            output_raw = run_dir / str(task.get("output_raw"))
            raw = _extract_raw_content(payload)
            if _is_mergeable_task(task):
                mergeable_raws.setdefault(task_id, []).append({
                    "raw": raw,
                    "output_raw": str(output_raw),
                    "session": str(session_path),
                })
                recovered[task_id] = {
                    "output_raw": str(output_raw),
                    "session": str(session_path),
                    "bytes": 0,
                    "merged_pending": True,
                }
                continue
            output_raw.parent.mkdir(parents=True, exist_ok=True)
            output_raw.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
            recovered[task_id] = {
                "output_raw": str(output_raw),
                "session": str(session_path),
                "bytes": output_raw.stat().st_size,
            }
            for task_key in _task_keys(task):
                wanted.pop(task_key, None)

    for task_id, items in mergeable_raws.items():
        task = task_by_id.get(task_id)
        if not task or not items:
            continue
        output_raw = run_dir / str(task.get("output_raw"))
        raw_payloads = [item["raw"] for item in reversed(items)]
        merged = _merged_raw_payload(task, raw_payloads)
        output_raw.parent.mkdir(parents=True, exist_ok=True)
        output_raw.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
        recovered[task_id] = {
            "output_raw": str(output_raw),
            "session": items[0]["session"],
            "bytes": output_raw.stat().st_size,
            "merged_raw_count": len(items),
            "row_count": merged.get("row_count"),
        }
        for task_key in _task_keys(task):
            wanted.pop(task_key, None)

    return {
        "run_dir": str(run_dir),
        "sessions_dir": str(sessions_dir),
        "scanned_files": scanned_files,
        "min_event_time": min_event_time.isoformat() if min_event_time else None,
        "recovered_count": len(recovered),
        "recovered": recovered,
        "missing_task_ids": sorted({str(task.get("id") or "") for task in wanted.values()}),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Recover raw MCP payloads from subagent session JSONL files.")
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--sessions-dir", type=Path, default=Path(os.path.expanduser("~/.codex/sessions")))
    parser.add_argument("--lookback-hours", type=float, default=12)
    parser.add_argument("--agent-id", action="append", default=[])
    parser.add_argument("--task-id", action="append", default=[])
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--allow-stale",
        action="store_true",
        help="Disable the per-run event timestamp guard. Intended only for manual forensics.",
    )
    args = parser.parse_args()

    result = recover(
        run_dir=args.run_dir,
        sessions_dir=args.sessions_dir,
        lookback_hours=args.lookback_hours,
        agent_ids=args.agent_id,
        task_ids=set(args.task_id) if args.task_id else None,
        force=args.force,
        min_event_time=None if not args.allow_stale else datetime.fromtimestamp(0, timezone.utc),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
