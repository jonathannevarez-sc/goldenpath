# 3. CLI quickstart — 15 minutes

**Getting started · Doc 3 of 10** · [Index](./readme.md)

**This guide is the CLI path only.** For wizard or MCP, see the alternatives below.

| Path | Instead of this doc |
|------|---------------------|
| **Wizard** (bash, Python, PS, or Streamlit) | [05-journey-wizard.md](./05-journey-wizard.md) — menu **1** |
| **MCP (Claude)** | [08-journey-mcp.md](./08-journey-mcp.md) — `scaffold_service` + `shop publish` |

> **Replace placeholders:** `YOUR_ORG`, `YOUR_GCP_PROJECT` — examples use `YOUR_GCP_SANDBOX_PROJECT` ([sandbox](../environments/sandbox-env.md)).

**Goal:** Scaffold a service and deploy to **`dev`** with minimal manual steps.

> Repo map: [repository-guide.md](../repository-guide.md)

## 0. CLI setup

From the repo root:

```bash
cd goldenpath
export PATH="$PWD/cli:$PATH"
```

All commands below use bare `shop`. Equivalent: `./cli/shop <command>`.

## 1. Prerequisites

- GCP bootstrap applied ([sandbox-env.md](../environments/sandbox-env.md) or [getting-started-platform.md](../platform/getting-started-platform.md))
- `gcloud`, `git`, `gh` installed and authenticated
- Platform repo `goldenpath` on GitHub with reusable workflow access enabled for caller repos

**Fastest sandbox:**

```bash
./scripts/standup-teardown-env.sh --yes --skip-labels
```

## 2. Steps

### 1. Configure CLI (1 min)

```bash
shop config init --github-org YOUR_ORG --gcp-dev YOUR_GCP_SANDBOX_PROJECT
```

Saves defaults to `.goldenpath-cli.local.json`. Or export env vars manually:

```bash
export SHOP_GITHUB_ORG=YOUR_ORG
export SHOP_GOLDENPATH_REPO=goldenpath
export SHOP_GCP_DEV_PROJECT=YOUR_GCP_SANDBOX_PROJECT
export SHOP_GCP_PROD_PROJECT=YOUR_GCP_SANDBOX_PROJECT
export SHOP_GCP_REGION="${GCP_REGION}"
export SHOP_ARTIFACT_REGISTRY_REPO="${ARTIFACT_REGISTRY_REPO}"
```

Values for `GCP_REGION` and `ARTIFACT_REGISTRY_REPO` come from [`config/enterprise.env`](../../config/enterprise.env) — see [`config/README.md`](../../config/README.md).

### 2. Pick a template (1 min)

```bash
shop list
```

Default: `nextjs`. **MCP equivalent:** `list_templates`.

### 3. Scaffold (2 min)

```bash
shop new hello-golden --template nextjs --output ..
```

Creates `../hello-golden/` (sibling of the platform repo) with app code, `Dockerfile`, `infra/`, and `.github/workflows/deploy.yml`.

**MCP:** Load skill `scaffold-shop-service`, call `scaffold_service` with the same parameters.

### 4. Publish to GitHub (5 min)

One command handles repo creation, secrets, WIF trust, push, and deploy watch:

```bash
shop publish ../hello-golden
```

This:

1. Creates `gh` repo with default branch **`main`**
2. Sets `GCP_WIF_PROVIDER` and `GCP_WIF_SERVICE_ACCOUNT` secrets
3. Adds per-repo WIF IAM bindings (`scripts/lib/wif-trust-repo.sh`)
4. Pushes `main` and watches GitHub Actions
5. Verifies Cloud Run health (`scripts/lib/verify-deployment.sh`)

**Manual alternative** (if you skip `shop publish`):

```bash
cd ../hello-golden
gh repo create hello-golden --public --source=. --push
# Then add WIF secrets from: cd platform/bootstrap && terraform output
```

### 5. Verify (2 min)

```bash
shop verify ../hello-golden
```

**MCP:**

```
get_deploy_status(service_name="hello-golden", environment="dev", project="YOUR_GCP_SANDBOX_PROJECT")
```

Expected health response: `{"status":"ok",...}`

| Template | Health path |
|----------|-------------|
| nextjs, fastapi, express | `/api/health` |
| streamlit | `/_stcore/health` |
| react-spa, svelte-spa | `/health` |

## 3. Done

You have a live `dev` service on the Golden Path. Edit app code, push to `main`, auto-deploy.

## 4. Promote to prod

GitHub Actions → **Deploy** workflow → `workflow_dispatch` → environment `prod`.

```bash
gh workflow run deploy.yml -f environment=prod
```

**MCP:** `trigger_deploy(github_repo="YOUR_ORG/hello-golden", environment="prod", confirm=true)`

## 5. Teardown

When finished testing:

```bash
./scripts/teardown-personal-test.sh --delete-project YOUR_GCP_SANDBOX_PROJECT --yes
```

## 6. Troubleshooting

| Issue | Check |
|-------|-------|
| Workflow not triggered | Default branch must be `main` — use `shop publish` |
| Reusable workflow not found | `goldenpath` → Settings → Actions → accessible from org repos |
| `startup_failure` / OIDC | Caller workflow needs `permissions: id-token: write` (in scaffolds) |
| Workflow failed auth | WIF secrets on service repo; bootstrap trusts org repos |
| Docker push denied | `shop publish` adds `tokenCreator` binding |
| Health check failed | Match template health path (`shop list`) |
| Something broken | `shop doctor ../hello-golden` |

## 7. Related

| # | Doc |
|---|-----|
| 4 | [04-journey-cli.md](./04-journey-cli.md) — full CLI narrative |
| 2 | [02-pick-your-path.md](./02-pick-your-path.md) — CLI vs wizard vs MCP |
| — | [sandbox-env.md](../environments/sandbox-env.md) — sandbox details |
