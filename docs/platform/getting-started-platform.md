# Getting started — platform team

Step-by-step to bring Golden Path online for a pilot team.

**Platform repository name:** `goldenpath` (GitHub: `your-org/goldenpath`).

## Prerequisites

- Phase 0 checklist complete: [phase-0-checklist.md](./phase-0-checklist.md)
- Enterprise config: [`config/README.md`](../../config/README.md)
- `gcloud` CLI authenticated with org/project admin
- Terraform >= 1.5
- GitHub org admin (for WIF + template repo)

For a quick isolated test first, see [sandbox-env.md](../environments/sandbox-env.md).

## Step 0 — Enterprise config

```bash
cp config/enterprise.env.example config/enterprise.env
$EDITOR config/enterprise.env
```

Required: `PARENT_PROJECT_ID`, `BILLING_ACCOUNT_ID`, `GITHUB_ORG`. See [`config/README.md`](../../config/README.md).

## Step 1 — Bootstrap GCP (one time)

```bash
cd platform/bootstrap
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your project IDs, GitHub org, github_repo=goldenpath, etc.
terraform init
terraform plan
terraform apply
```

Save outputs — you need them for GitHub org variables and service repos:

- `dev_artifact_registry_url`
- `prod_artifact_registry_url` (skipped when `personal_test = true`)
- `dev_github_wif_provider_name` (full resource name for Actions)
- `dev_github_actions_sa_email`
- `prod_github_wif_provider_name` / `prod_github_actions_sa_email` (non-sandbox footprints)

See [platform/bootstrap/README.md](../../platform/bootstrap/README.md).

## Step 2 — Configure GitHub

### Org variables (optional)

In GitHub org **Settings → Secrets and variables → Actions**:

| Variable | Example |
|----------|---------|
| `GCP_DEV_PROJECT` | From `config/enterprise.env` |
| `GCP_PROD_PROJECT` | From `config/enterprise.env` |
| `GCP_REGION` | From `config/enterprise.env` |
| `GOLDENPATH_ORG` | `GITHUB_ORG` from enterprise.env |
| `GOLDENPATH_VERSION` | From `config/enterprise.env` |

### WIF secrets (per service repo or org-wide)

| Secret | Source |
|--------|--------|
| `GCP_WIF_PROVIDER` | Terraform output `dev_github_wif_provider_name` |
| `GCP_WIF_SERVICE_ACCOUNT` | Terraform output `dev_github_actions_sa_email` |

### Reusable workflow access

On **`goldenpath`** → Settings → Actions → General:

- Enable **Accessible from repositories in the organization** (or equivalent for personal accounts).

Service repos reference:

```yaml
uses: YOUR_ORG/goldenpath/.github/workflows/deploy.yml@GOLDENPATH_VERSION
```

Caller workflows must include:

```yaml
permissions:
  contents: read
  id-token: write
```

(Scaffolds from `shop new` include this.)

## Step 3 — Publish goldenpath release tags

```bash
git push origin main --tags
```

Tags on remote should include: `phase-1`, `phase-2`, `v0.2.0`, `v0.3.8`.

Service templates pin modules and workflow at **`v0.3.8`** (set in `config/enterprise.env`).

## Step 4 — Validate template deploy (platform smoke test)

```bash
export PATH="$PWD/cli:$PATH"
./scripts/standup-teardown-env.sh --yes --skip-labels   # sandbox smoke test
shop config init --github-org YOUR_ORG --gcp-dev YOUR_GCP_SANDBOX_PROJECT
shop new my-service --template nextjs --output .. --dry-run   # review path only
shop new my-service --template nextjs --output ..
shop publish ../my-service
shop verify ../my-service
```

Confirm GitHub Actions deploys to `dev` Cloud Run. **Zero manual edits** after scaffold.

## Step 5 — Pilot handoff

1. Platform runs bootstrap + smoke test
2. Pilot engineer runs `shop new <pilot-service>` **without** platform help for edits
3. Time the run; file friction in GitHub issues
4. Iterate until acceptance test passes

## Step 6 — Phase 2 (MCP)

Phase 2 is delivered in repo (`v0.3.8`). Configure team clients:

- [mcp/README.md](../../mcp/README.md)
- [mcp/examples/claude-mcp.example.json](../../mcp/examples/claude-mcp.example.json)
- [08-journey-mcp.md](../getting-started/08-journey-mcp.md)

## Repo map

| Path | Purpose |
|------|---------|
| `platform/bootstrap/` | One-time GCP + WIF |
| `modules/` | Shared Terraform modules |
| `.github/workflows/deploy.yml` | Reusable deploy workflow |
| `templates/nextjs/` | Service scaffold source |
| `cli/shop` | `shop new` command |
| `skills/` | Agent skills (MCP Phase 2) |
| `mcp/` | MCP server (Phase 2) |
| `scripts/` | Standup / teardown helpers |
