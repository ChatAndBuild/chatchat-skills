---
id: content-hash-cache-pattern
name: Content Hash Cache Pattern
description: Use this skill when implementing content-hash caching for AI or data systems, including cache keys, invalidation, reproducibility, artifact reuse, and avoiding stale outputs.
category: Data & AI
---

# Content Hash Cache Pattern

Help the agent provide practical guidance for designing robust content-hash caching.

## When to Use

- The user needs help reducing repeated compute with deterministic caching.
- The user asks about hash keys, invalidation, or cache consistency.
- The user wants an implementation strategy for production workloads.

## Instructions

1. Clarify workload characteristics and cache hit-rate goals.
2. Recommend hash input design and stable canonicalization rules.
3. Define invalidation/versioning strategy and fallback behavior.
4. Address storage, eviction policy, and observability requirements.
5. End with a rollout and validation checklist.

## Output

- Recommended caching approach
- Step-by-step implementation checklist
- Risks, assumptions, and verification steps
