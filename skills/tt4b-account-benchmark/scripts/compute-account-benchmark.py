#!/usr/bin/env python3
import argparse
import json
import math
import re
import sys
from pathlib import Path
from urllib.parse import quote, urlencode


CORE_METRICS = {
    "spend": {"label": "Spend", "format": "currency", "direction": "neutral", "role": "scale"},
    "impressions": {"label": "Impressions", "format": "number", "direction": "neutral", "role": "scale"},
    "clicks": {"label": "Clicks", "format": "number", "direction": "neutral", "role": "traffic"},
    "conversion": {"label": "Conversions", "format": "number", "direction": "higher", "role": "outcome"},
    "video_play_actions": {"label": "Video Plays", "format": "number", "direction": "neutral", "role": "scale"},
    "video_watched_2s": {"label": "2s Video Views", "format": "number", "direction": "neutral", "role": "scale"},
    "video_watched_6s": {"label": "6s Video Views", "format": "number", "direction": "neutral", "role": "scale"},
    "video_views_p25": {"label": "Video 25%", "format": "number", "direction": "higher", "role": "engagement"},
    "video_views_p50": {"label": "Video 50%", "format": "number", "direction": "higher", "role": "engagement"},
    "video_views_p75": {"label": "Video 75%", "format": "number", "direction": "higher", "role": "engagement"},
    "video_views_p100": {"label": "Video 100%", "format": "number", "direction": "higher", "role": "engagement"},
    "profile_visits": {"label": "Profile Visits", "format": "number", "direction": "higher", "role": "engagement"},
    "follows": {"label": "Follows", "format": "number", "direction": "higher", "role": "engagement"},
    "likes": {"label": "Likes", "format": "number", "direction": "higher", "role": "engagement"},
    "comments": {"label": "Comments", "format": "number", "direction": "higher", "role": "engagement"},
    "shares": {"label": "Shares", "format": "number", "direction": "higher", "role": "engagement"},
}

ALIASES = {
    "cpa": "cost_per_conversion",
    "cvr": "conversion_rate",
    "conversions": "conversion",
}

ADS_MANAGER_COLUMNS = [
    "campaign_budget",
    "ad_id",
    "budget",
    "bid",
    "schedule",
    "attribution_window",
    "attribution_statistic_type",
    "ad_name",
    "creative_id",
    "po_number",
    "stat_cost",
    "cpc",
    "cpm",
    "show_cnt",
    "click_cnt",
    "ctr",
    "time_attr_convert_cnt",
    "skan_convert_cnt",
    "time_attr_conversion_cost",
    "skan_conversion_cost",
    "time_attr_conversion_rate",
    "time_attr_conversion_rate_imp",
    "skan_conversion_rate",
    "skan_conversion_rate_imp",
    "time_attr_effect_cnt",
    "time_attr_effect_cost",
    "time_attr_effect_rate",
    "time_attr_deep_convert_cnt_v2",
    "time_attr_cost_per_deep_convert_v2",
    "time_attr_deep_convert_rate_v2",
]

LINK_KINDS = {
    "campaign": {"route": "campaign", "field": "campaign_ids", "grain": "Campaign", "idField": "campaign_id"},
    "adgroup": {"route": "adgroup", "field": "ad_ids", "grain": "AdGroup", "idField": "adgroup_link_id"},
    "creative": {"grain": "Creative"},
    "smart_plus_creative": {"grain": "Creative"},
}


def normalize_link_kind(value):
    if value == "ad":
        return "creative"
    if value in {"smart-plus-creative", "smart_plus", "splus_creative", "splus"}:
        return "smart_plus_creative"
    return value


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Compute same-account TikTok benchmark statistics from raw report JSON."
    )
    parser.add_argument("--analysis")
    parser.add_argument("--benchmark")
    parser.add_argument("--analysis-id")
    parser.add_argument("--analysis-label", default="analysis window")
    parser.add_argument("--benchmark-label", default="benchmark window")
    parser.add_argument("--analysis-days", type=float, default=1)
    parser.add_argument("--benchmark-days", type=float, default=1)
    parser.add_argument("--metrics", default="cpc,cost_per_conversion,cpm,ctr,conversion_rate")
    parser.add_argument("--cost-active-min", type=float, default=0)
    parser.add_argument("--objective-field")
    parser.add_argument("--objective-type")
    parser.add_argument("--advertiser-id")
    parser.add_argument("--link-kind", default="auto", help="campaign|adgroup|creative|smart_plus_creative|auto. Ad/Creative grains render plain object names without Ads Manager links.")
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--relative-time", default="last_7_days", help="Deprecated compatibility flag; object links use st/et only")
    parser.add_argument("--format", default="markdown", choices=["markdown", "json"])
    parser.add_argument("--language", default="zh", choices=["en", "zh"])
    args = parser.parse_args(argv)
    args.link_kind = normalize_link_kind(args.link_kind)
    if args.link_kind not in {"campaign", "adgroup", "creative", "smart_plus_creative", "auto"}:
        parser.error(f"Unsupported link kind: {args.link_kind}")
    args.metric_keys = [item.strip() for item in args.metrics.split(",") if item.strip()]
    if not args.analysis or not args.benchmark:
        parser.error("--analysis and --benchmark are required")
    return args


def read_json(file_path):
    return json.loads(Path(file_path).read_text(encoding="utf-8"))


def unwrap_report(value):
    if isinstance(value, list) and len(value) == 1 and value[0].get("type") == "text":
        return unwrap_report(json.loads(value[0]["text"]))
    if isinstance(value, dict) and value.get("type") == "text" and isinstance(value.get("text"), str):
        return unwrap_report(json.loads(value["text"]))
    if isinstance(value, dict) and isinstance(value.get("data"), dict) and isinstance(value["data"].get("list"), list):
        return value["data"]
    if isinstance(value, dict) and isinstance(value.get("list"), list):
        return value
    raise ValueError("Unsupported report shape: expected TikTok report data.list")


def normalize_metric_key(key):
    return ALIASES.get(key, key)


def to_number(value):
    if value is None or value == "-":
        return 0
    try:
        number = float(str(value).replace(",", ""))
    except ValueError:
        return 0
    return number if math.isfinite(number) else 0


def to_string_or_empty(value):
    if value is None or value == "":
        return ""
    return str(value)


def normalize_rows(report):
    rows = []
    for row in report["list"]:
        metrics = row.get("metrics") or {}
        dimensions = row.get("dimensions") or {}
        normalized = {key: to_number(value) for key, value in metrics.items()}
        campaign_id = to_string_or_empty(dimensions.get("campaign_id") or metrics.get("campaign_id") or row.get("campaign_id"))
        adgroup_id = to_string_or_empty(dimensions.get("adgroup_id") or metrics.get("adgroup_id") or row.get("adgroup_id"))
        ad_id = to_string_or_empty(dimensions.get("ad_id") or metrics.get("ad_id") or row.get("ad_id"))
        creative_id = to_string_or_empty(
            dimensions.get("creative_id") or metrics.get("creative_id") or row.get("creative_id")
        )
        smart_plus_ad_id = to_string_or_empty(
            dimensions.get("smart_plus_ad_id")
            or metrics.get("smart_plus_ad_id")
            or row.get("smart_plus_ad_id")
        )
        virtual_creative_id = to_string_or_empty(
            dimensions.get("virtual_creative_id")
            or metrics.get("virtual_creative_id")
            or row.get("virtual_creative_id")
        )
        adgroup_link_id = adgroup_id or ad_id
        creative_link_id = ad_id or smart_plus_ad_id
        smart_plus_creative_link_id = virtual_creative_id or smart_plus_ad_id
        advertiser_id = to_string_or_empty(
            dimensions.get("advertiser_id") or metrics.get("advertiser_id") or row.get("advertiser_id")
        )
        object_id = ad_id or adgroup_id or campaign_id or smart_plus_ad_id or advertiser_id or "unknown"
        name_candidate = (
            metrics.get("ad_name")
            or metrics.get("adgroup_name")
            or metrics.get("campaign_name")
            or row.get("ad_name")
            or row.get("adgroup_name")
            or row.get("campaign_name")
        )
        name_field_available = name_candidate is not None and str(name_candidate).strip() != ""
        normalized.update(
            {
                "id": object_id,
                "campaign_id": campaign_id,
                "adgroup_id": adgroup_id,
                "ad_id": ad_id,
                "creative_id": creative_id,
                "smart_plus_ad_id": smart_plus_ad_id,
                "virtual_creative_id": virtual_creative_id,
                "adgroup_link_id": adgroup_link_id,
                "creative_link_id": creative_link_id,
                "smart_plus_creative_link_id": smart_plus_creative_link_id,
                "advertiser_id": advertiser_id,
                "name": str(name_candidate) if name_field_available else "Unknown name",
                "nameFieldAvailable": name_field_available,
                "objective_type": str(metrics.get("objective_type") or dimensions.get("objective_type") or ""),
                "campaign_type": str(metrics.get("campaign_type") or dimensions.get("campaign_type") or ""),
                "spend": to_number(metrics.get("spend")),
                "impressions": to_number(metrics.get("impressions")),
                "clicks": to_number(metrics.get("clicks")),
                "conversion": to_number(metrics.get("conversion") if metrics.get("conversion") is not None else metrics.get("conversions")),
            }
        )
        rows.append(normalized)
    return rows


def select_analysis_target(rows, analysis_id):
    if analysis_id:
        for row in rows:
            if row["id"] == str(analysis_id):
                return row
        raise ValueError(f"Analysis target not found: {analysis_id}")
    if len(rows) == 1:
        return rows[0]
    raise ValueError("Analysis report has multiple rows. Pass --analysis-id to select one target.")


def totals(rows):
    result = {"spend": 0, "impressions": 0, "clicks": 0, "conversion": 0}
    for row in rows:
        for key in set(result) | set(row):
            result_value = result.get(key)
            row_value = row.get(key)
            if (
                isinstance(result_value, (int, float))
                and not isinstance(result_value, bool)
            ) or (
                isinstance(row_value, (int, float))
                and not isinstance(row_value, bool)
            ):
                result[key] = to_number(result.get(key)) + to_number(row.get(key))
    return result


def percentile(values, p):
    if not values:
        return None
    sorted_values = sorted(values)
    idx = (len(sorted_values) - 1) * p
    lo = math.floor(idx)
    hi = math.ceil(idx)
    if lo == hi:
        return sorted_values[lo]
    weight = idx - lo
    return sorted_values[lo] * (1 - weight) + sorted_values[hi] * weight


def percentile_rank(values, current, direction):
    if current is None or not math.isfinite(current) or not values:
        return None
    if direction == "lower":
        better_or_equal = len([value for value in values if value >= current])
    else:
        better_or_equal = len([value for value in values if value <= current])
    return float(f"{(better_or_equal / len(values)) * 100:.2f}")


def average(values):
    if not values:
        return None
    return sum(values) / len(values)


def confidence(count):
    if count == 0:
        return "unavailable"
    if count < 10:
        return "low"
    if count < 30:
        return "medium"
    return "high"


def finite(value):
    return value is not None and isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def fmt(value, format_name):
    if not finite(value):
        return "-"
    if format_name == "currency":
        return f"${value:,.2f}"
    if format_name == "percent":
        return f"{value:.2f}%"
    return f"{value:,.2f}"


def verdict(current, median, definition):
    if current is None or median is None:
        return "Unavailable"
    delta = (current - median) / abs(median or 1)
    if abs(delta) < 0.05:
        return "Near median"
    pct = f"{abs(delta * 100):.0f}"
    if definition["direction"] == "neutral":
        return f"{pct}% higher than median" if current > median else f"{pct}% lower than median"
    better = current < median if definition["direction"] == "lower" else current > median
    return f"{pct}% better than median" if better else f"{pct}% worse than median"


def relative_position(metric):
    rank = metric.get("percentileRank")
    direction = metric.get("direction")
    if rank is None:
        return "-"
    rank_text = f"{rank:g}"
    if direction != "neutral" and rank <= 0:
        return "Worse than most comparable objects"
    if direction != "neutral" and rank >= 100:
        return "Better than nearly all comparable objects"
    if direction == "neutral" and rank <= 0:
        return "Lower than most comparable objects"
    if direction == "neutral" and rank >= 100:
        return "Higher than nearly all comparable objects"
    if direction == "neutral":
        return f"Higher than {rank_text}% of comparable objects"
    if rank >= 50:
        return f"Better than {rank_text}% of comparable objects"
    return f"Worse than {100 - rank:g}% of comparable objects"


def relative_position_text(metric, language="en"):
    if language != "zh":
        return metric.get("positionLabel") or relative_position(metric)
    rank = metric.get("percentileRank")
    if rank is None:
        return "-"
    rank_text = f"{rank:g}"
    if metric.get("direction") == "neutral":
        if rank <= 0:
            return "低于大多数可比对象"
        if rank >= 100:
            return "高于几乎所有可比对象"
        return f"高于 {rank_text}% 的可比对象"
    if rank <= 0:
        return "弱于大多数可比对象"
    if rank >= 100:
        return "优于几乎所有可比对象"
    if rank >= 50:
        return f"优于 {rank_text}% 的可比对象"
    return f"差于 {100 - rank:g}% 的可比对象"


def verdict_text(metric, language="en"):
    if language != "zh":
        return metric["verdict"]
    current = metric.get("current")
    p50 = metric.get("p50")
    if current is None or p50 is None:
        return "不可判断"
    delta = (current - p50) / abs(p50 or 1)
    if abs(delta) < 0.05:
        return "接近中位数"
    pct = f"{abs(delta * 100):.0f}"
    if metric.get("direction") == "neutral":
        return f"比中位数高 {pct}%" if current > p50 else f"比中位数低 {pct}%"
    better = current < p50 if metric.get("direction") == "lower" else current > p50
    return f"比中位数好 {pct}%" if better else f"比中位数差 {pct}%"


def metric_label(metric, language="en"):
    if language != "zh":
        return metric["label"]
    labels = {
        "Spend": "消耗",
        "Impressions": "展示",
        "Clicks": "点击",
        "Conversions": "转化",
        "Video Plays": "视频播放",
        "2s Video Views": "2 秒播放",
        "6s Video Views": "6 秒播放",
        "Video 25%": "视频 25%",
        "Video 50%": "视频 50%",
        "Video 75%": "视频 75%",
        "Video 100%": "视频完播",
        "Profile Visits": "主页访问",
        "Follows": "关注",
        "Likes": "点赞",
        "Comments": "评论",
        "Shares": "分享",
    }
    return labels.get(metric["label"], metric["label"])


def infer_link_kind(row, requested="auto"):
    if is_smart_plus_creative_row(row) and (not requested or requested in {"auto", "creative", "ad"}):
        return "smart_plus_creative"
    if requested and requested != "auto":
        return requested
    if row.get("ad_id"):
        return "creative"
    if row.get("adgroup_id"):
        return "adgroup"
    if row.get("campaign_id"):
        return "campaign"
    return "campaign"


def is_smart_plus_creative_row(row):
    return bool(
        row.get("virtual_creative_id")
        or row.get("smart_plus_ad_id")
        or re.search(r"SMART|UPGRADED_SMART_PLUS", row.get("campaign_type") or "", re.IGNORECASE)
    )


def grain_label(row, args):
    return LINK_KINDS.get(infer_link_kind(row, args.link_kind), {}).get("grain", "Object")


def markdown_link_label(value):
    return str(value).replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def object_link_state(row, args):
    kind = infer_link_kind(row, args.link_kind)
    if kind in {"creative", "smart_plus_creative"}:
        return {"kind": kind, "url": "", "reason": "ad grain links disabled", "disabled": True}
    config = LINK_KINDS.get(kind)
    if not config:
        return {"kind": kind, "url": "", "reason": "unsupported link kind"}
    if not args.advertiser_id:
        return {"kind": kind, "url": "", "reason": "missing advertiser_id"}
    object_id = row.get(config["idField"])
    if not object_id:
        return {"kind": kind, "url": "", "reason": f"missing {config['idField']}"}
    params = {
        "aadvid": args.advertiser_id,
        "navigate_from": "campaignList",
        "columns": ",".join(ADS_MANAGER_COLUMNS),
    }
    if args.start_date:
        params["st"] = args.start_date
    if args.end_date:
        params["et"] = args.end_date
    params.update(
        {
            "filters[0][field]": config["field"],
            "filters[0][filter_type]": "0",
            "filters[0][in_field_values][0]": object_id,
        }
    )
    if config.get("includeSource") is not False:
        params["filters[0][source]"] = "sidebar"
    return {
        "kind": kind,
        "field": config["field"],
        "objectId": object_id,
        "url": f"https://ads.tiktok.com/i18n/manage/{config['route']}?{urlencode(params)}",
        "reason": "",
    }


def object_label(row, args):
    label = row["name"] if row.get("nameFieldAvailable") else "Unknown name"
    link = object_link_state(row, args)
    return f"[{markdown_link_label(label)}]({link['url']})" if link["url"] else label


def metric_definition(key, options):
    normalized_key = normalize_metric_key(key)
    if normalized_key == "cpc":
        return {
            "key": "cpc",
            "label": "CPC",
            "direction": "lower",
            "role": "efficiency",
            "format": "currency",
            "eligible": lambda row: row["spend"] > 0 and row["clicks"] > 0,
            "value": lambda row: row["spend"] / row["clicks"],
            "current": lambda row: row["spend"] / row["clicks"] if row["spend"] > 0 and row["clicks"] > 0 else None,
            "blended": lambda total, _rows: total["spend"] / total["clicks"] if total["spend"] > 0 and total["clicks"] > 0 else None,
        }
    if normalized_key == "cost_per_conversion":
        return {
            "key": "cost_per_conversion",
            "label": "CPA",
            "direction": "lower",
            "role": "efficiency",
            "format": "currency",
            "eligible": lambda row: row["spend"] > 0 and row["conversion"] > 0,
            "value": lambda row: row["spend"] / row["conversion"],
            "current": lambda row: row["spend"] / row["conversion"] if row["spend"] > 0 and row["conversion"] > 0 else None,
            "blended": lambda total, _rows: total["spend"] / total["conversion"] if total["spend"] > 0 and total["conversion"] > 0 else None,
        }
    if normalized_key == "cpm":
        return {
            "key": "cpm",
            "label": "CPM",
            "direction": "lower",
            "role": "efficiency",
            "format": "currency",
            "eligible": lambda row: row["spend"] > 0 and row["impressions"] > 0,
            "value": lambda row: (row["spend"] / row["impressions"]) * 1000,
            "current": lambda row: (row["spend"] / row["impressions"]) * 1000 if row["spend"] > 0 and row["impressions"] > 0 else None,
            "blended": lambda total, _rows: (total["spend"] / total["impressions"]) * 1000 if total["spend"] > 0 and total["impressions"] > 0 else None,
        }
    if normalized_key == "ctr":
        return {
            "key": "ctr",
            "label": "CTR",
            "direction": "higher",
            "role": "rate",
            "format": "percent",
            "eligible": lambda row: row["impressions"] > 0,
            "value": lambda row: (row["clicks"] / row["impressions"]) * 100,
            "current": lambda row: (row["clicks"] / row["impressions"]) * 100 if row["impressions"] > 0 else None,
            "blended": lambda total, _rows: (total["clicks"] / total["impressions"]) * 100 if total["impressions"] > 0 else None,
        }
    if normalized_key == "conversion_rate":
        return {
            "key": "conversion_rate",
            "label": "CVR",
            "direction": "higher",
            "role": "outcome",
            "format": "percent",
            "eligible": lambda row: row["clicks"] > 0,
            "value": lambda row: (row["conversion"] / row["clicks"]) * 100,
            "current": lambda row: (row["conversion"] / row["clicks"]) * 100 if row["clicks"] > 0 else None,
            "blended": lambda total, _rows: (total["conversion"] / total["clicks"]) * 100 if total["clicks"] > 0 else None,
        }
    meta = CORE_METRICS.get(normalized_key, {"label": normalized_key, "format": "number", "direction": "higher"})
    analysis_days = max(1, float(options.get("analysisDays") or 1))
    benchmark_days = max(1, float(options.get("benchmarkDays") or 1))

    def has_metric(row):
        return normalized_key in row

    return {
        "key": normalized_key,
        "label": meta["label"] if analysis_days == benchmark_days else f"{meta['label']} / day",
        "direction": meta["direction"],
        "role": meta.get("role", "scale"),
        "format": meta["format"],
        "eligible": has_metric,
        "value": lambda row: to_number(row.get(normalized_key)) / benchmark_days if has_metric(row) else math.nan,
        "current": lambda row: to_number(row.get(normalized_key)) / analysis_days if has_metric(row) else None,
        "blended": lambda _total, rows: average([to_number(row.get(normalized_key)) / benchmark_days for row in rows if has_metric(row)]),
    }


def compute(analysis_target, benchmark_rows, options=None):
    options = options or {}
    cost_active_min = float(options.get("costActiveMin") or 0)
    seen = set()
    metric_keys = []
    for key in options.get("metricKeys") or []:
        normalized = normalize_metric_key(key)
        if normalized not in seen:
            seen.add(normalized)
            metric_keys.append(normalized)
    objective_field = options.get("objectiveField") or None
    objective_type = options.get("objectiveType") or None
    if objective_field and objective_type:
        objective_filtered_rows = [
            row for row in benchmark_rows if str(row.get(objective_field, "")) == str(objective_type)
        ]
    else:
        objective_filtered_rows = benchmark_rows
    cost_active_rows = [row for row in objective_filtered_rows if row["spend"] > cost_active_min]
    benchmark_totals = totals(cost_active_rows)
    zero_conversion_cost_active = len([row for row in cost_active_rows if row["conversion"] == 0])
    metrics = []
    for key in metric_keys:
        definition = metric_definition(key, options)
        values = [definition["value"](row) for row in cost_active_rows if definition["eligible"](row)]
        values = [value for value in values if finite(value)]
        current = definition["current"](analysis_target)
        blended = definition["blended"](benchmark_totals, cost_active_rows)
        p25 = percentile(values, 0.25)
        p50 = percentile(values, 0.5)
        p75 = percentile(values, 0.75)
        rank = percentile_rank(values, current, definition["direction"])
        metric = {
            "key": definition["key"],
            "label": definition["label"],
            "direction": definition["direction"],
            "current": current,
            "blended": blended,
            "p25": p25,
            "p50": p50,
            "p75": p75,
            "top25": p25 if definition["direction"] == "lower" else p75,
            "percentileRank": rank,
            "eligibleSample": len(values),
            "confidence": confidence(len(values)),
            "verdict": verdict(current, p50, definition),
            "format": definition["format"],
            "role": definition.get("role", "metric"),
            "positionLabel": relative_position({"direction": definition["direction"], "percentileRank": rank}),
        }
        metrics.append(metric)
    return {
        "analysis": {"target": analysis_target},
        "benchmark": {
            "totalRows": len(benchmark_rows),
            "objectiveFilteredRows": len(objective_filtered_rows),
            "objectiveField": objective_field,
            "objectiveType": objective_type,
            "costActiveRows": len(cost_active_rows),
            "excludedRows": len(benchmark_rows) - len(cost_active_rows),
            "excludedByObjective": len(benchmark_rows) - len(objective_filtered_rows),
            "zeroConversionCostActive": zero_conversion_cost_active,
            "totals": benchmark_totals,
        },
        "metrics": metrics,
    }


def compute_account_benchmark(analysis_report, benchmark_report, args):
    analysis = unwrap_report(analysis_report)
    benchmark = unwrap_report(benchmark_report)
    analysis_target = select_analysis_target(normalize_rows(analysis), args.analysis_id)
    return compute(
        analysis_target,
        normalize_rows(benchmark),
        {
            "metricKeys": args.metric_keys,
            "analysisDays": args.analysis_days,
            "benchmarkDays": args.benchmark_days,
            "costActiveMin": args.cost_active_min,
            "objectiveField": args.objective_field,
            "objectiveType": args.objective_type,
        },
    )


def primary_verdict_metric(metrics):
    for key in ["cost_per_conversion", "conversion_rate", "cpc", "ctr", "cpm"]:
        for metric in metrics:
            if metric["key"] == key and metric["direction"] != "neutral":
                return metric
    for metric in metrics:
        if metric["direction"] != "neutral":
            return metric
    return metrics[0] if metrics else None


def qualitative_read(metric, language="en"):
    if not metric or metric.get("percentileRank") is None:
        return "暂不可判断" if language == "zh" else "unavailable"
    if metric["direction"] == "neutral":
        if metric["percentileRank"] >= 70:
            return "规模偏高" if language == "zh" else "high scale"
        if metric["percentileRank"] <= 30:
            return "规模偏低" if language == "zh" else "low scale"
        return "规模接近中位数" if language == "zh" else "near median scale"
    if metric["percentileRank"] >= 70:
        return "表现强" if language == "zh" else "strong"
    if metric["percentileRank"] <= 30:
        return "表现弱" if language == "zh" else "weak"
    return "表现接近中位数" if language == "zh" else "near median"


def compact_metric_bullets(metrics, language="en"):
    lines = []
    for metric in metrics:
        label = metric_label(metric, language)
        current = fmt(metric["current"], metric["format"])
        median_value = fmt(metric["p50"], metric["format"])
        position = relative_position_text(metric, language)
        if language == "zh":
            lines.append(f"- {label}：当前 {current}；中位数 {median_value}；{position}。")
        else:
            lines.append(f"- {label}: current {current}; median {median_value}; {position}.")
    return lines


def escaped_regexp(value):
    return re.escape(str(value))


def validate_markdown_output(markdown, result, args):
    target = result["analysis"]["target"]
    grain = grain_label(target, args)
    link = object_link_state(target, args)
    if re.search(r"\|\s*ID\s*\|", markdown):
        raise ValueError("Output validation failed: object tables must not include a standalone ID column.")
    if re.search(r"\|\s*(对象|Object)\s*\|", markdown):
        raise ValueError("Output validation failed: object table header must use the concrete grain, not Object/对象.")
    if f"| {grain} |" not in markdown:
        raise ValueError(f"Output validation failed: object overview must use '{grain}' as the first column.")
    if target.get("id") and target["id"] != "unknown" and f"{target['name']} ({target['id']})" in markdown:
        raise ValueError("Output validation failed: object references must not use the legacy name-plus-ID style.")
    if link.get("disabled"):
        label = target["name"] if target.get("nameFieldAvailable") else "Unknown name"
        linked_label = re.compile(rf"\[{escaped_regexp(markdown_link_label(label))}\]\([^\n]+\)")
        if linked_label.search(markdown):
            raise ValueError("Output validation failed: Ad-grain object names must render as plain text, not Markdown links.")
        if (
            re.search(r"https://ads\.tiktok\.com/i18n/manage/creative", markdown)
            or re.search(r"filters%5B0%5D%5Bfield%5D=(creative_ids|virtual_creative_id)", markdown)
            or re.search(r"filters\[0\]\[field\]=(creative_ids|virtual_creative_id)", markdown)
        ):
            raise ValueError("Output validation failed: Ad-grain output must not include Creative Ads Manager links.")
    if link["url"]:
        for forbidden_param in ["relative_time=", "sort_state=", "sort_order="]:
            if forbidden_param in markdown:
                raise ValueError(f"Output validation failed: object links must not include {forbidden_param.replace('=', '')}.")
        if "navigate_from=campaignList" not in markdown:
            raise ValueError("Output validation failed: object links must use navigate_from=campaignList.")
        if "columns=" not in markdown:
            raise ValueError("Output validation failed: object links must include the standard columns parameter.")
        if "filters%5B0%5D%5Bfield%5D=" not in markdown and "filters[0][field]=" not in markdown:
            raise ValueError("Output validation failed: object links must use filters[0][field], not shorthand ID parameters.")
        encoded_field = quote(str(link["field"]), safe="")
        if (
            f"filters%5B0%5D%5Bfield%5D={encoded_field}" not in markdown
            and f"filters[0][field]={link['field']}" not in markdown
        ):
            raise ValueError(f"Output validation failed: object link filter field must use {link['field']}.")
        encoded_link_id = quote(str(link["objectId"]), safe="")
        if (
            f"filters%5B0%5D%5Bin_field_values%5D%5B0%5D={encoded_link_id}" not in markdown
            and f"filters[0][in_field_values][0]={link['objectId']}" not in markdown
        ):
            raise ValueError(f"Output validation failed: object link filter must use {link['kind']} link ID {link['objectId']}.")
        if re.search(r"filters%5B0%5D%5Bin_field_values%5D%5B[1-9]\d*%5D=", markdown) or re.search(r"filters\[0\]\[in_field_values\]\[[1-9]\d*\]=", markdown):
            raise ValueError("Output validation failed: object links must target one object per link.")
        if re.search(r"[?&](campaign_ids|ad_ids|creative_ids)=", markdown):
            raise ValueError("Output validation failed: object links must not use top-level campaign_ids/ad_ids/creative_ids parameters.")
        label = target["name"] if target.get("nameFieldAvailable") else "Unknown name"
        linked_label = re.compile(rf"\[{escaped_regexp(markdown_link_label(label))}\]\([^\n]+\)")
        if not linked_label.search(markdown):
            raise ValueError("Output validation failed: linked object label is missing.")
        if target.get("nameFieldAvailable"):
            without_linked_labels = linked_label.sub("", markdown)
            if target["name"] in without_linked_labels:
                raise ValueError("Output validation failed: known object name appears outside Markdown link syntax.")


def render_markdown(result, args):
    language = args.language or "en"
    zh = language == "zh"
    lines = []
    target = result["analysis"]["target"]
    target_label = object_label(target, args)
    target_grain = grain_label(target, args)
    target_link_state = object_link_state(target, args)
    verdict_metric = primary_verdict_metric(result["metrics"])
    lines.append("# 账号基准摘要" if zh else "# Account Benchmark Summary")
    lines.append("")
    lines.append("## 结论先说" if zh else "## Bottom line")
    if verdict_metric:
        if zh:
            lines.append(
                f"{target_label} {qualitative_read(verdict_metric, language)}："
                f"{metric_label(verdict_metric, language)} {verdict_text(verdict_metric, language)}。"
            )
        else:
            lines.append(
                f"{target_label} is {qualitative_read(verdict_metric, language)}: "
                f"{metric_label(verdict_metric, language)} is {verdict_text(verdict_metric, language)}."
            )
    else:
        lines.append(
            f"{target_label} 暂不可判断：没有可用指标生成基准结论。"
            if zh
            else f"{target_label} is unavailable: no metric could be used to produce a benchmark verdict."
        )
    lines.append("")
    lines.extend(compact_metric_bullets(result["metrics"], language))
    important_samples = [
        metric["eligibleSample"]
        for metric in result["metrics"]
        if metric["key"] in ["cost_per_conversion", "conversion_rate", "cpc", "ctr", "cpm"]
    ]
    min_important_sample = min(important_samples) if important_samples else result["benchmark"]["costActiveRows"]
    if min_important_sample == 0:
        lines.append("")
        lines.append(
            "样本提示：至少一个关键指标没有可比样本，因此不要对该指标下 benchmark 结论。"
            if zh
            else "Sample caveat: no eligible comparable rows are available for at least one key metric, so no benchmark conclusion should be drawn for that metric."
        )
    elif min_important_sample < 10:
        lines.append("")
        lines.append(
            f"样本提示：至少一个关键指标只有 {min_important_sample} 个可比样本。这个结论更适合作为方向性信号，建议用更长窗口或更粗粒度验证。"
            if zh
            else f"Sample caveat: only {min_important_sample} eligible comparable rows are available for at least one key metric. Treat the result as a directional signal and verify with a longer window or coarser grain."
        )
    elif min_important_sample < 30:
        lines.append("")
        lines.append(
            f"样本提示：至少一个关键指标有 {min_important_sample} 个可比样本，结论具备参考价值；如果要影响投放决策，仍建议用更长窗口验证。"
            if zh
            else f"Sample caveat: {min_important_sample} eligible comparable rows are available for at least one key metric. The result is useful, but should still be verified with a longer window if it will drive decisions."
        )
    lines.append("")
    lines.append("## 对象指标概览" if zh else "## Object metric overview")
    lines.append(
        f"| {target_grain} | {' | '.join(metric_label(metric, language) for metric in result['metrics'])} | "
        f"{'定位' if zh else 'Position'} |"
    )
    lines.append(f"|---{''.join('|---:' for _ in result['metrics'])}|---|")
    lines.append(
        f"| {target_label} | {' | '.join(fmt(metric['current'], metric['format']) for metric in result['metrics'])} | "
        f"{qualitative_read(verdict_metric, language) if verdict_metric else '-'} |"
    )
    lines.append("")
    lines.append("## 核心对比" if zh else "## Benchmark table")
    lines.append(
        "| 指标 | 当前对象 | 中位数 | 相对位置 | 有效样本 | 业务判断 |"
        if zh
        else "| Metric | Current | Median | Relative position | Eligible sample | Business read |"
    )
    lines.append("|---|---:|---:|---|---:|---|")
    for metric in result["metrics"]:
        lines.append(
            f"| {metric_label(metric, language)} | {fmt(metric['current'], metric['format'])} | "
            f"{fmt(metric['p50'], metric['format'])} | {relative_position_text(metric, language)} | "
            f"{metric['eligibleSample']} | {verdict_text(metric, language)} |"
        )
    lines.append("")
    lines.append("## 基准结论" if zh else "## Benchmark verdict")
    if verdict_metric:
        if zh:
            lines.append(
                f"{metric_label(verdict_metric, language)} 是当前主判断指标；当前 "
                f"{fmt(verdict_metric['current'], verdict_metric['format'])}，中位数 "
                f"{fmt(verdict_metric['p50'], verdict_metric['format'])}，{verdict_text(verdict_metric, language)}。"
            )
        else:
            lines.append(
                f"{metric_label(verdict_metric, language)} is the primary read: current "
                f"{fmt(verdict_metric['current'], verdict_metric['format'])}, median "
                f"{fmt(verdict_metric['p50'], verdict_metric['format'])}, {verdict_text(verdict_metric, language)}."
            )
    else:
        lines.append("没有可用指标生成基准结论。" if zh else "No available metric could be used to produce a benchmark verdict.")
    lines.append("")
    lines.append("## 下一步建议" if zh else "## Next steps")
    lines.append(
        "以下建议基于报表数据，执行前请结合实时投放状态确认。"
        if zh
        else "These suggestions are based on report data; confirm current delivery status before acting."
    )
    lines.append(
        "- 先复核主判断指标对应的对象状态、预算节奏和样本量，再决定是否进入优化或管理流程。"
        if zh
        else "- Review current object status, pacing, and sample size for the primary metric before moving into optimization or management."
    )
    lines.append("- 如果样本偏小，优先扩大窗口或切到更粗粒度复验。" if zh else "- If the sample is small, verify with a longer window or coarser grain first.")
    lines.append("")
    lines.append("## 附录：基准范围" if zh else "## Appendix: Benchmark scope")
    lines.append(f"分析窗口：{args.analysis_label}" if zh else f"Analysis window: {args.analysis_label}")
    lines.append(f"基准窗口：{args.benchmark_label}" if zh else f"Benchmark window: {args.benchmark_label}")
    lines.append(f"分析对象：{target_label}" if zh else f"Analysis target: {target_label}")
    if not target.get("nameFieldAvailable"):
        lines.append("名称字段不可用：使用 Unknown name 作为兜底展示。" if zh else "Name field unavailable: using Unknown name as the display fallback.")
    if args.advertiser_id and not target_link_state["url"] and not target_link_state.get("disabled"):
        lines.append(
            f"Partial link state：对象链接未生成，原因是 {target_link_state['reason']}。"
            if zh
            else f"Partial link state: object link was not generated because {target_link_state['reason']}."
        )
    if target_link_state["url"] and (not args.start_date or not args.end_date):
        lines.append(
            "Partial link state：对象链接已生成，但日期参数不完整；请以实际 benchmark 请求窗口为准。"
            if zh
            else "Partial link state: object link was generated without a complete date range; use the actual benchmark request window as the source of truth."
        )
    benchmark = result["benchmark"]
    if benchmark.get("objectiveField") and benchmark.get("objectiveType"):
        lines.append(
            f"目标过滤：{benchmark['objectiveField']} = {benchmark['objectiveType']}"
            if zh
            else f"Objective filter: {benchmark['objectiveField']} = {benchmark['objectiveType']}"
        )
    lines.append(f"基准池：spend > {args.cost_active_min:g}" if zh else f"Benchmark pool: spend > {args.cost_active_min:g}")
    lines.append(
        f"样本：{benchmark['costActiveRows']} 个有消耗对象 / {benchmark['totalRows']} 个总对象（排除 {benchmark['excludedRows']} 个）"
        if zh
        else f"Sample: {benchmark['costActiveRows']} cost-active rows / {benchmark['totalRows']} total rows ({benchmark['excludedRows']} excluded)"
    )
    if benchmark["excludedByObjective"] > 0:
        lines.append(f"按目标排除对象数：{benchmark['excludedByObjective']}" if zh else f"Objective excluded rows: {benchmark['excludedByObjective']}")
    lines.append(
        f"有消耗但 0 转化对象数：{benchmark['zeroConversionCostActive']}"
        if zh
        else f"Zero-conversion cost-active rows: {benchmark['zeroConversionCostActive']}"
    )
    lines.append(
        f"分析对象汇总：消耗 {fmt(target['spend'], 'currency')}，展示 {round(target['impressions']):,}，"
        f"点击 {round(target['clicks']):,}，转化 {round(target['conversion']):,}"
        if zh
        else f"Analysis target totals: spend {fmt(target['spend'], 'currency')}, impressions {round(target['impressions']):,}, clicks {round(target['clicks']):,}, conversions {round(target['conversion']):,}"
    )
    benchmark_totals = benchmark["totals"]
    lines.append(
        f"基准汇总：消耗 {fmt(benchmark_totals['spend'], 'currency')}，展示 {round(benchmark_totals['impressions']):,}，"
        f"点击 {round(benchmark_totals['clicks']):,}，转化 {round(benchmark_totals['conversion']):,}"
        if zh
        else f"Benchmark totals: spend {fmt(benchmark_totals['spend'], 'currency')}, impressions {round(benchmark_totals['impressions']):,}, clicks {round(benchmark_totals['clicks']):,}, conversions {round(benchmark_totals['conversion']):,}"
    )
    markdown = "\n".join(lines) + "\n"
    validate_markdown_output(markdown, result, args)
    return markdown


def main(argv):
    args = parse_args(argv)
    result = compute_account_benchmark(read_json(args.analysis), read_json(args.benchmark), args)
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    else:
        sys.stdout.write(render_markdown(result, args))


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except Exception as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
