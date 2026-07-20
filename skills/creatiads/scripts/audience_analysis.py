#!/usr/bin/env python3
"""Audience breakdown analysis for TikTok MCP-first reports.

Pulls country, age/gender, placement, and device/platform breakdowns.
Normalizes segments and tags each with action labels.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from utils import STATUS_OK, STATUS_PARTIAL, STATUS_SUPPORTED_EMPTY, extract_rows, write_json
except ImportError:  # pragma: no cover
    from .utils import STATUS_OK, STATUS_PARTIAL, STATUS_SUPPORTED_EMPTY, extract_rows, write_json


SEGMENT_TAGS = {
    "scale": "High spend with strong conversion — scale this segment.",
    "monitor": "Moderate performance — monitor for changes.",
    "reduce": "High spend with weak conversion — consider reducing.",
    "weak_cvr": "Above-average spend, below-average conversion rate.",
    "cheap_click_trap": "High clicks, very low conversion — likely low-quality traffic.",
    "no_result_spend": "Spending without measurable conversion.",
    "high_roas": "Strong value-to-spend ratio — candidate for budget increase.",
    "measurement_limited": "Insufficient data to tag.",
}

AUDIENCE_BASE_METRICS = [
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
]

AUDIENCE_VALUE_METRICS = ["total_purchase_value", "total_active_pay_roas", "onsite_total_purchase_value"]

AUDIENCE_BREAKDOWN_MAP = {
    "country": {
        "report_type": "AUDIENCE",
        "candidates": [
            ["advertiser_id", "country_code"],
            ["advertiser_id", "country"],
        ],
    },
    "age_gender": {
        "report_type": "AUDIENCE",
        "candidates": [
            ["advertiser_id", "age", "gender"],
            ["advertiser_id", "age"],
            ["advertiser_id", "gender"],
        ],
    },
    "placement": {
        "report_type": "AUDIENCE",
        "candidates": [
            ["advertiser_id", "placement"],
            ["advertiser_id", "placement_type"],
            ["advertiser_id", "site_id"],
        ],
    },
    "device": {
        "report_type": "AUDIENCE",
        "candidates": [
            ["advertiser_id", "platform"],
            ["advertiser_id", "device_platform"],
            ["advertiser_id", "device_os"],
            ["advertiser_id", "operating_system"],
        ],
    },
}


def _metric(row: dict[str, Any], key: str) -> float:
    value = row.get(key)
    if value is None and isinstance(row.get("metrics"), dict):
        value = row["metrics"].get(key)
    if value is None and key == "conversion":
        value = row.get("result")
        if value is None and isinstance(row.get("metrics"), dict):
            value = row["metrics"].get("result")
    try:
        return float(str(value or 0).replace(",", "").replace("%", ""))
    except Exception:
        return 0.0


def _dimension(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    if value is None and isinstance(row.get("dimensions"), dict):
        value = row["dimensions"].get(key)
    if value is None and isinstance(row.get("dimension_values"), dict):
        value = row["dimension_values"].get(key)
    return str(value or "")


def _segment_label(row: dict[str, Any], dimensions: list[str]) -> str:
    values = [_dimension(row, dimension) for dimension in dimensions if dimension != "advertiser_id"]
    values = [value for value in values if value]
    return " / ".join(values) if values else "all"


def _normalize_audience_rows(rows: list[dict[str, Any]], dimensions: list[str], totals: dict[str, float]) -> list[dict[str, Any]]:
    segment_dimensions = [dimension for dimension in dimensions if dimension != "advertiser_id"]
    tagged = []
    for row in rows:
        source_tags = row.get("tags") if isinstance(row.get("tags"), list) else []
        tag = str(source_tags[0]) if source_tags else tag_segment(row, totals)
        if tag == "neutral":
            tag = "monitor"
        dimension_values = {dimension: _dimension(row, dimension) for dimension in segment_dimensions}
        tagged.append({
            **dimension_values,
            "segment": _segment_label(row, dimensions),
            "dimension_values": dimension_values,
            "spend": _metric(row, "spend"),
            "impressions": _metric(row, "impressions"),
            "clicks": _metric(row, "clicks"),
            "conversion": max(_metric(row, "conversion"), _metric(row, "result")),
            "result": max(_metric(row, "conversion"), _metric(row, "result")),
            "value": max(_metric(row, "total_purchase_value"), _metric(row, "onsite_total_purchase_value")),
            "tag": tag,
            "tag_label": SEGMENT_TAGS.get(tag, ""),
            "source_tags": source_tags,
        })
    tagged.sort(key=lambda r: r["spend"], reverse=True)
    return tagged


def tag_segment(row: dict[str, Any], totals: dict[str, float]) -> str:
    spend = _metric(row, "spend")
    conversion = max(_metric(row, "conversion"), _metric(row, "result"))
    total_spend = totals.get("spend", 1) or 1
    total_conversion = totals.get("conversion", 1) or 1
    avg_cvr = total_conversion / (totals.get("clicks", 1) or 1)
    seg_cvr = conversion / (_metric(row, "clicks") or 1)
    spend_share = spend / total_spend if total_spend else 0
    if spend == 0 and conversion == 0:
        return "measurement_limited"
    if conversion and spend and (max(_metric(row, "total_purchase_value"), _metric(row, "onsite_total_purchase_value"))) / spend >= 2.0:
        return "high_roas"
    if spend_share > 0.3 and conversion > 0 and seg_cvr >= avg_cvr:
        return "scale"
    if spend_share > 0.2 and conversion == 0:
        return "no_result_spend"
    if spend_share > 0.15 and seg_cvr < avg_cvr * 0.5:
        return "weak_cvr"
    if _metric(row, "clicks") > 0 and conversion == 0 and spend > 0:
        return "cheap_click_trap"
    if spend_share > 0.1 and seg_cvr < avg_cvr * 0.7:
        return "reduce"
    return "monitor"


def analyze_audience_breakdowns(
    *,
    audience_breakdown_results: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Analyze audience breakdowns from pre-fetched MCP data.

    audience_breakdown_results is keyed by breakdown type (country, age_gender, placement, device),
    each value is a dict with 'rows' (list of report rows) and 'dimensions' (list of dimension names).
    """
    sources = audience_breakdown_results or {}
    sections: dict[str, Any] = {}
    request_stats = {"requests": 0, "fallback_count": 0, "failed_breakdowns": 0, "base_metric_retries": 0}

    for breakdown, spec in AUDIENCE_BREAKDOWN_MAP.items():
        source = sources.get(breakdown)
        source_rows = source.get("rows") if source else None
        if not source_rows and source and isinstance(source.get("segments"), list):
            source_rows = source.get("segments")
        if not source or not source_rows:
            status = source.get("status") if source else STATUS_SUPPORTED_EMPTY
            if status in {STATUS_OK, None}:
                status = STATUS_SUPPORTED_EMPTY
            sections[breakdown] = {
                "report_type": spec["report_type"],
                "data_level": "AUCTION_ADVERTISER",
                "dimensions": source.get("dimensions", []) if source else [],
                "status": status,
                "rows": [],
                "attempts": [],
                "metadata": {"segments_analyzed": 0, "segments_with_spend": 0},
            }
            continue

        rows = source_rows
        dimensions = source.get("dimensions", [])
        totals = {key: sum(_metric(row, key) for row in rows) for key in ("spend", "clicks", "conversion", "result")}
        tagged = _normalize_audience_rows(rows, dimensions, totals)
        sections[breakdown] = {
            "report_type": spec["report_type"],
            "data_level": "AUCTION_ADVERTISER",
            "dimensions": dimensions,
            "status": STATUS_OK if tagged else STATUS_SUPPORTED_EMPTY,
            "rows": tagged,
            "attempts": [],
            "metadata": {"segments_analyzed": len(tagged), "segments_with_spend": sum(1 for r in tagged if r["spend"] > 0)},
        }

    has_any = any(s.get("rows") for s in sections.values())
    recommendations: list[str] = []
    for breakdown, section in sections.items():
        for row in (section.get("rows") or [])[:5]:
            if row["tag"] in {"scale", "reduce", "no_result_spend", "high_roas"}:
                recommendations.append(f"{breakdown}: {row.get('segment') or row.get('country_code') or row.get('age') or row.get('placement') or row.get('platform')} tagged {row['tag']}")

    return {
        "status": STATUS_OK if has_any else "supported_empty",
        "sections": sections,
        "recommendations": recommendations[:10],
        "request_stats": request_stats,
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Audience breakdown analysis for TikTok reports.")
    parser.add_argument("--input", help="JSON file with pre-fetched audience breakdown results")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    audience_breakdown_results = {}
    if args.input:
        audience_breakdown_results = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = analyze_audience_breakdowns(audience_breakdown_results=audience_breakdown_results)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
