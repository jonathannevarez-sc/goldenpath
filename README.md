# Golden Path

Enterprise-agnostic platform for building and deploying containerized services to GCP. No org-specific values are hardcoded — every enterprise configures their own GCP account via `config/enterprise.env`.

**Platform repo, not your app.** `shop new` copies a template into a **separate service repo** (sibling directory or its own GitHub repo). See [docs/repository-guide.md](./docs/repository-guide.md) for the full map.

## Quick start

### 1. Configure your enterprise

```bash
cp config/enterprise.env.example config/enterprise.env
$EDITOR config/enterprise.env   # billing, projects, GitHub org, region
```

### 2. Authenticate to GCP

```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project YOUR_SANDBOX_OR_DEV_PROJECT
```

### 3. Bootstrap (pick one)

**Enterprise** — dev + prod projects, long-lived (typical production path):

```bash
cp platform/bootstrap/terraform.tfvars.example platform/bootstrap/terraform.tfvars
# Edit dev_project_id, prod_project_id, github_org (personal_test = false)
cd platform/bootstrap && terraform init && terraform apply
```

**Sandbox** — disposable single project (`personal_test = true`):

```bash
./scripts/standup-teardown-env.sh --yes
```

Enterprises bootstrap once and rarely tear down. Teardown scripts are **sandbox-only** — see [Sandbox teardown](#sandbox-teardown).

### 4. Scaffold and deploy a service

Scaffold **outside** this repo (`--output ..` from repo root):

**CLI path:**

```bash
shop config init --github-org YOUR_ORG --gcp-dev YOUR_DEV_PROJECT --gcp-prod YOUR_PROD_PROJECT
shop new my-service --template nextjs --output ..
shop publish ../my-service
```

`shop publish` creates a **public** GitHub repo and fails if post-deploy health checks fail. For **private** repos, use the wizard publish path (menu **7**).

**Wizard path** (no PowerShell required):

```bash
./scripts/goldenpath-setup-bash.sh    # or: -py.sh, -ui.sh, or goldenpath-setup.sh (auto)
```

Service repos call the reusable workflow (pin from `GOLDENPATH_VERSION` in `enterprise.env`):

```yaml
uses: YOUR_ORG/goldenpath/.github/workflows/deploy.yml@v0.3.8
```

## Repository layout

```
goldenpath/
├── config/                      # enterprise.env (gitignored) + example
├── .github/workflows/           # Reusable deploy.yml, tests.yml, MCP deploy
├── platform/bootstrap/          # One-time GCP + WIF bootstrap
├── modules/                     # Shared Terraform modules
├── templates/                   # 6 service scaffolds ({{TOKEN}} placeholders)
├── cli/shop                     # Bash CLI
├── scripts/
│   ├── goldenpath-setup.sh      # Unified wizard launcher (auto backend)
│   ├── goldenpath-setup-{bash,py,ps,ui}.sh
│   ├── lib/                     # load-config, scaffold-tokens, wif-*, verify-deployment
│   ├── setup/                   # Wizard (PS, bash, Python, Streamlit)
│   ├── standup-teardown-env.sh  # Sandbox standup
│   └── teardown-personal-test.sh # Sandbox teardown only
├── mcp/                         # MCP server (stdio + hosted HTTP)
├── skills/                      # 6 official MCP skills
└── tests/                       # Tier 1 contract + Tier 2 integration tests
```

## Pick your path

| Path | Start here |
|------|------------|
| **CLI** | `shop config init` → `shop new … --output ..` → `shop publish ../<name>` |
| **Wizard** | `./scripts/goldenpath-setup.sh` (auto) or `-bash.sh` / `-py.sh` / `-ui.sh` |
| **MCP (Claude)** | [mcp/guide.md](./mcp/guide.md) · [mcp/README.md](./mcp/README.md) |

Do not mix CLI and wizard config files. See [docs/getting-started/02-pick-your-path.md](./docs/getting-started/02-pick-your-path.md).

| Path | Config file |
|------|-------------|
| CLI | `.goldenpath-cli.local.json` |
| Wizard | `.goldenpath-setup.local.json` |

## Setup wizard backends

All backends share the same 15-option menu and `.goldenpath-setup.local.json`. Defaults come from `config/enterprise.env`. Scaffold, publish, doctor, and upgrade pins share `scripts/setup/goldenpath_ops.py`.

| Backend | Command | Needs |
|---------|---------|-------|
| **Auto** | `./scripts/goldenpath-setup.sh` | `pwsh` if available, else bash |
| **Bash** | `./scripts/goldenpath-setup-bash.sh` | bash, gcloud, terraform, gh |
| **Python** | `./scripts/goldenpath-setup-py.sh` | python3, gcloud, terraform, gh |
| **PowerShell** | `./scripts/goldenpath-setup-ps.sh` | pwsh |
| **Streamlit** | `./scripts/goldenpath-setup-ui.sh` | streamlit; pwsh only for bootstrap / verify / teardown |

Full reference: [docs/getting-started/07-setup-wizard-usage.md](./docs/getting-started/07-setup-wizard-usage.md)

## Configuration reference

All enterprise values live in `config/enterprise.env`:

| Variable | Purpose |
|----------|---------|
| `PARENT_PROJECT_ID` | Billing anchor (never deploy here; list in `PROTECTED_PROJECTS`) |
| `BILLING_ACCOUNT_ID` | GCP billing account |
| `GCP_DEV_PROJECT` / `GCP_PROD_PROJECT` | Environment projects |
| `GCP_SANDBOX_PROJECT` | Isolated test project |
| `GITHUB_ORG` / `PLATFORM_REPO` | GitHub + WIF trust |
| `GOLDENPATH_VERSION` | Tag for reusable deploy workflows |
| `PROTECTED_PROJECTS` | Projects teardown must never delete |
| `ALLOWED_TEARDOWN_PROJECTS` | Optional allowlist for sandbox project delete |

Override config path: `export GOLDENPATH_CONFIG=/path/to/custom.env`

Details: [config/README.md](./config/README.md)

## MCP skills

Six official skills served via MCP (`goldenpath://skills/{name}/SKILL.md`):

| Skill | Purpose |
|-------|---------|
| `goldenpath-setup-wizard` | Full wizard onboarding playbook |
| `scaffold-shop-service` | Template selection and scaffolding |
| `deploy-to-shop-gcp` | Deploy troubleshooting |
| `shop-terraform-conventions` | Safe Terraform extensions |
| `shop-observability` | Logs, metrics, alerts |
| `test-coverage-gap-analysis` | Platform test gap audit playbook |

Catalog: [skills/README.md](./skills/README.md)

## Tests

| Tier | When | Command |
|------|------|---------|
| **1 — Contract** | Every PR | `./tests/run-all-tests.sh` |
| **2 — Integration** | Release tags | `./tests/run-integration-tests.sh` (sandbox credentials) |

Details: [tests/README.md](./tests/README.md)

## Sandbox teardown

For **disposable sandboxes only** (`personal_test = true` in `platform/bootstrap/terraform.tfvars`). Not used on the enterprise bootstrap-once path.

```bash
# Destroy bootstrap resources (WIF, AR, etc.) — project remains
./scripts/teardown-personal-test.sh --yes

# Also delete the GCP project (irreversible)
./scripts/teardown-personal-test.sh --delete-project YOUR_GCP_SANDBOX_PROJECT --yes
```

Projects in `PROTECTED_PROJECTS` are blocked on `--delete-project`. `--yes` only skips confirmation prompts.

## Documentation

| Doc | Audience |
|-----|----------|
| [docs/readme.md](./docs/readme.md) | Full documentation index |
| [docs/repository-guide.md](./docs/repository-guide.md) | Every folder and file |
| [docs/getting-started/01-start-here.md](./docs/getting-started/01-start-here.md) | Entry point |
| [docs/platform/problem-statement.md](./docs/platform/problem-statement.md) | Problem definition and evidence |
| [mcp/guide.md](./mcp/guide.md) | MCP overview (local vs Cloud Run) |
| [docs/platform/architecture.md](./docs/platform/architecture.md) | Architecture diagrams |
| [cli/README.md](./cli/README.md) | `shop` CLI reference |
| [skills/README.md](./skills/README.md) | MCP skills catalog |
| [tests/README.md](./tests/README.md) | Test pyramid and CI gates |

**Repo hygiene:** `./scripts/check-repo-hygiene.sh` · **Layout explain:** `./scripts/check-repo-hygiene.sh --explain`
