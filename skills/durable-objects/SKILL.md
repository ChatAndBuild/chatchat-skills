---
id: durable-objects
name: Durable Objects
description: Use this skill when implementing or operating Cloudflare Durable Objects for strongly consistent coordination, stateful workflows, actor-style services, single-writer state, or low-latency edge logic.
category: Development
---

# Durable Objects

Use Durable Objects when one logical entity needs serialized writes and predictable state transitions.

## When to Use

- You need per-entity consistency (rooms, carts, sessions, rate limit buckets).
- You are building actor-like edge services with state and coordination.
- You need alarms, lifecycle hooks, or object-local storage.

## Storage API Patterns

Use `ctx.storage.get(key)`, `ctx.storage.put(key, value)`, and `ctx.storage.delete(key)` for single-key ops. Use `ctx.storage.list({ prefix: "room:" })` for range scans. Values must be JSON-serializable. For transactional reads and writes, use `ctx.storage.transaction(async (txn) => { ... })` so multiple get/put/delete ops commit atomically. Avoid large values; split into smaller keys with a prefix convention (e.g. `room:123:messages`, `room:123:meta`).

## Alarm Scheduling

Schedule work with `ctx.storage.setAlarm(scheduledTime)` and handle in `alarm()`. Use for retries, compaction, and periodic tasks. Alarms survive hibernation. Example: set alarm 60 seconds from now for retry; in `alarm()`, check state and either retry or mark failed.

## WebSocket Hibernation

Use `ctx.setWebSocketAutoResponse(new WebSocketRequestResponsePair(...))` and `ctx.acceptWebSocket(ws)` for WebSocket connections. Hibernation allows the object to evict while connections stay open; `webSocketMessage` and `webSocketClose` handlers wake the object. Always clean up on `webSocketClose`: remove from in-memory maps, persist final state, and cancel related alarms if needed.

## Routing and Naming

Generate IDs deterministically: `id = env.MY_DO.idFromName("room-" + roomId)` so the same logical entity always maps to the same object. Use namespaces for isolation: `idFromName("prod:cart:" + userId)` vs `idFromName("staging:cart:" + userId)`. Document the key format and collision rules.

## Common Pitfalls

- **Cross-object consistency**: There is no transaction across objects. Design so each object is self-contained; use sagas or compensating actions for multi-object workflows.
- **Unbounded state growth**: Implement retention and compaction. Use alarms to prune old data; cap list sizes or paginate.
- **Cold start latency for large state**: Avoid loading entire storage on first request. Lazy-load or use indexes; keep hot path small.
- **Storage quota limits**: Monitor usage; implement backpressure when approaching limits. Reject or defer writes if storage is full.
- **WebSocket disconnect without cleanup**: Clean up in `webSocketClose`; otherwise orphaned state and stale references accumulate.

## Workflow

1. Define the object boundary (what one instance represents).
2. Map routing keys to object IDs with deterministic naming.
3. Keep all writes through the target object to preserve ordering.
4. Design storage model: small hot state in-memory, durable state in object storage.
5. Use alarms for scheduled work, retries, and compaction.
6. Handle concurrency explicitly (idempotency keys and replay-safe handlers).
7. Add observability: request counts, latency, storage ops, alarm outcomes.

## Design Checklist

- [ ] Entity-to-object mapping is stable and well documented.
- [ ] Handlers are idempotent for retries/replays.
- [ ] State recovery on cold start is tested.
- [ ] Backpressure and rate limits are defined.

## Output Format

Return:

- **Object model**: Entity key format, lifecycle (creation, migration), storage layout (keys, prefixes, value shapes).
- **API surface and routing strategy**: Endpoints, ID generation, namespace isolation.
- **Concrete code patterns**: Storage get/put/list/transaction examples, alarm setup, WebSocket accept/close handling.
- **Failure modes and consistency guarantees**: What is atomic, what is not, recovery behavior.
- **Operational runbook**: Metrics to watch, alarm behavior, retry and backoff policy.

## Constraints

- Avoid cross-object transactional assumptions.
- Keep object logic focused; move bulk analytics elsewhere.
- Do not bypass object writes with side channels that break consistency.