# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

**Platform repo, not an application.** Golden Path is an enterprise developer platform that scaffolds, deploys, and manages containerized services on GCP. The platform repo provides templates, a CLI, setup wizards, an MCP server, and shared GitHub Actions workflows. Actual services live in separate repos created by `shop new`.

No org-specific values are hardcoded anywhere — every enterprise configures via `config/enterprise.env`.

## Commands

### Tests (Tier 1 — run on every change)

```bash
# All three test suites
./tests/run-all-tests.sh

# Individual suites
bash tests/bash/run-bash-tests.sh
python3 -m venv tests/.venv && tests/.venv/bin/pip install -q -r tests/requirements-test.txt -e mcp
tests/.venv/bin/python -m pytest tests -q --tb=short
pwsh ./tests/Run-SetupWizardTests.ps1 -NoCoverage

# Single pytest test file
tests/.venv/bin/python -m pytest tests/test_mcp_server_tools.py -q

# Single bash test file
bash tests/bash/test_shop_cli.sh

# Integration tests (Tier 2 — requires sandbox credentials)
INTEGRATION_TEST_ENABLED=1 SHOP_GITHUB_ORG=... SHOP_GCP_DEV_PROJECT=... GCP_REGION=... GH_TOKEN=... \
  ./tests/run-integration-tests.sh
```

### MCP server (local stdio)

```bash
cd mcp
python3 -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export GOLDENPATH_ROOT="$(cd .. && pwd)"
python -m goldenpath_mcp
```

### MCP server (Cloud Run / hosted HTTP)

```bash
./scripts/deploy-mcp-cloudrun.sh
```

### CLI (`shop`)

```bash
# Add to PATH for convenience
export PATH="$PWD/cli:$PATH"

shop list                                    # show service templates
shop config init --github-org ORG --gcp-dev DEV --gcp-prod PROD
shop new my-service --template nextjs --output ..   # scaffold OUTSIDE this repo
shop publish ../my-service                   # create GitHub repo + deploy
shop verify ../my-service
shop doctor ../my-service
```

### Setup wizards

```bash
./scripts/goldenpath-setup.sh          # auto-picks best backend
./scripts/goldenpath-setup-bash.sh     # bash
./scripts/goldenpath-setup-py.sh       # Python
./scripts/goldenpath-setup-ps.sh       # PowerShell
./scripts/goldenpath-setup-ui.sh       # Streamlit
```

### Platform hygiene

```bash
./scripts/check-repo-hygiene.sh
./scripts/check-repo-hygiene.sh --explain
```

## Architecture

### Repository layout

```
goldenpath/
├── cli/shop                    # Bash CLI (single file, all subcommands)
├── config/                     # enterprise.env (gitignored) + examples
├── mcp/                        # MCP server (Python, FastMCP)
│   └── goldenpath_mcp/         # server.py, config.py, gcp.py, github_ops.py, ...
├── modules/                    # Shared Terraform modules (cloud-run, artifact-registry, ...)
├── platform/bootstrap/         # One-time GCP + WIF Terraform bootstrap
├── scripts/
│   ├── lib/                    # load-config.sh, scaffold-tokens.sh, wif-*.sh, verify-deployment.sh
│   └── setup/                  # goldenpath-setup.ps1, goldenpath_ops.py, goldenpath_setup_ops.sh
├── skills/                     # 6 MCP SKILL.md playbooks (read-only; served via MCP)
├── templates/                  # 6 service scaffold templates ({{TOKEN}} placeholders)
│   └── catalog.json            # Template registry
└── tests/                      # Tier 1 contract + Tier 2 integration tests
    ├── bash/                   # Shell lib tests
    ├── integration/            # Live sandbox tests
    └── test_*.py               # pytest (MCP, wizard, ops, catalog schema)
```

### Service templates

Six templates in `templates/`, each using `{{TOKEN}}` placeholders replaced at scaffold time:

| Template | Runtime | Port | Health path |
|----------|---------|------|-------------|
| `nextjs` (default) | node | 3000 | `/api/health` |
| `fastapi` | python | 8000 | `/api/health` |
| `express` | node | 3000 | `/api/health` |
| `streamlit` | python | 8501 | `/_stcore/health` |
| `react-spa` | docker | 8080 | `/health` |
| `svelte-spa` | docker | 8080 | `/health` |

### MCP server

The MCP server (`mcp/goldenpath_mcp/`) exposes the platform over the Model Context Protocol:

- **Resources** (`goldenpath://docs/{path}`, `goldenpath://skills/{name}/SKILL.md`, `goldenpath://meta/version`) — read-only content from the repo
- **Read tools** — `list_templates`, `list_skills`, `get_skill`, `list_services`, `get_deploy_status`, `get_service_config`, `get_cost_estimate`
- **Write tools (audited)** — `scaffold_service` (runs `cli/shop new`), `trigger_deploy` (requires `confirm=true`)

Transport is `stdio` locally and `streamable-http` on Cloud Run. The `ContentStore` class reads skills and docs from `GOLDENPATH_ROOT` at runtime — never baked into the server.

### GitHub Actions

- `.github/workflows/deploy.yml` — **reusable only** (`workflow_call`); no `push:` trigger on the platform repo itself. Service repos call this with `uses: ORG/goldenpath/.github/workflows/deploy.yml@GOLDENPATH_VERSION`.
- `.github/workflows/tests.yml` — Tier 1 (bash + pytest + Pester), runs on every PR.
- `.github/workflows/deploy-mcp.yml` — builds and deploys the hosted MCP server to Cloud Run.
- `.github/workflows/integration-tests.yml` — Tier 2, triggered on release tags.

`GOLDENPATH_VERSION` in `config/enterprise.env` controls which tag service repos pin.

### CLI vs wizard — config files are separate, do not mix

| Path | Config file | Scaffold | Publish |
|------|-------------|---------|---------|
| `shop` CLI | `.goldenpath-cli.local.json` | `shop new` | `shop publish` (public repos only) |
| Wizard | `.goldenpath-setup.local.json` | menu 6 | menu 7 (respects visibility) |

### Test pyramid

| Tier | Framework | Command | Gate |
|------|-----------|---------|------|
| 1 — Bash | custom `assert.sh` | `bash tests/bash/run-bash-tests.sh` | Blocks merge |
| 1 — Python | pytest | `pytest tests -m "not integration"` | Blocks merge |
| 1 — PowerShell | Pester 5+ | `pwsh ./tests/Run-SetupWizardTests.ps1` | Blocks merge |
| 2 — Integration | bash + publish + verify | `./tests/run-integration-tests.sh` | Blocks release |

Tier 1 runs without cloud credentials. Tier 2 requires a live sandbox GCP project with WIF and GitHub secrets.

## Key rules

- **Scaffold outside this repo.** Always use `--output ..` with `shop new` or MCP `scaffold_service`. The platform repo and service repos are siblings, not nested.
- **`deploy.yml` must stay reusable.** Never add `push:` triggers to the platform workflow — `check-repo-hygiene.sh` enforces this.
- **All enterprise values come from `config/enterprise.env`.** Never hardcode GCP project IDs, GitHub orgs, billing accounts, or regions in templates, scripts, or Terraform.
- **MCP write tools are audited.** `scaffold_service` and `trigger_deploy` emit JSON audit lines to stderr via `audit.py`. `trigger_deploy` always requires `confirm=true`.
- **`shop publish` is not an MCP tool.** It runs in the terminal. Hosted Cloud Run MCP cannot scaffold to your local disk or publish repos.
