---
id: cdc
name: CDC
description: Use this skill when designing or implementing change data capture, including source logs, event ordering, snapshots, schema changes, downstream consumers, and replay-safe data pipelines.
category: Data & AI
---

# CDC

Help the agent provide practical guidance for CDC architectures and operations.

## When to Use

- The user needs help choosing a CDC pattern for replication or streaming.
- The user asks about consistency, ordering, deduplication, or replay behavior.
- The user wants implementation-ready advice for production pipelines.

## Instructions

1. Clarify source systems, latency targets, and downstream consumers.
2. Recommend a CDC pattern (log-based, trigger-based, or batch diff) with trade-offs.
3. Define schema evolution, idempotency, and exactly-once/at-least-once handling.
4. Include monitoring, backfill, and recovery procedures.
5. End with a rollout and verification checklist.

## Output

- Recommended CDC design with rationale
- Implementation checklist
- Risks, assumptions, and validation steps
