#!/usr/bin/env python3
"""TikTok MCP route definitions and utility functions.

This file defines the 145-route mapping (ToolRoute, ROUTES, UNAVAILABLE_CAPABILITIES)
and changelog/ID parsing utilities.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from utils import (
        STATUS_OK,
        STATUS_SUPPORTED_EMPTY,
        STATUS_STRUCTURED_UNAVAILABLE,
        STATUS_UNSUPPORTED,
        STATUS_DEGRADED,
        extract_rows,
        write_json,
        chunked,
    )
except ImportError:
    from .utils import (
        STATUS_OK,
        STATUS_SUPPORTED_EMPTY,
        STATUS_STRUCTURED_UNAVAILABLE,
        STATUS_UNSUPPORTED,
        STATUS_DEGRADED,
        extract_rows,
        write_json,
        chunked,
    )


SMART_PLUS_AD_BATCH_SIZE = 50
MAX_CANDIDATE_ROWS = 3000


@dataclass(frozen=True)
class ToolRoute:
    capability: str
    direct: tuple[str, ...]
    dispatcher_tool: str | None = None
    api_path: str | None = None


ROUTES: dict[str, ToolRoute] = {
    # ═══════════════════════════════════════════════════════════
    # Reports
    # ═══════════════════════════════════════════════════════════
    "integrated_report": ToolRoute(
        "integrated_report",
        ("report_integrated_get",),
        dispatcher_tool="report_integrated_get",
        api_path="/report/integrated/get/",
    ),
    "async_report_create": ToolRoute(
        "async_report_create",
        (),
        dispatcher_tool="report_task_create",
        api_path="/report/task/create/",
    ),
    "async_report_check": ToolRoute(
        "async_report_check",
        (),
        dispatcher_tool="report_task_check",
        api_path="/report/task/check/",
    ),
    "async_report_download": ToolRoute(
        "async_report_download",
        (),
        dispatcher_tool=None,
        api_path="/report/task/download/",
    ),
    # ═══════════════════════════════════════════════════════════
    # Advertiser / Account
    # ═══════════════════════════════════════════════════════════
    "advertiser_info": ToolRoute(
        "advertiser_info",
        ("advertiser_info_get",),
        dispatcher_tool="advertiser_info_get",
        api_path="/advertiser/info/",
    ),
    "advertiser_update": ToolRoute(
        "advertiser_update",
        (),
        dispatcher_tool="advertiser_update",
        api_path="/advertiser/update/",
    ),
    "advertiser_balance": ToolRoute(
        "advertiser_balance",
        (),
        dispatcher_tool="advertiser_balance_get",
        api_path="/advertiser/balance/get/",
    ),
    "advertiser_transactions": ToolRoute(
        "advertiser_transactions",
        (),
        dispatcher_tool="advertiser_transaction_get",
        api_path="/advertiser/transaction/get/",
    ),
    # ═══════════════════════════════════════════════════════════
    # Smart+ campaigns (L0 direct tools)
    # ═══════════════════════════════════════════════════════════
    "smart_plus_campaign_get": ToolRoute(
        "smart_plus_campaign_get",
        ("smart_plus_campaign_get",),
        dispatcher_tool="smart_plus_campaign_get",
        api_path="/smart_plus/campaign/get/",
    ),
    "smart_plus_campaign_create": ToolRoute(
        "smart_plus_campaign_create",
        ("smart_plus_campaign_create",),
        dispatcher_tool="smart_plus_campaign_create",
        api_path="/smart_plus/campaign/create/",
    ),
    "smart_plus_campaign_update": ToolRoute(
        "smart_plus_campaign_update",
        ("smart_plus_campaign_update",),
        dispatcher_tool="smart_plus_campaign_update",
        api_path="/smart_plus/campaign/update/",
    ),
    "smart_plus_campaign_status": ToolRoute(
        "smart_plus_campaign_status",
        ("smart_plus_campaign_status_update",),
        dispatcher_tool="smart_plus_campaign_status_update",
        api_path="/smart_plus/campaign/status/update/",
    ),
    # ═══════════════════════════════════════════════════════════
    # Smart+ ad groups (L0 direct tools)
    # ═══════════════════════════════════════════════════════════
    "smart_plus_adgroups_get": ToolRoute(
        "smart_plus_adgroups_get",
        ("smart_plus_adgroup_get",),
        dispatcher_tool="smart_plus_adgroup_get",
        api_path="/smart_plus/adgroup/get/",
    ),
    "smart_plus_adgroup_create": ToolRoute(
        "smart_plus_adgroup_create",
        ("smart_plus_adgroup_create",),
        dispatcher_tool="smart_plus_adgroup_create",
        api_path="/smart_plus/adgroup/create/",
    ),
    "smart_plus_adgroup_update": ToolRoute(
        "smart_plus_adgroup_update",
        ("smart_plus_adgroup_update",),
        dispatcher_tool="smart_plus_adgroup_update",
        api_path="/smart_plus/adgroup/update/",
    ),
    "smart_plus_adgroup_budget": ToolRoute(
        "smart_plus_adgroup_budget",
        ("smart_plus_adgroup_budget_update",),
        dispatcher_tool="smart_plus_adgroup_budget_update",
        api_path="/smart_plus/adgroup/budget/update/",
    ),
    "smart_plus_adgroup_status": ToolRoute(
        "smart_plus_adgroup_status",
        ("smart_plus_adgroup_status_update",),
        dispatcher_tool="smart_plus_adgroup_status_update",
        api_path="/smart_plus/adgroup/status/update/",
    ),
    # ═══════════════════════════════════════════════════════════
    # Smart+ ads (L0 direct tools)
    # ═══════════════════════════════════════════════════════════
    "smart_plus_ads_get": ToolRoute(
        "smart_plus_ads_get",
        ("smart_plus_ad_get",),
        dispatcher_tool="smart_plus_ad_get",
        api_path="/smart_plus/ad/get/",
    ),
    "smart_plus_ad_create": ToolRoute(
        "smart_plus_ad_create",
        ("smart_plus_ad_create",),
        dispatcher_tool="smart_plus_ad_create",
        api_path="/smart_plus/ad/create/",
    ),
    "smart_plus_ad_update": ToolRoute(
        "smart_plus_ad_update",
        ("smart_plus_ad_update",),
        dispatcher_tool="smart_plus_ad_update",
        api_path="/smart_plus/ad/update/",
    ),
    "smart_plus_ad_status": ToolRoute(
        "smart_plus_ad_status",
        ("smart_plus_ad_status_update",),
        dispatcher_tool="smart_plus_ad_status_update",
        api_path="/smart_plus/ad/status/update/",
    ),
    "smart_plus_ad_preview": ToolRoute(
        "smart_plus_ad_preview",
        (),
        dispatcher_tool="smart_plus_ad_preview",
        api_path="/smart_plus/ad/preview/",
    ),
    "smart_plus_ad_review": ToolRoute(
        "smart_plus_ad_review",
        ("smart_plus_ad_review_info_get",),
        dispatcher_tool="smart_plus_ad_review_info_get",
        api_path="/smart_plus/ad/review_info/",
    ),
    "smart_plus_creative_review": ToolRoute(
        "smart_plus_creative_review",
        (),
        dispatcher_tool="smart_plus_material_review_info_get",
        api_path="/smart_plus/material/review_info/",
    ),
    "smart_plus_ad_appeal": ToolRoute(
        "smart_plus_ad_appeal",
        (),
        dispatcher_tool="smart_plus_ad_appeal",
        api_path="/smart_plus/ad/appeal/",
    ),
    "smart_plus_creative_status": ToolRoute(
        "smart_plus_creative_status",
        (),
        dispatcher_tool="smart_plus_ad_material_status_update",
        api_path="/smart_plus/ad/material_status/update/",
    ),
    "smart_material_overview": ToolRoute(
        "smart_material_overview",
        (),
        dispatcher_tool="smart_plus_material_report_overview_run",
        api_path="/smart_plus/material_report/overview/",
    ),
    "smart_material_breakdown": ToolRoute(
        "smart_material_breakdown",
        (),
        dispatcher_tool="smart_plus_material_report_breakdown_run",
        api_path="/smart_plus/material_report/breakdown/",
    ),
    # ═══════════════════════════════════════════════════════════
    # Regular campaigns (L1 dispatcher — campaign group)
    # ═══════════════════════════════════════════════════════════
    "campaigns_get": ToolRoute(
        "campaigns_get",
        (),
        dispatcher_tool="campaign_get",
        api_path="/campaign/get/",
    ),
    "campaign_create": ToolRoute(
        "campaign_create",
        (),
        dispatcher_tool="campaign_create",
        api_path="/campaign/create/",
    ),
    "campaign_update": ToolRoute(
        "campaign_update",
        (),
        dispatcher_tool="campaign_update",
        api_path="/campaign/update/",
    ),
    "campaign_status": ToolRoute(
        "campaign_status",
        (),
        dispatcher_tool="campaign_status_update",
        api_path="/campaign/status/update/",
    ),
    "campaign_copy": ToolRoute(
        "campaign_copy",
        (),
        dispatcher_tool="campaign_copy_task_create",
        api_path="/campaign/copy/task/create/",
    ),
    "campaign_copy_check": ToolRoute(
        "campaign_copy_check",
        (),
        dispatcher_tool="campaign_copy_task_check",
        api_path="/campaign/copy/task/check/",
    ),
    # ═══════════════════════════════════════════════════════════
    # Regular ad groups (L1 dispatcher — adgroup group)
    # ═══════════════════════════════════════════════════════════
    "adgroups_get": ToolRoute(
        "adgroups_get",
        (),
        dispatcher_tool="adgroup_get",
        api_path="/adgroup/get/",
    ),
    "adgroup_update": ToolRoute(
        "adgroup_update",
        (),
        dispatcher_tool="adgroup_update",
        api_path="/adgroup/update/",
    ),
    "adgroup_budget": ToolRoute(
        "adgroup_budget",
        (),
        dispatcher_tool="adgroup_budget_update",
        api_path="/adgroup/budget/update/",
    ),
    "adgroup_status": ToolRoute(
        "adgroup_status",
        (),
        dispatcher_tool="adgroup_status_update",
        api_path="/adgroup/status/update/",
    ),
    "review_adgroups": ToolRoute(
        "review_adgroups",
        (),
        dispatcher_tool="adgroup_review_info_get",
        api_path="/adgroup/review_info/",
    ),
    "appeal_adgroup": ToolRoute(
        "appeal_adgroup",
        (),
        dispatcher_tool="adgroup_appeal",
        api_path="/adgroup/appeal/",
    ),
    "adgroup_quota": ToolRoute(
        "adgroup_quota",
        (),
        dispatcher_tool="adgroup_quota_get",
        api_path="/adgroup/quota/",
    ),
    # ═══════════════════════════════════════════════════════════
    # Regular ads (L1 dispatcher — ad group)
    # ═══════════════════════════════════════════════════════════
    "ads_get": ToolRoute(
        "ads_get",
        (),
        dispatcher_tool="ad_get",
        api_path="/ad/get/",
    ),
    "ad_create": ToolRoute(
        "ad_create",
        (),
        dispatcher_tool="ad_create",
        api_path="/ad/create/",
    ),
    "ad_update": ToolRoute(
        "ad_update",
        (),
        dispatcher_tool="ad_update",
        api_path="/ad/update/",
    ),
    "ad_status": ToolRoute(
        "ad_status",
        (),
        dispatcher_tool="ad_status_update",
        api_path="/ad/status/update/",
    ),
    "review_ads": ToolRoute(
        "review_ads",
        (),
        dispatcher_tool="ad_review_info_get",
        api_path="/ad/review_info/",
    ),
    "smart_creative_materials_get": ToolRoute(
        "smart_creative_materials_get",
        (),
        dispatcher_tool=None,
        api_path="/ad/aco/get/",
    ),
    "smart_creative_materials_update": ToolRoute(
        "smart_creative_materials_update",
        (),
        dispatcher_tool=None,
        api_path="/ad/aco/update/",
    ),
    "smart_creative_materials_status": ToolRoute(
        "smart_creative_materials_status",
        (),
        dispatcher_tool=None,
        api_path="/ad/aco/material_status/update/",
    ),
    "audience_estimate": ToolRoute(
        "audience_estimate",
        (),
        dispatcher_tool="ad_audience_size_estimate",
        api_path="/ad/audience_size/estimate/",
    ),
    # ═══════════════════════════════════════════════════════════
    # File / media (L1 dispatcher — file group)
    # ═══════════════════════════════════════════════════════════
    "image_upload": ToolRoute(
        "image_upload",
        (),
        dispatcher_tool=None,
        api_path="/file/image/ad/upload/",
    ),
    "video_upload": ToolRoute(
        "video_upload",
        (),
        dispatcher_tool=None,
        api_path="/file/video/ad/upload/",
    ),
    "image_info": ToolRoute(
        "image_info",
        ("file_image_ad_info_get",),
        dispatcher_tool="file_image_ad_info_get",
        api_path="/file/image/ad/info/",
    ),
    "video_info": ToolRoute(
        "video_info",
        ("file_video_ad_info_get",),
        dispatcher_tool="file_video_ad_info_get",
        api_path="/file/video/ad/info/",
    ),
    "video_search": ToolRoute(
        "video_search",
        ("file_video_ad_search",),
        dispatcher_tool="file_video_ad_search",
        api_path="/file/video/ad/search/",
    ),
    "video_update": ToolRoute(
        "video_update",
        (),
        dispatcher_tool="file_video_ad_update",
        api_path="/file/video/ad/update/",
    ),
    "image_update": ToolRoute(
        "image_update",
        (),
        dispatcher_tool="file_image_ad_update",
        api_path="/file/image/ad/update/",
    ),
    "image_search": ToolRoute(
        "image_search",
        ("file_image_ad_search",),
        dispatcher_tool="file_image_ad_search",
        api_path="/file/image/ad/search/",
    ),
    "music_upload": ToolRoute(
        "music_upload",
        (),
        dispatcher_tool=None,
        api_path="/file/music/upload/",
    ),
    "video_thumbnails": ToolRoute(
        "video_thumbnails",
        (),
        dispatcher_tool="file_video_suggestcover_get",
        api_path="/file/video/suggestcover/",
    ),
    "file_name_check": ToolRoute(
        "file_name_check",
        (),
        dispatcher_tool="file_name_check",
        api_path="/file/name/check/",
    ),
    "video_packages": ToolRoute(
        "video_packages",
        ("catalog_video_package_get",),
        dispatcher_tool="catalog_video_package_get",
        api_path="/catalog/video_package/get/",
    ),
    # ═══════════════════════════════════════════════════════════
    # Creative (L1 dispatcher — creative group)
    # ═══════════════════════════════════════════════════════════
    "portfolio_create": ToolRoute(
        "portfolio_create",
        (),
        dispatcher_tool="creative_portfolio_create",
        api_path="/creative/portfolio/create/",
    ),
    "portfolio_get": ToolRoute(
        "portfolio_get",
        (),
        dispatcher_tool="creative_portfolio_get",
        api_path="/creative/portfolio/get/",
    ),
    "portfolio_list": ToolRoute(
        "portfolio_list",
        ("creative_portfolio_list_get",),
        dispatcher_tool="creative_portfolio_list_get",
        api_path="/creative/portfolio/list/",
    ),
    "portfolio_delete": ToolRoute(
        "portfolio_delete",
        (),
        dispatcher_tool="creative_portfolio_delete",
        api_path="/creative/portfolio/delete/",
    ),
    "asset_delete": ToolRoute(
        "asset_delete",
        (),
        dispatcher_tool="creative_asset_delete",
        api_path="/creative/asset/delete/",
    ),
    "asset_share": ToolRoute(
        "asset_share",
        (),
        dispatcher_tool="creative_asset_share_get",
        api_path="/creative/asset/share/",
    ),
    "smart_text": ToolRoute(
        "smart_text",
        (),
        dispatcher_tool="creative_smart_text_get",
        api_path="/creative/smart_text/generate/",
    ),
    "cta_recommend": ToolRoute(
        "cta_recommend",
        (),
        dispatcher_tool="creative_cta_recommend_get",
        api_path="/creative/cta/recommend/",
    ),
    "creative_preview": ToolRoute(
        "creative_preview",
        (),
        dispatcher_tool="creative_ads_preview_create",
        api_path="/creative/ads_preview/create/",
    ),
    "creative_report": ToolRoute(
        "creative_report",
        (),
        dispatcher_tool="creative_report_get",
        api_path="/creative/report/get/",
    ),
    "creative_image_edit": ToolRoute(
        "creative_image_edit",
        (),
        dispatcher_tool="creative_image_edit_get",
        api_path="/creative/image/edit/",
    ),
    # ═══════════════════════════════════════════════════════════
    # Changelog (L1 dispatcher — changelog group)
    # ═══════════════════════════════════════════════════════════
    "change_log_create": ToolRoute(
        "change_log_create",
        (),
        dispatcher_tool="changelog_task_create",
        api_path="/changelog/task/create/",
    ),
    "change_log_check": ToolRoute(
        "change_log_check",
        (),
        dispatcher_tool="changelog_task_check",
        api_path="/changelog/task/check/",
    ),
    "change_log_download": ToolRoute(
        "change_log_download",
        (),
        dispatcher_tool="changelog_task_download",
        api_path="/changelog/task/download/",
    ),
    "bc_activity_log": ToolRoute(
        "bc_activity_log",
        (),
        dispatcher_tool="changelog_get",
        api_path="/changelog/get/",
    ),
    # ═══════════════════════════════════════════════════════════
    # Identity (L0 + L1 dispatcher)
    # ═══════════════════════════════════════════════════════════
    "identity_list": ToolRoute(
        "identity_list",
        ("identity_get",),
        dispatcher_tool="identity_get",
        api_path="/identity/get/",
    ),
    "identity_create": ToolRoute(
        "identity_create",
        (),
        dispatcher_tool=None,
        api_path="/identity/create/",
    ),
    "identity_delete": ToolRoute(
        "identity_delete",
        (),
        dispatcher_tool=None,
        api_path="/identity/delete/",
    ),
    "identity_info": ToolRoute(
        "identity_info",
        (),
        dispatcher_tool="identity_info_get",
        api_path="/identity/info/",
    ),
    "identity_posts": ToolRoute(
        "identity_posts",
        ("identity_video_get",),
        dispatcher_tool="identity_video_get",
        api_path="/identity/video/get/",
    ),
    "identity_post_info": ToolRoute(
        "identity_post_info",
        ("identity_video_info_get",),
        dispatcher_tool="identity_video_info_get",
        api_path="/identity/video/info/",
    ),
    "identity_live": ToolRoute(
        "identity_live",
        (),
        dispatcher_tool="identity_live_get",
        api_path="/identity/live/get/",
    ),
    "identity_music_auth": ToolRoute(
        "identity_music_auth",
        (),
        dispatcher_tool="identity_music_authorization_get",
        api_path="/identity/music/auth/",
    ),
    # ═══════════════════════════════════════════════════════════
    # Spark Ads / tt_video (L1 dispatcher)
    # ═══════════════════════════════════════════════════════════
    "spark_posts": ToolRoute(
        "spark_posts",
        ("tt_video_list_get",),
        dispatcher_tool="tt_video_list_get",
        api_path="/tt_video/list/",
    ),
    "spark_post_info": ToolRoute(
        "spark_post_info",
        ("tt_video_info_get",),
        dispatcher_tool="tt_video_info_get",
        api_path="/tt_video/info/",
    ),
    "spark_authorize": ToolRoute(
        "spark_authorize",
        (),
        dispatcher_tool="tt_video_authorize_apply",
        api_path="/tt_video/authorize/",
    ),
    "spark_unbind": ToolRoute(
        "spark_unbind",
        (),
        dispatcher_tool="tt_video_unbind",
        api_path="/tt_video/unbind/",
    ),
    # ═══════════════════════════════════════════════════════════
    # App / pixel / catalog / feeds
    # ═══════════════════════════════════════════════════════════
    "app_list": ToolRoute(
        "app_list",
        ("app_list_get",),
        dispatcher_tool="app_list_get",
        api_path="/app/list/",
    ),
    "app_info": ToolRoute(
        "app_info",
        ("app_info_get",),
        dispatcher_tool="app_info_get",
        api_path="/app/info/",
    ),
    "app_conversion_events": ToolRoute(
        "app_conversion_events",
        ("app_optimization_event_get",),
        dispatcher_tool="app_optimization_event_get",
        api_path="/app/optimization_event/",
    ),
    "pixel_list": ToolRoute(
        "pixel_list",
        ("pixel_list_get",),
        dispatcher_tool="pixel_list_get",
        api_path="/pixel/list/",
    ),
    "pixel_create": ToolRoute(
        "pixel_create",
        (),
        dispatcher_tool="pixel_create",
        api_path="/pixel/create/",
    ),
    "pixel_update": ToolRoute(
        "pixel_update",
        (),
        dispatcher_tool="pixel_update",
        api_path="/pixel/update/",
    ),
    "pixel_events": ToolRoute(
        "pixel_events",
        (),
        dispatcher_tool="pixel_event_stats_get",
        api_path="/pixel/event/stats/",
    ),
    "catalog_list": ToolRoute(
        "catalog_list",
        ("catalog_get",),
        dispatcher_tool="catalog_get",
        api_path="/catalog/get/",
    ),
    "catalog_create": ToolRoute(
        "catalog_create",
        (),
        dispatcher_tool="catalog_create",
        api_path="/catalog/create/",
    ),
    "catalog_overview": ToolRoute(
        "catalog_overview",
        ("catalog_overview_get",),
        dispatcher_tool="catalog_overview_get",
        api_path="/catalog/overview/",
    ),
    "catalog_event_bindings": ToolRoute(
        "catalog_event_bindings",
        (),
        dispatcher_tool="catalog_eventsource_bind_get",
        api_path="/catalog/eventsource_bind/get/",
    ),
    "product_sets": ToolRoute(
        "product_sets",
        ("catalog_set_get",),
        dispatcher_tool="catalog_set_get",
        api_path="/catalog/set/get/",
    ),
    "products": ToolRoute(
        "products",
        ("catalog_product_get",),
        dispatcher_tool="catalog_product_get",
        api_path="/catalog/product/get/",
    ),
    "products_in_set": ToolRoute(
        "products_in_set",
        (),
        dispatcher_tool="catalog_set_product_get",
        api_path="/catalog/set/product/get/",
    ),
    "feeds": ToolRoute(
        "feeds",
        ("catalog_feed_get",),
        dispatcher_tool="catalog_feed_get",
        api_path="/catalog/feed/get/",
    ),
    "catalog_videos": ToolRoute(
        "catalog_videos",
        (),
        dispatcher_tool="catalog_video_get",
        api_path="/catalog/video/get/",
    ),
    "catalog_trending_products": ToolRoute(
        "catalog_trending_products",
        (),
        dispatcher_tool="catalog_insight_product_get",
        api_path="/catalog/trending/product/",
    ),
    "catalog_trending_categories": ToolRoute(
        "catalog_trending_categories",
        (),
        dispatcher_tool="catalog_insight_category_get",
        api_path="/catalog/trending/category/",
    ),
    # ═══════════════════════════════════════════════════════════
    # Audience / targeting (L1 dispatcher — audience group)
    # ═══════════════════════════════════════════════════════════
    "audiences": ToolRoute(
        "audiences",
        ("dmp_custom_audience_list_get",),
        dispatcher_tool="dmp_custom_audience_list_get",
        api_path="/audience/list/",
    ),
    "audience_details": ToolRoute(
        "audience_details",
        (),
        dispatcher_tool="dmp_custom_audience_get",
        api_path="/audience/get/",
    ),
    "saved_audiences": ToolRoute(
        "saved_audiences",
        ("dmp_saved_audience_list_get",),
        dispatcher_tool="dmp_saved_audience_list_get",
        api_path="/audience/saved/get/",
    ),
    "targeting_locations": ToolRoute(
        "targeting_locations",
        (),
        dispatcher_tool="search_region_get",
        api_path="/search/region/",
    ),
    "targeting_search": ToolRoute(
        "targeting_search",
        (),
        dispatcher_tool="tool_targeting_search",
        api_path="/tool/targeting/search/",
    ),
    "targeting_info": ToolRoute(
        "targeting_info",
        (),
        dispatcher_tool="tool_targeting_info_get",
        api_path="/tool/targeting/info/",
    ),
    "targeting_carriers": ToolRoute(
        "targeting_carriers",
        (),
        dispatcher_tool="tool_carrier_get",
        api_path="/tool/carrier/get/",
    ),
    "targeting_isps": ToolRoute(
        "targeting_isps",
        (),
        dispatcher_tool="tool_targeting_list_get",
        api_path="/tool/isp/get/",
    ),
    "targeting_device_models": ToolRoute(
        "targeting_device_models",
        (),
        dispatcher_tool="tool_device_model_get",
        api_path="/tool/device_model/get/",
    ),
    "targeting_interest_categories": ToolRoute(
        "targeting_interest_categories",
        (),
        dispatcher_tool="tool_interest_category_get",
        api_path="/tool/interest_category/get/",
    ),
    "targeting_action_categories": ToolRoute(
        "targeting_action_categories",
        (),
        dispatcher_tool="tool_action_category_get",
        api_path="/tool/action_category/get/",
    ),
    "targeting_hashtags": ToolRoute(
        "targeting_hashtags",
        (),
        dispatcher_tool="tool_hashtag_recommend_search",
        api_path="/tool/hashtag/search/",
    ),
    "targeting_interest_recommend": ToolRoute(
        "targeting_interest_recommend",
        (),
        dispatcher_tool="tool_targeting_category_recommend_get",
        api_path="/tool/interest_recommend/get/",
    ),
    "bid_recommend": ToolRoute(
        "bid_recommend",
        (),
        dispatcher_tool="tool_bid_recommend",
        api_path="/tool/bid/recommend/",
    ),
    "brand_safety": ToolRoute(
        "brand_safety",
        (),
        dispatcher_tool="tiktok_inventory_filters_get",
        api_path="/brand_safety/get/",
    ),
    "conversion_events": ToolRoute(
        "conversion_events",
        ("app_optimization_event_get",),
        dispatcher_tool="app_optimization_event_get",
        api_path="/app/optimization_event/",
    ),
    "custom_conversions": ToolRoute(
        "custom_conversions",
        ("custom_conversion_list_get",),
        dispatcher_tool="custom_conversion_list_get",
        api_path="/custom_conversion/list/",
    ),
    # ═══════════════════════════════════════════════════════════
    # Store / TikTok Shop (L1 dispatcher — store group)
    # ═══════════════════════════════════════════════════════════
    "shop_list": ToolRoute(
        "shop_list",
        (),
        dispatcher_tool="store_list_get",
        api_path="/store/list/",
    ),
    "shop_products": ToolRoute(
        "shop_products",
        (),
        dispatcher_tool="store_product_get",
        api_path="/store/product/get/",
    ),
    # ═══════════════════════════════════════════════════════════
    # GMV Max (L1 dispatcher — gmv_max group)
    # ═══════════════════════════════════════════════════════════
    "gmv_max_campaigns_get": ToolRoute(
        "gmv_max_campaigns_get",
        (),
        dispatcher_tool="gmv_max_campaign_get",
        api_path="/gmv_max/campaign/get/",
    ),
    "gmv_max_campaign_detail": ToolRoute(
        "gmv_max_campaign_detail",
        (),
        dispatcher_tool="campaign_gmv_max_info_get",
        api_path="/campaign/gmv_max/info/",
    ),
    "gmv_max_campaign_create": ToolRoute(
        "gmv_max_campaign_create",
        (),
        dispatcher_tool="campaign_gmv_max_create",
        api_path="/gmv_max/campaign/create/",
    ),
    "gmv_max_campaign_update": ToolRoute(
        "gmv_max_campaign_update",
        (),
        dispatcher_tool="campaign_gmv_max_update",
        api_path="/gmv_max/campaign/update/",
    ),
    "gmv_max_report": ToolRoute(
        "gmv_max_report",
        (),
        dispatcher_tool="gmv_max_report_get",
        api_path="/report/gmv_max/get/",
    ),
    "gmv_max_stores": ToolRoute(
        "gmv_max_stores",
        (),
        dispatcher_tool="gmv_max_store_list_get",
        api_path="/gmv_max/store/list/",
    ),
    "gmv_max_identities": ToolRoute(
        "gmv_max_identities",
        (),
        dispatcher_tool="gmv_max_identity_get",
        api_path="/gmv_max/identity/get/",
    ),
    "gmv_max_bid_recommend": ToolRoute(
        "gmv_max_bid_recommend",
        (),
        dispatcher_tool="gmv_max_bid_recommend_get",
        api_path="/gmv_max/bid/recommend/",
    ),
    "gmv_max_sessions": ToolRoute(
        "gmv_max_sessions",
        (),
        dispatcher_tool="campaign_gmv_max_session_list_get",
        api_path="/gmv_max/session/list/",
    ),
    "gmv_max_posts": ToolRoute(
        "gmv_max_posts",
        (),
        dispatcher_tool="gmv_max_video_get",
        api_path="/gmv_max/video/get/",
    ),
    # ═══════════════════════════════════════════════════════════
    # Diagnostic (L1 dispatcher — diagnostic group)
    # ═══════════════════════════════════════════════════════════
    "delivery_diagnostic": ToolRoute(
        "delivery_diagnostic",
        (),
        dispatcher_tool="tool_diagnosis_get",
        api_path="/tool/diagnosis/get/",
    ),
    # ═══════════════════════════════════════════════════════════
    # Creative fatigue (L1 dispatcher)
    # ═══════════════════════════════════════════════════════════
    "creative_fatigue_detect": ToolRoute(
        "creative_fatigue_detect",
        (),
        dispatcher_tool="creative_fatigue_get",
        api_path="/creative_fatigue/get/",
    ),
    # ═══════════════════════════════════════════════════════════
    # Page / lead gen / music
    # ═══════════════════════════════════════════════════════════
    "page_id": ToolRoute(
        "page_id",
        ("page_get",),
        dispatcher_tool="page_get",
        api_path="/page/get/",
    ),
    "music_list": ToolRoute(
        "music_list",
        ("file_music_get",),
        dispatcher_tool="file_music_get",
        api_path="/file/music/get/",
    ),
    # ═══════════════════════════════════════════════════════════
    # Offline events
    # ═══════════════════════════════════════════════════════════
    "offline_event_sets": ToolRoute(
        "offline_event_sets",
        (),
        dispatcher_tool="offline_get",
        api_path="/offline/get/",
    ),
    # ═══════════════════════════════════════════════════════════
    # BC (Business Center)
    # ═══════════════════════════════════════════════════════════
    "bc_list": ToolRoute(
        "bc_list",
        (),
        dispatcher_tool="bc_get",
        api_path="/bc/get/",
    ),
    "bc_assets": ToolRoute(
        "bc_assets",
        (),
        dispatcher_tool="bc_asset_get",
        api_path="/bc/asset/get/",
    ),
    # ═══════════════════════════════════════════════════════════
    # Report benchmarks / video performance
    # ═══════════════════════════════════════════════════════════
    "ad_benchmarks": ToolRoute(
        "ad_benchmarks",
        (),
        dispatcher_tool="report_ad_benchmark_get",
        api_path="/report/ad_benchmark/get/",
    ),
    "video_performance": ToolRoute(
        "video_performance",
        (),
        dispatcher_tool="report_video_performance_get",
        api_path="/report/video_performance/get/",
    ),
}

# ── Verified-absent capabilities ───────────────────────────────
# The official v1 -> v2 mapping sheet has no new_name for these routes, so the
# v2 layered MCP cannot be called with a replacement tool name yet.
UNAVAILABLE_CAPABILITIES: frozenset[str] = frozenset({
    "async_report_download",
    "smart_creative_materials_get",
    "smart_creative_materials_update",
    "smart_creative_materials_status",
    "image_upload",
    "video_upload",
    "music_upload",
    "identity_create",
    "identity_delete",
})


def _request_id() -> str:
    """Generate a unique integer-ish request_id for TikTok MCP API calls."""
    import time as _time
    return str(int(_time.time() * 1000000) + hash(_time.time()) % 1000)


def _unique(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


def _row_id(row: dict[str, Any], key: str) -> str:
    if key in row:
        return str(row.get(key) or "")
    dimensions = row.get("dimensions")
    if isinstance(dimensions, dict) and key in dimensions:
        return str(dimensions.get(key) or "")
    metrics = row.get("metrics")
    if isinstance(metrics, dict) and key in metrics:
        return str(metrics.get(key) or "")
    return ""


def _find_value(payload: Any, key: str) -> str:
    if isinstance(payload, dict):
        if key in payload and payload.get(key) is not None:
            return str(payload.get(key) or "")
        for value in payload.values():
            found = _find_value(value, key)
            if found:
                return found
    elif isinstance(payload, list):
        for item in payload:
            found = _find_value(item, key)
            if found:
                return found
    return ""


def _as_changelog_time(value: str | None, *, end_of_day: bool = False) -> str | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        return f"{text} {'23:59:59' if end_of_day else '00:00:00'}"
    return text


def _decode_changelog_file_data(file_data: Any) -> str:
    if isinstance(file_data, bytes):
        return file_data.decode("utf-8-sig", errors="replace")
    text = str(file_data or "")
    text = text.replace("\\'", "'").replace('\\"', '"')
    if (text.startswith("b'") and text.endswith("'")) or (text.startswith('b"') and text.endswith('"')):
        text = text[2:-1]
    for _ in range(2):
        if ("\\r\\n" in text and "\r\n" not in text) or ("\\n" in text and "\n" not in text):
            text = text.encode("utf-8").decode("unicode_escape")
    return text


def _extract_changelog_rows(changelog: Any) -> list[dict[str, Any]]:
    if not changelog:
        return []
    payload: Any = changelog
    if isinstance(changelog, str):
        try:
            payload = json.loads(changelog)
        except json.JSONDecodeError:
            file_match = re.search(r'"file_data"\s*:\s*"(.*?)(?<!\\)"', changelog, flags=re.DOTALL)
            name_match = re.search(r'"file_name"\s*:\s*"(.*?)(?<!\\)"', changelog, flags=re.DOTALL)
            payload = {
                "file_data": file_match.group(1) if file_match else changelog,
                "file_name": name_match.group(1) if name_match else None,
            }
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []

    file_data = payload.get("file_data") or payload.get("csv") or payload.get("content")
    if not file_data:
        return []
    text = _decode_changelog_file_data(file_data)
    lines = text.splitlines()
    header_index: int | None = None
    for index, line in enumerate(lines):
        if line.startswith("Time,") or ("Activity details" in line and "Object ID" in line):
            header_index = index
            break
    if header_index is None:
        return []

    csv_text = "\n".join(lines[header_index:])
    rows: list[dict[str, Any]] = []
    for row in csv.DictReader(io.StringIO(csv_text)):
        if not any(value not in (None, "") for value in row.values()):
            continue
        clean_row = {str(key or "").strip(): value for key, value in row.items() if key}
        file_name = payload.get("file_name")
        if file_name:
            clean_row["_file_name"] = file_name
        rows.append(clean_row)
    return rows


def _extract_changelog_file_data(payload: Any) -> Any:
    if not isinstance(payload, dict):
        return None
    data = payload.get("data")
    candidates: list[Any] = []
    if isinstance(data, dict):
        candidates.extend([data.get("changelog"), data.get("file_data"), data.get("csv"), data.get("content")])
    candidates.extend([payload.get("changelog"), payload.get("file_data"), payload.get("csv"), payload.get("content")])
    for candidate in candidates:
        if candidate:
            return candidate
    return None


def _extract_changelog_payload_rows(payload: Any) -> list[dict[str, Any]]:
    rows = extract_rows(payload)
    if rows:
        return rows
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, dict):
            for key in ("list", "logs", "operation_logs", "activities", "items"):
                value = data.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]
            rows = _extract_changelog_rows(data.get("changelog"))
            if rows:
                return rows
        rows = _extract_changelog_rows(_extract_changelog_file_data(payload))
        if rows:
            return rows
    return []


def _extract_task_status(payload: Any) -> str:
    for key in ("status", "task_status"):
        value = _find_value(payload, key)
        if value:
            return value
    return ""


def _task_completed(status: str | None) -> bool:
    return str(status or "").strip().upper() in {"SUCCESS", "SUCCEED", "SUCCEEDED", "COMPLETED", "COMPLETE", "FINISHED", "DONE"}


def _task_failed(status: str | None) -> bool:
    return str(status or "").strip().upper() in {"FAIL", "FAILED", "ERROR", "EXPIRED", "CANCELED", "CANCELLED"}



def select_top_ids(rows: list[dict[str, Any]], key: str, *, limit: int) -> list[str]:
    def spend(row: dict[str, Any]) -> float:
        metrics = row.get("metrics") if isinstance(row.get("metrics"), dict) else row
        try:
            return float(str(metrics.get("spend") or 0).replace(",", ""))
        except Exception:
            return 0.0

    sorted_rows = sorted(rows, key=spend, reverse=True)
    return _unique([_row_id(row, key) for row in sorted_rows[:limit]])


def smart_plus_ids_from_ad_v2_rows(rows: list[dict[str, Any]]) -> list[str]:
    ids: list[str] = []
    for row in rows:
        automation = (_row_id(row, "campaign_automation_type") or str(row.get("campaign_automation_type") or "")).upper()
        ad_id_v2 = _row_id(row, "ad_id_v2")
        smart_plus_ad_id = _row_id(row, "smart_plus_ad_id") or ad_id_v2
        if smart_plus_ad_id and "UPGRADED_SMART_PLUS" in automation:
            ids.append(smart_plus_ad_id)
    return _unique(ids)


def main() -> int:
    parser = argparse.ArgumentParser(description="Creatiads TikTok MCP adapter — utility reference (compute-only)")
    parser.add_argument("command", choices=["select-top-ids", "smart-plus-ids", "parse-changelog"])
    parser.add_argument("--input", help="JSON file with input data")
    parser.add_argument("--key", default="ad_id", help="Key for select-top-ids")
    parser.add_argument("--limit", type=int, default=30, help="Limit for select-top-ids")
    parser.add_argument("--out")
    args = parser.parse_args()

    payload: Any = {}
    if args.command == "select-top-ids":
        data = json.loads(Path(args.input).read_text(encoding="utf-8")) if args.input else []
        rows = data if isinstance(data, list) else data.get("rows", [])
        payload = {"top_ids": select_top_ids(rows, args.key, limit=args.limit)}
    elif args.command == "smart-plus-ids":
        data = json.loads(Path(args.input).read_text(encoding="utf-8")) if args.input else []
        rows = data if isinstance(data, list) else data.get("rows", [])
        payload = {"smart_plus_ids": smart_plus_ids_from_ad_v2_rows(rows)}
    elif args.command == "parse-changelog":
        data = json.loads(Path(args.input).read_text(encoding="utf-8")) if args.input else {}
        rows = _extract_changelog_rows(data.get("file_data") or data)
        payload = {"rows": rows, "count": len(rows)}

    if args.out:
        write_json(Path(args.out), payload)
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
