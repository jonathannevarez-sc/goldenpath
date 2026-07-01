# 10. Shell scripts — what to run, when, and why

**Getting started · Doc 10 of 10** · [Index](./readme.md)

Golden Path ships **bash scripts** for GCP bootstrap, the setup wizard, MCP deploy, and shared helpers. The **`shop` CLI** (`cli/shop`) is also a shell script — but it uses a **separate config file** from the wizard.

> **Replace placeholders:** `YOUR_ORG`, `YOUR_GCP_SANDBOX_PROJECT` — see [`config/enterprise.env`](../../config/enterprise.env).

---

## Two shell entry points (do not mix config)

| | **`cli/shop`** | **Setup wizard scripts** |
|---|----------------|--------------------------|
| **Run** | `./cli/shop` or `export PATH="$PWD/cli:$PATH"` | `./scripts/goldenpath-setup.sh` (or `-bash`, `-py`, `-ps`, `-ui`) |
| **Config** | `.goldenpath-cli.local.json` | `.goldenpath-setup.local.json` |
| **Best for** | Fast terminal flow: `new` → `publish` → `verify` | Guided menu: bootstrap, scaffold, publish, teardown |
| **Guide** | [04-journey-cli.md](./04-journey-cli.md) | [05-journey-wizard.md](./05-journey-wizard.md) |

Everything else under `scripts/` supports one of those paths or platform ops (env, deploy, lib).

---

## How `scripts/` is organized

**Rule:** Files at `scripts/*.sh` are **launchers** (stable paths in docs). Logic lives in subfolders.

```
scripts/
├── goldenpath-setup.sh              ← wizard router (auto: pwsh → ps, else bash)
├── goldenpath-setup-{bash,py,ps,ui}.sh
├── standup-teardown-env.sh          → env/
├── teardown-personal-test.sh        → env/
├── deploy-mcp-cloudrun.sh           → deploy/
├── check-repo-hygiene.sh            platform layout check
├── setup/                           wizard implementations
├── env/                             GCP project lifecycle
├── deploy/                          MCP Cloud Run
└── lib/                             shared helpers (sourced, not run directly)
```

**Why it looks like duplicates:** `goldenpath-setup.sh` and `setup/goldenpath_setup.sh` are not copies — the top-level file only routes to bash, Python, PowerShell, or Streamlit backends. Same menu, same saved settings, different runtime.

```bash
./scripts/check-repo-hygiene.sh --explain   # full launcher ↔ implementation map
```

---

## Before any script

### 1. Enterprise config (required)

```bash
cd goldenpath
cp config/enterprise.env.example config/enterprise.env
$EDITOR config/enterprise.env
```

Standup and wizard scripts read this file (or `GOLDENPATH_CONFIG` if you override the path).

| Variable | Why scripts need it |
|----------|---------------------|
| `PARENT_PROJECT_ID` | Billing anchor — never deploy here |
| `BILLING_ACCOUNT_ID` | Link sandbox project billing |
| `GITHUB_ORG` | Bootstrap + publish |
| `GCP_SANDBOX_PROJECT` | Default sandbox project ID |
| `PROTECTED_PROJECTS` | Teardown safety blocklist |

Full list: [`config/README.md`](../../config/README.md).

### 2. Auth (for GCP scripts)

```bash
gcloud auth login
gcloud auth application-default login
gh auth login    # for publish / WIF
```

### 3. Run from repo root

Unless noted, invoke scripts with `./scripts/...` from the **goldenpath** repo root.

---

## Scripts by job

### Bootstrap & teardown (`env/`)

| Script | What it does |
|--------|----------------|
| [`standup-teardown-env.sh`](../../scripts/env/standup-teardown-env.sh) | Create/link sandbox GCP project, run `platform/bootstrap` Terraform |
| [`teardown-personal-test.sh`](../../scripts/env/teardown-personal-test.sh) | **Sandbox only** (`personal_test = true`): destroy bootstrap resources; add `--delete-project` to remove the GCP project |

**Launcher paths (same scripts):**

```bash
./scripts/standup-teardown-env.sh
./scripts/teardown-personal-test.sh
```

**Common standup:**

```bash
./scripts/standup-teardown-env.sh --yes --skip-labels
```

Requires `ARTIFACT_REGISTRY_REPO` in [`config/enterprise.env`](../../config/enterprise.env) — standup writes `artifact_registry_id` into `platform/bootstrap/terraform.tfvars`.

| Flag | Effect |
|------|--------|
| `--yes` | Skip confirmation before `terraform apply` |
| `--skip-labels` | Skip `gcloud alpha` project labels (avoids hangs) |
| `--project-id <id>` | Override `GCP_SANDBOX_PROJECT` |
| `--skip-apply` | Create project only; no Terraform |

**Teardown** is for sandboxes only — enterprises bootstrap once and rarely use it. `--yes` skips prompts; it does **not** delete the GCP project unless you pass `--delete-project`. Project delete respects `PROTECTED_PROJECTS` and optional `ALLOWED_TEARDOWN_PROJECTS` — see [`sandbox-env.md`](../environments/sandbox-env.md).

Wizard equivalent: menu **3** (bootstrap), menu **13** (tear down).

---

### Setup wizard (`setup/` + launchers)

Interactive onboarding — menu options 1–15, saved to `.goldenpath-setup.local.json`.

| You have… | Run |
|-----------|-----|
| `pwsh` installed | `./scripts/goldenpath-setup.sh` (auto picks PowerShell) |
| No PowerShell | `./scripts/goldenpath-setup-bash.sh` |
| Prefer Python | `./scripts/goldenpath-setup-py.sh` |
| Browser UI | `./scripts/goldenpath-setup-ui.sh` (needs `streamlit`) |

```bash
./scripts/goldenpath-setup.sh --help
./scripts/goldenpath-setup.sh --dryrun         # read-only audit (menu 15)
./scripts/goldenpath-setup.sh --backend bash    # force backend
./scripts/goldenpath-setup.sh --wizard          # guided steps 1–6
pwsh ./scripts/setup/goldenpath-setup.ps1 -h   # comprehensive PS help
```

| Backend | Implementation |
|---------|----------------|
| bash | `setup/goldenpath_setup.sh` → `goldenpath_setup_ops.sh` → `goldenpath_ops_cli.py` |
| Python | `setup/goldenpath_setup.py` → `goldenpath_ops.py` |
| PowerShell | `setup/goldenpath-setup.ps1` + `setup/modules/*.ps1` + `OpsCli.ps1` |
| Streamlit | `setup/goldenpath_setup_app.py` → `goldenpath_ops.py` (scaffold/publish/doctor) |
| shop CLI | `cli/shop` → `goldenpath_ops_cli.py` (separate config file) |

**Docs:** [05-journey-wizard.md](./05-journey-wizard.md) (journey) · [07-setup-wizard-usage.md](./07-setup-wizard-usage.md) (menu reference)

---

### MCP deploy (`deploy/`)

| Script | What it does |
|--------|----------------|
| [`deploy-mcp-cloudrun.sh`](../../scripts/deploy/deploy-mcp-cloudrun.sh) | Build MCP image, push to Artifact Registry, deploy to Cloud Run |
| [`import-mcp-infra-state.sh`](../../scripts/deploy/import-mcp-infra-state.sh) | Import existing MCP infra into Terraform state |

```bash
./scripts/deploy-mcp-cloudrun.sh
```

Hosted MCP guide: [`mcp/guide.md`](../../mcp/guide.md).

---

### Platform hygiene

| Script | What it does |
|--------|----------------|
| [`check-repo-hygiene.sh`](../../scripts/check-repo-hygiene.sh) | Verify platform repo layout (no stray service files at root, wizard files present) |

```bash
./scripts/check-repo-hygiene.sh           # health check
./scripts/check-repo-hygiene.sh --explain # why launchers exist
```

Run this if you accidentally scaffolded a service **inside** the platform repo.

---

### Library scripts (`lib/`) — do not run directly

Sourced by `shop`, wizard ops, and env scripts:

| File | Role |
|------|------|
| `load-config.sh` | Load `enterprise.env`, export `SHOP_*` mirrors |
| `wizard_defaults.py` | Wizard defaults + `--merge` / `--shell-exports` for bash wizard |
| `scaffold-tokens.sh` | Replace `{{SERVICE_NAME}}`, `{{GCP_DEV_PROJECT}}`, etc. in templates |
| `wif-trust-repo.sh` | Per-repo Workload Identity Federation IAM |
| `verify-deployment.sh` | Poll Cloud Run URL + health after publish |
| `teardown-safety.sh` | Block deletes of protected projects |

---

## Common workflows

### A. CLI path (scripts + `shop`)

```bash
cp config/enterprise.env.example config/enterprise.env && $EDITOR config/enterprise.env

./scripts/standup-teardown-env.sh --yes --skip-labels

export PATH="$PWD/cli:$PATH"
shop config init --github-org YOUR_ORG --gcp-dev YOUR_GCP_SANDBOX_PROJECT
shop new my-app --template fastapi --output ..
shop publish ../my-app
shop verify ../my-app
```

Full walkthrough: [03-quickstart.md](./03-quickstart.md) · [04-journey-cli.md](./04-journey-cli.md).

### B. Wizard path (scripts only)

```bash
cp config/enterprise.env.example config/enterprise.env && $EDITOR config/enterprise.env

./scripts/goldenpath-setup-bash.sh
# Menu 3 → bootstrap
# Menu 6 → scaffold
# Menu 7 → publish
# Menu 10 → generate MCP client config
```

Walkthrough: [05-journey-wizard.md](./05-journey-wizard.md).

### C. MCP + scripts

```bash
./scripts/standup-teardown-env.sh --yes    # bootstrap (MCP has no bootstrap tool)
# … local MCP venv + client config (see mcp/guide.md)
shop publish ../my-service               # publish is always terminal/wizard
./scripts/deploy-mcp-cloudrun.sh         # optional hosted MCP
```

### D. Clean up sandbox

```bash
# Destroy bootstrap resources (project remains)
./scripts/teardown-personal-test.sh --yes

# Also delete the GCP project (irreversible)
./scripts/teardown-personal-test.sh --delete-project YOUR_GCP_SANDBOX_PROJECT --yes

# or wizard menu 13
```

---

## What shell scripts do **not** do

| Task | Use instead |
|------|-------------|
| Service app code / Dockerfile edits | Your scaffolded **service repo** |
| Per-service Terraform in prod | Service repo `infra/` + GitHub Actions |
| Replace `shop` for publish on CLI path | `shop publish` (wizard menu **7** on wizard path) |
| Mix wizard + CLI config | Pick one path — [02-pick-your-path.md](./02-pick-your-path.md) |
| Install `pwsh` for you | Install PowerShell yourself or use `-bash` / `-py` |

---

## Quick reference

| I want to… | Command |
|------------|---------|
| Create sandbox GCP + bootstrap | `./scripts/standup-teardown-env.sh --yes` |
| Interactive setup menu | `./scripts/goldenpath-setup.sh` or `-bash.sh` |
| Scaffold (CLI) | `shop new <name> --output ..` |
| Publish (CLI) | `shop publish <dir>` |
| Check deploy health | `shop verify <dir>` |
| Deploy MCP to Cloud Run | `./scripts/deploy-mcp-cloudrun.sh` |
| Destroy sandbox bootstrap | `./scripts/teardown-personal-test.sh --yes` |
| Delete sandbox GCP project | `./scripts/teardown-personal-test.sh --delete-project <id> --yes` |
| Check repo layout | `./scripts/check-repo-hygiene.sh` |
| Understand script layout | `./scripts/check-repo-hygiene.sh --explain` |

---

## Troubleshooting

| Problem | Check |
|---------|--------|
| `missing config/enterprise.env` | `cp config/enterprise.env.example config/enterprise.env` |
| `PARENT_PROJECT_ID required` | Edit `enterprise.env` — standup cannot run without billing anchor |
| Wizard vs CLI settings conflict | Two config files — use only one path |
| `protected project` on teardown | Project listed in `PROTECTED_PROJECTS` |
| Service files at platform root | `./scripts/check-repo-hygiene.sh` — move scaffold outside `goldenpath` |
| No `pwsh` | `./scripts/goldenpath-setup-bash.sh` or `-py.sh` |

---

## Related docs

| Doc | Topic |
|-----|-------|
| [scripts/README.md](../../scripts/README.md) | Full scripts tree (contributors) |
| [cli/README.md](../../cli/README.md) | `shop` commands and flags |
| [02-pick-your-path.md](./02-pick-your-path.md) | CLI vs wizard vs MCP |
| [sandbox-env.md](../environments/sandbox-env.md) | Sandbox project lifecycle |
| [mcp/guide.md](../../mcp/guide.md) | MCP local vs Cloud Run |