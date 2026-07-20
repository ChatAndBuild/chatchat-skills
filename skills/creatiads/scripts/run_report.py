#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import subprocess
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    from classify_user_type import build_user_type_report
    from utils import STATUS_OK, STATUS_PARTIAL, STATUS_STRUCTURED_UNAVAILABLE, STATUS_SUPPORTED_EMPTY, extract_rows, write_json
    from metric_probe import recommend_metric_preset, run_tiktok_metric_probe
    from tiktok_adapter import select_top_ids, smart_plus_ids_from_ad_v2_rows
    from tiktok_app_landing_evidence import collect_app_landing_evidence
    from landing_app_analyzer import analyze_landing_app_paths as analyze_landing
    from creative_enrichment import build_creative_previews, build_creative_retention
    from activity_analysis import run_activity_analysis
    from audience_analysis import analyze_audience_breakdowns
    from validation_rebuild import diagnose_bottlenecks, validate_creative, validate_ad_link, validate_promoted_object
except ImportError:  # pragma: no cover
    from .classify_user_type import build_user_type_report
    from .utils import STATUS_OK, STATUS_PARTIAL, STATUS_STRUCTURED_UNAVAILABLE, STATUS_SUPPORTED_EMPTY, extract_rows, write_json
    from .metric_probe import recommend_metric_preset, run_tiktok_metric_probe
    from .tiktok_adapter import select_top_ids, smart_plus_ids_from_ad_v2_rows
    from .tiktok_app_landing_evidence import collect_app_landing_evidence
    from .landing_app_analyzer import analyze_landing_app_paths as analyze_landing
    from .creative_enrichment import build_creative_previews, build_creative_retention
    from .activity_analysis import run_activity_analysis
    from .audience_analysis import analyze_audience_breakdowns
    from .validation_rebuild import diagnose_bottlenecks, validate_creative, validate_ad_link, validate_promoted_object


RUN_ROOT = Path("build/creatiads_runs")
CORE_METRICS = [
    "spend",
    "impressions",
    "clicks",
    "ctr",
    "cpc",
    "cpm",
    "conversion",
    "cost_per_conversion",
    "result",
    "cost_per_result",
    "total_purchase_value",
    "complete_payment_roas",
]
CAMPAIGN_ATTR_METRICS = ["campaign_name", "objective_type", "campaign_automation_type"]
CAMPAIGN_STRUCTURE_FIELDS = [
    "campaign_id", "campaign_name", "objective_type",
    "campaign_automation_type", "operation_status", "secondary_status",
]
ADGROUP_ATTR_METRICS = [
    "campaign_id",
    "campaign_name",
    "campaign_automation_type",
    "adgroup_name",
    "promotion_type",
    "billing_event",
    "placement_type",
    "adgroup_download_url",
]
ADGROUP_STRUCTURE_FIELDS = [
    "adgroup_id", "adgroup_name", "campaign_id", "campaign_name",
    "promotion_type", "promotion_target_type", "app_id", "app_download_url",
    "app_type", "optimization_goal", "billing_event", "operation_status",
    "secondary_status",
]
AD_ATTR_METRICS = [
    "campaign_id",
    "campaign_name",
    "campaign_automation_type",
    "adgroup_id",
    "adgroup_name",
    "ad_name",
    "ad_url",
    "adgroup_download_url",
    "objective_type",
    "promotion_type",
    "tt_app_name",
    "mobile_app_id",
    "call_to_action",
]
AD_STRUCTURE_FIELDS = [
    "ad_id", "smart_plus_ad_id", "ad_name", "campaign_id", "campaign_name",
    "campaign_automation_type", "adgroup_id", "adgroup_name",
    "landing_page_url", "landing_page_urls", "creative_type", "ad_text",
    "ad_texts", "call_to_action", "call_to_action_id", "identity_id", "identity_type",
    "identity_authorized_bc_id", "ad_format", "image_mode", "playable_url",
    "profile_image_url", "avatar_icon_web_uri",
    "app_name", "page_id", "video_id", "image_ids", "tracking_pixel_id", "tiktok_item_id",
    "catalog_id", "catalog_authorized_bc_id", "product_ids", "product_set_id",
]
VIDEO_METRICS = [
    "video_play_actions",
    "video_watched_2s",
    "video_watched_6s",
    "video_views_p25",
    "video_views_p50",
    "video_views_p75",
    "video_views_p100",
    "average_video_play",
    "engaged_view",
]

RESULT_OBJECTIVE_TOKENS = {
    "ENGAGEMENT", "TRAFFIC", "REACH", "VIDEO_VIEW", "LEAD_GENERATION",
    "CONVERSATION", "CLICK", "MESSAGING", "FOLLOWERS",
}

SOURCE_PHASES = {
    "mcp_ready": "bootstrap",
    "current_account": "bootstrap",
    "advertiser_info": "bootstrap",
    "app_list": "classification",
    "catalog_list": "classification",
    "shop_list": "classification",
    "smart_plus_ads": "classification",
    "apps": "enrichment",
    "user_type_evidence": "classification",
    "user_type": "classification",
    "metric_preset": "preset",
    "metric_probe": "preset",
    "metric_probe_results": "preset",
}

SOURCE_ALIASES = {
    "current_campaigns": ["current_campaign_insights"],
    "current_adgroups": ["current_adgroup_insights"],
    "current_ads": ["current_ad_insights"],
    "previous_campaigns": ["previous_campaign_insights"],
    "previous_adgroups": ["previous_adgroup_insights"],
    "previous_ads": ["previous_ad_insights"],
    "landing_app_paths": ["landing_pages"],
}


def _infer_phase(name: str) -> str:
    if name in SOURCE_PHASES:
        return SOURCE_PHASES[name]
    if name.startswith("classification_"):
        return "classification"
    if name.startswith(("current_", "previous_")):
        return "report_data"
    if name.endswith("_structure"):
        return "enrichment"
    if name.startswith(("audience_", "creative_", "activity_", "landing_", "targeted_", "bottleneck_")):
        return "enrichment"
    return "analysis"


# Depth plan: defines which sources are queried at each depth
DEPTH_PLANS: dict[str, dict[str, Any]] = {
    "fast": {
        "sources": ["mcp_ready", "current_account", "current_advertiser_insights", "current_campaigns", "current_ads",
                    "current_ad_v2_insights", "user_type", "metric_preset",
                    "previous_advertiser_insights", "previous_campaigns",
                    "audience_country", "smart_plus_ads", "landing_app_paths",
                    "activities", "activity_targeted_insights", "activity_daily_breakdown", "activity_factors"],
        "previous": True,
        "audience": True,
        "previews": False,
        "landing": True,
        "retention": False,
        "activities": True,
        "metric_probe": False,
    },
    "standard": {
        "sources": ["mcp_ready", "current_account", "current_advertiser_insights", "current_campaigns", "current_adgroups", "current_ads",
                    "current_ad_v2_insights", "user_type", "metric_preset",
                    "previous_advertiser_insights", "previous_campaigns", "previous_adgroups", "previous_ads",
                    "audience_country", "audience_age_gender", "audience_placement",
                    "smart_plus_ads", "apps", "landing_app_paths",
                    "campaign_structure", "adgroup_structure", "ad_structure",
                    "creative_retention", "creative_previews",
                    "activities", "activity_targeted_insights", "activity_daily_breakdown", "activity_factors",
                    "targeted_creative_retention"],
        "previous": True,
        "audience": True,
        "previews": True,
        "landing": True,
        "retention": True,
        "activities": True,
        "metric_probe": False,
    },
    "full": {
        "sources": ["mcp_ready", "current_account", "current_advertiser_insights", "current_campaigns", "current_adgroups", "current_ads",
                    "current_ad_v2_insights", "user_type", "metric_preset", "metric_probe",
                    "previous_advertiser_insights", "previous_campaigns", "previous_adgroups", "previous_ads",
                    "audience_country", "audience_age_gender", "audience_placement", "audience_device",
                    "smart_plus_ads", "apps", "landing_app_paths",
                    "campaign_structure", "adgroup_structure", "ad_structure",
                    "creative_retention", "creative_previews",
                    "activities", "activity_targeted_insights", "activity_daily_breakdown", "activity_factors",
                    "targeted_creative_retention"],
        "previous": True,
        "audience": True,
        "previews": True,
        "landing": True,
        "retention": True,
        "activities": True,
        "metric_probe": True,
    },
    "deep": {
        "sources": ["mcp_ready", "current_account", "current_advertiser_insights", "current_campaigns", "current_adgroups", "current_ads",
                    "current_ad_v2_insights", "user_type", "metric_preset", "metric_probe",
                    "previous_advertiser_insights", "previous_campaigns", "previous_adgroups", "previous_ads",
                    "audience_country", "audience_age_gender", "audience_placement", "audience_device",
                    "smart_plus_ads", "apps", "landing_app_paths",
                    "campaign_structure", "adgroup_structure", "ad_structure",
                    "creative_retention", "creative_previews",
                    "activities", "activity_targeted_insights", "activity_daily_breakdown", "activity_factors",
                    "targeted_creative_retention", "advertiser_level_changelog",
                    "bottleneck_diagnosis"],
        "previous": True,
        "audience": True,
        "previews": True,
        "landing": True,
        "retention": True,
        "activities": True,
        "metric_probe": True,
    },
}


@dataclass(frozen=True)
class PeriodWindow:
    since: str
    until: str
    previous_since: str | None = None
    previous_until: str | None = None


def _date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def resolve_period(period: str, *, since: str | None = None, until: str | None = None, previous_since: str | None = None, previous_until: str | None = None) -> PeriodWindow:
    today = datetime.now().date()
    if period == "daily":
        current = _date(until) if until else today - timedelta(days=1)
        prev = current - timedelta(days=1)
        return PeriodWindow(str(current), str(current), str(prev), str(prev))
    if period == "weekly":
        end = _date(until) if until else today - timedelta(days=1)
        start = _date(since) if since else end - timedelta(days=6)
        prev_end = _date(previous_until) if previous_until else start - timedelta(days=1)
        prev_start = _date(previous_since) if previous_since else prev_end - timedelta(days=(end - start).days)
        return PeriodWindow(str(start), str(end), str(prev_start), str(prev_end))
    if not since or not until:
        raise ValueError("custom period requires --since and --until")
    start = _date(since)
    end = _date(until)
    if previous_since and previous_until:
        return PeriodWindow(str(start), str(end), previous_since, previous_until)
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=(end - start).days)
    return PeriodWindow(str(start), str(end), str(prev_start), str(prev_end))


def report_period_label(period: str) -> str:
    return {
        "daily": "日报",
        "weekly": "周报",
    }.get(period, "报告")


def report_period_noun(period: str) -> str:
    return {
        "daily": "本日",
        "weekly": "本周",
    }.get(period, "本期")


def _metric(row: dict[str, Any], key: str) -> float:
    value = row.get(key)
    if value is None and isinstance(row.get("metrics"), dict):
        value = row["metrics"].get(key)
    try:
        return float(str(value or 0).replace(",", "").replace("%", ""))
    except Exception:
        return 0.0


def _dimension(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    if value is None and isinstance(row.get("dimensions"), dict):
        value = row["dimensions"].get(key)
    if value is None and isinstance(row.get("metrics"), dict):
        value = row["metrics"].get(key)
    return str(value or "")


def _sum(rows: list[dict[str, Any]], key: str) -> float:
    return round(sum(_metric(row, key) for row in rows), 4)


def _conversion(row: dict[str, Any]) -> float:
    return _metric(row, "conversion")


def _primary_result(row: dict[str, Any]) -> tuple[float, str]:
    conversion = _metric(row, "conversion")
    result = _metric(row, "result")
    objective = _dimension(row, "objective_type").upper()
    if result and not conversion and any(token in objective for token in RESULT_OBJECTIVE_TOKENS):
        return result, "result"
    return conversion, "conversion"


def _primary_cost(row: dict[str, Any]) -> tuple[float | None, str]:
    value, label = _primary_result(row)
    spend = _metric(row, "spend")
    if label == "result":
        cost = _metric(row, "cost_per_result") or (spend / value if value else 0)
        return (cost if cost else None), "cost_per_result"
    cost = _metric(row, "cost_per_conversion") or (spend / value if value else 0)
    return (cost if cost else None), "cost_per_conversion"


def _summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    spend = _sum(rows, "spend")
    impressions = _sum(rows, "impressions")
    clicks = _sum(rows, "clicks")
    conversion = round(sum(_conversion(row) for row in rows), 4)
    result = round(sum(_metric(row, "result") for row in rows), 4)
    return {
        "spend": spend,
        "impressions": impressions,
        "clicks": clicks,
        "conversion": conversion,
        "result": result,
        "ctr": clicks / impressions if impressions else None,
        "cpc": spend / clicks if clicks else None,
        "cpm": spend / impressions * 1000 if impressions else None,
        "cpa": spend / conversion if conversion else None,
    }


def _flat_row(row: dict[str, Any]) -> dict[str, Any]:
    flat: dict[str, Any] = {}
    if isinstance(row.get("dimensions"), dict):
        flat.update(row["dimensions"])
    if isinstance(row.get("metrics"), dict):
        flat.update(row["metrics"])
    for key, value in row.items():
        if key not in {"dimensions", "metrics"} and key not in flat:
            flat[key] = value
    return flat


def _string_value(row: dict[str, Any], key: str) -> str:
    return str(_flat_row(row).get(key) or "")


def _merge_fields_from_reference(
    rows: list[dict[str, Any]],
    reference_rows: list[dict[str, Any]],
    key: str,
    fields: list[str],
) -> list[dict[str, Any]]:
    """Backfill names/attributes when a report source fell back to lean metrics."""
    best_ref: dict[str, dict[str, Any]] = {}
    for ref in reference_rows:
        ref_key = _string_value(ref, key)
        if not ref_key:
            continue
        current = best_ref.get(ref_key)
        if current is None or _metric(ref, "spend") > _metric(current, "spend"):
            best_ref[ref_key] = ref

    merged: list[dict[str, Any]] = []
    for row in rows:
        clone = json.loads(json.dumps(row, ensure_ascii=False))
        ref = best_ref.get(_string_value(clone, key))
        if not ref:
            merged.append(clone)
            continue
        clone.setdefault("metrics", {})
        for field in fields:
            if _string_value(clone, field):
                continue
            value = _flat_row(ref).get(field)
            if value not in (None, ""):
                clone["metrics"][field] = value
        merged.append(clone)
    return merged


def _needs_activity_rebuild(source: dict[str, Any]) -> bool:
    rows = source.get("rows") or []
    if not rows:
        return False
    checked = [row for row in rows[:20] if isinstance(row, dict)]
    if not checked:
        return False
    blank_objects = sum(1 for row in checked if not row.get("object_id") and not row.get("object_level"))
    return blank_objects >= max(1, len(checked) // 2)


def _needs_activity_factor_rebuild(source: dict[str, Any]) -> bool:
    if source.get("status") == "not_queried":
        return False
    if source.get("status") == STATUS_OK and source.get("ranked_factors") and not source.get("rows"):
        return True
    factors = source.get("factors")
    if source.get("status") == STATUS_OK and source.get("activity_targets") and not factors:
        return True
    if isinstance(factors, list) and factors:
        sample = next((item for item in factors if isinstance(item, dict)), None)
        if sample and not (sample.get("current") or sample.get("current_kpi") or sample.get("daily_trend")):
            return True
    return False


def _has_activity_content(source: dict[str, Any]) -> bool:
    return bool(source.get("rows") or source.get("ranked_factors") or source.get("activity_targets"))


def _normalize_landing_payload(payload: dict[str, Any]) -> dict[str, Any]:
    rows = payload.get("rows") or []
    normalized_rows: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        conversion = row.get("conversion")
        if conversion is None:
            conversion = row.get("conversions", row.get("result"))
        value = row.get("value")
        if value is None:
            value = row.get("revenue")
        normalized_rows.append({
            **row,
            "normalized_url": row.get("normalized_url") or row.get("url") or row.get("landing_url") or "",
            "url_type": row.get("url_type") or row.get("url_source") or row.get("source") or "",
            "source": row.get("source") or row.get("url_source") or "",
            "conversion": conversion or 0,
            "value": value or 0,
            "cost": row.get("cost", row.get("cpa")),
            "roas": row.get("roas"),
        })
    return {
        "status": payload.get("status") or STATUS_OK,
        "rows": normalized_rows,
        "row_count": len(normalized_rows),
        "phase": payload.get("phase") or "enrichment",
        "generated_at": payload.get("generated_at") or datetime.now(timezone.utc).isoformat(),
        "source": payload.get("source", "precomputed_landing_source"),
        "raw_summary": {k: payload.get(k) for k in ("ad_count", "group_count", "skipped_url_probe_count", "no_url_count") if k in payload},
    }


def _normalize_retention_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("winners") or payload.get("fatigue_candidates"):
        return payload
    sections = payload.get("sections") if isinstance(payload.get("sections"), dict) else {}
    winners = sections.get("top_retention_creatives") or sections.get("creative_winners") or []
    fatigue = sections.get("fatigue_candidates") or sections.get("low_quality_creatives") or []
    rows = []
    for value in sections.values():
        if isinstance(value, list):
            rows.extend(item for item in value if isinstance(item, dict))
    return {
        **payload,
        "status": payload.get("status") or STATUS_OK,
        "rows": rows,
        "winners": winners,
        "fatigue_candidates": fatigue,
        "coverage": payload.get("core_metric_coverage", {}),
    }


def build_targeted_creative_retention_payload(
    *,
    existing_targeted: dict[str, Any],
    raw_targeted: dict[str, Any],
    current_ad_rows: list[dict[str, Any]],
    raw_is_fresh: bool,
) -> dict[str, Any]:
    """Prefer fresh raw retention evidence over stale derived retention output."""
    existing_status = existing_targeted.get("status")
    raw_status = raw_targeted.get("status")
    if raw_status != "not_queried" and (raw_is_fresh or existing_status == "not_queried"):
        payload = build_creative_retention(raw_targeted.get("rows") or [])
        metadata = dict(payload.get("metadata") or {})
        metadata.update({
            "rebuilt_from": "targeted_creative_retention_raw",
            "raw_is_fresh": bool(raw_is_fresh),
        })
        payload["metadata"] = metadata
        return payload
    if existing_status != "not_queried":
        return _normalize_retention_payload(existing_targeted)
    if raw_status != "not_queried":
        payload = build_creative_retention(raw_targeted.get("rows") or [])
        payload.setdefault("metadata", {})["rebuilt_from"] = "targeted_creative_retention_raw"
        return payload
    payload = build_creative_retention(current_ad_rows)
    payload.setdefault("metadata", {})["rebuilt_from"] = "current_ads"
    return payload


def compact_manifest_summary(run_dir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_dir": str(run_dir),
        "validation_status": manifest.get("validation_status"),
        "completeness_passed": manifest.get("completeness_passed"),
        "audit_passed": manifest.get("audit_passed"),
        "source_count": len(manifest.get("source_files") or []),
        "file_count": len(manifest.get("files") or []),
        "degraded_source_count": len(manifest.get("degraded_sources") or []),
        "partial_source_count": len(manifest.get("partial_sources") or []),
        "not_queried_source_count": len(manifest.get("not_queried_sources") or []),
        "report_html": str(run_dir / "report.html") if (run_dir / "report.html").exists() else "",
        "report_audit": str(run_dir / "report_audit.json") if (run_dir / "report_audit.json").exists() else "",
    }


def _source_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("rows")
    if isinstance(rows, list):
        return [row for row in rows if isinstance(row, dict)]
    extracted = extract_rows(payload)
    return extracted if isinstance(extracted, list) else []


def _top_rows(rows: list[dict[str, Any]], id_key: str, limit: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in sorted(rows, key=lambda item: (_metric(item, "spend"), _conversion(item)), reverse=True):
        row_id = _dimension(row, id_key)
        if not row_id or row_id in seen:
            continue
        seen.add(row_id)
        selected.append(row)
        if len(selected) >= limit:
            break
    return selected


def build_structure_fallback(
    *,
    rows: list[dict[str, Any]],
    id_key: str,
    fields: list[str],
    limit: int,
    source: str,
) -> dict[str, Any]:
    output_rows: list[dict[str, Any]] = []
    for row in _top_rows(rows, id_key, limit):
        flat = _flat_row(row)
        output_rows.append({field: flat.get(field) for field in fields if flat.get(field) not in (None, "")})
    return {
        "status": STATUS_SUPPORTED_EMPTY if not output_rows else "partial",
        "rows": output_rows,
        "row_count": len(output_rows),
        "source": source,
        "warning": "MCP structure detail source was not available; derived from report rows.",
    }


def build_apps_summary(
    *,
    advertiser_id: str,
    start_date: str,
    end_date: str,
    user_type: dict[str, Any],
    campaign_rows: list[dict[str, Any]],
    adgroup_rows: list[dict[str, Any]],
    ad_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    campaigns = campaign_rows or user_type.get("campaigns") or []
    adgroups = adgroup_rows or user_type.get("adgroups") or []
    ads = ad_rows or user_type.get("ads") or []
    app_ids = sorted({value for row in [*campaigns, *adgroups, *ads] for value in (_dimension(row, "app_id"), _dimension(row, "mobile_app_id")) if value and value != "0"})
    app_names = sorted({value for row in [*campaigns, *adgroups, *ads] for value in (_dimension(row, "app_name"), _dimension(row, "tt_app_name")) if value and value != "-"})
    app_urls = sorted({value for row in [*campaigns, *adgroups, *ads] for value in (_dimension(row, "app_download_url"), _dimension(row, "adgroup_download_url")) if value and value != "-"})
    promotion_types = sorted({value for row in [*campaigns, *adgroups, *ads] for value in (_dimension(row, "promotion_type"), _dimension(row, "objective_type")) if value and value != "-"})
    row = {
        "app_key": app_ids[0] if app_ids else "unknown",
        "app_ids": app_ids,
        "app_names": app_names,
        "app_urls": app_urls,
        "promotion_types": promotion_types,
        "advertisers": [advertiser_id] if advertiser_id else [],
        "campaign_count": len({ _dimension(item, "campaign_id") for item in campaigns if _dimension(item, "campaign_id") }),
        "adgroup_count": len({ _dimension(item, "adgroup_id") for item in adgroups if _dimension(item, "adgroup_id") }),
        "ad_count": len({ _dimension(item, "ad_id") for item in ads if _dimension(item, "ad_id") }),
        "spend": _sum(campaigns, "spend") if campaigns else _sum(ads, "spend"),
        "impressions": _sum(campaigns, "impressions") if campaigns else _sum(ads, "impressions"),
        "clicks": _sum(campaigns, "clicks") if campaigns else _sum(ads, "clicks"),
        "conversions": round(sum(_conversion(item) for item in (campaigns or ads)), 4),
        "derived_user_type": user_type.get("derived_user_type"),
        "top_types": user_type.get("top_types") or [],
        "campaigns": _top_rows(campaigns, "campaign_id", 20),
    }
    impressions = float(row["impressions"] or 0)
    clicks = float(row["clicks"] or 0)
    row["ctr"] = round(clicks / impressions * 100, 4) if impressions else 0
    return {
        "status": STATUS_OK if campaigns or adgroups or ads else STATUS_SUPPORTED_EMPTY,
        "start_date": start_date,
        "end_date": end_date,
        "advertisers": [advertiser_id] if advertiser_id else [],
        "app_count": len(app_ids) or (1 if campaigns or adgroups or ads else 0),
        "total_spend": row["spend"],
        "rows": [row] if campaigns or adgroups or ads else [],
        "row_count": 1 if campaigns or adgroups or ads else 0,
    }


def _collect_tool_names(payload: Any) -> list[str]:
    names: list[str] = []
    if isinstance(payload, dict):
        tool = payload.get("tool")
        if isinstance(tool, str) and tool:
            names.append(tool)
        for value in payload.values():
            names.extend(_collect_tool_names(value))
    elif isinstance(payload, list):
        for item in payload:
            names.extend(_collect_tool_names(item))
    return names


def _collect_values(payload: Any, keys: set[str]) -> list[str]:
    found: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in keys:
                if isinstance(value, list):
                    found.extend(str(item) for item in value if item)
                elif value:
                    found.append(str(value))
            found.extend(_collect_values(value, keys))
    elif isinstance(payload, list):
        for item in payload:
            found.extend(_collect_values(item, keys))
    return sorted(set(found))


class TikTokReportRunner:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.data_dir = Path(args.data_dir) if args.data_dir else None
        if self.data_dir:
            self.sources_dir = self.data_dir / "sources"
        self.window = resolve_period(args.period, since=args.since, until=args.until, previous_since=args.previous_since, previous_until=args.previous_until)
        self.run_dir = self.data_dir or (Path(args.run_dir) if args.run_dir else RUN_ROOT / f"tiktok_{args.advertiser_id}_{args.period}_{args.depth}_{self.window.until}")
        if not self.data_dir:
            self.sources_dir = self.run_dir / "sources"
        self.depth_plan = DEPTH_PLANS.get(args.depth, DEPTH_PLANS["standard"])
        self.start_time = datetime.now(timezone.utc)
        self.source_durations: dict[str, float] = {}
        self.source_attempts: dict[str, int] = {}
        self.manifest: dict[str, Any] = {
            "platform": "tiktok",
            "advertiser_id": args.advertiser_id or "",
            "account_or_advertiser_id": args.advertiser_id or "",
            "period": args.period,
            "depth": args.depth,
            "since": self.window.since,
            "until": self.window.until,
            "previous_since": self.window.previous_since,
            "previous_until": self.window.previous_until,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "mcp_servers": {"tiktok": "tiktok-mcp"},
            "tools_used": [],
            "coverage": {},
            "source_files": [],
            "source_durations_ms": {},
            "source_attempts": {},
            "source_phases": {},
            "degraded_sources": [],
            "partial_sources": [],
            "not_queried_sources": [],
            "comparison_eligible": bool(self.window.previous_since and self.window.previous_until),
            "depth_plan_sources": self.depth_plan["sources"],
            "candidate_row_limits": {},
            "selected_row_counts": {},
            "dry_run": bool(getattr(args, "dry_run", False)),
            "data_dir_mode": bool(self.data_dir),
        }

    def _mark_partial(self, name: str) -> None:
        if name not in self.manifest["partial_sources"]:
            self.manifest["partial_sources"].append(name)

    def _mark_degraded(self, name: str, status: Any, **extra: Any) -> None:
        item = {"name": name, "status": status, **extra}
        for existing in self.manifest["degraded_sources"]:
            if isinstance(existing, dict) and existing.get("name") == name and existing.get("status") == status:
                existing.update(extra)
                return
        self.manifest["degraded_sources"].append(item)

    def _source_candidate_paths(self, name: str) -> list[tuple[str, Path]]:
        candidates = [
            (name, self.sources_dir / f"{name}.json"),
            (name, self.run_dir / f"{name}.json"),
        ]
        for alias in SOURCE_ALIASES.get(name, []):
            candidates.extend([
                (alias, self.sources_dir / f"{alias}.json"),
                (alias, self.run_dir / f"{alias}.json"),
            ])
        return candidates

    def _read_source(self, name: str) -> dict[str, Any]:
        """Read a pre-fetched source file from the sources directory."""
        found: tuple[str, Path] | None = None
        for source_name, path in self._source_candidate_paths(name):
            if path.exists():
                found = (source_name, path)
                break
        if not found:
            return {"status": "not_queried", "rows": []}
        source_name, path = found
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {"status": "degraded", "rows": [], "error": "Failed to parse source file"}
        rel = str(path.relative_to(self.run_dir))
        if rel not in self.manifest["source_files"]:
            self.manifest["source_files"].append(rel)
        status = data.get("status") if isinstance(data, dict) else STATUS_OK
        phase = data.get("phase") if isinstance(data, dict) else None
        self.manifest["source_phases"][name] = phase or _infer_phase(name)
        self.manifest["coverage"][name] = status or STATUS_OK
        if source_name != name:
            self.manifest.setdefault("source_aliases", {})[name] = source_name
        if status in {"partial"}:
            self._mark_partial(name)
        elif status not in {STATUS_OK, "supported_empty", "not_queried", None}:
            self._mark_degraded(name, status)
        for tool_name in _collect_tool_names(data):
            if tool_name not in self.manifest["tools_used"]:
                self.manifest["tools_used"].append(tool_name)
        return data

    def _source_file_path(self, name: str) -> Path | None:
        for _, path in self._source_candidate_paths(name):
            if path.exists():
                return path
        return None

    def _source_newer_than(self, source: str, target: str) -> bool:
        source_path = self._source_file_path(source)
        target_path = self._source_file_path(target)
        if not source_path:
            return False
        if not target_path:
            return True
        try:
            return source_path.stat().st_mtime > target_path.stat().st_mtime
        except OSError:
            return False

    def write_source(self, name: str, payload: Any, *, phase: str | None = None, tool: str | None = None, depends_on: list[str] | None = None) -> Any:
        path = self.sources_dir / f"{name}.json"
        if isinstance(payload, dict):
            payload = dict(payload)
            payload.setdefault("phase", phase or _infer_phase(name))
            payload.setdefault("generated_at", datetime.now(timezone.utc).isoformat())
            if tool:
                payload.setdefault("tool", tool)
            if depends_on:
                payload.setdefault("depends_on", depends_on)
        write_json(path, payload)
        rel = str(path.relative_to(self.run_dir))
        if rel not in self.manifest["source_files"]:
            self.manifest["source_files"].append(rel)
        status = payload.get("status") if isinstance(payload, dict) else STATUS_OK
        self.manifest["source_phases"][name] = (payload.get("phase") if isinstance(payload, dict) else None) or phase or _infer_phase(name)
        self.manifest["coverage"][name] = status or STATUS_OK
        if status in {"partial"}:
            self._mark_partial(name)
        elif status not in {STATUS_OK, "supported_empty", None}:
            self._mark_degraded(name, status)
        for tool_name in _collect_tool_names(payload):
            if tool_name not in self.manifest["tools_used"]:
                self.manifest["tools_used"].append(tool_name)
        return payload

    def source_exists(self, name: str) -> bool:
        return any(path.exists() for _, path in self._source_candidate_paths(name))

    def read_first_source(self, preferred: str, fallback: str) -> dict[str, Any]:
        if self.source_exists(preferred):
            return self._read_source(preferred)
        return self._read_source(fallback)

    def source_names(self) -> list[str]:
        return list(self.depth_plan["sources"])

    def pull_report_level(self, name: str, previous: bool = False) -> dict[str, Any]:
        """Read a pre-fetched report level from the sources directory."""
        return self._read_source(name)

    def check_source_completeness(self) -> tuple[bool, list[str]]:
        """Verify required sources exist and have complete pagination.

        Returns (passed, errors).  If passed is False, the run must stop
        before generating HTML or audit artifacts.
        """
        errors: list[str] = []
        depth = self.args.depth

        # Hard-required KPI anchors by depth, aligned with Motata's
        # fast/standard/full/deep source plan.
        required = [
            "current_advertiser_insights",
            "current_campaigns",
            "current_ads",
        ]
        if depth in {"standard", "full", "deep"}:
            required.append("current_adgroups")

        if depth in {"standard", "full", "deep"}:
            required.extend([
                "previous_advertiser_insights",
                "previous_campaigns",
                "previous_adgroups",
                "previous_ads",
            ])
        elif depth == "fast":
            required.extend([
                "previous_advertiser_insights",
                "previous_campaigns",
            ])

        if depth in {"full", "deep"}:
            required.extend([
                "audience_placement",
                "audience_country",
                "audience_age_gender",
                "audience_device",
            ])

        for name in required:
            source = self._read_source(name)
            status = source.get("status")
            if status in ("not_queried", None, "not_applicable"):
                errors.append(f"required source {name} is missing (status={status})")
            elif status == STATUS_OK:
                page_info = source.get("page_info") or {}
                try:
                    tn = int(page_info.get("total_number", 0))
                except (TypeError, ValueError):
                    tn = 0
                rc = source.get("row_count")
                if rc is None:
                    rc = len(source.get("rows") or source.get("segments") or [])
                if tn > rc:
                    errors.append(f"{name}: pagination incomplete (row_count={rc}, total_number={tn})")
                tp = page_info.get("total_page", 1)
                try:
                    tp_i = int(tp)
                except (TypeError, ValueError):
                    tp_i = 1
                merged = (source.get("merged_page_info") or {}).get("merged")
                if tp_i > 1 and not merged:
                    errors.append(f"{name}: multi-page source not merged (total_page={tp_i})")
            elif status == "unsupported":
                attempts = source.get("attempts")
                if not attempts or (isinstance(attempts, list) and len(attempts) == 0):
                    errors.append(f"{name}: status=unsupported but no retry attempts recorded")

        # KPI anchor sources must have exactly 1 row
        for anchor in ("current_advertiser_insights", "previous_advertiser_insights"):
            src = self._read_source(anchor)
            if src.get("status") == STATUS_OK:
                rc = src.get("row_count")
                if rc is None:
                    rc = len(src.get("rows") or src.get("segments") or [])
                if rc != 1 and anchor in required:
                    errors.append(f"{anchor}: expected 1 row, got {rc}")

        return len(errors) == 0, errors

    def run(self) -> dict[str, Any]:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.sources_dir.mkdir(parents=True, exist_ok=True)

        # Dry-run: output plan only
        if self.manifest["dry_run"]:
            plan = {
                "advertiser_id": self.args.advertiser_id,
                "period": self.args.period,
                "depth": self.args.depth,
                "window": {"since": self.window.since, "until": self.window.until, "previous_since": self.window.previous_since, "previous_until": self.window.previous_until},
                "source_names": self.source_names(),
                "run_dir": str(self.run_dir),
            }
            self.write_source("dry_run_plan", plan)
            self.manifest["files"] = ["sources/dry_run_plan.json", "manifest.json"]
            write_json(self.run_dir / "manifest.json", self.manifest)
            return self.manifest

        # Read pre-fetched MCP data from sources directory
        mcp_ready = self._read_source("mcp_ready")
        if mcp_ready.get("status") != STATUS_OK:
            self._mark_degraded("mcp_ready", mcp_ready.get("status"))

        current_account = self.pull_report_level("current_account")
        self.manifest["candidate_row_limits"]["current_account"] = len(current_account.get("rows") or [])
        classification_campaigns = self.read_first_source("classification_campaigns", "current_campaigns")
        classification_adgroups = self.read_first_source("classification_adgroups", "current_adgroups")
        classification_ads = self.read_first_source("classification_ads", "current_ads")
        classification_ad_v2 = self.read_first_source("classification_ad_v2_insights", "current_ad_v2_insights")

        self.manifest["candidate_row_limits"]["classification_campaigns"] = len(classification_campaigns.get("rows") or [])
        self.manifest["candidate_row_limits"]["classification_adgroups"] = len(classification_adgroups.get("rows") or [])
        self.manifest["candidate_row_limits"]["classification_ads"] = len(classification_ads.get("rows") or [])
        self.manifest["candidate_row_limits"]["classification_ad_v2"] = len(classification_ad_v2.get("rows") or [])

        # User type classification
        user_type_evidence_data = self._read_source("user_type_evidence")
        if user_type_evidence_data.get("status") == "not_queried":
            # Build from pre-fetched individual sources
            advertiser_info = self._read_source("advertiser_info")
            app_list = self._read_source("app_list")
            catalog_list = self._read_source("catalog_list")
            shop_list = self._read_source("shop_list")
            smart_plus_details = self._read_source("smart_plus_ads")
            user_type_evidence = collect_app_landing_evidence(
                current_ad_rows=classification_ads.get("rows") or [],
                current_ad_v2_rows=classification_ad_v2.get("rows") or [],
                current_campaign_rows=classification_campaigns.get("rows") or [],
                advertiser_info=advertiser_info if advertiser_info.get("status") != "not_queried" else None,
                app_list=app_list if app_list.get("status") != "not_queried" else None,
                catalog_list=catalog_list if catalog_list.get("status") != "not_queried" else None,
                shop_list=shop_list if shop_list.get("status") != "not_queried" else None,
                smart_plus_details=smart_plus_details if smart_plus_details.get("status") != "not_queried" else None,
            )
            user_type_evidence_data = self.write_source("user_type_evidence", user_type_evidence.to_dict(), phase="classification", depends_on=["classification_ads", "classification_ad_v2_insights", "app_list", "catalog_list", "shop_list", "smart_plus_ads"])
        else:
            # Use pre-fetched evidence bundle
            smart_plus_details = self._read_source("smart_plus_ads")
            user_type_evidence_smart_rows = smart_plus_details.get("rows") or []
            # Build a minimal EvidenceBundle from pre-fetched data (used as dict)
            user_type_evidence_data["smart_plus_rows"] = user_type_evidence_smart_rows

        existing_user_type = self._read_source("user_type")
        if existing_user_type.get("status") == "not_queried":
            user_type = build_user_type_report(
                advertiser_id=self.args.advertiser_id or "",
                start_date=self.window.since,
                end_date=self.window.until,
                account_rows=current_account.get("rows") or [],
                campaign_rows=classification_campaigns.get("rows") or [],
                adgroup_rows=classification_adgroups.get("rows") or [],
                ad_rows=classification_ads.get("rows") or [],
                smart_plus_rows=user_type_evidence_data.get("smart_plus_rows", []),
                landing_rows=user_type_evidence_data.get("landing_rows", []),
                app_rows=user_type_evidence_data.get("app_rows", []),
                catalog_rows=user_type_evidence_data.get("catalog_rows") or user_type_evidence_data.get("catalog_evidence", []),
                shop_rows=user_type_evidence_data.get("shop_rows") or user_type_evidence_data.get("shop_evidence", []),
                skipped_app_url_rows=user_type_evidence_data.get("skipped_app_url_rows", []),
                scraped_content=user_type_evidence_data.get("scraped_content", []),
                errors=user_type_evidence_data.get("errors", []),
            )
            self.write_source("user_type", user_type, phase="classification", depends_on=["current_account", "classification_campaigns", "classification_adgroups", "classification_ads", "user_type_evidence"])
        else:
            user_type = existing_user_type
        write_json(self.run_dir / "user_type.json", user_type)
        top_type = ((user_type.get("top_types") or [{}])[0].get("type") or "代理商/多类型")
        derived_user_type = user_type.get("derived_user_type") or top_type
        w2a = derived_user_type == "工具/W2A"
        shop = bool(user_type.get("catalog_rows") or user_type.get("shop_rows"))
        existing_preset = self._read_source("metric_preset")
        expected_preset = recommend_metric_preset(top_type, profile="vertical", derived_user_type=derived_user_type, w2a=w2a, shop=shop, source_user_type=user_type)
        if existing_preset.get("status") != "not_queried" and existing_preset.get("source_user_type_hash") == expected_preset.get("source_user_type_hash"):
            preset = existing_preset
        else:
            preset = expected_preset
            self.write_source("metric_preset", preset, phase="preset", depends_on=["user_type"])
        write_json(self.run_dir / "metric_preset.json", preset)
        if self.depth_plan["metric_probe"]:
            probe_data = self._read_source("metric_probe_results")
            probe = run_tiktok_metric_probe(
                probe_results=probe_data.get("probe_results") if probe_data.get("status") != "not_queried" else None,
                traffic_check=probe_data.get("traffic_check") if probe_data.get("status") != "not_queried" else None,
                user_type=top_type,
                derived_user_type=derived_user_type,
                profile="vertical",
                w2a=w2a,
                shop=shop,
                source_user_type=user_type,
            )
            self.write_source("metric_probe", probe, phase="preset", depends_on=["metric_preset", "metric_probe_results"])

        current_advertiser = self.pull_report_level("current_advertiser_insights")
        current_campaigns = self.pull_report_level("current_campaigns")
        current_adgroups = self.pull_report_level("current_adgroups")
        current_ads = self.pull_report_level("current_ads")
        current_ad_v2 = self.pull_report_level("current_ad_v2_insights")
        if current_campaigns.get("status") == "not_queried":
            current_campaigns = classification_campaigns
        if current_adgroups.get("status") == "not_queried":
            current_adgroups = classification_adgroups
        if current_ads.get("status") == "not_queried":
            current_ads = classification_ads
        if current_ad_v2.get("status") == "not_queried":
            current_ad_v2 = classification_ad_v2

        self.manifest["candidate_row_limits"]["current_campaigns"] = len(current_campaigns.get("rows") or [])
        self.manifest["candidate_row_limits"]["current_adgroups"] = len(current_adgroups.get("rows") or [])
        self.manifest["candidate_row_limits"]["current_ads"] = len(current_ads.get("rows") or [])
        self.manifest["candidate_row_limits"]["current_ad_v2"] = len(current_ad_v2.get("rows") or [])
        self.manifest["candidate_row_limits"]["current_advertiser_insights"] = len(current_advertiser.get("rows") or [])

        # Previous period data
        if self.depth_plan["previous"]:
            previous_advertiser = self.pull_report_level("previous_advertiser_insights")
            previous_campaigns = self.pull_report_level("previous_campaigns")
            previous_adgroups = self.pull_report_level("previous_adgroups")
            previous_ads = self.pull_report_level("previous_ads")
            self.manifest["candidate_row_limits"]["previous_advertiser_insights"] = len(previous_advertiser.get("rows") or [])
            self.manifest["candidate_row_limits"]["previous_campaigns"] = len(previous_campaigns.get("rows") or [])
            self.manifest["candidate_row_limits"]["previous_adgroups"] = len(previous_adgroups.get("rows") or [])
            self.manifest["candidate_row_limits"]["previous_ads"] = len(previous_ads.get("rows") or [])
        else:
            previous_advertiser = {"status": "not_applicable", "rows": []}
            previous_campaigns = {"status": "not_applicable", "rows": []}
            previous_adgroups = {"status": "not_applicable", "rows": []}
            previous_ads = {"status": "not_applicable", "rows": []}

        # Motata-style app and top-structure enrichment. The primary path is
        # MCP detail pulls planned by build_mcp_pull_plan.py; these local
        # fallbacks keep the report explicit when detail pulls are unavailable.
        existing_apps = self._read_source("apps")
        if "apps" in self.depth_plan["sources"]:
            if existing_apps.get("status") == "not_queried":
                apps = build_apps_summary(
                    advertiser_id=self.args.advertiser_id or "",
                    start_date=self.window.since,
                    end_date=self.window.until,
                    user_type=user_type,
                    campaign_rows=current_campaigns.get("rows") or [],
                    adgroup_rows=current_adgroups.get("rows") or [],
                    ad_rows=current_ads.get("rows") or [],
                )
            else:
                apps = {**existing_apps, "rows": _source_rows(existing_apps), "row_count": len(_source_rows(existing_apps))}
            self.write_source("apps", apps, phase="enrichment")

        structure_specs = [
            ("campaign_structure", current_campaigns.get("rows") or [], "campaign_id", CAMPAIGN_STRUCTURE_FIELDS),
            ("adgroup_structure", current_adgroups.get("rows") or [], "adgroup_id", ADGROUP_STRUCTURE_FIELDS),
            ("ad_structure", current_ads.get("rows") or [], "ad_id", AD_STRUCTURE_FIELDS),
        ]
        for source_name, rows, id_key, fields in structure_specs:
            if source_name not in self.depth_plan["sources"]:
                continue
            existing_structure = self._read_source(source_name)
            if existing_structure.get("status") == "not_queried":
                payload = build_structure_fallback(
                    rows=rows,
                    id_key=id_key,
                    fields=fields,
                    limit=self.args.top_objects,
                    source=f"derived_from_{id_key}_report",
                )
            else:
                structure_rows = _source_rows(existing_structure)
                payload = {**existing_structure, "rows": structure_rows, "row_count": len(structure_rows)}
            self.write_source(source_name, payload, phase="enrichment")

        # Audience breakdowns
        audience_result = {"status": "not_applicable", "sections": {}}
        if self.depth_plan["audience"]:
            audience_breakdown_results: dict[str, Any] = {}
            for breakdown in ("country", "age_gender", "placement", "device"):
                source = self._read_source(f"audience_{breakdown}")
                if source.get("status") != "not_queried":
                    audience_breakdown_results[breakdown] = source
            audience_result = analyze_audience_breakdowns(audience_breakdown_results=audience_breakdown_results if audience_breakdown_results else None)
            audience_sections = audience_result.get("sections") or {}
            for breakdown, section_data in audience_sections.items():
                self.write_source(f"audience_{breakdown}", section_data)
        else:
            audience_sections = {}
        self.write_source("audience_breakdowns", audience_result)

        # Smart+ details and landing analysis
        smart_details = self._read_source("smart_plus_ads")
        existing_landing = self._read_source("landing_app_paths")
        if existing_landing.get("status") != "not_queried":
            landing = _normalize_landing_payload(existing_landing)
        else:
            landing = analyze_landing(
                ad_rows=current_ads.get("rows") or [],
                ad_v2_rows=current_ad_v2.get("rows") or [],
                smart_details=smart_details.get("rows") or [],
            )
        self.write_source("landing_app_paths", landing, phase="enrichment")

        # Select final rows before enrichment
        top_ad_ids = select_top_ids(current_ads.get("rows") or [], "ad_id", limit=self.args.top_objects)
        self.manifest["selected_row_counts"]["top_ad_ids"] = len(top_ad_ids)
        final_ad_rows = [row for row in current_ads.get("rows") or [] if _dimension(row, "ad_id") in set(top_ad_ids)]
        self.manifest["selected_row_counts"]["final_ad_rows"] = len(final_ad_rows)
        current_ad_rows = current_ads.get("rows") or []
        previous_ad_rows = previous_ads.get("rows") or []
        campaign_fields = ["campaign_name", "objective_type", "campaign_automation_type"]
        adgroup_fields = [
            "campaign_id", "campaign_name", "campaign_automation_type",
            "adgroup_name", "promotion_type", "billing_event", "placement_type",
            "adgroup_download_url",
        ]
        self._current_campaign_rows_for_html = _merge_fields_from_reference(
            current_campaigns.get("rows") or [], current_ad_rows, "campaign_id", campaign_fields
        )
        self._current_adgroup_rows_for_html = _merge_fields_from_reference(
            current_adgroups.get("rows") or [], current_ad_rows, "adgroup_id", adgroup_fields
        )
        self._current_ad_rows_for_html = current_ad_rows
        self._previous_campaign_rows_for_html = _merge_fields_from_reference(
            previous_campaigns.get("rows") or [], previous_ad_rows, "campaign_id", campaign_fields
        )
        self._previous_adgroup_rows_for_html = _merge_fields_from_reference(
            previous_adgroups.get("rows") or [], previous_ad_rows, "adgroup_id", adgroup_fields
        )
        self._previous_ad_rows_for_html = previous_ad_rows

        # Creative retention + preview
        existing_retention = self._read_source("creative_retention")
        if existing_retention.get("status") != "not_queried":
            retention = _normalize_retention_payload(existing_retention)
        else:
            retention = build_creative_retention(final_ad_rows)
        ad_details_data = self._read_source("ad_details_for_enrichment")
        ad_structure_data = self._read_source("ad_structure")
        media_data = self._read_source("creative_preview_media")
        image_media_data = self._read_source("creative_preview_images")
        video_media_data = self._read_source("creative_preview_videos")
        spark_media_data = self._read_source("creative_preview_spark_posts")
        catalog_product_data = self._read_source("creative_preview_catalog_products")
        catalog_set_data = self._read_source("creative_preview_catalog_sets")
        ad_detail_rows: list[dict[str, Any]] = []
        if ad_details_data.get("status") != "not_queried":
            ad_detail_rows.extend(ad_details_data.get("rows") or [])
        if ad_structure_data.get("status") != "not_queried":
            ad_detail_rows.extend(ad_structure_data.get("rows") or [])
        targeted_raw_data = self._read_source("targeted_creative_retention_raw")
        targeted_existing_data = self._read_source("targeted_creative_retention")
        for payload in (targeted_raw_data, targeted_existing_data, retention):
            if isinstance(payload, dict) and payload.get("status") != "not_queried":
                ad_detail_rows.extend(payload.get("rows") or [])
        media_rows: list[dict[str, Any]] = []
        for payload in (media_data, image_media_data, video_media_data):
            if payload.get("status") != "not_queried":
                media_rows.extend(payload.get("rows") or [])
        spark_rows: list[dict[str, Any]] = []
        if spark_media_data.get("status") != "not_queried":
            spark_rows.extend(spark_media_data.get("rows") or [])
        catalog_rows: list[dict[str, Any]] = []
        for payload in (catalog_product_data, catalog_set_data):
            if payload.get("status") != "not_queried":
                catalog_rows.extend(payload.get("rows") or [])
        previews = build_creative_previews(
            final_ad_rows,
            smart_details.get("rows") or [],
            ad_details_rows=ad_detail_rows or None,
            media_rows=media_rows or None,
            spark_rows=spark_rows or None,
            catalog_rows=catalog_rows or None,
        )
        if self.depth_plan["retention"]:
            self.write_source("creative_retention", retention)
        if self.depth_plan["previews"]:
            self.write_source("creative_previews", previews)

        # Activity analysis
        activities_result = {"activities": {"status": STATUS_SUPPORTED_EMPTY, "rows": []}, "activity_factors": {"status": STATUS_SUPPORTED_EMPTY, "rows": [], "ranked_factors": []}}
        existing_activities = self._read_source("activities")
        existing_activity_factors = self._read_source("activity_factors")
        existing_activity_targeted = self._read_source("activity_targeted_insights")
        existing_activity_daily = self._read_source("activity_daily_breakdown")
        if (
            existing_activities.get("status") != "not_queried"
            and existing_activity_factors.get("status") != "not_queried"
            and _has_activity_content(existing_activities)
            and _has_activity_content(existing_activity_factors)
            and not _needs_activity_rebuild(existing_activities)
            and not _needs_activity_factor_rebuild(existing_activity_factors)
        ):
            activities_result = {
                "activities": existing_activities,
                "activity_targeted_insights": existing_activity_targeted,
                "activity_daily_breakdown": existing_activity_daily,
                "activity_factors": existing_activity_factors,
            }
        elif self.depth_plan["activities"]:
            changelog_data = self._read_source("activity_changelog")
            activity_input = changelog_data if changelog_data.get("status") != "not_queried" else existing_activities
            activities_result = run_activity_analysis(
                changelog_result=activity_input if activity_input.get("status") != "not_queried" else None,
                current_rows={
                    "campaign": current_campaigns.get("rows") or [],
                    "adgroup": current_adgroups.get("rows") or [],
                    "ad": current_ads.get("rows") or [],
                },
                previous_rows={
                    "campaign": previous_campaigns.get("rows") or [],
                    "adgroup": previous_adgroups.get("rows") or [],
                    "ad": previous_ads.get("rows") or [],
                },
                targeted_results={
                    "campaign": self._read_source("activity_targeted_campaign_insights"),
                    "adgroup": self._read_source("activity_targeted_adgroup_insights"),
                    "ad": self._read_source("activity_targeted_ad_insights"),
                },
                daily_results={
                    "campaign": self._read_source("activity_daily_campaign_breakdown"),
                    "adgroup": self._read_source("activity_daily_adgroup_breakdown"),
                    "ad": self._read_source("activity_daily_ad_breakdown"),
                },
            )
            if existing_activity_targeted.get("status") != "not_queried" and _has_activity_content(existing_activity_targeted):
                activities_result["activity_targeted_insights"] = existing_activity_targeted
            if existing_activity_daily.get("status") != "not_queried" and _has_activity_content(existing_activity_daily):
                activities_result["activity_daily_breakdown"] = existing_activity_daily
            if (
                existing_activity_factors.get("status") != "not_queried"
                and _has_activity_content(existing_activity_factors)
                and not _needs_activity_factor_rebuild(existing_activity_factors)
            ):
                activities_result["activity_factors"] = existing_activity_factors
        self.write_source("activities", activities_result.get("activities", {"status": STATUS_SUPPORTED_EMPTY, "rows": []}))
        self.write_source("activity_targeted_insights", activities_result.get("activity_targeted_insights", {"status": STATUS_SUPPORTED_EMPTY, "rows": []}))
        self.write_source("activity_daily_breakdown", activities_result.get("activity_daily_breakdown", {"status": STATUS_SUPPORTED_EMPTY, "rows": []}))
        self.write_source("activity_factors", activities_result.get("activity_factors", {"status": STATUS_SUPPORTED_EMPTY, "rows": [], "ranked_factors": []}))

        if not self.manifest["tools_used"]:
            self.manifest["tools_used"].append("structured_unavailable_no_tool_bridge")

        # Bottleneck diagnosis (read-only)
        if self.args.depth in {"full", "deep"}:
            advertiser_info_data = self._read_source("advertiser_info")
            bottlenecks = diagnose_bottlenecks(
                campaign_rows=current_campaigns.get("rows") or [],
                adgroup_rows=current_adgroups.get("rows") or [],
                ad_rows=current_ads.get("rows") or [],
                advertiser_info=advertiser_info_data if advertiser_info_data.get("status") != "not_queried" else None,
            )
            self.write_source("bottleneck_diagnosis", bottlenecks)

        # Deep/full-specific sources
        if "targeted_creative_retention" in self.depth_plan["sources"]:
            existing_targeted = self._read_source("targeted_creative_retention")
            raw_targeted = self._read_source("targeted_creative_retention_raw")
            targeted_retention = build_targeted_creative_retention_payload(
                existing_targeted=existing_targeted,
                raw_targeted=raw_targeted,
                current_ad_rows=current_ads.get("rows") or [],
                raw_is_fresh=self._source_newer_than("targeted_creative_retention_raw", "targeted_creative_retention"),
            )
            self.write_source("targeted_creative_retention", targeted_retention)
        if self.args.depth == "deep":
            deep_changelog = self._read_source("advertiser_level_changelog")
            if deep_changelog.get("status") == "not_queried":
                broad_changelog = self._read_source("activity_changelog")
                if broad_changelog.get("status") != "not_queried":
                    deep_changelog = {
                        **broad_changelog,
                        "source_alias": "activity_changelog",
                        "note": "Deep depth uses the broad advertiser-level activity_changelog as advertiser_level_changelog.",
                    }
            self.write_source("advertiser_level_changelog", deep_changelog)

        # Honour not_queried for depth-gated sources
        for source_name in self.source_names():
            if source_name not in self.manifest["coverage"]:
                self.manifest["not_queried_sources"].append(source_name)

        # Hard gate: verify source completeness before any analysis or HTML
        passed, completeness_errors = self.check_source_completeness()
        if not passed:
            self.manifest["completeness_errors"] = completeness_errors
            self.manifest["completeness_passed"] = False
            self.manifest["validation_status"] = "failed"
            self.manifest["files"] = list(self.manifest["source_files"]) + [
                "manifest.json", "user_type.json", "metric_preset.json"
            ]
            write_json(self.run_dir / "manifest.json", self.manifest)
            validation = {
                "status": "failed",
                "source_status": self.manifest.get("coverage", {}),
                "completeness_errors": completeness_errors,
                "required_sources": self.depth_plan["sources"],
            }
            write_json(self.run_dir / "validation_summary.json", validation)
            if not getattr(self.args, "quiet", False):
                print(json.dumps({
                    "error": "source completeness check failed",
                    "completeness_errors": completeness_errors,
                    "run_dir": str(self.run_dir),
                }, ensure_ascii=False, indent=2))
            return self.manifest

        analysis = self.build_analysis(
            current_account.get("rows") or [],
            current_advertiser.get("rows") or [],
            self._current_campaign_rows_for_html,
            previous_advertiser.get("rows") or [],
            self._previous_campaign_rows_for_html if self.depth_plan["previous"] else [],
            user_type, landing, retention, previews,
        )
        write_json(self.run_dir / "analysis_brief.json", analysis)
        validation = self.build_validation(previews, landing, activities_result.get("activities", {}), audience_sections)
        write_json(self.run_dir / "validation_summary.json", validation)
        self.manifest["validation_status"] = validation["status"]
        self.manifest["files"] = list(self.manifest["source_files"]) + ["manifest.json", "analysis_brief.json", "validation_summary.json", "report.html", "report_audit.json", "user_type.json", "metric_preset.json"]
        write_json(self.run_dir / "manifest.json", self.manifest)
        self.write_html(analysis, validation, landing, retention, previews, user_type)
        self.run_audit()
        return self.manifest

    def build_analysis(
        self,
        account_rows: list[dict[str, Any]],
        current_advertiser_rows: list[dict[str, Any]],
        campaigns: list[dict[str, Any]],
        previous_advertiser_rows: list[dict[str, Any]],
        previous_campaigns: list[dict[str, Any]],
        user_type: dict[str, Any],
        landing: dict[str, Any],
        retention: dict[str, Any],
        previews: dict[str, Any],
    ) -> dict[str, Any]:
        # KPI topline MUST come from advertiser-level — no campaign fallback
        if not current_advertiser_rows:
            raise ValueError(
                "current_advertiser_insights is missing or empty — "
                "cannot compute KPI topline. Pull and normalize this source first."
            )
        if self.depth_plan["previous"] and not previous_advertiser_rows:
            raise ValueError(
                "previous_advertiser_insights is required for comparison but is missing or empty."
            )

        current_summary = _summarize_rows(current_advertiser_rows)
        previous_summary = _summarize_rows(previous_advertiser_rows) if previous_advertiser_rows else {}
        spend = current_summary["spend"]
        previous_spend = previous_summary.get("spend", 0)

        # Driver pool counts (informational, not KPI truth)
        driver_pool_counts = {
            "campaigns": len(campaigns),
            "adgroups": len(self._current_adgroup_rows_for_html),
            "ads": len(self._current_ad_rows_for_html),
        }

        degraded_sources = [
            d["name"] if isinstance(d, dict) else d
            for d in self.manifest.get("degraded_sources", [])
        ]
        spend_bearing_ad_text = " ".join(
            _row_text
            for _row_text in (
                " ".join(
                    _string_value(row, field)
                    for field in ("campaign_name", "adgroup_name", "ad_name", "ad_text", "promotion_type", "objective_type")
                )
                for row in self._current_ad_rows_for_html
                if _metric(row, "spend") > 0
            )
        ).lower()
        has_short_drama_signal = any(token in spend_bearing_ad_text for token in ("reelshort", "short drama", "mini-series", "mini series", "短剧"))
        has_app_signal = bool(user_type.get("w2a_evidence")) or "app" in spend_bearing_ad_text
        top_user_type = ((user_type.get("top_types") or [{}])[0].get("type")) or user_type.get("top_type")
        has_ecommerce_signal = top_user_type == "电商" or any(token in spend_bearing_ad_text for token in ("ecommerce", "电商", "shopify", "woocommerce"))
        business_lens = " / ".join(
            part
            for part, present in (
                ("短剧", has_short_drama_signal),
                ("App", has_app_signal),
                ("电商转化", has_ecommerce_signal),
            )
            if present
        ) or (user_type.get("derived_user_type") or ((user_type.get("top_types") or [{}])[0].get("type")) or "代理商/多类型")

        return {
            "status": "ok",
            "topline": {
                **current_summary,
                "previous_spend": previous_spend,
                "previous_impressions": previous_summary.get("impressions", 0),
                "previous_clicks": previous_summary.get("clicks", 0),
                "previous_conversion": previous_summary.get("conversion", 0),
                "previous_ctr": previous_summary.get("ctr"),
                "previous_cpc": previous_summary.get("cpc"),
                "previous_cpm": previous_summary.get("cpm"),
                "previous_cpa": previous_summary.get("cpa"),
                "spend_delta": spend - previous_spend,
                "topline_source": "current_advertiser_insights",
                "previous_topline_source": "previous_advertiser_insights",
            },
            "user_type": (user_type.get("top_types") or [{}])[0],
            "business_lens": business_lens,
            "landing_rows": len(landing.get("rows") or []),
            "creative_preview_coverage": previews.get("coverage", {}),
            "creative_winners": retention.get("winners", [])[:5],
            "driver_pool_counts": driver_pool_counts,
            "degraded_sources": degraded_sources,
            "next_actions": [
                "Prioritize rows with high spend and weak conversion.",
                "Refresh creatives marked as fatigue candidates after preview review.",
                "Treat measurement-limited value metrics as directional until probe confirms active revenue fields.",
            ],
        }

    def build_validation(self, previews: dict[str, Any], landing: dict[str, Any], activities: dict[str, Any], audience_sections: dict[str, Any]) -> dict[str, Any]:
        source_status = dict(self.manifest["coverage"])
        required = self.depth_plan["sources"]
        not_queried = [name for name in required if source_status.get(name) is None]
        degraded = self.manifest["degraded_sources"]
        degraded_names = {d["name"] if isinstance(d, dict) else d for d in degraded}
        not_applicable = {name for name, status in source_status.items() if status == "not_applicable"}
        actually_missing = [name for name in not_queried if name not in not_applicable]
        status = "passed" if not actually_missing and not degraded else "passed_with_degradation" if not actually_missing else "failed"
        return {
            "status": status,
            "source_status": source_status,
            "not_queried_sources": actually_missing,
            "required_sources": required,
            "audience_sections": audience_sections,
            "row_counts": {
                "creative_previews": len(previews.get("rows") or []),
                "landing_app_paths": len(landing.get("rows") or []),
                "activities": len(activities.get("rows") or []),
                "audience_breakdowns": sum(len((section.get("rows") or [])) for section in audience_sections.values() if isinstance(section, dict)),
            },
            "preview_coverage": previews.get("coverage", {}),
            "degraded_sources": degraded,
            "partial_sources": self.manifest["partial_sources"],
        }

    def write_html(self, analysis: dict[str, Any], validation: dict[str, Any], landing: dict[str, Any], retention: dict[str, Any], previews: dict[str, Any], user_type: dict[str, Any]) -> None:
        def esc(value: Any) -> str:
            return html.escape(str(value if value is not None else ""))

        def money(value: Any) -> str:
            try:
                return f"${float(value):,.2f}"
            except Exception:
                return "-"

        def number(value: Any, digits: int = 0) -> str:
            try:
                return f"{float(value):,.{digits}f}"
            except Exception:
                return "-"

        def percent(value: Any) -> str:
            try:
                return f"{float(value) * 100:.2f}%"
            except Exception:
                return "-"

        def ratio_delta(current: Any, previous: Any, *, inverse_good: bool = False) -> tuple[str, str]:
            try:
                curr = float(current)
                prev = float(previous)
            except Exception:
                return "-", "neutral"
            if prev == 0:
                return ("new" if curr else "-", "neutral")
            change = (curr - prev) / prev
            cls = "good" if (change < 0 if inverse_good else change > 0) else "bad" if change else "neutral"
            return f"{change:+.1%}", cls

        def cpa_for(row: dict[str, Any]) -> float | None:
            cost, _ = _primary_cost(row)
            return cost

        def roas_for(row: dict[str, Any]) -> float | None:
            spend = _metric(row, "spend")
            value = max(_metric(row, "total_purchase_value"), _metric(row, "onsite_total_purchase_value"), _metric(row, "value"))
            return value / spend if spend else None

        def judgement(row: dict[str, Any]) -> str:
            spend = _metric(row, "spend")
            conv = _conversion(row)
            primary_value, primary_label = _primary_result(row)
            cpa = cpa_for(row)
            account_cpa = analysis["topline"].get("cpa")
            if spend > 0 and not conv and primary_label == "conversion":
                return '<span class="tag bad">高花费无转化</span>'
            if primary_label == "result" and primary_value >= 5 and cpa:
                return '<span class="tag good">Result 成本优</span>'
            if account_cpa and cpa and cpa <= account_cpa * 0.75 and conv >= 5:
                return '<span class="tag good">转化优先保留</span>'
            if account_cpa and cpa and cpa >= account_cpa * 1.5 and spend >= analysis["topline"].get("spend", 0) * 0.02:
                return '<span class="tag warn">控量观察</span>'
            return '<span class="tag">正常</span>'

        def cell(row: dict[str, Any], field: str) -> str:
            flat = _flat_row(row)
            if field == "spend":
                return money(flat.get(field))
            if field in {"impressions", "clicks", "conversion", "result"}:
                return number(flat.get(field), 0)
            if field == "primary_result":
                value, label = _primary_result(row)
                return f'{number(value, 0)} <span class="muted">({esc(label)})</span>'
            if field == "ctr":
                raw = _metric(row, "ctr")
                return f"{raw:.2f}%" if raw > 1 else percent(raw)
            if field in {"cpc", "cpm", "cost_per_conversion", "cost_per_result"}:
                return money(flat.get(field))
            if field == "cpa":
                return money(cpa_for(row))
            if field == "primary_cost":
                cost, label = _primary_cost(row)
                return f'{money(cost)} <span class="muted">({esc(label)})</span>'
            if field == "roas":
                value = roas_for(row)
                return f"{value:.2f}" if value is not None else "-"
            if field == "judgement":
                return judgement(row)
            if field == "preview":
                preview_row = preview_by_ad.get(_dimension(row, "ad_id"), row)
                return preview_cell(preview_row)
            if field == "dimension":
                dims = _flat_row(row).get("dimension_values")
                if isinstance(dims, dict) and dims:
                    return esc(", ".join(f"{k}={v}" for k, v in dims.items()))
                return esc(_flat_row(row).get("segment") or "all")
            return esc(flat.get(field, ""))[:500]

        def table(rows: list[dict[str, Any]], columns: list[tuple[str, str]], *, max_rows: int = 12) -> str:
            if not rows:
                return '<p class="muted">无可展示数据。</p>'
            head = "".join(f"<th>{esc(label)}</th>" for _, label in columns)
            body = ""
            for row in rows[:max_rows]:
                body += "<tr>" + "".join(f"<td>{cell(row, key)}</td>" for key, _ in columns) + "</tr>"
            return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'

        def preview_cell(row: dict[str, Any]) -> str:
            image_url = str(row.get("preview_image_url") or row.get("image_url") or row.get("thumbnail_url") or row.get("cover_url") or "")
            action_url = str(row.get("preview_action_url") or row.get("preview_url") or row.get("video_url") or row.get("playable_url") or row.get("spark_post_url") or "")
            title = esc(row.get("ad_name") or row.get("ad_id") or "Preview")
            pieces: list[str] = []
            if image_url:
                pieces.append(f'<img class="creative-thumb" src="{esc(image_url)}" alt="{title}" loading="lazy">')
            if action_url:
                pieces.append(f'<a class="preview-link" href="{esc(action_url)}" target="_blank" rel="noopener noreferrer">打开预览</a>')
            return "".join(pieces) or f'<span class="muted">{esc(row.get("preview_status") or "unavailable")}</span>'

        def preview_table(rows: list[dict[str, Any]]) -> str:
            if not rows:
                return '<p class="muted">无创意预览数据。</p>'
            body = ""
            for row in rows[:20]:
                body += (
                    "<tr>"
                    f"<td>{preview_cell(row)}</td>"
                    f"<td>{esc(row.get('ad_id'))}</td>"
                    f"<td>{esc(row.get('ad_name'))}</td>"
                    f"<td>{money(row.get('spend'))}</td>"
                    f"<td>{esc(row.get('preview_status'))}</td>"
                    "</tr>"
                )
            return (
                '<div class="table-wrap"><table><thead><tr>'
                '<th>Preview</th><th>Ad ID</th><th>Ad</th><th>Spend</th><th>Status</th>'
                f'</tr></thead><tbody>{body}</tbody></table></div>'
            )

        preview_by_ad = {
            str(row.get("ad_id")): row
            for row in (previews.get("rows") or [])
            if isinstance(row, dict) and row.get("ad_id")
        }

        def metric_card(label: str, current: str, previous: str, delta_text: str, delta_cls: str, note: str = "") -> str:
            hint_html = f'<div class="hint">{esc(note)}</div>' if note else ""
            return (
                '<div class="metric">'
                f'<div class="label">{esc(label)}</div><div class="value">{esc(current)}</div>'
                f'<div class="note">本期 {esc(current)} / 上期 {esc(previous)} <span class="{delta_cls}">{esc(delta_text)}</span></div>'
                f'{hint_html}'
                '</div>'
            )

        topline = analysis["topline"]
        spend_delta, spend_cls = ratio_delta(topline.get("spend"), topline.get("previous_spend"))
        conv_delta, conv_cls = ratio_delta(topline.get("conversion"), topline.get("previous_conversion"))
        cpa_delta, cpa_cls = ratio_delta(topline.get("cpa"), topline.get("previous_cpa"), inverse_good=True)
        click_delta, click_cls = ratio_delta(topline.get("clicks"), topline.get("previous_clicks"))
        business_lens = analysis.get("business_lens") or user_type.get("derived_user_type") or "代理商/多类型"

        campaigns = sorted(self._current_campaign_rows_for_html, key=lambda row: _metric(row, "spend"), reverse=True)
        adgroups = sorted(self._current_adgroup_rows_for_html, key=lambda row: _metric(row, "spend"), reverse=True)
        ads_by_conversion = sorted(self._current_ad_rows_for_html, key=lambda row: (_primary_result(row)[0], _conversion(row), _metric(row, "spend")), reverse=True)
        ads_by_spend = sorted(self._current_ad_rows_for_html, key=lambda row: _metric(row, "spend"), reverse=True)
        landing_rows = [row for row in (landing.get("rows") or []) if _metric(row, "spend") > 0]
        landing_rows = landing_rows or (landing.get("rows") or [])
        activity = self._read_source("activity_factors")
        activity_targets = activity.get("activity_targets") or []
        activity_factors = activity.get("ranked_factors") or []
        metric_probe = self._read_source("metric_probe")
        measurement_limited = metric_probe.get("measurement_limited")

        activity_rows = ""
        for item in activity_targets[:8]:
            current_kpi = item.get("current") if isinstance(item.get("current"), dict) else {}
            previous_kpi = item.get("previous") if isinstance(item.get("previous"), dict) else {}
            activity_rows += (
                "<tr>"
                f"<td>{esc(item.get('object_level'))}</td><td>{esc(item.get('object_id'))}</td>"
                f"<td>{number(item.get('change_count'), 0)}</td><td>{esc(', '.join(item.get('operations') or []))}</td>"
                f"<td>{money(current_kpi.get('spend'))} / {number(current_kpi.get('conversion'), 0)} / {number(current_kpi.get('result'), 0)}</td>"
                f"<td>{money(previous_kpi.get('spend'))} / {number(previous_kpi.get('conversion'), 0)} / {number(previous_kpi.get('result'), 0)}</td>"
                f"<td>{esc('; '.join(item.get('sample_details') or [])[:260])}</td>"
                "</tr>"
            )
        if not activity_rows:
            activity_rows = '<tr><td colspan="7" class="muted">无可展示活动对象。</td></tr>'

        factor_tags = " ".join(
            f'<span class="pill">{esc(item.get("area"))}: {number(item.get("count"), 0)}</span>'
            for item in activity_factors[:6]
        )

        audience_html = ""
        for name, section in (validation.get("audience_sections") or {}).items():
            if not isinstance(section, dict):
                continue
            rows = sorted(section.get("rows") or [], key=lambda row: _metric(row, "spend"), reverse=True)
            if not rows:
                continue
            audience_html += f"<h3>{esc(name)}</h3>" + table(rows, [
                ("dimension", "Segment"), ("spend", "Spend"), ("clicks", "Clicks"),
                ("conversion", "CV"), ("cpa", "CPA"), ("tag", "Tag"),
            ], max_rows=6)
        if not audience_html:
            audience_html = '<p class="muted">Audience breakdowns available but no priority segments were returned.</p>'

        quality_rows = ""
        for name, status in sorted((validation.get("source_status") or {}).items()):
            row_count = validation.get("row_counts", {}).get(name, "")
            quality_rows += f"<tr><td>{esc(name)}</td><td>{esc(status)}</td><td>{esc(row_count)}</td></tr>"

        report_noun = report_period_noun(self.args.period)
        conclusions = [
            f"{report_noun} spend {money(topline.get('spend'))}，较上期 {money(topline.get('previous_spend'))} {spend_delta}；conversion {number(topline.get('conversion'), 0)}，较上期 {conv_delta}。",
            f"CPA 从 {money(topline.get('previous_cpa'))} 到 {money(topline.get('cpa'))}，变化 {cpa_delta}，说明{report_noun}量级变化与获客效率需要结合判断。",
            "Value / ROAS 目前按平台回传为 0 或 measurement-limited，本版报告把 ROAS 作为诊断占位，不把它当作预算决策的唯一依据。",
        ]
        if activity_targets:
            conclusions.append("Activities 已重新解析到具体 campaign/ad group/ad 对象，用于解释波动，不替代 KPI 事实。")

        actions = [
            "预算优先保留 CPA 低于账户均值且转化量稳定的 campaign/ad group；高 spend 低 CVR 的对象先控量观察。",
            "主路径聚焦 spend-bearing landing/app URL，零花费配置 URL 不进入主结论，避免稀释判断。",
            "素材侧优先复用高 CV 且预览可检查的结构；高花费低转化或缺少有效预览的素材进入刷新队列。",
        ]

        report_label = report_period_label(self.args.period)
        html_text = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>Creatiads TikTok {esc(report_label)} - {esc(self.args.advertiser_id)}</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,"PingFang SC","Microsoft YaHei",sans-serif;margin:0;color:#17202a;background:#f6f7f9;line-height:1.5}}
.page{{max-width:1240px;margin:0 auto;padding:28px 28px 48px}}
.hero{{background:#ffffff;border:1px solid #dde3ea;border-radius:8px;padding:22px 24px;margin-bottom:16px}}
h1{{font-size:26px;margin:0 0 8px}} h2{{font-size:18px;margin:0 0 14px}} h3{{font-size:15px;margin:18px 0 8px}}
.subtitle,.muted,.note,.hint{{color:#64748b}} .hint{{font-size:12px;margin-top:4px}}
.pill-row{{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}} .pill{{display:inline-block;border:1px solid #d8dee8;background:#fff;border-radius:999px;padding:4px 10px;font-size:12px}} .pill.ok{{background:#ecfdf3;color:#116033}} .pill.warn{{background:#fff7ed;color:#9a3412}}
.section,.panel{{background:#fff;border:1px solid #dde3ea;border-radius:8px;padding:18px 20px;margin-top:16px}}
.grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}} .metric{{border:1px solid #dde3ea;border-radius:8px;padding:14px;background:#fbfcfe}} .label{{font-size:12px;color:#64748b;text-transform:uppercase}} .value{{font-size:24px;font-weight:700;margin:4px 0}}
.good{{color:#047857}} .bad{{color:#b91c1c}} .neutral{{color:#64748b}} .warn{{color:#b45309}}
.table-wrap{{overflow-x:auto}} table{{border-collapse:collapse;width:100%;font-size:13px}} th,td{{border-bottom:1px solid #e5eaf0;padding:8px 10px;text-align:left;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}} th{{background:#f8fafc;color:#475569;font-weight:650}}
.tag{{display:inline-block;border-radius:4px;background:#eef2f7;color:#334155;padding:2px 7px;font-size:12px}} .tag.good{{background:#ecfdf3;color:#047857}} .tag.warn{{background:#fff7ed;color:#b45309}} .tag.bad{{background:#fef2f2;color:#b91c1c}}
.creative-thumb{{width:84px;max-height:124px;object-fit:cover;border-radius:6px;display:block;margin-bottom:6px}} .preview-link{{font-size:12px}}
ul{{margin:0;padding-left:20px}} li{{margin:5px 0}}
@media(max-width:860px){{.page{{padding:16px}}.grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}}}
</style></head><body><main class="page">
<section class="hero" id="scope">
  <h1>TikTok {esc(report_label)} - {esc(self.args.advertiser_id)}</h1>
  <p class="subtitle">Scope: {esc(self.window.since)} 至 {esc(self.window.until)}，对比 {esc(self.window.previous_since)} 至 {esc(self.window.previous_until)} · Coverage: advertiser/campaign/adgroup/ad + landing + creative + audience。</p>
  <div class="pill-row">
    <span class="pill ok">Business lens: {esc(business_lens)}</span>
    <span class="pill">用户类型 / classification: {esc(user_type.get("derived_user_type") or ((user_type.get("top_types") or [{}])[0].get("type")) or "unknown")}</span>
    <span class="pill">Depth: {esc(self.args.depth)}</span>
    <span class="pill warn">Limits: platform attribution only</span>
  </div>
</section>

<section class="section" id="kpi-snapshot">
  <h2>KPI 快照</h2>
  <div class="grid">
    {metric_card("Spend", money(topline.get("spend")), money(topline.get("previous_spend")), spend_delta, spend_cls)}
    {metric_card("Conversion", number(topline.get("conversion"), 0), number(topline.get("previous_conversion"), 0), conv_delta, conv_cls)}
    {metric_card("CPA", money(topline.get("cpa")), money(topline.get("previous_cpa")), cpa_delta, cpa_cls)}
    {metric_card("Clicks", number(topline.get("clicks"), 0), number(topline.get("previous_clicks"), 0), click_delta, click_cls)}
  </div>
</section>

<section class="panel"><h2>结论</h2><ul>{''.join(f'<li>{esc(item)}</li>' for item in conclusions)}</ul></section>
<section class="panel"><h2>建议动作</h2><ul>{''.join(f'<li>{esc(item)}</li>' for item in actions)}</ul></section>

<section class="section" id="metric-context">
  <h2>Metric Context / 指标</h2>
  <p>Metric preset follows user type classification before report interpretation. 当前固定核心指标包含 spend、impressions、clicks、conversion、CPA；value / ROAS 字段在本次 TikTok 回传中为 measurement-limited。</p>
</section>

<section class="section" id="activity-context">
  <h2>Activities 影响因素</h2>
  <div class="pill-row">{factor_tags or '<span class="pill">无活动分解</span>'}</div>
  <div class="table-wrap"><table><thead><tr><th>Level</th><th>Object ID</th><th>Changes</th><th>Areas</th><th>Current Spend / CV / Result</th><th>Previous Spend / CV / Result</th><th>Sample</th></tr></thead><tbody>{activity_rows}</tbody></table></div>
</section>

<section class="section" id="campaign-drivers">
  <h2>Campaign 排名</h2>
  {table(campaigns, [("campaign_id","Campaign ID"),("campaign_name","Campaign"),("objective_type","Objective"),("spend","Spend"),("clicks","Clicks"),("conversion","Conversion"),("result","Result"),("primary_result","Primary"),("primary_cost","Primary Cost"),("roas","ROAS"),("judgement","判断")], max_rows=12)}
</section>

<section class="section" id="adgroup-drivers">
  <h2>Ad Group 排名</h2>
  {table(adgroups, [("adgroup_id","Ad Group ID"),("adgroup_name","Ad Group"),("campaign_name","Campaign"),("promotion_type","Promotion"),("spend","Spend"),("clicks","Clicks"),("conversion","Conversion"),("result","Result"),("primary_result","Primary"),("primary_cost","Primary Cost"),("judgement","判断")], max_rows=12)}
</section>

<section class="section" id="top-creatives">
  <h2>Top Creative</h2>
  {table(ads_by_conversion, [("preview","Preview"),("ad_id","Ad ID"),("ad_name","Ad"),("campaign_name","Campaign"),("adgroup_name","Ad Group"),("spend","Spend"),("clicks","Clicks"),("conversion","Conversion"),("result","Result"),("primary_result","Primary"),("primary_cost","Primary Cost"),("judgement","判断")], max_rows=12)}
</section>

<section class="section" id="creative-refresh">
  <h2>Creative Refresh Queue</h2>
  {table(ads_by_spend, [("preview","Preview"),("ad_id","Ad ID"),("ad_name","Ad"),("spend","Spend"),("clicks","Clicks"),("conversion","Conversion"),("result","Result"),("primary_result","Primary"),("primary_cost","Primary Cost"),("judgement","判断")], max_rows=12)}
</section>

<section class="section" id="creative-preview">
  <h2>Creative Preview</h2>
  <p class="preview-action">Preview 使用图片或可打开素材链接承载，不把裸 URL 当作单独结论。</p>
  {preview_table(previews.get("rows") or [])}
</section>

<section class="section" id="landing-app">
  <h2>Landing / W2A 路径</h2>
  {table(landing_rows, [("normalized_url","URL"),("url_type","Type"),("source","Source"),("spend","Spend"),("clicks","Clicks"),("conversion","CV"),("cpa","CPA"),("roas","ROAS")], max_rows=10)}
</section>

<section class="section" id="creative-retention">
  <h2>素材留存</h2>
  <h3>Winners</h3>{table(retention.get("winners", [])[:8], [("preview","Preview"),("ad_id","Ad ID"),("ad_name","Ad"),("spend","Spend"),("conversion","Conversion"),("result","Result"),("primary_result","Primary"),("hook_rate","Hook"),("completion_rate","Complete"),("roas","ROAS")], max_rows=8)}
  <h3>Refresh / Fatigue</h3>{table(retention.get("fatigue_candidates", [])[:8], [("preview","Preview"),("ad_id","Ad ID"),("ad_name","Ad"),("spend","Spend"),("conversion","Conversion"),("result","Result"),("primary_result","Primary"),("mid_retention","Mid"),("cost_per_retained_viewer","Cost / Retained")], max_rows=8)}
</section>

<section class="section" id="audience">
  <h2>Audience 分层</h2>
  {audience_html}
</section>

<section class="section" id="measurement">
  <h2>ROAS / 归因拆分</h2>
  <p>本期 spend-bearing rows 的平台收入字段为 0 或不可确认；measurement_limited={esc(measurement_limited)}。因此报告保留 ROAS 列用于核对，但预算建议以 Spend、CV、CPA 与活动变更解释为主。</p>
</section>

<section class="section" id="data-quality">
  <h2>Data Quality</h2>
  <p>Validation: <strong>{esc(validation.get("status"))}</strong>。Degraded sources: {esc(json.dumps([d.get('name','') if isinstance(d, dict) else d for d in validation.get('degraded_sources', [])], ensure_ascii=False))}</p>
  <div class="table-wrap"><table><thead><tr><th>Source</th><th>Status</th><th>Rows / Count</th></tr></thead><tbody>{quality_rows}</tbody></table></div>
</section>
</main></body></html>"""
        (self.run_dir / "report.html").write_text(html_text, encoding="utf-8")
        return

        def _flat(row: dict[str, Any]) -> dict[str, Any]:
            """Flatten a report row that may have nested dimensions/metrics dicts."""
            flat: dict[str, Any] = {}
            if isinstance(row.get("dimensions"), dict):
                flat.update(row["dimensions"])
            if isinstance(row.get("metrics"), dict):
                flat.update(row["metrics"])
            for k, v in row.items():
                if k not in ("dimensions", "metrics") and k not in flat:
                    flat[k] = v
            return flat

        def rows_table(rows: list[dict[str, Any]], fields: list[str], max_rows: int = 20, flatten: bool = False) -> str:
            if not rows:
                return "<p>No rows available.</p>"
            head = "".join(f"<th>{html.escape(field)}</th>" for field in fields)
            body = ""
            for row in rows[:max_rows]:
                r = _flat(row) if flatten else row
                body += "<tr>" + "".join(f"<td>{html.escape(str(r.get(field, ''))[:200])}</td>" for field in fields) + "</tr>"
            return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"

        def preview_cell(row: dict[str, Any]) -> str:
            image_url = str(row.get("preview_image_url") or row.get("image_url") or row.get("thumbnail_url") or row.get("cover_url") or "")
            action_url = str(row.get("preview_action_url") or row.get("preview_url") or row.get("video_url") or row.get("playable_url") or row.get("spark_post_url") or "")
            name = html.escape(str(row.get("ad_name") or row.get("ad_id") or "Creative preview"))
            pieces = []
            if image_url:
                pieces.append(
                    f'<img class="creative-thumb" src="{html.escape(image_url, quote=True)}" '
                    f'alt="{name}" loading="lazy">'
                )
            if action_url:
                pieces.append(
                    f'<a class="preview-link" href="{html.escape(action_url, quote=True)}" '
                    f'target="_blank" rel="noopener noreferrer">Open preview</a>'
                )
            if not pieces:
                status = html.escape(str(row.get("preview_status") or "Unavailable"))
                ref = html.escape(str(row.get("asset_reference") or ""))
                return f'<span class="muted">{status}</span><br><small>{ref}</small>' if ref else f'<span class="muted">{status}</span>'
            return "".join(pieces)

        def preview_table(rows: list[dict[str, Any]]) -> str:
            if not rows:
                return "<p>No creative preview rows available.</p>"
            body = ""
            for row in rows:
                body += (
                    "<tr>"
                    f"<td>{preview_cell(row)}</td>"
                    f"<td>{html.escape(str(row.get('ad_id', '')))}</td>"
                    f"<td>{html.escape(str(row.get('ad_name', ''))[:200])}</td>"
                    f"<td>{html.escape(str(row.get('spend', '')))}</td>"
                    f"<td>{html.escape(str(row.get('preview_status', '')))}</td>"
                    "</tr>"
                )
            return (
                "<table><thead><tr>"
                "<th>Preview</th><th>ad_id</th><th>ad_name</th><th>spend</th><th>status</th>"
                "</tr></thead><tbody>"
                f"{body}</tbody></table>"
            )

        def metric_card(label: str, value: Any, fmt: str = ".2f") -> str:
            try:
                display = f"{float(value):{fmt}}" if isinstance(value, (int, float)) else str(value)
            except (ValueError, TypeError):
                display = str(value)
            return f'<div class="metric"><span class="metric-label">{html.escape(label)}</span><br><strong>{html.escape(display)}</strong></div>'

        top_type = (user_type.get("top_types") or [{}])[0]
        type_label = html.escape(str(top_type.get("type", "Unknown")))
        derived_label = html.escape(str(user_type.get("derived_user_type") or top_type.get("type", "Unknown")))
        conf = html.escape(str(top_type.get("confidence", "low")))
        validation_status = html.escape(validation.get("status", "unknown"))
        source_count = len(self.manifest.get("source_files", []))
        tool_count = len(self.manifest.get("tools_used", []))
        preset_data = self._read_source("metric_preset")
        probe_data = self._read_source("metric_probe")
        metric_groups = preset_data.get("groups") or []
        metric_names = preset_data.get("metrics") or []
        active_metrics = [item.get("metric") for item in (probe_data.get("active_metrics") or []) if isinstance(item, dict) and item.get("metric")]
        supported_empty_metrics = [item.get("metric") for item in (probe_data.get("supported_empty_metrics") or []) if isinstance(item, dict) and item.get("metric")]
        unsupported_metrics = [item.get("metric") for item in (probe_data.get("unsupported_metrics") or []) if isinstance(item, dict) and item.get("metric")]
        accepted_metrics = active_metrics + [m for m in supported_empty_metrics if m not in active_metrics]
        metric_context = {
            "user_type": preset_data.get("user_type"),
            "derived_user_type": preset_data.get("derived_user_type"),
            "groups": metric_groups,
            "metric_count": len(metric_names),
            "accepted_metric_count": len(accepted_metrics) if probe_data.get("status") != "not_queried" else "preset_only",
            "unsupported_metric_count": len(unsupported_metrics),
        }

        all_types_rows = ""
        for t in (user_type.get("all_types") or [])[:5]:
            all_types_rows += f"<tr><td>{html.escape(str(t.get('type','')))}</td><td>{html.escape(str(t.get('index','')))}</td><td>{html.escape(str(t.get('confidence','')))}</td></tr>"

        landing_priority = ""
        if landing.get("rows"):
            landing_priority = "<h3>Landing/App Priority</h3><ul>"
            for i, row in enumerate(landing.get("rows") or []):
                cost = row.get("cost")
                roas = row.get("roas")
                if cost is not None and cost > 0 and (roas is None or roas < 1.0):
                    tag = "fix or pause" if i < 5 else "inspect"
                elif roas and roas >= 2.0:
                    tag = "scale"
                else:
                    tag = "monitor"
                landing_priority += f"<li><strong>{html.escape(tag)}</strong>: {html.escape(str(row.get('normalized_url',''))[:80])} (spend: {row.get('spend',0):.2f})</li>"
                if i >= 7:
                    break
            landing_priority += "</ul>"

        audience_html = ""
        audience_sections = validation.get("audience_sections") or {}
        for breakdown, section_data in audience_sections.items():
            if isinstance(section_data, dict) and section_data.get("rows"):
                tagged = [r for r in section_data["rows"] if r.get("tag") in {"scale", "reduce", "no_result_spend", "high_roas"}]
                if tagged:
                    audience_html += f"<h4>{html.escape(breakdown)}</h4><ul>"
                    for r in tagged[:5]:
                        audience_html += f"<li>{html.escape(str(r))}: <strong>{html.escape(r.get('tag',''))}</strong></li>"
                    audience_html += "</ul>"

        next_actions_html = "<ul>"
        for item in analysis.get("next_actions", []):
            next_actions_html += f"<li>{html.escape(item)}</li>"
        next_actions_html += "</ul>"

        html_text = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Creatiads TikTok Report — {type_label}</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;margin:24px;color:#17202a;line-height:1.5}}
table{{border-collapse:collapse;width:100%;font-size:13px;margin-bottom:16px}}
th,td{{border:1px solid #d8dee8;padding:8px 10px;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}}
th{{background:#f3f6fa;font-weight:600;text-align:left}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px}}
.metric{{border:1px solid #d8dee8;padding:12px;border-radius:6px;background:#fafbfc}}
.metric-label{{font-size:11px;color:#657786;text-transform:uppercase;letter-spacing:0.5px}}
.metric strong{{font-size:20px;display:block;margin-top:4px}}
.warn{{color:#8a4b00;background:#fff8e1;padding:8px;border-radius:4px;margin:8px 0}}
.section{{margin-top:24px}}
h2{{border-bottom:2px solid #e1e8ed;padding-bottom:6px;margin-top:32px}}
h3{{margin-top:20px;color:#384650}}
.preview-action{{font-size:12px;color:#657786;margin-bottom:8px}}
.creative-thumb{{width:96px;max-height:140px;object-fit:cover;border-radius:6px;display:block;margin-bottom:6px}}
.preview-link{{font-size:12px}}
.muted{{color:#657786}}
.degraded-badge{{display:inline-block;background:#ffebee;color:#b71c1c;padding:2px 8px;border-radius:4px;font-size:12px}}
</style></head><body>
<h1>TikTok Report — {type_label}</h1>

<div class="section" id="scope">
<h2>Scope</h2>
<p>Scope: Advertiser <strong>{html.escape(self.args.advertiser_id or "from sources")}</strong> | {html.escape(self.window.since)} to {html.escape(self.window.until)} | Depth: <strong>{html.escape(self.args.depth)}</strong> | Sources: {source_count} files via {tool_count} MCP tools</p>
</div>

<div class="section" id="data-quality">
<h2>Data Quality</h2>
<p>Validation: <strong>{validation_status}</strong>. Degraded sources: {html.escape(json.dumps([d.get('name','') for d in validation.get('degraded_sources',[])], ensure_ascii=False))}</p>
<div class="warn">This report is directional MCP-first output. All findings are limited by declared source artifacts. Missing rows are treated as degraded evidence, not as zero performance.</div>
</div>

<div class="section" id="kpi-snapshot">
<h2>KPI Snapshot</h2>
<div class="grid">
{metric_card("Spend", analysis["topline"]["spend"])}
{metric_card("Previous Spend", analysis["topline"]["previous_spend"])}
{metric_card("Spend Delta", analysis["topline"]["spend_delta"])}
{metric_card("Clicks", analysis["topline"]["clicks"], ".0f")}
{metric_card("Conversion", analysis["topline"]["conversion"], ".0f")}
{metric_card("CTR", analysis["topline"].get("ctr", 0)*100 if analysis["topline"].get("ctr") else "—")}
{metric_card("Landing Rows", analysis.get("landing_rows", 0), ".0f")}
{metric_card("Preview Coverage", analysis.get("creative_preview_coverage", {}).get("with_preview", 0), ".0f")}
</div>
</div>

	<div class="section" id="vertical-diagnosis">
	<h2>Vertical Diagnosis / User Type Classification</h2>
	<p>Top vertical / user type: <strong>{type_label}</strong> (confidence: {conf}). Derived user type: <strong>{derived_label}</strong>.</p>
	<p>All detected types:</p>
	<table><thead><tr><th>Type</th><th>Index</th><th>Confidence</th></tr></thead><tbody>{all_types_rows}</tbody></table>
	</div>

	<div class="section" id="metric-context">
	<h2>Metric Context</h2>
	<p>Metric preset is selected after user type classification and before formal report-data interpretation.</p>
	<p>Metric groups: <strong>{html.escape(", ".join(str(group) for group in metric_groups) or "none")}</strong></p>
	<p>Preset metrics ({len(metric_names)}): {html.escape(", ".join(str(metric) for metric in metric_names[:40]))}</p>
	<p>Probe summary: {html.escape(json.dumps(metric_context, ensure_ascii=False))}</p>
	</div>

<div class="section" id="campaign-drivers">
<h2>Campaign Drivers</h2>
{rows_table(self._current_campaign_rows_for_html, ["campaign_id", "campaign_name", "objective_type", "spend", "conversion"], flatten=True)}
</div>

<div class="section" id="creative-preview">
<h2>Creative Preview</h2>
<p class="preview-action">One row per final report ad row. Coverage statuses: inline_image, action_url_only, spark_post_url count as concrete preview. asset_reference and unavailable do not.</p>
{preview_table(previews.get("rows") or [])}
</div>

<div class="section" id="landing-app">
<h2>Landing / App / SKU Paths</h2>
{rows_table(landing.get("rows") or [], ["normalized_url", "url_type", "source", "spend", "clicks", "conversion", "value", "cost", "roas"])}
{landing_priority}
</div>

<div class="section" id="creative-retention">
<h2>Creative Retention</h2>
<h3>Winners (top 5)</h3>
{rows_table(retention.get("winners", [])[:5], ["ad_id", "ad_name", "spend", "conversion", "hook_rate", "completion_rate", "roas"])}
<h3>Fatigue Candidates (top 5)</h3>
{rows_table(retention.get("fatigue_candidates", [])[:5], ["ad_id", "ad_name", "spend", "conversion", "mid_retention", "cost_per_retained_viewer"])}
</div>

<div class="section" id="audience">
<h2>Audience</h2>
{audience_html if audience_html else "<p>Audience breakdowns available in source artifacts. Key segments are tagged scale / reduce / monitor / no_result_spend / high_roas.</p>"}
</div>

<div class="section" id="activities">
<h2>Activity Context</h2>
<p>Activity evidence is context only — never KPI truth. See sources/activity_factors.json for full decomposition.</p>
</div>

<div class="section" id="measurement">
<h2>Measurement Caveats</h2>
<p>Value and revenue metrics are marked measurement-limited if the metric probe cannot confirm active value/revenue fields. All ROAS figures are directional until probe confirms active revenue.</p>
<div class="warn">{html.escape(json.dumps([d.get('name','') for d in validation.get('degraded_sources',[])], ensure_ascii=False)) if validation.get('degraded_sources') else "No degraded sources."}</div>
</div>

<div class="section" id="next-actions">
<h2>Next Actions</h2>
{next_actions_html}
<h3>Approval-Gated Operations</h3>
<p>Budget, bid, status, and creative changes require explicit approval. Staged plans available in the adapter layer.</p>
</div>

</body></html>"""
        (self.run_dir / "report.html").write_text(html_text, encoding="utf-8")

    def run_audit(self) -> dict[str, Any]:
        audit_script = Path(__file__).with_name("audit_creatiads_report.py")
        proc = subprocess.run(
            ["python3", str(audit_script), "--run-dir", str(self.run_dir), "--html", str(self.run_dir / "report.html"), "--out", str(self.run_dir / "report_audit.json")],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        audit_path = self.run_dir / "report_audit.json"
        if audit_path.exists():
            try:
                audit_data = json.loads(audit_path.read_text(encoding="utf-8"))
            except Exception:
                audit_data = {"status": "failed", "parse_error": True, "stdout": proc.stdout, "stderr": proc.stderr}
        else:
            audit_data = {"status": "failed", "stdout": proc.stdout, "stderr": proc.stderr}
        passed = audit_data.get("required_passed", False)
        self.manifest["audit_passed"] = passed
        if not passed:
            self._mark_degraded("report_audit", "failed", failed_checks={k: v for k, v in audit_data.get("checks", {}).items() if not v})
            validation_path = self.run_dir / "validation_summary.json"
            if validation_path.exists():
                try:
                    vs = json.loads(validation_path.read_text(encoding="utf-8"))
                    if vs.get("status") == "passed":
                        vs["status"] = "failed"
                        vs.setdefault("not_queried_sources", [])
                        vs.setdefault("degraded_sources", [])
                        vs["degraded_sources"].append("report_audit_failed")
                        write_json(validation_path, vs)
                except Exception:
                    pass
        write_json(self.run_dir / "manifest.json", self.manifest)
        return audit_data


def main() -> int:
    parser = argparse.ArgumentParser(description="Creatiads TikTok MCP-first report runner")
    parser.add_argument("--platform", choices=["tiktok"], default="tiktok")
    parser.add_argument("--data-dir", help="Directory with pre-fetched MCP data in sources/*.json")
    parser.add_argument("--advertiser-id", default="")
    parser.add_argument("--period", choices=["daily", "weekly", "custom"], default="weekly")
    parser.add_argument("--depth", choices=["quick", "fast", "standard", "full", "deep"], default="standard")
    parser.add_argument("--since")
    parser.add_argument("--until")
    parser.add_argument("--previous-since")
    parser.add_argument("--previous-until")
    parser.add_argument("--run-dir")
    parser.add_argument("--top-objects", type=int, default=30)
    parser.add_argument("--dry-run", action="store_true", help="Output the depth plan and exit without processing data.")
    parser.add_argument("--quiet", action="store_true", help="Print only a compact machine-readable summary.")
    parser.add_argument("--summary-json", type=Path, help="Write the compact run summary to this JSON path.")
    args = parser.parse_args()
    if args.depth == "quick":
        args.depth = "fast"
    runner = TikTokReportRunner(args)
    manifest = runner.run()
    summary = compact_manifest_summary(runner.run_dir, manifest)
    if args.summary_json:
        write_json(args.summary_json, summary)
    if args.quiet:
        print(json.dumps(summary, ensure_ascii=False))
    else:
        print(json.dumps({"run_dir": str(runner.run_dir), "manifest": manifest}, ensure_ascii=False, indent=2))
    if manifest.get("completeness_passed") is False:
        return 1
    if manifest.get("validation_status") == "failed":
        return 1
    if manifest.get("audit_passed") is False:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
