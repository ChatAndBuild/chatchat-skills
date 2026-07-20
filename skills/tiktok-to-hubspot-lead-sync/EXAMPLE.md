# Example: Syncing TikTok Leads to HubSpot

This walkthrough shows a complete sync for a marketing manager who wants to check whether any TikTok leads have come in and get them into HubSpot.

---

**User:** Have I received any leads in my TikTok ads account?

**Agent:** Let me check what's connected and find your TikTok accounts.

> Checks TikTok Ads MCP (`auth_advertiser_get`) ✓  
> Checks HubSpot MCP (`get_organization_details`) ✓  
> Confirms contact write access (`get_user_details`) ✓

Both MCPs are connected and you have contact write access. I found 1 TikTok ad account with a lead gen form set up: **Acme Corp – US**. It has one form, "Spring Promo."

Exporting leads to check what's there...

> Creates export task (`page_lead_task_create`)  
> Polls until `status = SUCCEED`  
> Downloads export (`page_lead_task_download`)

Found 1 lead:

| Field | Value |
|---|---|
| Email | jane.smith@example.com |
| Name | Jane Smith |
| Custom field: "What's your budget range?" | $10k–$50k |
| Submitted | April 27, 2026 |

Your form has a standard email and name field, plus one custom question: "What's your budget range?" There's no matching HubSpot property for that custom field, so it would be skipped unless you create one first. Would you like to sync this lead to HubSpot?

---

**User:** Before we sync, can you check if this lead has already been synced?

**Agent:** Checking HubSpot for a contact with email jane.smith@example.com...

> Searches by email (`search_crm_objects`) — no match found

No contact with that email exists in HubSpot yet. This lead has not been synced. Want me to go ahead and create the contact?

---

**User:** Yes, let's do that.

**Agent:** Creating contact in HubSpot...

> Creates contact (`manage_crm_objects` with `createRequest`):
> - `email`: jane.smith@example.com
> - `firstname`: Jane
> - `lastname`: Smith
> - `hs_analytics_source`: PAID_SOCIAL
> - Custom field skipped (no matching HubSpot property)

---

```
TikTok to HubSpot Lead Sync Complete

Account:      Acme Corp – US
Time window:  April 27, 2026 to April 27, 2026
Forms synced: 1

Results:
  1 contact created
  0 contacts updated
  0 leads skipped (no email field)

Note: 1 custom field ("What's your budget range?") was skipped because no
matching HubSpot property exists. To capture it in future syncs, create a
custom contact property in HubSpot Settings > Properties, then run this
skill again.

Set up automatic sync in HubSpot
Running this skill manually works, but HubSpot's native TikTok Ads
integration syncs leads automatically going forward with no manual effort.

  1. Go to Settings > Marketing > Ads
  2. Click the Lead syncing tab
  3. Click Connect and select TikTok
  4. Check the box next to your ad account

Full setup guide: https://knowledge.hubspot.com/ads/sync-leads-from-your-facebook-page-or-linkedin-ads-account-to-hubspot
```
