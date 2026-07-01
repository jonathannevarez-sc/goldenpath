# Platform bootstrap

One-time Terraform to prepare **dev** and **prod** GCP projects for Golden Path.

## Creates

- Enables required GCP APIs
- Shared Artifact Registry repository (`artifact_registry_id` — set from `ARTIFACT_REGISTRY_REPO` in `config/enterprise.env`)
- GitHub Actions CI service accounts (`github-actions`)
- **Workload Identity Federation** pools + OIDC providers (no JSON keys)
- IAM for CI: Cloud Run admin, Artifact Registry admin, service account admin/user, Secret Manager admin, monitoring editor, project IAM admin, storage object admin

## Before you apply

1. Copy `config/enterprise.env.example` → `config/enterprise.env` and fill in values (including `ARTIFACT_REGISTRY_REPO`)
2. Create `dev` and `prod` GCP projects (or identify existing ones)
3. Copy `terraform.tfvars.example` → `terraform.tfvars` and fill in project IDs, GitHub org, and `artifact_registry_id`
4. (Recommended) Create a GCS bucket for remote state and uncomment `backend` in `versions.tf`

## Variables

| Variable | Source | Notes |
|----------|--------|-------|
| `artifact_registry_id` | `ARTIFACT_REGISTRY_REPO` in enterprise.env | Shared Docker repo for all services |
| `github_org` / `github_repo` | `GITHUB_ORG` / `PLATFORM_REPO` | WIF trusts `github_org/*` via `attribute_condition` |
| `github_trusted_service_repos` | Manual list in tfvars | Explicit WIF bindings for service repos (needed for AR `docker login`); or run `scripts/lib/wif-trust-repo.sh` after publish |

Standup script and wizard menu **3** write `terraform.tfvars` automatically from `config/enterprise.env`.

## Apply (two-project production)

```bash
terraform init
terraform plan
terraform apply
```

## Apply (isolated sandbox)

```bash
./scripts/standup-teardown-env.sh
```

From `platform/bootstrap/`, use `../../scripts/standup-teardown-env.sh`. Reads `config/enterprise.env` — creates sandbox project, links billing, runs apply with `personal_test = true`.

## Wire GitHub Actions

Use terraform outputs per environment:

| Output | Use in GitHub |
|--------|----------------|
| `dev_github_wif_provider_name` | Secret `GCP_WIF_PROVIDER` (dev workflows) |
| `dev_github_actions_sa_email` | Secret `GCP_WIF_SERVICE_ACCOUNT` (dev) |
| `prod_github_wif_provider_name` | Secret `GCP_WIF_PROVIDER` (prod workflows) |
| `prod_github_actions_sa_email` | Secret `GCP_WIF_SERVICE_ACCOUNT` (prod) |
| `dev_artifact_registry_url` | Image push target for CI |

Service repos reference:

```yaml
uses: your-org/goldenpath/.github/workflows/deploy.yml@v0.3.8
```

Enable **reusable workflow access** on this repo. Caller workflows need `permissions: id-token: write`.
