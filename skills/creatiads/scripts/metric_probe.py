#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from utils import STATUS_OK, STATUS_SUPPORTED_EMPTY, STATUS_UNSUPPORTED, extract_rows, write_json
except ImportError:  # pragma: no cover
    from .utils import STATUS_OK, STATUS_SUPPORTED_EMPTY, STATUS_UNSUPPORTED, extract_rows, write_json


BASE_METRICS = {
    "core": ["spend", "impressions", "clicks", "ctr", "cpc", "cpm", "reach", "frequency"],
    "conversion": ["conversion", "cost_per_conversion", "conversion_rate_v2", "result", "cost_per_result", "result_rate", "purchase", "cost_per_purchase"],
    "value": ["total_purchase", "total_purchase_value", "total_active_pay_roas", "complete_payment", "complete_payment_roas", "value_per_complete_payment", "onsite_total_purchase", "onsite_total_purchase_value", "onsite_purchases_roas"],
    "creative_video": ["video_play_actions", "video_watched_2s", "video_watched_6s", "video_views_p25", "video_views_p50", "video_views_p75", "video_views_p100", "average_video_play", "engaged_view", "engaged_view_15s"],
    "app": ["app_install", "real_time_app_install", "skan_app_install", "launch_app", "registration", "subscribe", "start_trial", "in_app_ad_click", "in_app_purchase", "cost_per_app_install"],
    "shop": ["shop_total_purchase_by_order_submission", "shop_gross_revenue_by_order_submission", "onsite_total_add_to_cart", "onsite_total_product_details_page_view", "onsite_initiate_checkout", "onsite_shopping", "shop_product_click"],
    "lead": ["form", "onsite_form", "button_click", "messaging_total_conversation_tiktok_direct_message", "sales_lead", "phone_call", "loan_apply"],
    "game": ["level_achieved", "tutorial_complete", "create_gamerole", "achieve_level", "sales_achievement_unlocked"],
    "traffic_quality": ["landing_page_view", "traffic_landing_page_view", "cost_per_landing_page_view", "click_to_destination_rate"],
}


TYPE_GROUPS = {
    "电商": ["core", "conversion", "value", "shop", "creative_video"],
    "短剧": ["core", "conversion", "value", "creative_video", "app"],
    "小说": ["core", "conversion", "value", "creative_video", "app"],
    "工具": ["core", "conversion", "app", "creative_video"],
    "休闲游戏": ["core", "conversion", "value", "app", "creative_video"],
    "中重度游戏": ["core", "conversion", "value", "app", "creative_video", "game"],
    "金融借贷": ["core", "conversion", "lead"],
    "社交": ["core", "conversion", "lead", "app"],
    "泛娱乐": ["core", "conversion", "creative_video", "app"],
    "搜索套利": ["core", "conversion", "traffic_quality"],
    "网赚": ["core", "conversion", "lead"],
    "赌博": ["core", "conversion", "value"],
    "代理商/多类型": ["core", "conversion", "value", "app", "shop", "lead", "creative_video", "game", "traffic_quality"],
}


PROFILE_GROUPS = {
    "light": ["core", "conversion"],
    "batch": ["core", "conversion", "value"],
    "vertical": None,
    "full": list(BASE_METRICS.keys()),
}

TRAFFIC_CHECK_METRICS = ["spend", "impressions", "clicks", "conversion", "result"]


def _fnum(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(",", "").replace("%", ""))
    except Exception:
        return 0.0


def accept_metric_set(
    active_metrics: list[dict[str, Any]],
    supported_empty: list[dict[str, Any]],
    unsupported: list[dict[str, Any]],
) -> list[str]:
    """Return the accepted set of metric names for current and previous windows.

    Unsupported metrics are excluded. Supported-empty metrics are included for
    comparability between windows.
    """
    accepted: list[str] = []
    seen: set[str] = set()
    for item in active_metrics:
        name = str(item.get("metric") or "")
        if name and name not in seen:
            seen.add(name)
            accepted.append(name)
    for item in supported_empty:
        name = str(item.get("metric") or "")
        if name and name not in seen:
            seen.add(name)
            accepted.append(name)
    return accepted


def _is_active(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return float(value) != 0.0
    if isinstance(value, str):
        text = value.strip()
        if not text or text == "-":
            return False
        try:
            return float(text.replace(",", "")) != 0.0
        except Exception:
            return True
    if isinstance(value, list):
        return any(_is_active(item) for item in value)
    if isinstance(value, dict):
        return any(_is_active(item) for item in value.values())
    return bool(value)


def _metric_value(row: dict[str, Any], metric: str) -> Any:
    if metric in row:
        return row.get(metric)
    for key in ("metrics", "dimensions"):
        value = row.get(key)
        if isinstance(value, dict) and metric in value:
            return value[metric]
    return None


def user_type_hash(user_type_payload: dict[str, Any] | None) -> str | None:
    if not user_type_payload:
        return None
    top = (user_type_payload.get("top_types") or [{}])[0] if isinstance(user_type_payload.get("top_types"), list) else {}
    payload = {
        "top_type": user_type_payload.get("top_type") or top.get("type"),
        "top_index": top.get("index"),
        "derived_user_type": user_type_payload.get("derived_user_type"),
        "w2a_evidence": bool(user_type_payload.get("w2a_evidence")),
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def recommend_metric_groups(user_type: str, profile: str, *, derived_user_type: str | None = None, w2a: bool = False, shop: bool = False) -> list[str]:
    if profile != "vertical":
        groups = list(PROFILE_GROUPS[profile] or [])
    else:
        groups = list(TYPE_GROUPS.get(user_type, ["core", "conversion", "value", "creative_video"]))
    if derived_user_type == "工具/W2A":
        w2a = True
    if w2a and "app" not in groups:
        groups.append("app")
    if shop and "shop" not in groups:
        groups.append("shop")
    return groups


def recommend_metric_preset(
    user_type: str,
    *,
    profile: str = "vertical",
    derived_user_type: str | None = None,
    w2a: bool = False,
    shop: bool = False,
    source_user_type: dict[str, Any] | None = None,
) -> dict[str, Any]:
    groups = recommend_metric_groups(user_type, profile, derived_user_type=derived_user_type, w2a=w2a, shop=shop)
    metrics: list[str] = []
    for group in groups:
        metrics.extend(BASE_METRICS[group])
    deduped = []
    seen = set()
    for metric in metrics:
        if metric not in seen:
            seen.add(metric)
            deduped.append(metric)
    return {
        "platform": "tiktok",
        "user_type": user_type,
        "derived_user_type": derived_user_type or user_type,
        "profile": profile,
        "groups": groups,
        "metrics": deduped,
        "source_user_type_hash": user_type_hash(source_user_type),
    }


def classify_metric_states(rows: list[dict[str, Any]], metrics: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    active: list[dict[str, Any]] = []
    empty: list[dict[str, Any]] = []
    for metric in metrics:
        seen = False
        sample = None
        is_active = False
        for row in rows:
            value = _metric_value(row, metric)
            if value is None:
                continue
            seen = True
            sample = value
            if _is_active(value):
                is_active = True
                break
        entry = {"metric": metric, "sample_value": sample, "seen": seen}
        if is_active:
            active.append(entry)
        else:
            empty.append(entry)
    return active, empty


def run_tiktok_metric_probe(
    *,
    probe_results: dict[str, dict[str, Any]] | None = None,
    traffic_check: dict[str, Any] | None = None,
    user_type: str,
    profile: str = "vertical",
    w2a: bool = False,
    shop: bool = False,
    derived_user_type: str | None = None,
    source_user_type: dict[str, Any] | None = None,
    custom_metrics: list[str] | None = None,
) -> dict[str, Any]:
    preset = recommend_metric_preset(user_type, profile=profile, derived_user_type=derived_user_type, w2a=w2a, shop=shop, source_user_type=source_user_type)
    custom_metrics = [metric for metric in (custom_metrics or []) if metric and metric not in preset["metrics"]]
    if custom_metrics:
        preset = {
            **preset,
            "metrics": preset["metrics"] + custom_metrics,
            "user_adjustments": {"add_metrics": custom_metrics},
        }
    active: list[dict[str, Any]] = []
    empty: list[dict[str, Any]] = []
    unsupported: list[dict[str, Any]] = []
    invalid_combinations: list[dict[str, Any]] = []
    request_stats = {"requests": 0, "successful_groups": 0, "failed_groups": 0, "traffic_check_requests": 1}

    traffic = traffic_check or {}
    if not traffic.get("has_traffic"):
        return {
            "recommended_preset": preset,
            "active_metrics": [],
            "supported_empty_metrics": [],
            "unsupported_metrics": [],
            "invalid_combinations": [],
            "request_stats": {"requests": 1, "successful_groups": 0, "failed_groups": 0, "traffic_check_requests": 1},
            "measurement_limited": True,
            "traffic_check": traffic,
            "summary": {"notes": ["No non-zero traffic metrics found; skipped heavier metric groups."]},
        }

    results = probe_results or {}
    for group in preset["groups"]:
        metrics = BASE_METRICS[group]
        request_stats["requests"] += 1
        result = results.get(group, {})
        if result.get("status") == STATUS_OK:
            request_stats["successful_groups"] += 1
            group_active, group_empty = classify_metric_states(result.get("rows", []), metrics)
            for item in group_active:
                active.append({**item, "group": group})
            for item in group_empty:
                empty.append({**item, "group": group, "status": STATUS_SUPPORTED_EMPTY})
        else:
            request_stats["failed_groups"] += 1
            status = result.get("status") or STATUS_UNSUPPORTED
            target = invalid_combinations if status == "invalid_combination" else unsupported
            for metric in metrics:
                target.append({"metric": metric, "group": group, "status": status, "reason": "MCP report route did not return rows"})
    if custom_metrics:
        request_stats["requests"] += 1
        result = results.get("user_adjustments") or results.get("custom_metrics") or {}
        if result.get("status") == STATUS_OK:
            request_stats["successful_groups"] += 1
            custom_active, custom_empty = classify_metric_states(result.get("rows", []), custom_metrics)
            for item in custom_active:
                active.append({**item, "group": "user_adjustments"})
            for item in custom_empty:
                empty.append({**item, "group": "user_adjustments", "status": STATUS_SUPPORTED_EMPTY})
        else:
            request_stats["failed_groups"] += 1
            status = result.get("status") or STATUS_UNSUPPORTED
            target = invalid_combinations if status == "invalid_combination" else unsupported
            for metric in custom_metrics:
                target.append({"metric": metric, "group": "user_adjustments", "status": status, "reason": "User-added metric probe did not return rows"})
    measurement_limited = not any(item["metric"] in {"total_purchase_value", "complete_payment_roas", "onsite_total_purchase_value"} for item in active)
    return {
        "traffic_check": traffic,
        "recommended_preset": preset,
        "active_metrics": active,
        "supported_empty_metrics": empty,
        "unsupported_metrics": unsupported,
        "invalid_combinations": invalid_combinations,
        "request_stats": request_stats,
        "measurement_limited": measurement_limited,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Creatiads TikTok metric preset/probe")
    parser.add_argument("--input", help="JSON file with pre-fetched probe results")
    parser.add_argument("--user-type", default="代理商/多类型")
    parser.add_argument("--profile", choices=["light", "batch", "vertical", "full"], default="vertical")
    parser.add_argument("--w2a", action="store_true")
    parser.add_argument("--shop", action="store_true")
    parser.add_argument("--derived-user-type")
    parser.add_argument("--custom-metrics", default="", help="Comma-separated user-added metrics to probe once before caching.")
    parser.add_argument("--preset-only", action="store_true")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    if args.preset_only:
        payload = recommend_metric_preset(args.user_type, profile=args.profile, derived_user_type=args.derived_user_type, w2a=args.w2a, shop=args.shop)
    else:
        probe_data: dict[str, Any] = {}
        if args.input:
            probe_data = json.loads(Path(args.input).read_text(encoding="utf-8"))
        payload = run_tiktok_metric_probe(
            probe_results=probe_data.get("probe_results"),
            traffic_check=probe_data.get("traffic_check"),
            user_type=args.user_type,
            profile=args.profile,
            derived_user_type=args.derived_user_type,
            w2a=args.w2a,
            shop=args.shop,
            custom_metrics=[item.strip() for item in args.custom_metrics.split(",") if item.strip()],
        )
    write_json(Path(args.out), payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
