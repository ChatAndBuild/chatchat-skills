---
id: airflow-dag-patterns
name: Airflow DAG Patterns
description: Use this skill when designing or reviewing Apache Airflow DAGs for scheduling, retries, task dependencies, idempotency, backfills, sensors, and production reliability.
category: Data & AI
---

# Airflow DAG Patterns

Help the agent provide implementation-focused guidance for Airflow DAG design and operations.

## When to Use

- The user needs help designing DAG structure, dependencies, or scheduling.
- The user asks how to improve reliability, observability, or performance.
- The user wants practical trade-offs for orchestration patterns.

## Instructions

1. Clarify workload shape, cadence, SLAs, and dependency graph.
2. Recommend DAG structure, task boundaries, and idempotency practices.
3. Suggest retries, backfills, and failure-handling strategies.
4. Include monitoring, alerting, and cost/performance considerations.
5. End with a concise rollout and validation checklist.

## Output

- Recommended DAG pattern with rationale
- Step-by-step implementation checklist
- Risks, assumptions, and validation steps
