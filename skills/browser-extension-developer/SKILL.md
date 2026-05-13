---
id: browser-extension-developer
name: Browser Extension Developer
description: Use this skill when building or reviewing browser extensions that need extension-specific guidance for runtime boundaries, permissions, content scripts, background scripts, messaging, storage, security, or distribution.
category: Tools
---

# Browser Extension Developer

Use this skill when the user is building or reviewing a browser extension and needs guidance that accounts for extension-specific runtime boundaries, permissions, and distribution concerns.

## Clarify First
- Which browsers and extension model matter most.
- What the extension actually does in the page, popup, options UI, and background context.
- Which permissions are truly required versus just convenient.
- How state, secrets, and user preferences should be stored.
- What store-review, privacy, or performance constraints could block release.

## Design Priorities
- Keep permissions as narrow as possible.
- Separate content-script behavior from background orchestration clearly.
- Treat message passing as a real interface, not incidental glue.
- Be deliberate about storage, caching, and sync behavior.
- Design for least surprise in user-facing prompts and extension behavior.

## Key Areas To Review
- Manifest structure and permission footprint.
- Messaging between popup, background, content scripts, and options pages.
- DOM interaction safety and resilience on changing pages.
- Storage strategy for settings, caches, and per-site state.
- Error handling for restricted pages, browser differences, and revoked permissions.
- Packaging, privacy disclosures, and release-readiness.

## Common Mistakes
- Asking for broad host or extension permissions without clear need.
- Mixing background logic and UI logic until message flow becomes fragile.
- Assuming the DOM is stable on third-party sites.
- Storing sensitive or high-value data without clear threat thinking.
- Forgetting store-review implications until the extension is nearly done.

## Good Output
- Recommended extension architecture by runtime context.
- Permission and risk review.
- Messaging and state-flow guidance.
- Likely browser-compatibility or store-review issues.
- Testing and release checklist for the extension lifecycle.

## Boundaries
- Do not imply the extension already passes browser store review or security review without evidence.
- Prefer architectural guidance and risk analysis over pretending to inspect packaged extensions directly.
