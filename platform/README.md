# Platform infrastructure

One-time GCP bootstrap and shared platform Terraform — **not** per-service deploy infra (that lives in scaffolded service repos under `infra/`).

**Full map:** [docs/repository-guide.md](../docs/repository-guide.md#platform--one-time-gcp-bootstrap)

## Layout

```
platform/
└── bootstrap/          # WIF, github-actions SA, shared AR — apply once per GCP project
    ├── main.tf
    ├── wif.tf
    ├── profiles/       # Example tfvars profiles (optional)
    ├── terraform.tfvars.example
    └── terraform.tfvars.personal.example
```

## Bootstrap vs service infra

| | **`platform/bootstrap/`** | **Service `infra/`** (from templates) |
|---|---------------------------|---------------------------------------|
| **When** | Once per GCP project | Per service, per environment |
| **Creates** | WIF pool, `github-actions` SA, shared Artifact Registry repo, org-level IAM | Cloud Run, secrets, observability (uses bootstrap AR repo) |
| **Applied by** | `./scripts/standup-teardown-env.sh`, wizard menu **3** | GitHub Actions on push to `main` |
| **State** | Local `terraform.tfstate` (gitignored) or remote | Per service repo |

`artifact_registry_id` in bootstrap tfvars comes from `ARTIFACT_REGISTRY_REPO` in [`config/enterprise.env`](../config/enterprise.env).

## Committed vs local

| File | Committed? | Purpose |
|------|------------|---------|
| `bootstrap/profiles/*.example.tfvars` | Yes | Profile presets (sandbox) |
| `bootstrap/terraform.tfvars.example` | Yes | Manual bootstrap template (dev + prod) |
| `bootstrap/terraform.tfvars.personal.example` | Yes | Manual single-project sandbox template |
| `bootstrap/.terraform.lock.hcl` | Yes | Provider lock |
| `bootstrap/terraform.tfvars` | **No** (gitignored) | Active values — written by standup/wizard |
| `bootstrap/terraform.tfstate*` | **No** | Local state |

## Docs

- [platform/bootstrap/README.md](./bootstrap/README.md) — bootstrap how-to
- [getting-started-platform.md](../docs/platform/getting-started-platform.md) — platform team guide
- [sandbox-env.md](../docs/environments/sandbox-env.md) — isolated test project