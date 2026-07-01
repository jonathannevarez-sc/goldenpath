---
name: shop-observability
phase: 2
description: >
  Logs, metrics, and alerts for Golden Path Cloud Run services. Use for debugging
  deploys, dashboards, cost notes, and 5xx alert investigation.
distribution: mcp-resources
status: implemented
---

# Golden Path observability

## Defaults (every templated service)

| Signal | Location |
|--------|----------|
| **Logs** | Cloud Logging — stdout/stderr from Cloud Run revisions |
| **Metrics** | Cloud Monitoring — Golden Path dashboard per service (Terraform `observability` module) |
| **Traces** | Cloud Trace available in GCP; base templates do not ship OpenTelemetry instrumentation |
| **Alerts** | Baseline 5xx alert policy from `observability` module (no default notification channels — wire in GCP Console or extend Terraform) |

## Find a service

```
list_services(project="...", region="us-central1")
get_deploy_status(service_name="...", environment="dev", project="...")
```

Cloud Run resource name: `{service_name}-{environment}` (e.g. `orders-api-dev`).

## Logs

GCP Console → Logging → filter:

```
resource.type="cloud_run_revision"
resource.labels.service_name="SERVICE-ENV"
```

Or: `gcloud logging read` with the same filter.

## Dashboards

Provisioned automatically by Terraform `observability` module on first deploy (request count, p95 latency tiles).

## Cost visibility

```
get_cost_estimate(service_name="...", environment="dev", project="...")
```

Returns cost notes and console links (not live billing API data). Golden Path `zero_cost` dev profile: scale-to-zero, `cpu_idle` — idle compute ~$0.

## When alerts fire

1. `get_deploy_status` — check Ready condition and latest revision
2. Recent deploy? Check GitHub Actions **Deploy** workflow run
3. Logs filter above for 5xx stack traces
4. Escalate per your team's on-call process (service name + environment + project ID)

## Tools

- `list_services`
- `get_deploy_status`
- `get_service_config`
- `get_cost_estimate`