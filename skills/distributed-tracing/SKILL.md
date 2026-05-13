---
id: distributed-tracing
name: Distributed Tracing
description: Use this skill when instrumenting distributed systems with traces that expose latency, errors, dependency bottlenecks, service boundaries, and incident diagnostics.
category: DevOps
---

# Distributed Tracing

Design traces that make root-cause analysis fast during incidents and performance regressions.

## When to Use

- You need end-to-end request visibility across multiple services.
- Metrics show a latency/error spike but source is unclear.
- You are standardizing telemetry instrumentation.

## OpenTelemetry SDK Patterns

**TracerProvider setup** (Node.js example):

```javascript
const { NodeTracerProvider } = require('@opentelemetry/sdk-trace-node');
const { BatchSpanProcessor } = require('@opentelemetry/sdk-trace-base');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-http');

const provider = new NodeTracerProvider();
provider.addSpanProcessor(new BatchSpanProcessor(new OTLPTraceExporter()));
provider.register();
```

**W3C traceparent propagation**: Ensure `traceparent` and `tracestate` headers are forwarded on every outbound HTTP call. Use `@opentelemetry/api` `trace.getActiveSpan()` and inject into headers via `W3CTraceContextPropagator`.

**Auto-instrumentation vs manual spans**: Use auto-instrumentation for HTTP clients, Express/Fastify, and DB drivers. Add manual spans for business logic, queue publish/consume, and custom RPC. Manual spans should wrap only meaningful units of work.

## Sampling Strategies

- **AlwaysOn**: Every trace sampled. Use only in low-traffic or staging.
- **TraceIdRatioBased**: Sample N% of traces by trace ID. Use for cost control in production.
- **ParentBased**: Follow parent decision (sampled/not). Use with head sampling so children inherit.
- **Tail sampling** (collector): Sample based on span attributes (e.g., status=error, latency > threshold). Configure in OTel collector, not SDK.

## Span Attribute Best Practices

Follow semantic conventions for consistency:

- **HTTP**: `http.method`, `http.url`, `http.status_code`, `http.route`
- **DB**: `db.system`, `db.name`, `db.statement` (redact sensitive parts)
- **Messaging**: `messaging.system`, `messaging.destination`, `messaging.operation`

Avoid high-cardinality attributes: no full URLs, user IDs, or request IDs unless strictly needed for triage. Prefer bounded values (status code, route pattern, error type).

## Common Pitfalls

- **Broken context propagation through async queues**: When publishing to Kafka/RabbitMQ, inject trace context into message headers; when consuming, extract and set as current context before creating child spans.
- **High-cardinality span attributes**: Attributes like `user_id` or full `url` explode storage and query cost. Use bounded values.
- **Missing error status on spans**: Set `span.setStatus({ code: SpanStatusCode.ERROR, message })` and record exception with `span.recordException(err)`.
- **Orphaned spans from middleware gaps**: If middleware creates a span but does not set it as active, child spans become orphaned. Use `context.with(trace.setSpan(context.active(), span), () => { ... })`.

## OTel Collector Pipeline

```yaml
receivers:
  otlp:
    protocols:
      grpc: {}
      http: {}

processors:
  batch:
    timeout: 5s
    send_batch_size: 1024
  tail_sampling:
    decision_wait: 10s
    policies:
      - name: errors
        type: status_code
        status_code: { status_codes: [ERROR] }
      - name: slow
        type: latency
        latency: { threshold_ms: 1000 }
      - name: sample-10pct
        type: probabilistic
        probabilistic: { sampling_percentage: 10 }

exporters:
  otlp:
    endpoint: "jaeger:4317"
    tls: { insecure: true }

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch, tail_sampling]
      exporters: [otlp]
```

## Workflow

1. Define critical request paths and business transactions to trace first.
2. Instrument ingress, service-to-service calls, datastore calls, and queue boundaries.
3. Ensure context propagation headers are forwarded across every hop.
4. Add meaningful span names and attributes (service, route, tenant, error class).
5. Capture errors and status codes on spans with consistent taxonomy.
6. Configure sampling strategy: head sampling for baseline cost; tail or rule-based for high-value failures.
7. Create dashboards/queries for top latency contributors and failing spans.

## Instrumentation Checklist

- [ ] Trace IDs remain continuous across services.
- [ ] Queue publish/consume injects and extracts trace context.
- [ ] High-cardinality attributes are controlled.
- [ ] Error spans include `setStatus` and `recordException`.
- [ ] Sampling preserves incident-relevant traces (errors, slow).
- [ ] No orphaned spans from missing context propagation.

## Output Format

```markdown
## Instrumentation Coverage Map
| Service | Ingress | Outbound HTTP | DB | Queue | Gaps |
|---------|---------|---------------|-----|-------|------|
| ...     | ...     | ...           | ... | ...   | ...  |

## Propagation & Schema
- Propagation gaps: <list services/hops where context is lost>
- Schema inconsistencies: <naming, attribute mismatches>

## Sampling Recommendation
- Strategy: head / tail / hybrid
- Config: <SDK + collector snippet>
- Rationale: <cost vs coverage>

## Pitfalls Addressed
- [ ] Context propagation through async/queues
- [ ] High-cardinality attributes removed
- [ ] Error status on spans
- [ ] Middleware context set correctly

## Incident Triage Queries
- Top latency by service: <query>
- Failing traces: <query>
- Slow dependency: <query>

## Next Improvements
- <prioritized list>
```

## Constraints

- Do not emit sensitive payloads or secrets in span attributes.
- Keep span naming consistent and stable for long-term analysis.
- Avoid tracing every internal function; focus on network/storage boundaries.