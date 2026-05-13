---
id: observability-engineer
name: Observability Engineer
description: Use this skill when designing observability for services with logs, metrics, traces, alert thresholds, dashboards, SLO signals, and actionable incident-response context.
category: DevOps
---

# Observability Engineer

Build an observability baseline that supports fast detection, diagnosis, and recovery.

## When to Use

- You are launching or hardening a service and need meaningful telemetry.
- You need to define dashboards and alerts tied to user impact.
- You want better incident triage using correlated logs/metrics/traces.

## Three Pillars

**Metrics (Prometheus/StatsD):** Emit counters for requests and errors, histograms for latency, gauges for saturation (CPU, memory, queue depth). Use labels consistently: `service`, `env`, `method`, `status`. Avoid high-cardinality labels (user IDs, full URLs). Example: `http_requests_total{service="api",method="GET",status="500"}`.

**Logs (structured JSON):** Emit JSON with required fields: `timestamp`, `level`, `message`, `trace_id`, `span_id`, `service`, `correlation_id`. Use correlation IDs to link logs across services for a single request. Avoid free-form text; use structured key-value pairs for filtering.

**Traces (OpenTelemetry):** Instrument spans at service boundaries and critical operations. Propagate `trace_id` and `span_id` via headers. Ensure spans include `service.name`, `http.method`, `http.status_code`. Correlate traces with logs using the same `trace_id`.

## SLI/SLO Definition

- **Availability:** `1 - (error_requests / total_requests)`. Target: e.g. 99.9%.
- **Latency:** `p99 < threshold`. Target: e.g. p99 < 500ms.
- **Throughput:** requests per second; define minimum viable throughput for capacity planning.
- **Saturation:** resource utilization (CPU, memory, connections); define thresholds before degradation.

Express SLOs as error budgets (e.g. 0.1% downtime = ~43 min/month). Use error budget to drive release and alerting decisions.

## Alert Design

- **Multi-window burn rate:** Alert when error budget burns too fast over short and long windows (e.g. 14.4x over 5m OR 1x over 1h) to catch both fast and slow burns.
- **Symptom-based vs cause-based:** Prefer symptom-based alerts (user-facing SLO breach) over cause-based (disk full). Cause-based alerts support diagnosis but should not be the primary on-call signal.
- **Severity:** Critical = user impact, immediate action. Warning = approaching threshold, investigate soon.
- **Runbooks:** Every alert must link to a runbook with clear steps and escalation path.

## Common Pitfalls

- **Alert fatigue:** Low thresholds or overly sensitive rules cause noise. Tune thresholds using historical data; start conservative.
- **Metrics without labels:** Unlabeled metrics prevent filtering by service, env, or endpoint. Add essential dimensions from day one.
- **Traces without correlation:** Logs and traces must share `trace_id` for request-level debugging.
- **Dashboard sprawl:** Too many dashboards with overlapping panels. Consolidate into service health + incident triage views.

## PromQL/LogQL Examples

**Error rate (PromQL):**
```promql
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))
```

**Availability (PromQL):**
```promql
1 - (sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])))
```

**p99 latency (PromQL):**
```promql
histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service))
```

**Logs by trace_id (LogQL):**
```logql
{service="api"} | json | trace_id="abc123"
```

## Workflow

1. Identify critical user journeys and system dependencies.
2. Define SLIs and SLOs using the techniques above.
3. Specify log schema (structured JSON, correlation IDs) and trace context (OpenTelemetry).
4. Create alert rules with burn rate or threshold logic, clear severity, and runbook links.
5. Define dashboards for service health and incident investigation.
6. Add verification checks to ensure telemetry quality in each environment.

## Output Format

```markdown
## Telemetry Plan
- Metrics: <list with names, types, labels; Prometheus/StatsD>
- Logs: <required JSON fields, correlation_id usage>
- Traces: <span boundaries, OpenTelemetry context propagation>

## SLI/SLO
- Availability: <formula and target>
- Latency: <percentile and threshold>
- Error budget: <allowance and implications>

## Alerting
- Critical: <condition, burn rate or threshold, runbook link>
- Warning: <condition, runbook link>

## Dashboards
- Service health panel: <signals, PromQL where applicable>
- Incident triage panel: <signals, drill-down to logs/traces>

## PromQL/LogQL Snippets
- Error rate: <query>
- Latency p99: <query>
- Log correlation: <query>

## Validation Checklist
- [ ] Metrics emitted with correct labels
- [ ] Structured logs include trace_id and correlation_id
- [ ] Traces propagate context across services
- [ ] Alerts tested for signal quality and runbooks linked
- [ ] No high-cardinality labels; no alert fatigue
```

## Constraints

- Avoid noisy alerts without clear action paths.
- Prefer user-impact and SLO-aligned signals over infrastructure-only proxies.
- Keep naming conventions consistent across telemetry sources.