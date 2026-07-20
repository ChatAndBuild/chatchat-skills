#!/usr/bin/env python3
"""TikTok app, landing-page, and Smart+ evidence collector for user-type classification.

Builds the rich evidence pipeline required by :func:`classify_user_type.build_user_type_report`
using pre-fetched MCP data.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from utils import STATUS_OK, STATUS_PARTIAL, STATUS_STRUCTURED_UNAVAILABLE, extract_rows
    from tiktok_adapter import select_top_ids, smart_plus_ids_from_ad_v2_rows
except ImportError:  # pragma: no cover
    from .utils import STATUS_OK, STATUS_PARTIAL, STATUS_STRUCTURED_UNAVAILABLE, extract_rows
    from .tiktok_adapter import select_top_ids, smart_plus_ids_from_ad_v2_rows


APP_STORE_HOSTS = frozenset({"apps.apple.com", "itunes.apple.com", "play.google.com", "appgallery.huawei.com"})
W2A_HOSTS = frozenset({"app.adjust.com", "adjust.com", "appsflyer.com", "onelink.me", "branch.io", "app.link"})


@dataclass
class EvidenceBundle:
    landing_rows: list[dict[str, Any]] = field(default_factory=list)
    app_rows: list[dict[str, Any]] = field(default_factory=list)
    smart_plus_rows: list[dict[str, Any]] = field(default_factory=list)
    scraped_content: list[dict[str, Any]] = field(default_factory=list)
    catalog_evidence: list[dict[str, Any]] = field(default_factory=list)
    shop_evidence: list[dict[str, Any]] = field(default_factory=list)
    app_campaign_ids: list[str] = field(default_factory=list)
    skipped_app_url_rows: list[dict[str, Any]] = field(default_factory=list)
    skipped_url_probe_count: int = 0
    errors: list[dict[str, Any]] = field(default_factory=list)
    data_gaps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "landing_rows": self.landing_rows,
            "app_rows": self.app_rows,
            "smart_plus_rows": self.smart_plus_rows,
            "scraped_content": self.scraped_content,
            "catalog_evidence": self.catalog_evidence,
            "shop_evidence": self.shop_evidence,
            "catalog_rows": self.catalog_evidence,
            "shop_rows": self.shop_evidence,
            "app_campaign_ids": self.app_campaign_ids,
            "skipped_app_url_rows": self.skipped_app_url_rows,
            "skipped_url_probe_count": self.skipped_url_probe_count,
            "errors": self.errors,
            "data_gaps": self.data_gaps,
        }


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


def _source_rows(source: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Read normalized source rows first, then legacy MCP payload rows."""
    if not isinstance(source, dict):
        return []
    rows = extract_rows(source)
    if rows:
        return rows
    return extract_rows(source.get("payload"))


def _looks_like_app_url(url: str) -> bool:
    lowered = str(url or "").lower()
    return any(host in lowered for host in APP_STORE_HOSTS | W2A_HOSTS)


def _parse_urls_from_ad_details(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract URL evidence from ad details and Smart+ details."""
    landing_rows: list[dict[str, Any]] = []
    app_rows: list[dict[str, Any]] = []
    for row in rows:
        spend_val = _metric(row, "spend")
        ad_id = _dimension(row, "ad_id") or _dimension(row, "smart_plus_ad_id")
        ad_name = _dimension(row, "ad_name")
        campaign_id = _dimension(row, "campaign_id")
        campaign_name = _dimension(row, "campaign_name")
        for key in ("ad_url", "adgroup_download_url", "app_download_url", "landing_page_url"):
            url = _dimension(row, key)
            if not url or url in {"-", "--", "null", "None"}:
                continue
            entry = {"url": url, "source": key, "ad_id": ad_id, "ad_name": ad_name, "campaign_id": campaign_id, "campaign_name": campaign_name, "spend": spend_val}
            if _looks_like_app_url(url):
                app_rows.append({"app_url": url, "url": url, "source": key, "ad_id": ad_id, "campaign_id": campaign_id, "campaign_name": campaign_name, "spend": spend_val})
            else:
                landing_rows.append(entry)
        landing_url_list = row.get("landing_page_url_list") or row.get("landing_page_urls") or []
        if isinstance(landing_url_list, list):
            for item in landing_url_list:
                url = item.get("landing_page_url") if isinstance(item, dict) else str(item)
                if url and url not in {"-", "--"}:
                    entry = {"url": url, "source": "smart_plus_url_list", "ad_id": ad_id, "ad_name": ad_name, "campaign_id": campaign_id, "campaign_name": campaign_name, "spend": spend_val}
                    if _looks_like_app_url(url):
                        app_rows.append({"app_url": url, **entry})
                    else:
                        landing_rows.append(entry)
    return landing_rows, app_rows


def collect_app_landing_evidence(
    *,
    current_ad_rows: list[dict[str, Any]] | None = None,
    current_ad_v2_rows: list[dict[str, Any]] | None = None,
    current_campaign_rows: list[dict[str, Any]] | None = None,
    advertiser_info: dict[str, Any] | None = None,
    app_list: dict[str, Any] | None = None,
    smart_plus_details: dict[str, Any] | None = None,
    catalog_list: dict[str, Any] | None = None,
    shop_list: dict[str, Any] | None = None,
) -> EvidenceBundle:
    bundle = EvidenceBundle()
    ad_rows = current_ad_rows or []
    ad_v2_rows = current_ad_v2_rows or []
    campaign_rows = current_campaign_rows or []

    # App/W2A evidence via pre-fetched advertiser info
    info = advertiser_info or {}
    if info.get("status") == STATUS_OK:
        info_rows = _source_rows(info)
        if info_rows:
            bundle.app_rows.extend(
                {"app_name": _dimension(row, "name"), "app_url": _dimension(row, "url"), "source": "advertiser_info", "spend": 0.0}
                for row in info_rows
                if _dimension(row, "name") or _dimension(row, "url")
            )

    # App-list discovery via pre-fetched data
    apps = app_list or {}
    if apps.get("status") == STATUS_OK:
        for row in _source_rows(apps):
            bundle.app_rows.append(
                {"app_name": _dimension(row, "app_name") or _dimension(row, "name"), "app_url": _dimension(row, "app_url") or _dimension(row, "url"), "source": "app_list", "spend": 0.0}
            )

    # URL evidence from current ad + ad_v2 report rows
    l_rows, a_rows = _parse_urls_from_ad_details([*ad_rows, *ad_v2_rows])
    bundle.landing_rows.extend(l_rows)
    bundle.app_rows.extend(a_rows)
    app_campaign_ids = {str(row.get("campaign_id")) for row in bundle.app_rows if row.get("campaign_id")}

    # Smart+ detail evidence
    smart_detail_data = smart_plus_details or {}
    bundle.smart_plus_rows = _source_rows(smart_detail_data)
    if bundle.smart_plus_rows:
        sl_rows, sa_rows = _parse_urls_from_ad_details(bundle.smart_plus_rows)
        bundle.landing_rows.extend(sl_rows)
        bundle.app_rows.extend(sa_rows)
        app_campaign_ids.update(str(row.get("campaign_id")) for row in sa_rows if row.get("campaign_id"))

    if app_campaign_ids:
        retained_landing_rows = []
        for row in bundle.landing_rows:
            if str(row.get("campaign_id") or "") in app_campaign_ids:
                bundle.skipped_app_url_rows.append({**row, "skipped_for_app_campaign": True})
            else:
                retained_landing_rows.append(row)
        bundle.landing_rows = retained_landing_rows
        bundle.app_campaign_ids = sorted(app_campaign_ids)

    # Catalog evidence
    catalogs = catalog_list or {}
    if catalogs.get("status") == STATUS_OK:
        bundle.catalog_evidence = _source_rows(catalogs)
        if not bundle.catalog_evidence:
            bundle.data_gaps.append("no_catalog_evidence")

    # Shop evidence
    shops = shop_list or {}
    if shops.get("status") == STATUS_OK:
        bundle.shop_evidence = _source_rows(shops)
        if not bundle.shop_evidence:
            bundle.data_gaps.append("no_shop_evidence")

    # Campaign evidence for app/shop hints
    has_app_objective = False
    for row in campaign_rows:
        obj_type = (_dimension(row, "objective_type") or "").upper()
        promo_type = (_dimension(row, "promotion_type") or "").upper()
        if "APP" in obj_type or "APP" in promo_type:
            has_app_objective = True
            break
    if has_app_objective:
        bundle.data_gaps.append("app_objective_no_store_urls")

    bundle.skipped_url_probe_count = len(bundle.skipped_app_url_rows)

    # Scraped content: statused, not silently skipped
    if not bundle.scraped_content:
        bundle.data_gaps.append("no_scraped_content")
        bundle.scraped_content = [
            {"source": "status", "note": "Product page scraping was not performed. Available only when an approved local scraper is configured."}
        ]

    # Flag data gaps
    if not bundle.landing_rows and not bundle.app_rows:
        bundle.data_gaps.append("no_landing_or_app_urls")
    if not bundle.smart_plus_rows:
        bundle.data_gaps.append("no_smart_plus_details")

    return bundle


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Collect TikTok app/landing/Smart+ evidence for user-type classification.")
    parser.add_argument("--input", help="JSON file with pre-fetched evidence data")
    parser.add_argument("--current-ad-rows", help="JSON file with AUCTION_AD report rows")
    parser.add_argument("--current-ad-v2-rows", help="JSON file with AUCTION_AD (ad_id_v2) report rows")
    parser.add_argument("--current-campaign-rows", help="JSON file with AUCTION_CAMPAIGN report rows")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    def _load(path: str) -> list[dict[str, Any]]:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return data.get("rows") or data if isinstance(data, list) else []

    evidence_data: dict[str, Any] = {}
    if args.input:
        evidence_data = json.loads(Path(args.input).read_text(encoding="utf-8"))

    bundle = collect_app_landing_evidence(
        current_ad_rows=_load(args.current_ad_rows) if args.current_ad_rows else None,
        current_ad_v2_rows=_load(args.current_ad_v2_rows) if args.current_ad_v2_rows else None,
        current_campaign_rows=_load(args.current_campaign_rows) if args.current_campaign_rows else None,
        advertiser_info=evidence_data.get("advertiser_info"),
        app_list=evidence_data.get("app_list"),
        smart_plus_details=evidence_data.get("smart_plus_details"),
        catalog_list=evidence_data.get("catalog_list"),
        shop_list=evidence_data.get("shop_list"),
    )
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(bundle.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
