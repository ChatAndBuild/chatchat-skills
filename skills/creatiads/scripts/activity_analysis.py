#!/usr/bin/env python3
"""Activity changelog, targeted insights, daily breakdown, and activity factors.

Uses MCP changelog data from pre-fetched sources.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    from utils import STATUS_OK, extract_rows, write_json
    from tiktok_adapter import _extract_changelog_rows
except ImportError:  # pragma: no cover
    from .utils import STATUS_OK, extract_rows, write_json
    from .tiktok_adapter import _extract_changelog_rows


OPERATION_AREAS = {
    "budget_or_bid": frozenset({"budget", "bid", "bidding", "daily budget", "lifetime budget"}),
    "status": frozenset({"enable", "disable", "pause", "resume", "active", "inactive", "delete"}),
    "review_or_policy": frozenset({"review", "reject", "policy", "disapprove", "approved"}),
    "creative_or_material": frozenset({"creative", "video", "image", "material", "upload", "text"}),
    "targeting": frozenset({"target", "audience", "placement", "location", "interest", "behavior"}),
    "settings_or_name": frozenset({"name", "settings", "optimization", "schedule", "time", "daypart"}),
}


def _parse_csv_rows(file_data: Any) -> list[dict[str, Any]]:
    """Decode changelog file_data when returned as CSV or encoded text."""
    if isinstance(file_data, list):
        return file_data
    return _extract_changelog_rows(file_data)


def _first(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in row and row.get(key) not in (None, ""):
            return row.get(key)
    lower_map = {str(k).lower(): v for k, v in row.items()}
    for key in keys:
        value = lower_map.get(key.lower())
        if value not in (None, ""):
            return value
    return ""


def _normalize_object_level(value: Any) -> str:
    text = str(value or "").strip().lower().replace("_", " ")
    if text in {"campaign", "campaigns"}:
        return "campaign"
    if text in {"ad group", "adgroup", "ad groups", "adgroups"}:
        return "adgroup"
    if text in {"ad", "ads"}:
        return "ad"
    if text in {"advertiser", "account"}:
        return "advertiser"
    return str(value or "").strip()


def _parse_activity_details(value: Any) -> tuple[str, str]:
    if isinstance(value, (dict, list)):
        parsed = value
    else:
        text = str(value or "").strip()
        if not text:
            return "", ""
        try:
            parsed = json.loads(text)
        except Exception:
            return "", text

    actions: list[str] = []
    details: list[str] = []
    items = parsed if isinstance(parsed, list) else [parsed]
    for item in items:
        if not isinstance(item, dict):
            details.append(str(item))
            continue
        action = str(item.get("action") or item.get("type") or "").strip()
        name = str(item.get("name") or item.get("field") or "").strip()
        if action:
            actions.append(action)
        parts = [part for part in (name, action) if part]
        before_after = item.get("before_after") or item.get("change") or []
        if isinstance(before_after, list):
            for change in before_after[:3]:
                if isinstance(change, dict):
                    before = change.get("before")
                    after = change.get("after")
                    if before not in (None, "") or after not in (None, ""):
                        parts.append(f"{before} -> {after}")
        elif isinstance(before_after, dict):
            before = before_after.get("before")
            after = before_after.get("after")
            if before not in (None, "") or after not in (None, ""):
                parts.append(f"{before} -> {after}")
        if parts:
            details.append(" | ".join(parts))
    return ", ".join(dict.fromkeys(actions)), "; ".join(details)


def normalize_activity_rows(raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in raw_rows:
        detail_action, detail_text = _parse_activity_details(
            _first(row, "Activity details", "activity_details", "details", "description", "change")
        )
        text = json.dumps(row, ensure_ascii=False).lower()
        area = "settings_or_name"
        for candidate, tokens in OPERATION_AREAS.items():
            if any(token in text for token in tokens):
                area = candidate
                break
        normalized.append({
            "date": str(_first(row, "date", "Time", "operation_time", "create_time")),
            "object_level": _normalize_object_level(_first(row, "object_type", "log_object_type", "object_level", "level")),
            "object_id": str(_first(row, "object_id", "Object ID", "id")),
            "object_name": str(_first(row, "object_name", "Object Name", "Object")),
            "operation_type": str(_first(row, "operation", "action", "type")) or detail_action,
            "details": detail_text or str(_first(row, "details", "description", "change", "Activity details")),
            "actor": str(_first(row, "operator", "Operator", "user_name", "user")),
            "operation_area": area,
            "raw": row,
        })
    return normalized


def rank_activity_targets(rows: list[dict[str, Any]], limit: int = 20) -> list[dict[str, Any]]:
    counts: dict[str, int] = defaultdict(int)
    details: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = f"{row['object_level']}:{row['object_id']}"
        counts[key] += 1
        if len(details[key]) < 5:
            details[key].append(row)
    ranked = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    return [
        {
            "target": key,
            "object_level": key.split(":", 1)[0],
            "object_id": key.split(":", 1)[1] if ":" in key else "",
            "change_count": count,
            "operations": [r["operation_area"] for r in details[key][:5]],
            "sample_details": [r.get("details", "") for r in details[key][:3] if r.get("details")],
        }
        for key, count in ranked[:limit]
    ]


def build_activity_daily_breakdown(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    daily: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in rows:
        date = (row.get("date") or "")[:10]
        daily[date][row["operation_area"]] += 1
    return [{"date": date, **dict(areas)} for date, areas in sorted(daily.items())]


def build_activity_factors(normalized_rows: list[dict[str, Any]], limit: int = 20) -> dict[str, Any]:
    area_counts: dict[str, int] = defaultdict(int)
    for row in normalized_rows:
        area_counts[row["operation_area"]] += 1
    ranked = [{"area": area, "count": count} for area, count in sorted(area_counts.items(), key=lambda item: item[1], reverse=True)]
    targets = rank_activity_targets(normalized_rows, limit=limit)
    daily = build_activity_daily_breakdown(normalized_rows)
    conclusions: list[str] = []
    if area_counts:
        top_area = ranked[0]["area"]
        conclusions.append(f"{len(normalized_rows)} activity changes detected; primary area: {top_area}.")
        if len(targets) >= 3:
            conclusions.append(f"Multi-object changes detected on {len(targets)} targets — possible coordinated operation.")
    return {
        "status": STATUS_OK if normalized_rows else "supported_empty",
        "ranked_factors": ranked,
        "rows": ranked,
        "activity_targets": targets,
        "daily_breakdown": daily,
        "summary": {"rows_parsed": len(normalized_rows), "target_count": len(targets)},
        "conclusions": conclusions,
        "rows_parsed": len(normalized_rows),
    }


def _flat(row: dict[str, Any]) -> dict[str, Any]:
    flat: dict[str, Any] = {}
    if isinstance(row.get("dimensions"), dict):
        flat.update(row["dimensions"])
    if isinstance(row.get("metrics"), dict):
        flat.update(row["metrics"])
    for key, value in row.items():
        if key not in {"dimensions", "metrics"} and key not in flat:
            flat[key] = value
    return flat


def _metric(row: dict[str, Any], key: str) -> float:
    value = _flat(row).get(key)
    try:
        return float(str(value or 0).replace(",", "").replace("%", ""))
    except Exception:
        return 0.0


def _source_rows(source: Any) -> list[dict[str, Any]]:
    if isinstance(source, list):
        return [row for row in source if isinstance(row, dict)]
    if isinstance(source, dict):
        rows = source.get("rows") or source.get("data") or source.get("items") or source.get("list") or []
        if isinstance(rows, dict):
            rows = rows.get("rows") or rows.get("list") or rows.get("items") or []
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    return []


def _id_key_for_level(level: str) -> str:
    return {"campaign": "campaign_id", "adgroup": "adgroup_id", "ad": "ad_id"}.get(level, "object_id")


def _index_by_level(
    rows_by_level: dict[str, Any] | None,
    targeted_results: dict[str, Any] | None = None,
) -> dict[str, dict[str, dict[str, Any]]]:
    indexes: dict[str, dict[str, dict[str, Any]]] = {"campaign": {}, "adgroup": {}, "ad": {}}
    for level in indexes:
        id_key = _id_key_for_level(level)
        rows = _source_rows((rows_by_level or {}).get(level))
        if targeted_results and _source_rows(targeted_results.get(level)):
            rows = _source_rows(targeted_results.get(level)) + rows
        for row in rows:
            key = str(_flat(row).get(id_key) or "")
            if key:
                indexes[level].setdefault(key, row)
    return indexes


def _kpi_snapshot(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return {}
    spend = _metric(row, "spend")
    clicks = _metric(row, "clicks")
    conversion = _metric(row, "conversion")
    result = _metric(row, "result")
    cost_per_conversion = _metric(row, "cost_per_conversion") or (spend / conversion if conversion else 0)
    cost_per_result = _metric(row, "cost_per_result") or (spend / result if result else 0)
    return {
        "spend": spend,
        "clicks": clicks,
        "conversion": conversion,
        "result": result,
        "cpa": cost_per_conversion or None,
        "cost_per_result": cost_per_result or None,
    }


def _daily_trend(rows: list[dict[str, Any]], level: str, object_id: str) -> list[dict[str, Any]]:
    id_key = _id_key_for_level(level)
    trend: list[dict[str, Any]] = []
    for row in rows:
        flat = _flat(row)
        if str(flat.get(id_key) or "") != object_id:
            continue
        trend.append({
            "date": str(flat.get("stat_time_day") or flat.get("date") or "")[:10],
            **_kpi_snapshot(row),
        })
    return sorted(trend, key=lambda item: item.get("date") or "")[:14]


def build_activity_factor_report(
    normalized_rows: list[dict[str, Any]],
    *,
    current_rows: dict[str, Any] | None = None,
    previous_rows: dict[str, Any] | None = None,
    targeted_results: dict[str, Any] | None = None,
    daily_results: dict[str, Any] | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    base = build_activity_factors(normalized_rows, limit=limit)
    current_index = _index_by_level(current_rows, targeted_results)
    previous_index = _index_by_level(previous_rows)
    daily_by_level = {level: _source_rows((daily_results or {}).get(level)) for level in ("campaign", "adgroup", "ad")}

    factors: list[dict[str, Any]] = []
    for target in base.get("activity_targets", [])[:limit]:
        if not isinstance(target, dict):
            continue
        level = str(target.get("object_level") or "")
        object_id = str(target.get("object_id") or "")
        current = current_index.get(level, {}).get(object_id)
        previous = previous_index.get(level, {}).get(object_id)
        current_kpi = _kpi_snapshot(current)
        previous_kpi = _kpi_snapshot(previous)
        delta = {}
        for key in ("spend", "clicks", "conversion", "result"):
            if key in current_kpi or key in previous_kpi:
                delta[key] = round(float(current_kpi.get(key) or 0) - float(previous_kpi.get(key) or 0), 4)
        factor = {
            **target,
            "current": current_kpi,
            "previous": previous_kpi,
            "delta": delta,
            "daily_trend": _daily_trend(daily_by_level.get(level, []), level, object_id),
            "matched_kpi": bool(current_kpi or previous_kpi),
        }
        factors.append(factor)

    matched_count = sum(1 for item in factors if item.get("matched_kpi"))
    conclusions = list(base.get("conclusions") or [])
    if matched_count:
        conclusions.append(f"{matched_count} changed objects were joined with KPI snapshots.")
    return {
        **base,
        "factors": factors,
        "rows": factors or base.get("rows", []),
        "activity_targets": factors or base.get("activity_targets", []),
        "summary": {
            **(base.get("summary") or {}),
            "matched_factor_count": matched_count,
            "factor_count": len(factors),
        },
        "conclusions": conclusions,
    }


def run_activity_analysis(
    *,
    changelog_result: dict[str, Any] | None = None,
    current_rows: dict[str, Any] | None = None,
    previous_rows: dict[str, Any] | None = None,
    targeted_results: dict[str, Any] | None = None,
    daily_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    changelog = changelog_result or {}
    raw_rows = changelog.get("rows") or []
    raw_status = changelog.get("status") or "unknown"
    if not raw_rows:
        csv_rows = _parse_csv_rows(changelog.get("file_data") or changelog.get("payload", {}).get("file_data"))
        if csv_rows:
            raw_rows = csv_rows
    normalized = normalize_activity_rows(raw_rows)
    factors = build_activity_factor_report(
        normalized,
        current_rows=current_rows,
        previous_rows=previous_rows,
        targeted_results=targeted_results,
        daily_results=daily_results,
    )
    # When the changelog MCP source itself is unavailable, the activity status
    # must reflect that — not silently disguise it as supported_empty.
    source_failed = raw_status not in {"ok", "supported_empty"} and not normalized
    activity_status = raw_status if source_failed else factors["status"]
    targeted = {"status": activity_status, "rows": normalized, "targets": factors["activity_targets"]}
    return {
        "activities": {
            "status": activity_status,
            "rows": normalized,
            "raw_status": raw_status,
            "task_id": changelog.get("task_id"),
            "task_status": changelog.get("task_status"),
            "checks": changelog.get("checks") or [],
            "download_phase": {
                "attempted": bool(changelog.get("download_response")),
                "status": (changelog.get("download_response") or {}).get("status") if isinstance(changelog.get("download_response"), dict) else None,
                "row_count": len(raw_rows),
            },
        },
        "activity_targeted_insights": targeted,
        "activity_daily_breakdown": {"status": activity_status, "rows": factors["daily_breakdown"]},
        "activity_factors": {**factors, "status": activity_status},
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Activity changelog analysis for TikTok reports.")
    parser.add_argument("--input", help="JSON file with pre-fetched changelog result")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    changelog_result = {}
    if args.input:
        changelog_result = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = run_activity_analysis(changelog_result=changelog_result)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
