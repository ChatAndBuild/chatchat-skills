---
id: analytics-events
name: Analytics Events
description: Use this skill when keeping analytics instrumentation accurate, consistent, and release-ready across event definitions, tracking plans, schemas, implementation, QA, and governance.
category: DevOps
---

# Analytics Events

Use this skill to keep analytics instrumentation accurate, consistent, and release-ready.

## When to Use

- A feature needs new or updated product analytics tracking.
- Event naming/properties have drifted and require normalization.
- You need pre-release verification for event quality.

## Workflow

1. Define analytics goals and map them to concrete user/system events.
2. Standardize schema: event names, required properties, types, and ownership.
3. Implement instrumentation at reliable trigger points with minimal duplication.
4. Validate payloads locally/staging against schema and expected cardinality.
5. Add monitoring for event volume anomalies and ingestion failures.
6. Document taxonomy updates and communicate downstream reporting impacts.

## Event Taxonomy Patterns

Use **object_action** naming: `button_clicked`, `page_viewed`, `form_submitted`, `item_added_to_cart`. Object is the UI element or entity; action is the verb. Avoid generic names like `click` or `event_1`. Examples: `checkout_started`, `payment_method_selected`, `subscription_cancelled`.

## Schema Governance

**JSON Schema validation:** Define a schema per event type with required properties, types, and enums. Validate payloads at SDK send time and in a pipeline stage before ingestion. Reject invalid events with clear error codes.

**Breaking change detection:** Version event schemas. Treat new required properties, removed properties, or type changes as breaking. Use a compatibility matrix and deprecation windows. Run schema diff in CI before merge.

## Instrumentation Patterns

**SDK initialization:** Initialize once at app load with `api_key`, `endpoint`, and `options`. Set `user_id`, `session_id`, and `environment` in context. Do not re-initialize per event.

**Batching:** Buffer events and flush on interval (e.g., 5s) or batch size (e.g., 10). Reduces network calls and improves throughput. Ensure flush on page unload or app background.

**Retry:** Retry failed sends with exponential backoff. Use a dead-letter queue or local persistence for events that fail after max retries. Do not drop silently.

## Common Pitfalls

- **Event naming inconsistency:** Mixing `button_click` and `ButtonClicked` and `btn_clicked` breaks aggregation. Enforce snake_case and object_action in lint rules.
- **Missing required properties:** Omitting `user_id`, `timestamp`, or event-specific required fields causes pipeline rejection or null joins. Validate before send.
- **PII leakage:** Emailing full names, IPs, or raw identifiers in event properties. Sanitize or hash; use allowlists for approved fields.
- **High-cardinality dimensions:** Using free-text or unbounded values (e.g., `search_query`) as dimensions explodes storage and slows queries. Use buckets or separate tables for high-cardinality data.
- **Silent failures in event pipeline:** No alerts on drop rate or validation errors. Add metrics for sent, accepted, rejected, and failed events; alert on anomalies.

## Event Specification Pattern

For each event: `name`, `trigger` (user action or system condition), `required_properties` (with types), `optional_properties`, `owner`, `schema_version`. Example: `checkout_completed` | trigger: user clicks "Place Order" | required: `order_id` (string), `total_amount` (number), `currency` (string) | optional: `coupon_code` (string) | owner: checkout-team | v1.

## Output / Checklist

- Event specification table (name, trigger, properties, owner, schema version).
- Instrumentation points, SDK config (batching, retry), and deduplication strategy.
- JSON Schema snippet or validation rules for each event type.
- Breaking change assessment if modifying existing events.
- Validation evidence from staging/test environments.
- Post-release watchlist: volume metrics, validation error rate, drop rate.

## Constraints

- Do not emit PII or sensitive fields without explicit approval.
- Avoid event spam; keep high-cardinality fields intentional and controlled.
- Preserve compatibility with existing dashboards where possible.