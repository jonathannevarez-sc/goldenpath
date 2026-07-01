---
name: shop-terraform-conventions
phase: 2
description: >
  Extend Golden Path service infrastructure safely. Use when adding GCP resources
  to a service repo infra/ or reviewing module pins and tfvars.
distribution: mcp-resources
status: implemented
---

# Golden Path Terraform conventions

## Bootstrap vs service infra

| | **`platform/bootstrap/`** | **Service `infra/`** |
|---|---------------------------|----------------------|
| **When** | Once per GCP project | Per service, per environment |
| **Creates** | WIF, `github-actions` SA, shared Artifact Registry | Cloud Run, secrets, observability (uses existing AR repo) |
| **Applied by** | `standup-teardown-env.sh`, wizard **3** | GitHub Actions on push to `main` |

Do not add service Cloud Run resources to bootstrap. Do not recreate Artifact Registry in service infra.

## Rules

1. **Service repos** call shared modules from `goldenpath` git tag — do not copy module source
2. Pin `goldenpath_version` in `infra/*.tfvars` (from `GOLDENPATH_VERSION` in enterprise.env, e.g. `v0.3.7`)
3. Set `artifact_registry_repo` to `ARTIFACT_REGISTRY_REPO` — repo is created in bootstrap, referenced in deploy
4. **No click-ops** in production — all changes via Terraform + PR
5. **No external images** — Cloud Run pulls Artifact Registry only

## Service infra layout

```
infra/
├── main.tf       # module blocks only
├── variables.tf
├── dev.tfvars
└── prod.tfvars
```

## Adding resources

Prefer a new **platform-owned module** in `goldenpath/modules/` if multiple services need it.

For one-off service resources, add Terraform in `infra/main.tf` using standard GCP provider resources — keep changes minimal. Grant IAM to the runtime SA from `module.identity.email`.

## Common additions

| Need | Approach |
|------|----------|
| Pub/Sub topic | `google_pubsub_topic` in service infra + IAM for runtime SA |
| GCS bucket | `google_storage_bucket` + IAM binding to runtime SA |
| Cloud SQL | Request platform module (not in base template) |

## Validate before PR

```
validate_service_repo(path=".")
```

## Reference docs

```
get_doc(path="repository-guide.md")
get_doc(path="platform/golden-path.md")
get_doc(path="platform/getting-started-platform.md")
```

Module composition and bootstrap vs service boundaries: `modules/README.md` in the platform repo (not served by `get_doc` — read from disk or [repository-guide.md](../../docs/repository-guide.md)).

## Tools

- `get_service_config` — inspect current Cloud Run / scaling
- `validate_service_repo` — pre-PR checks