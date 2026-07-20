#!/usr/bin/env python3
"""Metric confirmation gate for account-level Creatiads profiles."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from account_profile_cache import write_account_profile_cache
    from metric_probe import BASE_METRICS, accept_metric_set
    from utils import STATUS_OK, STATUS_SUPPORTED_EMPTY, write_json
except ImportError:  # pragma: no cover
    from .account_profile_cache import write_account_profile_cache
    from .metric_probe import BASE_METRICS, accept_metric_set
    from .utils import STATUS_OK, STATUS_SUPPORTED_EMPTY, write_json


METRIC_LABELS: dict[str, dict[str, str]] = {
    "spend": {"zh": "花费", "en": "Spend"},
    "impressions": {"zh": "展示", "en": "Impressions"},
    "clicks": {"zh": "点击", "en": "Clicks"},
    "ctr": {"zh": "点击率", "en": "Click-through rate"},
    "cpc": {"zh": "单次点击成本", "en": "Cost per click"},
    "cpm": {"zh": "千次展示成本", "en": "Cost per mille"},
    "reach": {"zh": "触达人数", "en": "Reach"},
    "frequency": {"zh": "频次", "en": "Frequency"},
    "conversion": {"zh": "转化", "en": "Conversions"},
    "cost_per_conversion": {"zh": "单次转化成本", "en": "Cost per conversion"},
    "conversion_rate_v2": {"zh": "转化率", "en": "Conversion rate"},
    "result": {"zh": "结果数", "en": "Results"},
    "cost_per_result": {"zh": "单结果成本", "en": "Cost per result"},
    "result_rate": {"zh": "结果率", "en": "Result rate"},
    "purchase": {"zh": "购买", "en": "Purchases"},
    "cost_per_purchase": {"zh": "单次购买成本", "en": "Cost per purchase"},
    "total_purchase": {"zh": "总购买数", "en": "Total purchases"},
    "total_purchase_value": {"zh": "总购买价值", "en": "Total purchase value"},
    "total_active_pay_roas": {"zh": "总付费 ROAS", "en": "Total active pay ROAS"},
    "complete_payment": {"zh": "完成支付", "en": "Complete payments"},
    "complete_payment_roas": {"zh": "完成支付 ROAS", "en": "Complete payment ROAS"},
    "value_per_complete_payment": {"zh": "单次支付价值", "en": "Value per complete payment"},
    "onsite_total_purchase": {"zh": "站内总购买", "en": "Onsite total purchases"},
    "onsite_total_purchase_value": {"zh": "站内总购买价值", "en": "Onsite total purchase value"},
    "onsite_purchases_roas": {"zh": "站内购买 ROAS", "en": "Onsite purchase ROAS"},
    "video_play_actions": {"zh": "视频播放", "en": "Video play actions"},
    "video_watched_2s": {"zh": "2 秒播放", "en": "2-second video views"},
    "video_watched_6s": {"zh": "6 秒播放", "en": "6-second video views"},
    "video_views_p25": {"zh": "25% 播放", "en": "25% video views"},
    "video_views_p50": {"zh": "50% 播放", "en": "50% video views"},
    "video_views_p75": {"zh": "75% 播放", "en": "75% video views"},
    "video_views_p100": {"zh": "100% 播放", "en": "100% video views"},
    "average_video_play": {"zh": "平均播放时长", "en": "Average video play"},
    "engaged_view": {"zh": "互动观看", "en": "Engaged views"},
    "engaged_view_15s": {"zh": "15 秒互动观看", "en": "15-second engaged views"},
    "app_install": {"zh": "应用安装", "en": "App installs"},
    "real_time_app_install": {"zh": "实时应用安装", "en": "Real-time app installs"},
    "skan_app_install": {"zh": "SKAN 安装", "en": "SKAN app installs"},
    "launch_app": {"zh": "打开应用", "en": "App launches"},
    "registration": {"zh": "注册", "en": "Registrations"},
    "subscribe": {"zh": "订阅", "en": "Subscribes"},
    "start_trial": {"zh": "开始试用", "en": "Trial starts"},
    "in_app_ad_click": {"zh": "应用内广告点击", "en": "In-app ad clicks"},
    "in_app_purchase": {"zh": "应用内购买", "en": "In-app purchases"},
    "cost_per_app_install": {"zh": "单安装成本", "en": "Cost per app install"},
    "shop_total_purchase_by_order_submission": {"zh": "小店下单购买", "en": "Shop purchases by order submission"},
    "shop_gross_revenue_by_order_submission": {"zh": "小店下单收入", "en": "Shop gross revenue by order submission"},
    "onsite_total_add_to_cart": {"zh": "站内加购", "en": "Onsite add to cart"},
    "onsite_total_product_details_page_view": {"zh": "站内商品详情页浏览", "en": "Onsite product detail views"},
    "onsite_initiate_checkout": {"zh": "站内发起结账", "en": "Onsite initiate checkout"},
    "onsite_shopping": {"zh": "站内购物", "en": "Onsite shopping"},
    "shop_product_click": {"zh": "小店商品点击", "en": "Shop product clicks"},
    "form": {"zh": "表单", "en": "Forms"},
    "onsite_form": {"zh": "站内表单", "en": "Onsite forms"},
    "button_click": {"zh": "按钮点击", "en": "Button clicks"},
    "messaging_total_conversation_tiktok_direct_message": {"zh": "TikTok 私信会话", "en": "TikTok direct message conversations"},
    "sales_lead": {"zh": "销售线索", "en": "Sales leads"},
    "phone_call": {"zh": "电话拨打", "en": "Phone calls"},
    "loan_apply": {"zh": "贷款申请", "en": "Loan applications"},
    "level_achieved": {"zh": "达到关卡", "en": "Levels achieved"},
    "tutorial_complete": {"zh": "完成教程", "en": "Tutorial completes"},
    "create_gamerole": {"zh": "创建游戏角色", "en": "Game role creations"},
    "achieve_level": {"zh": "达到等级", "en": "Achieve level"},
    "sales_achievement_unlocked": {"zh": "解锁成就", "en": "Achievements unlocked"},
    "landing_page_view": {"zh": "落地页浏览", "en": "Landing page views"},
    "traffic_landing_page_view": {"zh": "流量落地页浏览", "en": "Traffic landing page views"},
    "cost_per_landing_page_view": {"zh": "单落地页浏览成本", "en": "Cost per landing page view"},
    "click_to_destination_rate": {"zh": "点击到达率", "en": "Click-to-destination rate"},
}


def _read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        name = str(value or "").strip()
        if name and name not in seen:
            seen.add(name)
            result.append(name)
    return result


def metric_entry(metric: str, *, group: str = "", source: str = "recommended") -> dict[str, str]:
    labels = METRIC_LABELS.get(metric, {})
    return {
        "metric": metric,
        "zh": labels.get("zh") or metric,
        "en": labels.get("en") or metric.replace("_", " ").title(),
        "group": group,
        "source": source,
    }


def build_metric_confirmation(user_type: dict[str, Any], preset: dict[str, Any]) -> dict[str, Any]:
    group_by_metric: dict[str, str] = {}
    for group in preset.get("groups") or []:
        for metric in BASE_METRICS.get(group, []):
            group_by_metric.setdefault(metric, group)
    metrics = _dedupe([str(metric) for metric in preset.get("metrics") or []])
    return {
        "status": "awaiting_user_confirmation",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "instruction_zh": "请确认以下垂类指标是否完整。如需补充，请提供 TikTok 指标英文名；补充指标会先做一次数据拉取测试，成功后才写入账户缓存。",
        "instruction_en": "Please confirm whether the vertical metric list is complete. If you want to add metrics, provide TikTok metric names in English; added metrics will be tested with one data pull before they are saved to the account cache.",
        "user_type": user_type.get("top_type") or ((user_type.get("top_types") or [{}])[0].get("type")),
        "derived_user_type": user_type.get("derived_user_type"),
        "groups": preset.get("groups") or [],
        "metrics": [metric_entry(metric, group=group_by_metric.get(metric, "")) for metric in metrics],
        "recommended_metric_count": len(metrics),
        "user_adjustments": {
            "add_metrics": [],
            "remove_metrics": [],
            "notes": "",
        },
        "confirmed": False,
        "cache_write_allowed": False,
    }


def merge_user_adjustments(preset: dict[str, Any], adjustments: dict[str, Any]) -> dict[str, Any]:
    add_metrics = _dedupe([str(metric) for metric in adjustments.get("add_metrics") or []])
    remove_metrics = set(_dedupe([str(metric) for metric in adjustments.get("remove_metrics") or []]))
    metrics = [metric for metric in _dedupe([str(metric) for metric in preset.get("metrics") or []] + add_metrics) if metric not in remove_metrics]
    merged = dict(preset)
    merged["metrics"] = metrics
    merged["user_adjustments"] = {
        "add_metrics": add_metrics,
        "remove_metrics": sorted(remove_metrics),
        "notes": str(adjustments.get("notes") or ""),
    }
    return merged


def _probe_metrics_by_state(probe: dict[str, Any]) -> dict[str, str]:
    states: dict[str, str] = {}
    for item in probe.get("active_metrics") or []:
        if isinstance(item, dict) and item.get("metric"):
            states[str(item["metric"])] = STATUS_OK
    for item in probe.get("supported_empty_metrics") or []:
        if isinstance(item, dict) and item.get("metric"):
            states.setdefault(str(item["metric"]), STATUS_SUPPORTED_EMPTY)
    for item in probe.get("unsupported_metrics") or []:
        if isinstance(item, dict) and item.get("metric"):
            states[str(item["metric"])] = str(item.get("status") or "unsupported")
    for item in probe.get("invalid_combinations") or []:
        if isinstance(item, dict) and item.get("metric"):
            states[str(item["metric"])] = str(item.get("status") or "invalid_combination")
    return states


def verify_adjustments(
    *,
    user_type: dict[str, Any],
    preset: dict[str, Any],
    adjustments: dict[str, Any],
    probe: dict[str, Any],
) -> dict[str, Any]:
    merged = merge_user_adjustments(preset, adjustments)
    added = merged.get("user_adjustments", {}).get("add_metrics") or []
    states = _probe_metrics_by_state(probe)
    failed = [
        {"metric": metric, "status": states.get(metric, "missing_from_probe")}
        for metric in added
        if states.get(metric) not in {STATUS_OK, STATUS_SUPPORTED_EMPTY}
    ]
    accepted_metrics = accept_metric_set(
        probe.get("active_metrics") or [],
        probe.get("supported_empty_metrics") or [],
        probe.get("unsupported_metrics") or [],
    )
    cache_write_allowed = not failed
    return {
        "status": "confirmed" if cache_write_allowed else "probe_failed",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "user_type": user_type.get("top_type") or ((user_type.get("top_types") or [{}])[0].get("type")),
        "derived_user_type": user_type.get("derived_user_type"),
        "groups": merged.get("groups") or [],
        "metrics": [metric_entry(metric, source="final") for metric in merged.get("metrics") or []],
        "accepted_probe_metrics": accepted_metrics,
        "failed_added_metrics": failed,
        "user_adjustments": merged.get("user_adjustments") or {},
        "confirmed": cache_write_allowed,
        "cache_write_allowed": cache_write_allowed,
        "final_metric_preset": merged if cache_write_allowed else None,
        "message": None if cache_write_allowed else "Some added metrics were not returned as active or supported-empty by the probe.",
    }


def maybe_write_confirmed_cache(
    *,
    advertiser_id: str,
    user_type: dict[str, Any],
    metric_preset: dict[str, Any],
    confirmation: dict[str, Any],
    evidence: dict[str, Any] | None = None,
    planner_version: str = "",
    root: Path | None = None,
) -> dict[str, Any] | None:
    if not confirmation.get("cache_write_allowed"):
        return None
    return write_account_profile_cache(
        advertiser_id,
        user_type=user_type,
        metric_preset=metric_preset,
        evidence=evidence,
        planner_version=planner_version,
        root=root,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare or verify Creatiads metric confirmation.")
    sub = parser.add_subparsers(dest="command", required=True)

    prepare = sub.add_parser("prepare")
    prepare.add_argument("--user-type", required=True, type=Path)
    prepare.add_argument("--metric-preset", required=True, type=Path)
    prepare.add_argument("--out", required=True, type=Path)

    verify = sub.add_parser("verify")
    verify.add_argument("--advertiser-id", required=True)
    verify.add_argument("--user-type", required=True, type=Path)
    verify.add_argument("--metric-preset", required=True, type=Path)
    verify.add_argument("--adjustments", required=True, type=Path)
    verify.add_argument("--probe", required=True, type=Path)
    verify.add_argument("--evidence", type=Path)
    verify.add_argument("--planner-version", default="")
    verify.add_argument("--out", required=True, type=Path)
    verify.add_argument("--write-cache", action="store_true")

    args = parser.parse_args()
    user_type = _read_json(args.user_type, {}) or {}
    preset = _read_json(args.metric_preset, {}) or {}
    if args.command == "prepare":
        payload = build_metric_confirmation(user_type, preset)
        write_json(args.out, payload)
        print(json.dumps(payload, ensure_ascii=False))
        return 0

    adjustments = _read_json(args.adjustments, {}) or {}
    probe = _read_json(args.probe, {}) or {}
    payload = verify_adjustments(user_type=user_type, preset=preset, adjustments=adjustments, probe=probe)
    if args.write_cache and payload.get("cache_write_allowed") and isinstance(payload.get("final_metric_preset"), dict):
        evidence = _read_json(args.evidence, {}) if args.evidence else {}
        maybe_write_confirmed_cache(
            advertiser_id=args.advertiser_id,
            user_type=user_type,
            metric_preset=payload["final_metric_preset"],
            confirmation=payload,
            evidence=evidence,
            planner_version=args.planner_version,
        )
    write_json(args.out, payload)
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if payload.get("cache_write_allowed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
