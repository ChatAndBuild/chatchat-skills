---
id: optimizing-database-connection-pool
name: Optimizing Database Connection Pool
description: Use this skill when reasoning about database connection-pool sizing and behavior before changing configuration, including workload-aware limits, timeouts, leak detection, saturation, and failure modes.
category: Databases
---

# Optimizing Database Connection Pool

Use this skill to reason about connection-pool sizing and behavior before changing configuration blindly.

## Clarify First
- Application concurrency and request shape.
- Database connection limits and competing clients.
- Typical query latency and long-running outliers.
- Whether the workload is bursty, steady, or background-heavy.
- Current symptoms such as queueing, timeouts, saturation, or idle waste.

## Tuning Principles
- Pool size should reflect concurrent useful work, not peak thread count.
- Long-running queries often matter more than raw pool size.
- Timeouts should fail noisy callers before the whole system backs up.
- Shared databases need headroom for maintenance and non-app traffic.
- Fixing query quality can outperform raising connection counts.

## Review Output
- Likely bottleneck explanation.
- Pool sizing guidance with assumptions.
- Timeout or backpressure suggestions.
- Query-pattern or workload issues worth investigating.
- Risks of over-allocating connections.

## Common Mistakes
- Setting pool size equal to server worker count by habit.
- Ignoring background jobs and admin traffic.
- Treating connection exhaustion as purely a config problem.
- Hiding slow queries with ever-larger pools.
