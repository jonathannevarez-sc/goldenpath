# Phase 0 — Pre-start checklist

Complete these **before** running platform bootstrap or onboarding a pilot team.

## Decisions (name an owner for each)

- [ ] **Compute:** Cloud Run (recommended)
- [ ] **IaC:** Terraform (recommended)
- [ ] **CI/CD:** GitHub Actions (if Shop uses GitHub)
- [ ] **Environments:** `dev` + `prod` (shared GCP projects to start)
- [ ] **Base template:** Next.js only for v1
- [ ] **MCP distribution:** Hosted MCP + git-backed skills (Phase 2)

## People

- [ ] **Platform DRI** named
- [ ] **Pilot team** named
- [ ] **Pilot service** named (real feature, 4–6 week horizon)
- [ ] **Pilot product engineer** committed to cold acceptance test
- [ ] **Security** reviewed WIF + Secret Manager + MCP auth model (async OK)
- [ ] **SRE** reviewed observability baseline (async OK)

## GCP prerequisites

- [ ] GCP organization / folder structure identified
- [ ] `dev` GCP project ID: `________________`
- [ ] `prod` GCP project ID: `________________`
- [ ] Default region (`GCP_REGION` from enterprise.env): `________________`
- [ ] Billing linked to projects
- [ ] Terraform state bucket planned (see `platform/bootstrap`)

## GitHub prerequisites

- [ ] GitHub org: `________________`
- [ ] `goldenpath` repo created and this code pushed ([github.com/YOUR_GITHUB_ORG/goldenpath](https://github.com/YOUR_GITHUB_ORG/goldenpath))
- [ ] GitHub org allows OIDC for Actions (for WIF)
- [ ] Branch protection with required reviews configured on `main` (recommended for production use)

## Baseline metrics (record before Golden Path)

- [ ] Last new service: time to first `dev` deploy: `____`
- [ ] Manual steps in that deploy: `____`
- [ ] Date captured: `____`

## Exit criterion (write on the wall)

> A **pilot product engineer** scaffolds a service and deploys to **`dev` with zero manual edits**.

---

## Shop production environment (template)

Fill this section when moving from personal/teardown test to Shop's real dev/prod footprint. Copy values from your platform team's source of truth.

### GCP — Shop prod footprint

| Setting | Dev | Prod | Owner |
|---------|-----|------|-------|
| GCP project ID | `shop-dev-________` | `shop-prod-________` | Platform |
| Default region | `GCP_REGION` from enterprise.env | same | Platform |
| Billing account | `________________` | same or dedicated | Finance |
| Folder / org | `________________` | `________________` | Platform |
| Artifact Registry repo | `ARTIFACT_REGISTRY_REPO` from enterprise.env | same | Platform |
| Terraform state bucket | `________________` | `________________` | Platform |
| Monthly budget alert | `$________` | `$________` | Finance |

### GitHub — Shop org

| Setting | Value | Owner |
|---------|-------|-------|
| GitHub org | `________________` | Platform |
| Platform repo | `{org}/goldenpath` | Platform |
| Reusable workflow pin | `@GOLDENPATH_VERSION` from enterprise.env (not `@main`) | Platform |
| WIF provider secret | `GCP_WIF_PROVIDER` | Platform |
| WIF SA secret | `GCP_WIF_SERVICE_ACCOUNT` | Platform |
| Private module token (if repo private) | `GOLDENPATH_MODULE_TOKEN` | Platform |
| GitHub environments | `dev`, `prod` on each service repo | Platform |
| Prod deploy gate | `workflow_dispatch` + environment protection | SRE |

### Bootstrap (one-time per footprint)

```bash
cd platform/bootstrap
cp terraform.tfvars.example terraform.tfvars
# Set: project IDs, region, github_org, allowed repos, billing
terraform init && terraform apply
```

Record outputs:

| Output | Dev value | Prod value |
|--------|-----------|------------|
| `dev_github_wif_provider_name` | `________________` | `prod_github_wif_provider_name` |
| `dev_github_actions_sa_email` | `________________` | `prod_github_actions_sa_email` |
| Artifact Registry URL | `________________` | `________________` |

### Service repo secrets (every new service)

Add to the service repo (and duplicate `_PROD` variants if using GitHub environment-specific secrets):

| Secret | Maps to |
|--------|---------|
| `GCP_WIF_PROVIDER` | Dev WIF provider |
| `GCP_WIF_SERVICE_ACCOUNT` | Dev CI service account |
| `GCP_WIF_PROVIDER_PROD` | Prod WIF provider (can match dev initially) |
| `GCP_WIF_SERVICE_ACCOUNT_PROD` | Prod CI service account |
| `GOLDENPATH_MODULE_TOKEN` | Optional PAT if `goldenpath` is private |

### Shop prod smoke validation

Before pilot handoff on Shop prod projects:

- [ ] `goldenpath` pushed with tag matching `GOLDENPATH_VERSION` in enterprise.env
- [ ] Bootstrap applied on Shop dev project
- [ ] Reference smoke service deploys green to Shop dev Cloud Run
- [ ] `/api/health` returns 200
- [ ] Prod deploy tested via `workflow_dispatch` on smoke or pilot service
- [ ] Budget alerts configured on dev + prod projects
- [ ] Security sign-off on WIF trust condition (org/repo scope)

### Teardown / test isolation (personal or pre-Shop)

For isolated validation **before** Shop prod (see [sandbox-env.md](../environments/sandbox-env.md)):

| Setting | Test value |
|---------|------------|
| Project | `YOUR_GCP_SANDBOX_PROJECT` |
| Billing | Shared with `YOUR_BILLING_ANCHOR_PROJECT` |
| GitHub org | `YOUR_GITHUB_ORG` |
| Test service repo | Scaffold with `shop new` (e.g. `YOUR_GITHUB_ORG/my-service`) |

---

## When all boxes are checked

1. Run [Platform bootstrap](../../platform/bootstrap/README.md)
2. Deploy the [Next.js template](../../templates/nextjs/README.md) once by hand to validate
3. Run `shop new <pilot-service> --output ..` and hand off to pilot engineer