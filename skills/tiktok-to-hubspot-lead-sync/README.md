# TikTok to HubSpot Lead Sync

Syncs leads from TikTok Instant Forms into HubSpot CRM contacts.

## What it does

- Discovers TikTok ad accounts and filters to those with Instant Forms
- Exports leads for a user-confirmed time window
- Maps TikTok form fields to HubSpot contact properties (standard fields automatically, custom fields with user confirmation)
- Creates new contacts or updates existing ones, deduplicated by email
- Offers to assign new contacts to a HubSpot owner
- Guides users toward HubSpot's native TikTok Ads integration for ongoing automated sync

## When to use it

- Sync TikTok leads into HubSpot on demand
- Backfill historical leads from before the native integration was connected

## Setup

### TikTok
Requires the TikTok Ads MCP connected in your AI environment, authenticated with an account that has admin access to at least one ad account.

### HubSpot
Requires the HubSpot MCP connected in your AI environment, with contact write access.

Setup guide (all platforms): https://developers.hubspot.com/mcp

Claude users can also follow this simplified guide: https://knowledge.hubspot.com/integrations/set-up-and-use-the-hubspot-connector-for-claude

This skill requires the HubSpot MCP. ChatGPT's native HubSpot connector uses a different protocol and will not work with this skill.

## MCP Dependencies

| MCP Server | Tools used |
|---|---|
| TikTok Ads | `auth_advertiser_get`, `advertiser_info_get`, `page_get`, `page_field_get`, `page_lead_task_create`, `page_lead_task_download` |
| HubSpot | `get_organization_details`, `get_user_details`, `query_crm_data`, `search_properties`, `search_crm_objects`, `manage_crm_objects`, `search_owners` |

## Field Mapping

Standard TikTok Instant Form fields map automatically to HubSpot contact properties. Custom fields are discovered at runtime via `page_field_get` and mapped interactively with the user using `search_properties` to suggest the closest HubSpot property match.

See `SKILL.md` for the full standard mapping table and custom field handling logic.

## Known Limitations

- `page_lead_task_download` currently only supports leads from regions outside EEA, CH, UK, and US. This affects most HubSpot customers. TikTok has confirmed this is a known gap and expects to resolve it in Q3 2026 (possibly as early as July). Users in affected markets will see a clear message when they run the skill.
- TikTok's export API has no date range filter. All leads for a form are downloaded and filtered locally.
- Leads without an email field are skipped (email is required for HubSpot contact deduplication).
- 90 days per run is the recommended limit for practical reasons (large exports take longer to process). TikTok's API has no hard date range constraint.
