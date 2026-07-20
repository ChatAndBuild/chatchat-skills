#!/usr/bin/env python3
"""Normalize TikTok MCP raw responses into the creatiads source contract.

Handles these input shapes:
  - MCP direct JSON (dict with rows/status)
  - MCP text-wrapped JSON ([{"type":"text","text":"{...}"}])
  - Multi-page raw files (merges by page)
  - L1 dispatcher nested responses (tool_execute results)

Usage:
  python3 creatiads/scripts/normalize_mcp_source.py \\
    --input raw_response.json \\
    --output sources/current_campaigns.json \\
    --tool report_integrated_get \\
    --phase report_data \\
    --depends-on metric_preset
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from utils import (
        STATUS_OK, STATUS_DEGRADED, STATUS_PARTIAL,
        STATUS_SUPPORTED_EMPTY, STATUS_UNSUPPORTED,
        extract_rows, classify_error, write_json,
    )
    from tiktok_adapter import _extract_changelog_payload_rows
except ImportError:
    from .utils import (
        STATUS_OK, STATUS_DEGRADED, STATUS_PARTIAL,
        STATUS_SUPPORTED_EMPTY, STATUS_UNSUPPORTED,
        extract_rows, classify_error, write_json,
    )
    from .tiktok_adapter import _extract_changelog_payload_rows


def _unwrap_mcp_text(payload: Any) -> Any:
    """Unwrap MCP text content blocks like [{"type":"text","text":"{...}"}]."""
    if isinstance(payload, dict) and payload.get("type") == "text" and isinstance(payload.get("text"), str):
        try:
            return json.loads(payload["text"])
        except (json.JSONDecodeError, TypeError):
            return payload
    if isinstance(payload, list) and len(payload) == 1:
        item = payload[0]
        if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
            try:
                return json.loads(item["text"])
            except (json.JSONDecodeError, TypeError):
                return payload
    if isinstance(payload, list):
        unwrapped: list[Any] = []
        for item in payload:
            if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
                try:
                    unwrapped.append(json.loads(item["text"]))
                except (json.JSONDecodeError, TypeError):
                    unwrapped.append(item)
            else:
                unwrapped.append(item)
        if len(unwrapped) == 1:
            return unwrapped[0]
        return unwrapped
    return payload


def _unwrap_l1_dispatcher(payload: Any) -> Any:
    """Unwrap L1 dispatcher tool_execute nested responses."""
    if not isinstance(payload, dict):
        return payload
    for key in ("data", "result", "payload", "response"):
        value = payload.get(key)
        if isinstance(value, dict):
            inner = _unwrap_l1_dispatcher(value)
            if inner is not value:
                return inner
        if isinstance(value, list) and value:
            inner = _unwrap_mcp_text(value)
            if inner is not value:
                return inner
    # Check for list wrapper from tool_execute
    list_val = payload.get("list")
    if isinstance(list_val, list) and list_val:
        return {"status": STATUS_OK, "rows": list_val, "row_count": len(list_val)}
    return payload


def _extract_page_info(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract pagination metadata from MCP response."""
    page_info = payload.get("page_info")
    if isinstance(page_info, dict):
        return dict(page_info)
    # Try nested location
    for key in ("data", "result", "payload"):
        inner = payload.get(key)
        if isinstance(inner, dict):
            pi = inner.get("page_info")
            if isinstance(pi, dict):
                return dict(pi)
    return {}


def _extract_rows_from_payload(payload: Any) -> list[dict[str, Any]]:
    """Extract rows from any MCP response shape."""
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    # Standard extract_rows
    rows = extract_rows(payload)
    if rows:
        return rows
    # Changelog downloads return CSV text under data.changelog/file_data
    # instead of the normal report list shape.
    rows = _extract_changelog_payload_rows(payload)
    if rows:
        return rows
    # Try nested response shapes
    for key in ("data", "result", "payload", "response"):
        inner = payload.get(key)
        if isinstance(inner, dict):
            rows = extract_rows(inner)
            if rows:
                return rows
            rows = _extract_changelog_payload_rows(inner)
            if rows:
                return rows
        if isinstance(inner, list):
            return [item for item in inner if isinstance(item, dict)]
    return []


def _params_hash(params: dict[str, Any] | None) -> str:
    if not params:
        return ""
    raw = json.dumps(params, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def normalize(
    raw: Any,
    *,
    tool: str = "",
    phase: str = "",
    depends_on: list[str] | None = None,
    params: dict[str, Any] | None = None,
    raw_request_ids: list[str] | None = None,
    attempts: list[dict[str, Any]] | None = None,
    backend: str = "",
    auth_status: str = "",
) -> dict[str, Any]:
    """Normalize a TikTok MCP response into the creatiads source contract.

    Args:
        raw: Raw MCP response (JSON string, dict, or list).
        tool: MCP tool name that produced this response.
        phase: Pipeline phase (bootstrap, classification, report_data, etc.).
        depends_on: List of source IDs this source depends on.
        params: The MCP tool params used (for hash/fingerprinting).
        raw_request_ids: Raw request IDs for audit trail.
        attempts: Retry ladder attempt records.
        backend: Execution backend (native_agent_mcp, mcp_subagent_executor, or legacy bridge_executor).
        auth_status: Legacy executor auth status (ok, auth_required, expired, permission_denied).

    Returns:
        Normalized source dict with status, rows, row_count, page_info, etc.
    """
    now = datetime.now(timezone.utc).isoformat()

    # Parse raw input if it's a JSON string
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return {
                "status": STATUS_DEGRADED,
                "phase": phase,
                "generated_at": now,
                "tool": tool,
                "backend": backend,
                "auth_status": auth_status,
                "params_hash": _params_hash(params),
                "depends_on": depends_on or [],
                "rows": [],
                "row_count": 0,
                "page_info": {},
                "raw_request_ids": raw_request_ids or [],
                "attempts": attempts or [],
                "error": "Failed to parse raw input as JSON",
                "raw_excerpt": raw[:500],
            }

    # Unwrap MCP text wrappers and L1 dispatcher nesting
    unwrapped = _unwrap_mcp_text(raw)
    unwrapped = _unwrap_l1_dispatcher(unwrapped)

    if not isinstance(unwrapped, dict):
        # If the result is a list, treat as rows
        if isinstance(unwrapped, list):
            rows = [item for item in unwrapped if isinstance(item, dict)]
            return {
                "status": STATUS_OK if rows else STATUS_SUPPORTED_EMPTY,
                "phase": phase,
                "generated_at": now,
                "tool": tool,
                "backend": backend,
                "auth_status": auth_status,
                "params_hash": _params_hash(params),
                "depends_on": depends_on or [],
                "rows": rows,
                "row_count": len(rows),
                "page_info": {"page": 1, "page_size": len(rows), "total_number": len(rows), "total_page": 1},
                "raw_request_ids": raw_request_ids or [],
                "attempts": attempts or [],
            }
        return {
            "status": STATUS_DEGRADED,
            "phase": phase,
            "generated_at": now,
            "tool": tool,
            "backend": backend,
            "auth_status": auth_status,
            "params_hash": _params_hash(params),
            "depends_on": depends_on or [],
            "rows": [],
            "row_count": 0,
            "page_info": {},
            "raw_request_ids": raw_request_ids or [],
            "attempts": attempts or [],
            "error": f"Unexpected top-level type: {type(unwrapped).__name__}",
        }

    # Check for error responses
    error_msg = unwrapped.get("error") or unwrapped.get("message") or ""
    if str(error_msg).strip().upper() == "OK":
        error_msg = ""
    code = unwrapped.get("code", 0)

    if error_msg or code not in (0, 200):
        status = classify_error(str(error_msg or code))
        return {
            "status": status,
            "phase": phase,
            "generated_at": now,
            "tool": tool,
            "backend": backend,
            "auth_status": auth_status,
            "params_hash": _params_hash(params),
            "depends_on": depends_on or [],
            "rows": [],
            "row_count": 0,
            "page_info": {},
            "raw_request_ids": raw_request_ids or [],
            "attempts": attempts or [],
            "error": error_msg or str(code),
            "raw_excerpt": json.dumps(unwrapped, ensure_ascii=False)[:500],
        }

    # Extract rows and page_info
    rows = _extract_rows_from_payload(unwrapped)
    page_info = _extract_page_info(unwrapped)

    # Determine status
    existing_status = unwrapped.get("status")
    if existing_status in {STATUS_OK, STATUS_SUPPORTED_EMPTY, STATUS_PARTIAL, STATUS_DEGRADED, STATUS_UNSUPPORTED}:
        status = existing_status
    elif rows:
        status = STATUS_OK
    else:
        status = STATUS_SUPPORTED_EMPTY

    row_count = len(rows)
    total_number = page_info.get("total_number")
    total_page = page_info.get("total_page", 1)

    # Detect pagination issues
    if status == STATUS_OK and isinstance(total_number, int) and total_number > row_count:
        status = STATUS_PARTIAL
    elif status == STATUS_OK and isinstance(total_page, int) and total_page > 1 and row_count > 0:
        status = STATUS_PARTIAL

    result: dict[str, Any] = {
        "status": status,
        "phase": phase,
        "generated_at": now,
        "tool": tool,
        "backend": backend,
        "auth_status": auth_status,
        "params_hash": _params_hash(params),
        "depends_on": depends_on or [],
        "rows": rows,
        "row_count": row_count,
        "page_info": page_info or {"page": 1, "page_size": row_count, "total_number": row_count, "total_page": 1},
        "raw_request_ids": raw_request_ids or [],
        "attempts": attempts or [],
    }

    if error_msg:
        result["error"] = error_msg

    return result


def merge_pages(pages: list[dict[str, Any]], *, tool: str = "", phase: str = "", depends_on: list[str] | None = None) -> dict[str, Any]:
    """Merge multiple normalized page responses into one consolidated source.

    Args:
        pages: List of normalized source dicts (one per page).
        tool: MCP tool name.
        phase: Pipeline phase.
        depends_on: Dependency list.

    Returns:
        Merged source dict with all rows combined and merged_page_info.
    """
    now = datetime.now(timezone.utc).isoformat()
    if not pages:
        return {
            "status": STATUS_SUPPORTED_EMPTY,
            "phase": phase,
            "generated_at": now,
            "tool": tool,
            "params_hash": pages[0].get("params_hash", "") if pages else "",
            "depends_on": depends_on or [],
            "rows": [],
            "row_count": 0,
            "page_info": {},
            "merged_page_info": {"total_pages": 0},
            "raw_request_ids": [],
        }

    all_rows: list[dict[str, Any]] = []
    all_request_ids: list[str] = []
    all_attempts: list[dict[str, Any]] = []
    statuses: set[str] = set()
    per_page_info: list[dict[str, Any]] = []
    total_number = 0

    for i, page in enumerate(pages):
        page_rows = page.get("rows") or []
        all_rows.extend(page_rows)
        all_request_ids.extend(page.get("raw_request_ids") or [])
        all_attempts.extend(page.get("attempts") or [])
        statuses.add(page.get("status", STATUS_OK))
        pi = page.get("page_info") or {}
        per_page_info.append({"page_index": i, **pi})
        tn = pi.get("total_number")
        if isinstance(tn, int) and tn > total_number:
            total_number = tn

    overall_status = STATUS_OK
    if STATUS_DEGRADED in statuses:
        overall_status = STATUS_DEGRADED
    elif total_number and len(all_rows) >= total_number:
        overall_status = STATUS_OK
    elif STATUS_PARTIAL in statuses:
        overall_status = STATUS_PARTIAL
    elif not all_rows:
        overall_status = STATUS_SUPPORTED_EMPTY

    merged: dict[str, Any] = {
        "status": overall_status,
        "phase": phase,
        "generated_at": now,
        "tool": tool,
        "backend": pages[0].get("backend", ""),
        "auth_status": pages[0].get("auth_status", ""),
        "params_hash": pages[0].get("params_hash", ""),
        "depends_on": depends_on or [],
        "rows": all_rows,
        "row_count": len(all_rows),
        "page_info": {
            "page": 1,
            "page_size": len(all_rows),
            "total_number": total_number or len(all_rows),
            "total_page": 1,
        },
        "merged_page_info": {
            "total_pages": len(pages),
            "per_page": per_page_info,
            "merged": True,
        },
        "raw_request_ids": all_request_ids,
        "attempts": all_attempts,
    }
    return merged


def normalize_file(
    input_path: Path,
    output_path: Path,
    *,
    tool: str = "",
    phase: str = "",
    depends_on: list[str] | None = None,
    params: dict[str, Any] | None = None,
    attempts: list[dict[str, Any]] | None = None,
    backend: str = "",
    auth_status: str = "",
    is_multi_page: bool = False,
    page_files: list[Path] | None = None,
) -> dict[str, Any]:
    """Read a raw MCP response file, normalize it, and write the output.

    If is_multi_page is True and page_files is provided, merges all pages.
    """
    if is_multi_page and page_files:
        pages: list[dict[str, Any]] = []
        for pf in page_files:
            raw = json.loads(pf.read_text(encoding="utf-8"))
            normalized = normalize(raw, tool=tool, phase=phase, depends_on=depends_on, params=params, attempts=attempts, backend=backend, auth_status=auth_status)
            pages.append(normalized)
        result = merge_pages(pages, tool=tool, phase=phase, depends_on=depends_on)
        result["backend"] = backend
        result["auth_status"] = auth_status
    else:
        raw_text = input_path.read_text(encoding="utf-8")
        result = normalize(raw_text, tool=tool, phase=phase, depends_on=depends_on, params=params, attempts=attempts, backend=backend, auth_status=auth_status)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(output_path, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Normalize a TikTok MCP raw response into creatiads source contract."
    )
    parser.add_argument("--input", required=True, type=Path, help="Raw MCP response JSON file")
    parser.add_argument("--output", required=True, type=Path, help="Normalized output path")
    parser.add_argument("--tool", default="", help="MCP tool name")
    parser.add_argument("--phase", default="", help="Pipeline phase")
    parser.add_argument("--depends-on", nargs="*", default=[], help="Source IDs this depends on")
    parser.add_argument("--params-file", type=Path, help="JSON file with the MCP params used")
    parser.add_argument("--attempts-file", type=Path, help="JSON file with retry/dispatcher attempts")
    parser.add_argument("--backend", default="", help="Execution backend (native_agent_mcp or mcp_subagent_executor)")
    parser.add_argument("--auth-status", default="", help="Legacy executor auth status")
    parser.add_argument("--merge-pages", nargs="*", type=Path, default=[], help="Multiple page files to merge")
    args = parser.parse_args()

    params = None
    if args.params_file and args.params_file.exists():
        params = json.loads(args.params_file.read_text(encoding="utf-8"))
    attempts = None
    if args.attempts_file and args.attempts_file.exists():
        loaded = json.loads(args.attempts_file.read_text(encoding="utf-8"))
        attempts = loaded if isinstance(loaded, list) else [loaded]

    is_multi = bool(args.merge_pages)
    result = normalize_file(
        args.input, args.output,
        tool=args.tool, phase=args.phase,
        depends_on=args.depends_on,
        params=params,
        attempts=attempts,
        backend=args.backend,
        auth_status=args.auth_status,
        is_multi_page=is_multi,
        page_files=args.merge_pages if is_multi else None,
    )
    print(json.dumps({
        "output": str(args.output),
        "status": result["status"],
        "row_count": result["row_count"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
