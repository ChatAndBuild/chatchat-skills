---
id: dns
name: DNS
description: Use this skill when understanding or troubleshooting DNS behavior across records, delegation, caching, propagation, resolution paths, and common domain misconfigurations.
category: Tools
---

# DNS

Use this skill when the user needs help understanding or troubleshooting DNS behavior across records, delegation, caching, and propagation.

## Clarify First
- Which domain or subdomain is in scope.
- What behavior is expected versus what is actually happening.
- Which record types matter for the issue.
- Whether the problem is resolution, delegation, verification, email delivery, or traffic routing.
- What changed recently in registrar, nameserver, or record configuration.

## Investigation Priorities
- Confirm authority chain before focusing on individual records.
- Distinguish authoritative answers from cached resolver behavior.
- Check the exact record type and hostname involved.
- Consider TTL and propagation before assuming a change failed.
- Separate DNS-layer issues from application, CDN, or TLS issues.

## Common Problem Areas
- Wrong nameserver delegation.
- Record collisions such as incompatible CNAME and other records at the same label.
- Confusing root and subdomain behavior.
- Email-related breakage from SPF, DKIM, MX, or DMARC mistakes.
- Expecting instant global consistency after a DNS change.

## Good Output
- DNS diagnosis or setup review by layer.
- Likely source of failure: delegation, record data, caching, or non-DNS system.
- Safe next checks to confirm the theory.
- Change-risk notes around propagation and rollback.

## Common Mistakes
- Looking only at one resolver and assuming it represents the whole internet.
- Fixing records before confirming nameserver authority is correct.
- Treating CDN or certificate issues as if they were purely DNS issues.
- Overlooking TTL and stale caches during validation.
- Making multiple DNS changes at once and obscuring the real fix.

## Boundaries
- Do not claim a DNS change has fully propagated without evidence from the right vantage points.
- Prefer reasoning about authority, records, and resolution paths over pretending to query live DNS unless the user provides results.
