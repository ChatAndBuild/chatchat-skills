---
id: add-provider-doc
name: Add Provider Doc
description: Use this skill when producing provider documentation that must be accurate, actionable, and support-friendly, including setup, usage, limits, troubleshooting, and release-ready structure.
category: Documentation
---

# Add Provider Doc

Use this skill to produce provider documentation that is accurate, actionable, and support-friendly.

## When to Use

- A new provider integration is being introduced.
- Existing provider docs are incomplete or hard to operationalize.
- Support/onboarding teams need a reliable setup and troubleshooting guide.

## Workflow

1. Gather provider capabilities, prerequisites, authentication model, and rate limits.
2. Document setup sequence: required configs, credentials, and environment assumptions.
3. Add usage examples for common operations and expected responses.
4. Include error catalog with probable causes and concrete remediation steps.
5. Define operational notes: quotas, retries, backoff, and incident contacts/escalation.
6. Validate doc accuracy against real setup flow before publishing.

## Documentation Patterns

**API reference structure.** Organize API docs by resource or action: endpoints, request/response schemas, required vs optional parameters, and example payloads. Use consistent formatting (e.g., method, path, headers, body). Include a quick-reference table for common operations.

**Authentication setup guides.** Provide step-by-step instructions for obtaining credentials: where to create apps/keys, which scopes to request, how to store secrets securely (env vars, vaults). Document token refresh flow and expiry handling. Include verification steps (e.g., test API call) to confirm auth works.

**Rate limit documentation.** Document limits per endpoint or per account: requests per second/minute, burst limits, and headers that indicate remaining quota. Explain behavior when limits are exceeded (429, retry-after, or throttling). Include recommended backoff strategies.

**Error code catalogs.** List each error code with: HTTP status, provider message, probable cause, and remediation steps. Group by category (auth, rate limit, validation, server). Include example error payloads and links to provider status pages or support.

## Documentation Testing

**Walkthrough validation.** Run the setup flow end-to-end on a fresh environment or VM. Follow the doc exactly as written. Fix any missing steps, ambiguous instructions, or incorrect assumptions. Document the exact environment used (OS, versions).

**Screenshot/example freshness.** Verify screenshots and examples match current UI and API versions. Re-capture screenshots when provider UI changes. Update code examples to use current SDK versions and endpoints. Add a "last verified" date.

**Broken link detection.** Run a link checker on all external URLs. Fix or remove broken links. Prefer stable documentation URLs over version-specific URLs when possible.

## Common Pitfalls

**Documenting happy path only.** Users hit errors, rate limits, and edge cases. Document failure modes and recovery steps. Include "what to do when X fails" for common failure points.

**Outdated screenshots.** Screenshots that no longer match the UI confuse users and erode trust. Re-screenshot when UI changes or at least every 6-12 months.

**Missing prerequisite steps.** Assume nothing. Document OS version, runtime version, dependencies, network requirements, and firewall rules. Users who skip prerequisites often fail silently.

**No troubleshooting section.** Without troubleshooting, users abandon support or guess. Include a troubleshooting matrix: symptom, cause, and fix. Link to common issues and known provider outages.

**Version-specific instructions without version callout.** If instructions apply only to a specific API or SDK version, state the version explicitly. Add a compatibility matrix or version table. Avoid "works with latest" without defining what "latest" means.

## Output / Checklist

- **Provider overview.** Supported features, limitations, and prerequisites. Link to provider status page.

- **Quick start.** Minimal setup to get a working integration in under 15 minutes.

- **Setup sequence.** Step-by-step setup with verification checkpoints. Required configs, credentials, environment variables. Prerequisites clearly stated.

- **API reference.** Endpoints, request/response schemas, parameters. Authentication and rate limit headers.

- **Authentication guide.** Credential creation, storage, refresh, and verification steps.

- **Usage examples.** Common operations with example requests and responses. Code snippets for supported languages.

- **Rate limit documentation.** Limits, behavior when exceeded, and backoff recommendations.

- **Error catalog.** Error codes, causes, and remediation steps. Links to provider support.

- **Troubleshooting matrix.** Symptoms, causes, and fixes. Known issues and workarounds.

- **Maintenance notes.** Upgrade procedures, deprecation notices, ownership, and escalation contacts.

- **Validation results.** Walkthrough completion status, screenshot freshness, and link check results.

## Constraints

- Keep security-sensitive values redacted in all examples.
- Align instructions with current production configuration and API versions.
- Avoid undocumented assumptions; call out prerequisites explicitly.