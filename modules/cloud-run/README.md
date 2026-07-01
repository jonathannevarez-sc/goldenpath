# cloud-run module

Provisions a Cloud Run v2 service with Golden Path defaults.

## Artifact Registry only

Cloud Run **must** pull from **Artifact Registry** in the same project/region. The module builds the image URL as:

```text
{region}-docker.pkg.dev/{project_id}/{repository_id}/{image_name}:{tag}
```

External registries (`docker.io`, `gcr.io`, etc.) are not supported on the Golden Path.

The runtime service account is granted `roles/artifactregistry.reader` on the repository.

## Zero-cost profile (`zero_cost = true`, default)

Minimizes spend for low-traffic and `dev` services:

| Setting | Value | Effect |
|---------|-------|--------|
| `min_instance_count` | `0` | **Scale to zero** — no compute charge when idle |
| `max_instance_count` | `3` | Caps burst spend |
| `cpu` | `0.5` vCPU | Lower per-request cost than 1 vCPU |
| `memory` | `512Mi` | Minimum practical for Node/Next.js |
| `cpu_idle` | `true` | **Request-based CPU billing** between requests |
| `startup_cpu_boost` | `false` | Avoids extra startup CPU charge |

With no traffic, cost is effectively **$0** for compute (you may still pay negligible Artifact Registry storage).

## Standard profile (`zero_cost = false`)

Use for latency-sensitive prod workloads:

```hcl
zero_cost         = false
min_instances     = 1   # always warm — not zero cost
max_instances     = 10
cpu               = "1"
startup_cpu_boost = true
cpu_idle          = false
```

## Override examples

```hcl
# Scale to zero but allow more burst
zero_cost               = true
max_instances_zero_cost = 5

# Dev minimum — module defaults are already zero-cost
zero_cost = true
```