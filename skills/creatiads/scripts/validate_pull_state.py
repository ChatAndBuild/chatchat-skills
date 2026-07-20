#!/usr/bin/env python3
"""Validate the pull state of a creatiads run against its pull_plan.json.

Reads the pull plan and the current state of sources/*.json to determine
whether the run can proceed to the next phase.  Enforces hard ordering and
completeness rules defined in the MCP Agent Pull Plan.

Usage:
  python3 creatiads/scripts/validate_pull_state.py \\
    --run-dir runs/7444033053753835536_2025w50_full
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from utils import STATUS_OK, STATUS_SUPPORTED_EMPTY, STATUS_PARTIAL
except ImportError:
    from .utils import STATUS_OK, STATUS_SUPPORTED_EMPTY, STATUS_PARTIAL


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

NATIVE_BACKEND = "native_agent_mcp"
SUBAGENT_BACKEND = "mcp_subagent_executor"
LEGACY_BRIDGE_BACKEND = "bridge_executor"
EXECUTOR_BACKEND_ALIASES = {SUBAGENT_BACKEND, LEGACY_BRIDGE_BACKEND}

# Sources that gate phase transitions
PRESET_GATE = ["user_type"]
REPORT_DATA_GATE = ["metric_preset"]
ANALYSIS_GATE = [
    "current_advertiser_insights",
    "previous_advertiser_insights",
    "current_campaigns",
    "previous_campaigns",
    "current_adgroups",
    "previous_adgroups",
    "current_ads",
    "previous_ads",
]


def _phase_index(phase: str) -> int:
    try:
        return PHASE_ORDER.index(phase)
    except ValueError:
        return 99


def _canonical_backend(backend: str) -> str:
    if backend == LEGACY_BRIDGE_BACKEND:
        return SUBAGENT_BACKEND
    return backend


def _read_source(sources_dir: Path, name: str) -> dict[str, Any] | None:
    path = sources_dir / f"{name}.json"
    if not path.exists():
        # Also check run_dir root for user_type.json, metric_preset.json
        alt = sources_dir.parent / f"{name}.json"
        if alt.exists():
            path = alt
        else:
            return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def validate(run_dir: Path) -> dict[str, Any]:
    plan_path = run_dir / "pull_plan.json"
    sources_dir = run_dir / "sources"

    if not plan_path.exists():
        return {
            "passed": False,
            "current_phase": "unknown",
            "next_allowed_phase": None,
            "missing_required": ["pull_plan.json"],
            "incomplete_pagination": [],
            "phase_order_errors": ["pull_plan.json not found"],
            "unsupported_without_attempts": [],
            "message": "pull_plan.json is missing — cannot validate pull state",
        }

    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "passed": False,
            "current_phase": "unknown",
            "next_allowed_phase": None,
            "missing_required": [],
            "incomplete_pagination": [],
            "phase_order_errors": [f"pull_plan.json is invalid: {exc}"],
            "unsupported_without_attempts": [],
            "message": "pull_plan.json is invalid JSON",
        }

    steps: list[dict[str, Any]] = plan.get("steps") or []
    depth = plan.get("depth", "standard")

    missing_required: list[str] = []
    incomplete_pagination: list[dict[str, Any]] = []
    phase_order_errors: list[str] = []
    unsupported_without_attempts: list[str] = []
    backend_errors: list[str] = []
    bridge_auth_errors: list[str] = []

    # Determine current phase: the highest phase for which ALL required sources exist
    completed_phases: set[str] = set()
    all_source_statuses: dict[str, str] = {}

    for step in steps:
        step_id = step.get("id", "")
        required = step.get("required", False)
        phase = step.get("phase", "")
        output = step.get("output", "")

        source_name = Path(output).stem if output else step_id
        source = _read_source(sources_dir, source_name)
        # Also check run_dir root
        if source is None and output:
            alt = run_dir / Path(output).name
            if alt.exists():
                try:
                    source = json.loads(alt.read_text(encoding="utf-8"))
                except Exception:
                    pass

        if source is None:
            if required:
                missing_required.append(step_id)
            continue

        status = source.get("status", STATUS_OK)
        all_source_statuses[source_name] = status

        # Pagination checks
        page_info = source.get("page_info") or {}
        merged_info = source.get("merged_page_info") or {}
        row_count = source.get("row_count", 0)
        total_number = page_info.get("total_number")
        total_page = page_info.get("total_page", 1)

        if status == STATUS_OK and phase != "classification":
            try:
                tn = int(total_number) if total_number is not None else None
            except (TypeError, ValueError):
                tn = None
            try:
                tp = int(total_page) if total_page is not None else 1
            except (TypeError, ValueError):
                tp = 1

            if tn is not None and tn > row_count:
                incomplete_pagination.append({
                    "source": step_id,
                    "file": output,
                    "row_count": row_count,
                    "total_number": tn,
                    "reason": "row_count < total_number",
                })
            elif tp > 1 and not merged_info.get("merged"):
                incomplete_pagination.append({
                    "source": step_id,
                    "file": output,
                    "total_page": tp,
                    "reason": "multi-page source not merged",
                })

        if required and status in {"permission_denied", "auth_required", "unsupported"}:
            missing_required.append(step_id)

        if status in {STATUS_PARTIAL, STATUS_OK, STATUS_SUPPORTED_EMPTY}:
            completed_phases.add(phase)

        # unsupported must have attempts
        if status == "unsupported":
            attempts = source.get("attempts")
            if not attempts or (isinstance(attempts, list) and len(attempts) == 0):
                unsupported_without_attempts.append(step_id)

    # ── Backend consistency checks ──────────────────────────────────
    # Same phase must use the same backend
    phase_backends: dict[str, set[str]] = {}
    for step in steps:
        step_id = step.get("id", "")
        phase = step.get("phase", "")
        output = step.get("output", "")
        source_name = Path(output).stem if output else step_id
        source = _read_source(sources_dir, source_name)
        if source is None and output:
            alt = run_dir / Path(output).name
            if alt.exists():
                try:
                    source = json.loads(alt.read_text(encoding="utf-8"))
                except Exception:
                    pass
        src_backend = _canonical_backend((source or {}).get("backend", ""))
        if step.get("l0_or_l1") == "local":
            continue
        if src_backend:
            if phase not in phase_backends:
                phase_backends[phase] = set()
            phase_backends[phase].add(src_backend)

    for phase, backends in phase_backends.items():
        if len(backends) > 1:
            backend_errors.append(
                f"phase '{phase}' has mixed backends: {sorted(backends)}"
            )

    # Bridge auth failure must not be swallowed
    for step in steps:
        step_id = step.get("id", "")
        output = step.get("output", "")
        source_name = Path(output).stem if output else step_id
        source = _read_source(sources_dir, source_name)
        if source is None:
            continue
        src_backend = source.get("backend", "")
        auth_status = source.get("auth_status", "")
        if src_backend in EXECUTOR_BACKEND_ALIASES and auth_status in {"auth_required", "permission_denied"}:
            if source.get("status") == STATUS_OK:
                bridge_auth_errors.append(
                    f"{step_id}: executor auth is '{auth_status}' but source status is 'ok' — auth failure swallowed"
                )

    # Fallback tasks must have attempts
    manifest_path = run_dir / "manifest.json"
    manifest: dict[str, Any] = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    fallbacks = manifest.get("backend_fallbacks") or []
    for fb in fallbacks:
        fb_task_id = fb.get("task_id", "")
        source = _read_source(sources_dir, fb_task_id)
        if source:
            attempts = source.get("attempts", [])
            if not attempts or (isinstance(attempts, list) and len(attempts) == 0):
                backend_errors.append(
                    f"{fb_task_id}: fallback recorded in manifest but source has no attempts"
                )

    # Determine the highest fully-completed phase
    current_phase = "bootstrap"
    for phase in PHASE_ORDER:
        phase_steps = [s for s in steps if s.get("phase") == phase]
        required_in_phase = [s for s in phase_steps if s.get("required")]
        if not required_in_phase:
            if phase in completed_phases:
                current_phase = phase
            continue
        all_done = all(
            s.get("id") not in missing_required
            for s in required_in_phase
        )
        if all_done:
            current_phase = phase
        else:
            break

    # Phase gate checks
    next_allowed = None
    ci = _phase_index(current_phase)

    # Check preset gate
    if ci < _phase_index("preset"):
        user_type = _read_source(sources_dir, "user_type")
        if user_type is None:
            phase_order_errors.append("user_type.json missing — cannot enter preset phase")
        else:
            next_allowed = "preset"
    elif ci < _phase_index("report_data"):
        metric_preset = _read_source(sources_dir, "metric_preset")
        if metric_preset is None:
            phase_order_errors.append("metric_preset.json missing — cannot enter report_data phase")
        else:
            next_allowed = "report_data"
    elif ci < _phase_index("analysis"):
        # Check analysis gate
        for gate_source in ANALYSIS_GATE:
            src = _read_source(sources_dir, gate_source)
            if src is None:
                phase_order_errors.append(f"{gate_source}.json missing — cannot enter analysis phase")
            else:
                pi = src.get("page_info") or {}
                tn = pi.get("total_number")
                rc = src.get("row_count", 0)
                try:
                    tn_i = int(tn) if tn is not None else None
                except (TypeError, ValueError):
                    tn_i = None
                if tn_i is not None and tn_i > rc:
                    phase_order_errors.append(
                        f"{gate_source}.json pagination incomplete (row_count={rc}, total_number={tn_i}) — cannot enter analysis"
                    )
        if not phase_order_errors:
            next_allowed = "analysis"
    else:
        next_allowed = "audit"

    # Audience placement retry check (plan §7)
    if depth in {"full", "deep"}:
        audience_placement = _read_source(sources_dir, "audience_placement")
        if audience_placement:
            ap_status = audience_placement.get("status")
            ap_attempts = audience_placement.get("attempts")
            ap_rows = audience_placement.get("rows") or []
            if ap_status == "unsupported" and (not ap_attempts or (isinstance(ap_attempts, list) and len(ap_attempts) == 0)):
                phase_order_errors.append(
                    "audience_placement status=unsupported but no retry attempts recorded"
                )
            elif ap_status == STATUS_OK and len(ap_rows) < 3 and depth == "full":
                page_info = audience_placement.get("page_info") or {}
                total_number = page_info.get("total_number")
                try:
                    total_number_i = int(total_number) if total_number is not None else None
                except (TypeError, ValueError):
                    total_number_i = None
                metadata = audience_placement.get("metadata") or {}
                analyzed_segments = metadata.get("segments_analyzed")
                try:
                    analyzed_segments_i = int(analyzed_segments) if analyzed_segments is not None else None
                except (TypeError, ValueError):
                    analyzed_segments_i = None
                # TikTok may legitimately return fewer than the historical 3 placement
                # buckets. Treat it as complete when page_info confirms all rows arrived.
                source_is_analyzed = analyzed_segments_i is not None and analyzed_segments_i == len(ap_rows)
                if not source_is_analyzed and (total_number_i is None or total_number_i > len(ap_rows)):
                    incomplete_pagination.append({
                        "source": "audience_placement",
                        "file": "sources/audience_placement.json",
                        "row_count": len(ap_rows),
                        "expected_min": 3,
                        "reason": "fewer placement rows than expected minimum (3)",
                    })

    passed = (
        not missing_required
        and not incomplete_pagination
        and not phase_order_errors
        and not unsupported_without_attempts
        and not backend_errors
        and not bridge_auth_errors
    )

    return {
        "passed": passed,
        "current_phase": current_phase,
        "next_allowed_phase": next_allowed,
        "missing_required": missing_required,
        "incomplete_pagination": incomplete_pagination,
        "phase_order_errors": phase_order_errors,
        "unsupported_without_attempts": unsupported_without_attempts,
        "backend_errors": backend_errors,
        "bridge_auth_errors": bridge_auth_errors,
        "all_source_statuses": all_source_statuses,
        "phase_backends": {phase: sorted(backends) for phase, backends in phase_backends.items()},
        "depth": depth,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate creatiads pull state against pull_plan.json."
    )
    parser.add_argument("--run-dir", required=True, type=Path)
    args = parser.parse_args()

    result = validate(args.run_dir)
    summary_path = args.run_dir / "validation_summary.json"
    summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
