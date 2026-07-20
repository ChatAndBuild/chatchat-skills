#!/usr/bin/env python3
"""Landing-page, app-path, and SKU analyzer for TikTok MCP-first reports.

Recursive URL evidence collection using MCP data access.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

try:
    from utils import STATUS_OK, STATUS_PARTIAL, extract_rows, write_json
except ImportError:  # pragma: no cover
    from .utils import STATUS_OK, STATUS_PARTIAL, extract_rows, write_json


URL_TYPE_LANDING = "landing"
URL_TYPE_APP_STORE = "app_store"
URL_TYPE_DEEPLINK = "deeplink"
URL_TYPE_PRODUCT = "product"
URL_TYPE_CATALOG = "catalog"
URL_TYPE_SHOP = "shop"
URL_TYPE_CREATIVE_ASSET = "creative_asset"
URL_TYPE_UNKNOWN = "unknown"

APP_STORE_HOSTS = frozenset({"apps.apple.com", "itunes.apple.com", "play.google.com", "appgallery.huawei.com"})
SHOP_HOST_SIGNALS = frozenset({"shop", "store", "checkout", "cart", "myshopify", "product"})
DEEPLINK_SCHEMES = frozenset({"fb", "instagram", "snapchat", "tiktok", "twitter", "whatsapp", "tg", "viber"})


def _dimension(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    if value is None and isinstance(row.get("dimensions"), dict):
        value = row["dimensions"].get(key)
    if value is None and isinstance(row.get("metrics"), dict):
        value = row["metrics"].get(key)
    return str(value or "")


def _metric(row: dict[str, Any], key: str) -> float:
    value = row.get(key)
    if value is None and isinstance(row.get("metrics"), dict):
        value = row["metrics"].get(key)
    try:
        return float(str(value or 0).replace(",", "").replace("%", ""))
    except Exception:
        return 0.0


def classify_url_type(url: str) -> str:
    url_lower = url.lower().strip()
    if not url_lower:
        return URL_TYPE_UNKNOWN
    parsed = urlparse(url_lower)
    host = parsed.netloc.lower()
    scheme = parsed.scheme.lower()
    path = parsed.path.lower()
    if any(store in host for store in APP_STORE_HOSTS):
        return URL_TYPE_APP_STORE
    if scheme in DEEPLINK_SCHEMES:
        return URL_TYPE_DEEPLINK
    if "catalog" in host or "catalog" in path:
        return URL_TYPE_CATALOG
    if any(sig in host for sig in SHOP_HOST_SIGNALS) or "/products/" in path or "/product/" in path:
        if "/products/" in path or "/product/" in path:
            return URL_TYPE_PRODUCT
        return URL_TYPE_SHOP
    if "cdn" in host or "image" in host or "video" in host or "media" in host:
        return URL_TYPE_CREATIVE_ASSET
    return URL_TYPE_LANDING


def normalize_url(raw: str) -> str:
    raw = str(raw or "").strip()
    if not raw or raw in {"-", "--", "null", "None"}:
        return ""
    parsed = urlparse(raw)
    if not parsed.netloc:
        return raw
    keep_keys = {"sku", "variant", "product", "item", "id", "app", "campaign"}
    query = parse_qs(parsed.query)
    kept = {key: values[:1] for key, values in query.items() if key.lower() in keep_keys}
    return urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path.rstrip("/") or "/", "", urlencode(kept, doseq=True), ""))


def extract_product_key(url: str) -> str:
    parsed = urlparse(url)
    path_parts = [part for part in parsed.path.split("/") if part]
    for i, part in enumerate(path_parts):
        if part in {"products", "product", "sku"} and i + 1 < len(path_parts):
            return path_parts[i + 1]
    query = parse_qs(parsed.query)
    for key in ("sku", "product", "item", "variant", "id"):
        if key in query and query[key]:
            return query[key][0]
    return parsed.path.rstrip("/") or "/"


def pick_landing_url(row: dict[str, Any], smart_detail_by_id: dict[str, dict[str, Any]]) -> tuple[str, str]:
    direct = _dimension(row, "ad_url")
    if direct and direct not in {"-", "--"}:
        return direct, "report_ad_url"
    smart_id = _dimension(row, "smart_plus_ad_id") or _dimension(row, "ad_id_v2")
    detail = smart_detail_by_id.get(smart_id) if smart_id else None
    if detail:
        for key in ("landing_page_url", "landing_page_urls"):
            value = detail.get(key)
            if isinstance(value, str) and value:
                return value, f"smart_plus_detail.{key}"
            if isinstance(value, list) and value:
                first = value[0]
                if isinstance(first, str):
                    return first, f"smart_plus_detail.{key}"
        for item in detail.get("landing_page_url_list") or []:
            if isinstance(item, dict) and item.get("landing_page_url"):
                return str(item["landing_page_url"]), "smart_plus_detail.landing_page_url_list"
    for key in ("app_download_url", "adgroup_download_url"):
        fallback = _dimension(row, key)
        if fallback and fallback not in {"-", "--"}:
            return fallback, f"report_{key}"
    return "", "unresolved"


def analyze_landing_app_paths(
    ad_rows: list[dict[str, Any]],
    ad_v2_rows: list[dict[str, Any]],
    smart_details: list[dict[str, Any]],
) -> dict[str, Any]:
    detail_by_id: dict[str, dict[str, Any]] = {}
    for detail in smart_details:
        for key in ("smart_plus_ad_id", "ad_id"):
            value = str(detail.get(key) or "")
            if value:
                detail_by_id[value] = detail

    url_groups: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "normalized_url": "", "url": "", "source": "", "url_type": URL_TYPE_UNKNOWN,
        "product_key": "", "spend": 0.0, "clicks": 0.0, "conversion": 0.0,
        "value": 0.0, "rows": 0,
    })
    unresolved_rows: list[dict[str, Any]] = []
    no_url_spend = 0.0

    for row in [*ad_v2_rows, *ad_rows]:
        url, source = pick_landing_url(row, detail_by_id)
        normalized = normalize_url(url)
        spend = _metric(row, "spend")
        if not normalized:
            unresolved_rows.append({
                "ad_id": _dimension(row, "ad_id"),
                "ad_id_v2": _dimension(row, "ad_id_v2"),
                "spend": spend,
                "source": source,
            })
            no_url_spend += spend
            continue
        key = normalized
        item = url_groups[key]
        item["normalized_url"] = normalized
        item["url"] = url
        item["source"] = source
        item["url_type"] = classify_url_type(normalized)
        item["product_key"] = extract_product_key(normalized) if item["url_type"] == URL_TYPE_PRODUCT else ""
        item["spend"] += spend
        item["clicks"] += _metric(row, "clicks")
        item["conversion"] += max(_metric(row, "conversion"), _metric(row, "result"))
        item["value"] += max(_metric(row, "total_purchase_value"), _metric(row, "onsite_total_purchase_value"))
        item["rows"] += 1

    rows = []
    for item in url_groups.values():
        spend = item["spend"]
        conversion = item["conversion"]
        item["cost"] = spend / conversion if conversion else None
        item["roas"] = item["value"] / spend if spend else None
        rows.append(item)

    rows.sort(key=lambda r: r["spend"], reverse=True)
    type_summary = defaultdict(lambda: {"spend": 0.0, "url_count": 0})
    for row in rows:
        t = row["url_type"]
        type_summary[t]["spend"] += row["spend"]
        type_summary[t]["url_count"] += 1

    status = STATUS_OK if rows else (STATUS_PARTIAL if unresolved_rows else "supported_empty")
    return {
        "status": status,
        "rows": rows,
        "unresolved": unresolved_rows,
        "unresolved_spend": round(no_url_spend, 4),
        "no_url_spend": round(no_url_spend, 4),
        "url_type_summary": {k: dict(v) for k, v in type_summary.items()},
        "total_url_groups": len(rows),
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Analyze TikTok landing/app/SKU paths with MCP data.")
    parser.add_argument("--ad-rows", help="JSON file with AUCTION_AD report rows")
    parser.add_argument("--ad-v2-rows", help="JSON file with AUCTION_AD (ad_id_v2) report rows")
    parser.add_argument("--smart-details", help="JSON file with smart_plus_ad_get result")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    def _load(path: str) -> list[dict[str, Any]]:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return data.get("rows") or data if isinstance(data, list) else []

    result = analyze_landing_app_paths(
        ad_rows=_load(args.ad_rows) if args.ad_rows else [],
        ad_v2_rows=_load(args.ad_v2_rows) if args.ad_v2_rows else [],
        smart_details=_load(args.smart_details) if args.smart_details else [],
    )
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())