# 4. Golden Path — the whole journey (CLI)

**Getting started · Doc 4 of 10** · [Index](./readme.md)

How a new user goes from zero to a live Cloud Run service using the **`shop` CLI** only.

> **Replace placeholders:** `YOUR_ORG`, `YOUR_GCP_PROJECT` — examples use `YOUR_GCP_SANDBOX_PROJECT` ([sandbox](../environments/sandbox-env.md)).

**Platform repo:** `goldenpath`  
**Test sandbox:** `YOUR_GCP_SANDBOX_PROJECT` (isolated — does not touch `YOUR_BILLING_ANCHOR_PROJECT`)  
**Repo map:** [repository-guide.md](../repository-guide.md)

**Pure CLI path only.** Do not mix with the wizard / Streamlit UI path. See [02-pick-your-path.md](./02-pick-your-path.md) for how to choose. Quick path: [03-quickstart.md](./03-quickstart.md).

---

## 1. The journey in one picture

```
Prerequisites installed
        ↓
./scripts/standup-teardown-env.sh  (one-time bootstrap)
        ↓
shop config init  →  saves .goldenpath-cli.local.json
        ↓
shop list  →  pick template
        ↓
shop new <name>  →  service repo on disk
        ↓
shop publish  →  GitHub repo + secrets + WIF + push main
        ↓
GitHub Actions  →  dev Cloud Run
        ↓
shop verify  →  health check
        ↓
Daily: edit → push main → auto-deploy dev
        ↓
gh workflow run  →  promote to prod (manual)
        ↓
./scripts/teardown-personal-test.sh  →  delete sandbox (optional)
```

---

## 2. Step-by-step

### 1. Prerequisites

| Tool | Purpose |
|------|---------|
| `gcloud` | GCP auth, verify deploys |
| `terraform` | Platform bootstrap (standup script runs it) |
| `git` | Version control |
| `gh` | `shop publish` creates repos and sets secrets |

**Running the `shop` CLI** (once per shell, from repo root):

```bash
cd goldenpath
export PATH="$PWD/cli:$PATH"
```

Examples below use bare `shop`. Equivalent: `./cli/shop <command>`.

```bash
gcloud auth login
gcloud auth application-default login
gcloud auth application-default set-quota-project YOUR_GCP_SANDBOX_PROJECT
```

---

### 2. Bootstrap GCP (one-time)

Creates the isolated project and wires Artifact Registry + WIF.

```bash
cd goldenpath
./scripts/standup-teardown-env.sh --yes --skip-labels
```

**What happens:** reads [`config/enterprise.env`](../../config/enterprise.env), creates `YOUR_GCP_SANDBOX_PROJECT`, links billing, runs `terraform apply` in [`platform/bootstrap/`](../../platform/bootstrap/).

Implementation: [`scripts/env/standup-teardown-env.sh`](../../scripts/env/standup-teardown-env.sh)

---

### 3. Configure the CLI

```bash
shop config init --github-org YOUR_GITHUB_ORG --gcp-dev YOUR_GCP_SANDBOX_PROJECT
```

Saves to `.goldenpath-cli.local.json` (gitignored). Or export env vars:

```bash
export SHOP_GITHUB_ORG=YOUR_GITHUB_ORG
export SHOP_GOLDENPATH_REPO=goldenpath
export SHOP_GCP_DEV_PROJECT=YOUR_GCP_SANDBOX_PROJECT
export SHOP_GCP_PROD_PROJECT=YOUR_GCP_SANDBOX_PROJECT
export SHOP_GCP_REGION="${GCP_REGION}"   # from config/enterprise.env
export SHOP_ARTIFACT_REGISTRY_REPO="${ARTIFACT_REGISTRY_REPO}"   # from config/enterprise.env
```

---

### 4. List templates

```bash
shop list
# or, if `shop` is not on your PATH: ./cli/shop list
```

Reads [`templates/catalog.json`](../../templates/catalog.json).

| Template | Use case |
|----------|----------|
| `nextjs` (default) | Full-stack web |
| `fastapi` | Python API |
| `streamlit` | Dashboards |
| `express` | Node API |
| `react-spa` / `svelte-spa` | Frontends |

---

### 5. Scaffold a service

```bash
shop new hello-golden --template nextjs --output ..
# or ./cli/shop new ...
```

Creates `../hello-golden/` (outside the platform repo) with app code, `Dockerfile`, `infra/`, and `.github/workflows/deploy.yml`.

Token replacement handled by [`scripts/lib/scaffold-tokens.sh`](../../scripts/lib/scaffold-tokens.sh).

---

### 6. Publish to GitHub (recommended)

One command replaces manual repo creation, secrets, and WIF wiring:

```bash
shop publish ../hello-golden
# or ./cli/shop publish ../hello-golden
```

(Note: `--dry-run` applies to `shop new` only — prints the target path without scaffolding.)

**What `shop publish` does:**

| Step | Action |
|------|--------|
| 1 | `gh repo create` with default branch **`main`** |
| 2 | Set `GCP_WIF_PROVIDER` and `GCP_WIF_SERVICE_ACCOUNT` secrets |
| 3 | Run [`scripts/lib/wif-trust-repo.sh`](../../scripts/lib/wif-trust-repo.sh) for IAM bindings |
| 4 | Push `main`, watch workflow |
| 5 | Verify health via [`scripts/lib/verify-deployment.sh`](../../scripts/lib/verify-deployment.sh) |

**Manual alternative** (not recommended):

```bash
cd ../hello-golden
gh repo create hello-golden --public --source=. --push
# Add WIF secrets from platform/bootstrap terraform output
# Add repo to github_trusted_service_repos, terraform apply
# Create GitHub environments dev and prod
```

---

### 7. Deploy to dev (automatic)

If `shop publish` pushed `main`, deploy is already running:

```bash
gh run watch
```

Workflow calls reusable [`.github/workflows/deploy.yml`](../../.github/workflows/deploy.yml) from this platform repo.

---

### 8. Verify

```bash
shop verify ../hello-golden
# or ./cli/shop verify ../hello-golden
```

Or manually:

```bash
curl "$(gcloud run services describe hello-golden-dev \
  --project=YOUR_GCP_SANDBOX_PROJECT \
  --region="${GCP_REGION}" \
  --format='value(status.url)')/api/health"
```

Expected: `{"status":"ok",...}`

---

### 9. Diagnose issues

```bash
shop doctor ../hello-golden
# or ./cli/shop doctor ../hello-golden
```

Checks branch name, WIF secrets, unreplaced `{{tokens}}`, project mismatch, stale `GOLDENPATH_VERSION` pins, and `gh` account vs `GITHUB_ORG`.

If doctor reports removed tags (`v0.3.0`–`v0.3.6`) or a pin not matching `enterprise.env`:

```bash
shop upgrade ../hello-golden
```

Only **`v0.3.8`** is published on the platform repo today.

---

### 10. Daily workflow

```
Edit code  →  git commit  →  git push main  →  dev updates automatically
```

---

### 11. Promote to prod (manual)

```bash
gh workflow run deploy.yml -f environment=prod
```

Or GitHub → Actions → Deploy → Run workflow → environment `prod`.

---

### 12. Teardown (optional)

```bash
cd goldenpath
./scripts/teardown-personal-test.sh --delete-project YOUR_GCP_SANDBOX_PROJECT --yes
```

Safety checks in [`scripts/lib/teardown-safety.sh`](../../scripts/lib/teardown-safety.sh) block protected projects.

---

## 3. CLI cheat sheet

| Task | Command |
|------|---------|
| Init config | `shop config init --github-org ORG --gcp-dev PROJECT` |
| List templates | `shop list` |
| Scaffold | `shop new <name> --template <tpl> --output ..` |
| Publish + deploy | `shop publish ../<name>` (when scaffolded with `--output ..`) |
| Verify health | `shop verify ../<name>` |
| Diagnose | `shop doctor ../<name>` |
| Fix stale pins | `shop upgrade ../<name>` |
| Stand up sandbox | `./scripts/standup-teardown-env.sh --yes --skip-labels` |
| WIF outputs | `cd platform/bootstrap && terraform output dev_github_wif_provider_name` |
| Tear down | `./scripts/teardown-personal-test.sh --delete-project YOUR_GCP_SANDBOX_PROJECT --yes` |

---

## 4. Key repo folders (CLI path)

| Folder | Role |
|--------|------|
| [`cli/shop`](../../cli/shop) | Main CLI |
| [`scripts/lib/`](../../scripts/lib/) | Token replacement, WIF trust, deploy verification |
| [`scripts/env/`](../../scripts/env/) | Standup and teardown |
| [`templates/`](../../templates/) | Service scaffolds |
| [`modules/`](../../modules/) | Terraform modules used by service `infra/` |
| [`platform/bootstrap/`](../../platform/bootstrap/) | One-time WIF + IAM setup |

---

## 5. When to use CLI alone

- You prefer the terminal
- You want `shop publish` as a single publish command
- You already know the paved road

For first-time guided setup, see [05-journey-wizard.md](./05-journey-wizard.md) (bash, Python, PowerShell, or Streamlit wizard). For AI in Claude, see [08-journey-mcp.md](./08-journey-mcp.md).

Full publish, bootstrap, and teardown require a live authenticated sandbox — see [sandbox-env.md](../environments/sandbox-env.md).
