#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    from utils import write_json
except ImportError:  # pragma: no cover
    from .utils import write_json


USER_TYPE_LABELS = [
    "短剧",
    "电商",
    "工具",
    "赌博",
    "代理商/多类型",
    "休闲游戏",
    "社交",
    "小说",
    "中重度游戏",
    "搜索套利",
    "泛娱乐",
    "网赚",
    "金融借贷",
]


KEYWORD_RULES: dict[str, list[tuple[str, float]]] = {
    "短剧": [
        ("短剧", 5), ("微短剧", 5), ("drama", 4), ("short drama", 6), ("mini drama", 5),
        ("episode", 3), ("episodes", 3), ("series", 2), ("reelshort", 6), ("werewolf", 3),
        ("billionaire", 3), ("revenge", 3), ("romance drama", 4), ("watch drama", 5),
        ("playletid", 8), ("playlet", 5), ("stardusttv", 5), ("continue watching", 4),
        ("王妃", 6), ("王爷", 5), ("狼王", 6), ("真千金", 7), ("重生", 6),
        ("豪门", 5), ("赘婿", 5), ("神医", 5), ("白莲", 5), ("崽崽", 4),
        ("皇帝", 4), ("公主", 4), ("归来", 4), ("复仇", 4), ("婚姻", 3.5),
    ],
    "电商": [
        ("shopify", 5), ("myshopify", 5), ("product", 3), ("products", 3), ("shop", 3),
        ("store", 2.5), ("buy", 3), ("sale", 2.5), ("discount", 3), ("coupon", 2.5),
        ("cart", 3), ("checkout", 4), ("amazon", 3), ("temu", 3), ("shein", 3),
        ("woocommerce", 4), ("ecommerce", 5), ("电商", 5), ("购物", 4), ("商城", 4),
    ],
    "工具": [
        ("utility", 4), ("utilities", 4), ("tool", 3), ("tools", 3), ("vpn", 5),
        ("cleaner", 4), ("scan", 3), ("scanner", 4), ("keyboard", 3), ("translator", 4),
        ("translate", 3), ("pdf", 3), ("photo editor", 4), ("editor", 2), ("ai assistant", 3),
        ("weather", 3), ("calculator", 3), ("security", 3), ("antivirus", 4), ("工具", 5),
    ],
    "赌博": [
        ("casino", 6), ("slots", 5), ("slot", 4), ("poker", 5), ("betting", 6),
        ("bet", 4), ("sportsbook", 6), ("lottery", 5), ("roulette", 5), ("blackjack", 5),
        ("jackpot", 5), ("bingo", 3.5), ("gambling", 6), ("博彩", 6), ("赌博", 6),
        ("nhà cái", 7), ("nha cai", 7), ("cá cược", 6), ("ca cuoc", 6),
        ("tài xỉu", 6), ("tai xiu", 6), ("nổ hũ", 6), ("no hu", 6),
        ("lượt chơi miễn phí", 5), ("luot choi mien phi", 5), ("789k", 6),
    ],
    "休闲游戏": [
        ("genre casual", 16), ("genres casual", 16), ("category casual", 14),
        ("casual", 4), ("puzzle", 4), ("match 3", 5), ("match-3", 5), ("merge", 4),
        ("tile", 3), ("solitaire", 4), ("mahjong", 6), ("word game", 4), ("coloring", 3), ("idle", 3),
        ("arcade", 3), ("小游戏", 4), ("休闲游戏", 6), ("消除", 4), ("益智", 4),
    ],
    "社交": [
        ("social", 4), ("chat", 4), ("dating", 5), ("date", 3), ("meet", 3),
        ("friends", 3), ("friend", 2.5), ("messenger", 4), ("community", 3),
        ("live chat", 5), ("video chat", 5), ("社交", 5), ("交友", 5), ("聊天", 4),
    ],
    "小说": [
        ("novel", 5), ("fiction", 4), ("webnovel", 6), ("ebook", 3), ("reader", 3),
        ("reading", 3), ("chapter", 4), ("chapters", 4), ("romance novel", 5),
        ("story app", 4), ("小说", 6), ("阅读", 4), ("书城", 4),
    ],
    "中重度游戏": [
        ("rpg", 5), ("mmorpg", 6), ("strategy", 4), ("slg", 5), ("war", 3),
        ("battle", 3), ("shooter", 4), ("survival", 4), ("kingdom", 3), ("empire", 3),
        ("heroes", 3), ("hero", 2.5), ("raid", 4), ("anime game", 4), ("gacha", 5),
        ("pc games", 5), ("drm-free", 4), ("drm free", 4), ("gog.com", 5),
        ("中重度", 6), ("策略游戏", 5), ("角色扮演", 5),
    ],
    "搜索套利": [
        ("search", 4), ("search results", 6), ("browser", 3), ("query", 4),
        ("find", 0.25), ("finder", 3), ("yahoo", 3), ("bing", 3), ("ask.com", 4),
        ("arbitrage", 6), ("domain parking", 6), ("搜索套利", 7), ("搜索", 3),
    ],
    "泛娱乐": [
        ("entertainment", 5), ("streaming", 4), ("video", 2.5), ("music", 3),
        ("wallpaper", 3), ("horoscope", 3), ("quiz", 3), ("celebrity", 3),
        ("anime", 2.5), ("meme", 3), ("fun", 2), ("泛娱乐", 5), ("娱乐", 4),
    ],
    "网赚": [
        ("earn money", 6), ("make money", 6), ("cash reward", 5), ("rewards", 4),
        ("reward", 3), ("survey", 4), ("cashback", 4), ("work from home", 5),
        ("side hustle", 5), ("赚钱", 6), ("网赚", 7), ("返现", 4),
    ],
    "金融借贷": [
        ("loan", 6), ("loans", 6), ("credit", 4), ("cash advance", 6), ("payday", 5),
        ("borrow", 5), ("installment", 4), ("finance", 4), ("financial", 3),
        ("wallet", 2.5), ("bank", 3), ("借贷", 6), ("贷款", 6), ("金融", 5), ("信贷", 6),
    ],
    "代理商/多类型": [
        ("agency", 6), ("代理商", 7), ("client", 4), ("clients", 4), ("portfolio", 3),
        ("multi vertical", 6), ("multiple vertical", 6), ("多类型", 6),
    ],
}


NEGATIVE_RULES: dict[str, list[str]] = {
    "赌博": ["bingo workout", "bingo fitness"],
    "搜索套利": ["search and rescue"],
}


APP_STORE_HOSTS = ("apps.apple.com", "itunes.apple.com", "play.google.com")
W2A_HOST_HINTS = (
    "apps.apple.com",
    "itunes.apple.com",
    "play.google.com",
    "app.adjust.com",
    "adjust.com",
    "appsflyer.com",
    "onelink.me",
    "branch.io",
    "app.link",
)
W2A_TEXT_HINTS = ("app store", "google play", "appstore", "app install", "download app", "w2a", "web to app")


def _fnum(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict) and "value" in value:
        return _fnum(value["value"])
    try:
        return float(str(value).replace(",", "").replace("%", ""))
    except Exception:
        return 0.0


def _source_weight(spend: float) -> float:
    if spend <= 0:
        return 0.25
    return max(1.0, min(6.0, math.log10(max(spend, 0.0) + 10.0)))


def _clean_text(value: Any) -> str:
    text = str(value or "")
    text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)
    text = re.sub(r"(?<=[A-Za-z])(?=\d)|(?<=\d)(?=[A-Za-z])", " ", text)
    text = text.lower()
    text = re.sub(r"[_\-./?&=#:+]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _domain_score(ref: str) -> dict[str, float]:
    parsed = urlparse(ref)
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    scores: dict[str, float] = {}
    if any(marker in host for marker in ("myshopify.com", "shopify", "amazon.", "temu.", "shein.")):
        scores["电商"] = scores.get("电商", 0.0) + 5
    if "/products/" in path or "/cart" in path or "/checkout" in path:
        scores["电商"] = scores.get("电商", 0.0) + 4
    if any(marker in host for marker in APP_STORE_HOSTS):
        scores["工具"] = scores.get("工具", 0.0) + 0.5
    if any(marker in host for marker in ("casino", "bet", "slots", "poker")):
        scores["赌博"] = scores.get("赌博", 0.0) + 5
    if re.search(r"(^|[.-])(?:789k|888k|88k)(?:[.-]|$)", host):
        scores["赌博"] = scores.get("赌博", 0.0) + 5
    if any(marker in host for marker in ("loan", "credit", "finance", "cash")):
        scores["金融借贷"] = scores.get("金融借贷", 0.0) + 4
    if "search" in host or "search" in path:
        scores["搜索套利"] = scores.get("搜索套利", 0.0) + 3
    if any(marker in host for marker in ("gog.com", "steampowered.com", "epicgames.com")):
        scores["中重度游戏"] = scores.get("中重度游戏", 0.0) + 5
    return scores


def _looks_like_w2a_reference(value: Any) -> bool:
    text = str(value or "").lower()
    if not text:
        return False
    if any(hint in text for hint in W2A_TEXT_HINTS):
        return True
    try:
        host = urlparse(text).netloc.lower()
    except Exception:
        host = ""
    if any(hint in host or hint in text for hint in W2A_HOST_HINTS):
        return True
    return False


def _match_keywords(text: str) -> dict[str, float]:
    haystack = _clean_text(text)
    scores: dict[str, float] = {label: 0.0 for label in USER_TYPE_LABELS}
    if not haystack:
        return scores
    for label, rules in KEYWORD_RULES.items():
        negatives = NEGATIVE_RULES.get(label, [])
        if any(negative in haystack for negative in negatives):
            continue
        for keyword, value in rules:
            needle = _clean_text(keyword)
            if not needle:
                continue
            if any("\u4e00" <= char <= "\u9fff" for char in needle):
                matched = needle in haystack
            else:
                pattern = re.escape(needle).replace(r"\ ", r"\s+")
                matched = re.search(rf"(?<![a-z0-9]){pattern}(?![a-z0-9])", haystack) is not None
            if matched:
                scores[label] += value
    return scores


def _looks_like_tiktok_short_drama(text: str) -> bool:
    lowered = text.lower()
    chinese_count = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
    if any(marker in lowered for marker in ("stardusttv", "dramabox", "short drama", "mini drama")):
        return True
    if ("_iap_" in lowered or " iap " in lowered) and (
        "ttm" in lowered or "breeze" in lowered or chinese_count >= 4
    ):
        return True
    return False


def _with_tiktok_hints(text: str) -> str:
    if _looks_like_tiktok_short_drama(text):
        return f"{text} short drama mini drama episodes"
    return text


def append_sample(samples: list[dict[str, Any]], *, text: Any, source: str, spend: Any = 0, ref: Any = None) -> None:
    content = _with_tiktok_hints(" ".join(str(text or "").split()))
    if content:
        samples.append({"text": content, "source": source, "spend": round(_fnum(spend), 2), "ref": str(ref or "")})


def classify_samples(samples: list[dict[str, Any]], *, include_evidence: bool = True) -> dict[str, Any]:
    raw_scores = {label: 0.0 for label in USER_TYPE_LABELS}
    evidence: dict[str, list[dict[str, Any]]] = {label: [] for label in USER_TYPE_LABELS}
    for sample in samples:
        spend = _fnum(sample.get("spend"))
        scores = _match_keywords(str(sample.get("text") or ""))
        ref = str(sample.get("ref") or "")
        if ref.startswith(("http://", "https://")):
            for label, value in _domain_score(ref).items():
                scores[label] += value
        weight = _source_weight(spend)
        for label, score in scores.items():
            if score <= 0:
                continue
            contribution = score * weight
            raw_scores[label] += contribution
            if include_evidence and len(evidence[label]) < 8:
                evidence[label].append(
                    {
                        "source": sample.get("source"),
                        "spend": round(spend, 2),
                        "ref": ref,
                        "matched_text": str(sample.get("text") or "")[:240],
                        "score": round(contribution, 2),
                    }
                )

    non_agency = {label: score for label, score in raw_scores.items() if label != "代理商/多类型"}
    sorted_non_agency = sorted(non_agency.items(), key=lambda item: item[1], reverse=True)
    top_score = sorted_non_agency[0][1] if sorted_non_agency else 0.0
    meaningful = [(label, score) for label, score in sorted_non_agency if top_score and score >= max(8.0, top_score * 0.28)]
    distinct_refs = {sample.get("ref") for sample in samples if sample.get("ref")}
    if len(meaningful) >= 3:
        raw_scores["代理商/多类型"] = max(raw_scores["代理商/多类型"], top_score * 0.82)
    elif len(meaningful) >= 2 and len(distinct_refs) >= 8:
        raw_scores["代理商/多类型"] = max(raw_scores["代理商/多类型"], top_score * 0.55)

    max_score = max(raw_scores.values()) if raw_scores else 0.0
    rows = []
    for label, score in sorted(raw_scores.items(), key=lambda item: item[1], reverse=True):
        item = {
            "type": label,
            "index": round(score / max_score * 100, 1) if max_score > 0 else 0.0,
            "raw_score": round(score, 2),
            "confidence": "high" if max_score and score >= max_score * 0.75 and score >= 20 else "medium" if score >= 8 else "low",
        }
        if include_evidence:
            item["evidence"] = evidence.get(label, [])
        rows.append(item)
    return {"top_types": rows[:3], "all_types": rows}


def detect_w2a_evidence(*row_groups: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for rows in row_groups:
        for row in rows or []:
            if not isinstance(row, dict):
                continue
            row_text = json.dumps(row, ensure_ascii=False, sort_keys=True)
            if not _looks_like_w2a_reference(row_text):
                continue
            evidence.append(
                {
                    "source": str(row.get("source") or row.get("url_type") or "w2a"),
                    "ref": str(row.get("url") or row.get("app_url") or row.get("landing_page_url") or row.get("ref") or "")[:300],
                    "campaign_id": str(row.get("campaign_id") or ""),
                    "ad_id": str(row.get("ad_id") or row.get("smart_plus_ad_id") or ""),
                }
            )
            if len(evidence) >= 12:
                return evidence
    return evidence


def _row_text(row: dict[str, Any], fields: list[str]) -> str:
    parts: list[str] = []
    for field in fields:
        value = row.get(field)
        if value is None and isinstance(row.get("dimensions"), dict):
            value = row["dimensions"].get(field)
        if value is None and isinstance(row.get("metrics"), dict):
            value = row["metrics"].get(field)
        if isinstance(value, (list, tuple)):
            parts.extend(str(item) for item in value)
        elif isinstance(value, dict):
            parts.append(json.dumps(value, ensure_ascii=False))
        elif value is not None:
            parts.append(str(value))
    return " ".join(parts)


def build_user_type_report(
    *,
    advertiser_id: str,
    start_date: str,
    end_date: str,
    account_rows: list[dict[str, Any]] | None = None,
    campaign_rows: list[dict[str, Any]] | None = None,
    adgroup_rows: list[dict[str, Any]] | None = None,
    ad_rows: list[dict[str, Any]] | None = None,
    smart_plus_rows: list[dict[str, Any]] | None = None,
    landing_rows: list[dict[str, Any]] | None = None,
    app_rows: list[dict[str, Any]] | None = None,
    catalog_rows: list[dict[str, Any]] | None = None,
    shop_rows: list[dict[str, Any]] | None = None,
    skipped_app_url_rows: list[dict[str, Any]] | None = None,
    scraped_content: list[dict[str, Any]] | None = None,
    errors: list[dict[str, Any]] | None = None,
    include_evidence: bool = True,
) -> dict[str, Any]:
    samples: list[dict[str, Any]] = []
    campaigns = campaign_rows or []
    landings = landing_rows or []
    apps = app_rows or []
    catalogs = catalog_rows or []
    shops = shop_rows or []
    skipped_app_urls = skipped_app_url_rows or []
    scraped = scraped_content or []
    for row in account_rows or []:
        append_sample(samples, text=_row_text(row, ["advertiser_name", "name", "industry"]), source="advertiser", spend=0, ref=advertiser_id)
    for row in campaigns:
        append_sample(
            samples,
            text=_row_text(row, ["campaign_name", "objective_type", "campaign_automation_type", "app_promotion_type"]),
            source="campaign",
            spend=(row.get("metrics") or row).get("spend"),
            ref=_row_text(row, ["campaign_id"]),
        )
    for row in adgroup_rows or []:
        append_sample(
            samples,
            text=_row_text(row, ["adgroup_name", "promotion_type", "optimization_goal", "billing_event", "placement_type"]),
            source="adgroup",
            spend=(row.get("metrics") or row).get("spend"),
            ref=_row_text(row, ["adgroup_id"]),
        )
    for row in ad_rows or []:
        append_sample(
            samples,
            text=_row_text(row, ["ad_name", "ad_text", "call_to_action", "ad_url", "tt_app_name", "mobile_app_id", "promotion_type"]),
            source="ad",
            spend=(row.get("metrics") or row).get("spend"),
            ref=_row_text(row, ["ad_url", "ad_id"]),
        )
    for row in smart_plus_rows or []:
        append_sample(
            samples,
            text=_row_text(row, ["ad_name", "ad_text_list", "landing_page_url", "landing_page_url_list", "creative_list", "ad_configuration"]),
            source="smart_plus",
            spend=(row.get("metrics") or row).get("spend"),
            ref=_row_text(row, ["smart_plus_ad_id", "ad_id", "landing_page_url"]),
        )
    for row in landings:
        append_sample(samples, text=_row_text(row, ["url", "normalized_url", "title", "product_name", "app_name"]), source="landing_page", spend=row.get("spend"), ref=row.get("url") or row.get("normalized_url"))
    for row in apps:
        append_sample(samples, text=_row_text(row, ["app_name", "app_names", "app_url", "app_urls", "category", "primary_genre", "genres", "url_type"]), source="app", spend=row.get("spend"), ref=row.get("app_url") or row.get("app_key"))
    for row in catalogs:
        append_sample(samples, text=_row_text(row, ["catalog_name", "name", "catalog_type", "business_type", "product_count", "ad_creation_eligible"]), source="catalog", spend=row.get("spend"), ref=row.get("catalog_id") or row.get("id"))
    for row in shops:
        append_sample(samples, text=_row_text(row, ["shop_name", "name", "shop_id", "catalog_id", "seller_name", "business_type"]), source="shop", spend=row.get("spend"), ref=row.get("shop_id") or row.get("id"))
    for row in skipped_app_urls:
        append_sample(samples, text=_row_text(row, ["url", "app_url", "campaign_name", "objective_type", "promotion_type", "app_name", "source"]), source="skipped_app_url", spend=row.get("spend"), ref=row.get("url") or row.get("app_url"))
    for row in scraped:
        append_sample(samples, text=_row_text(row, ["title", "name", "description", "text", "price", "brand", "url"]), source=f"scraped_{row.get('source') or 'content'}", spend=row.get("spend"), ref=row.get("url"))

    classification = classify_samples(samples, include_evidence=include_evidence)
    objective_counts = Counter(_row_text(row, ["objective_type", "promotion_type", "optimization_goal"]) for row in [*(campaigns or []), *(adgroup_rows or [])] if row)
    top_type = ((classification.get("top_types") or [{}])[0].get("type") or "")
    w2a_evidence = detect_w2a_evidence(apps, skipped_app_urls, landings, scraped, smart_plus_rows or [])
    derived_user_type = "工具/W2A" if top_type == "工具" and w2a_evidence else top_type or "代理商/多类型"
    landing_skipped_url_probe_count = len(skipped_app_urls) or sum(1 for row in landings if row.get("skipped_for_app_campaign"))
    return {
        "advertiser_id": advertiser_id,
        "start_date": start_date,
        "end_date": end_date,
        "taxonomy": USER_TYPE_LABELS,
        "top_types": classification["top_types"],
        "all_types": classification["all_types"],
        "top_type": top_type,
        "derived_user_type": derived_user_type,
        "w2a_evidence": w2a_evidence,
        "objective_evidence": dict(objective_counts.most_common(12)),
        "advertisers": account_rows or [],
        "campaigns": campaigns,
        "campaign_count": len(campaigns),
        "landing_pages": landings,
        "app_rows": apps,
        "catalog_rows": catalogs,
        "shop_rows": shops,
        "skipped_app_url_rows": skipped_app_urls,
        "scraped_content": scraped,
        "sample_count": len(samples),
        "scraped_content_count": len(scraped),
        "landing_skipped_url_probe_count": landing_skipped_url_probe_count,
        "errors": errors or [],
        "data_gaps": [
            gap
            for gap, present in (
                ("no_campaign_evidence", bool(campaigns)),
                ("no_ad_evidence", bool(ad_rows)),
                ("no_landing_or_app_evidence", bool(landings or apps)),
                ("no_scraped_content", bool(scraped)),
            )
            if not present
        ] + [
            err.get("data_gap") for err in (errors or [])
            if isinstance(err, dict) and err.get("data_gap")
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Creatiads user-type classifier")
    parser.add_argument("--input", required=True, help="JSON evidence file")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    report = build_user_type_report(
        advertiser_id=str(payload.get("advertiser_id") or ""),
        start_date=str(payload.get("start_date") or payload.get("since") or ""),
        end_date=str(payload.get("end_date") or payload.get("until") or ""),
        account_rows=payload.get("account_rows") or payload.get("advertisers"),
        campaign_rows=payload.get("campaign_rows") or payload.get("campaigns"),
        adgroup_rows=payload.get("adgroup_rows") or payload.get("adgroups"),
        ad_rows=payload.get("ad_rows") or payload.get("ads"),
        smart_plus_rows=payload.get("smart_plus_rows"),
        landing_rows=payload.get("landing_rows") or payload.get("landing_pages"),
        app_rows=payload.get("app_rows") or payload.get("apps"),
        catalog_rows=payload.get("catalog_rows") or payload.get("catalogs"),
        shop_rows=payload.get("shop_rows") or payload.get("shops"),
        skipped_app_url_rows=payload.get("skipped_app_url_rows"),
        scraped_content=payload.get("scraped_content"),
        errors=payload.get("errors"),
        include_evidence=bool(payload.get("include_evidence", True)),
    )
    write_json(Path(args.out), report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
