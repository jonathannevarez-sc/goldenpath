# Tests

Automated tests for the **goldenpath platform repository** — not for scaffolded service repos.

Service templates carry their own tests under `templates/*/tests/`; those ship with generated projects.

## Enterprise test pyramid

Golden Path uses a **two-tier** model suitable for customer-facing enterprise delivery:

| Tier | When | Gate | What it proves |
|------|------|------|----------------|
| **Tier 1 — Contract** | Every PR (`tests.yml`) | **Blocks merge** | Validators, scaffold integrity, deploy-spine preflight, MCP guards, wizard units |
| **Tier 2 — Integration** | Release tags + manual (`integration-tests.yml`) | **Blocks release** | Live `shop publish` → `shop verify` on enterprise sandbox (GitHub + Cloud Run) |

Tier 1 runs without cloud credentials. Tier 2 requires sandbox secrets configured in GitHub — see [Release acceptance](#release-acceptance).

## Quick start

```bash
# Tier 1 — required on every change
./tests/run-all-tests.sh

# Tier 2 — required before customer-facing release (sandbox credentials)
INTEGRATION_TEST_ENABLED=1 \
SHOP_GITHUB_ORG=... SHOP_GCP_DEV_PROJECT=... GCP_REGION=... GH_TOKEN=... \
  ./tests/run-integration-tests.sh
```

## Test suites (Tier 1)

| Suite | Framework | Entry point | What it covers |
|-------|-----------|-------------|----------------|
| Bash | Custom (`bash/lib/assert.sh`) | `tests/bash/run-bash-tests.sh` | Shell libs, launchers, `cli/shop`, deploy spine contracts |
| Python | pytest | `pytest tests -m "not integration"` | `wizard_defaults`, `goldenpath_ops`, MCP modules |
| PowerShell | Pester 5+ | `pwsh ./tests/Run-SetupWizardTests.ps1` | `scripts/setup/goldenpath-setup.ps1` validation/config |

### Bash tests (`tests/bash/`)

| File | Target |
|------|--------|
| `test_load_config.sh` | `scripts/lib/load-config.sh` |
| `test_scaffold_tokens.sh` | `scripts/lib/scaffold-tokens.sh` |
| `test_teardown_safety.sh` | `scripts/lib/teardown-safety.sh` (bash 3.2+) |
| `test_wizard_ops.sh` | `scripts/setup/goldenpath_setup_ops.sh` |
| `test_wizard_parity.sh` | PS / bash / Python wizard menu + module parity (static) |
| `test_launchers.sh` | `scripts/goldenpath-setup*.sh` |
| `test_shop_cli.sh` | `cli/shop` (`list`, usage, `new --dry-run`) |
| `test_shop_config.sh` | `cli/shop config set/show` roundtrip |
| `test_shop_scaffold.sh` | `cli/shop new` — all catalog templates, token-free output |
| `test_shop_publish_guards.sh` | `cli/shop publish` preflight (no live GitHub/GCP) |
| `test_shop_doctor.sh` | `cli/shop doctor` on scaffolded services |
| `test_verify_deployment.sh` | `verify-deployment.sh` with mocked gcloud/curl |
| `test_show_deployment_summary.sh` | `show_deployment_summary` health gate (publish/verify tail) |
| `test_wif_credentials.sh` | `scripts/lib/wif-credentials.sh` (terraform + gcloud fallback) |
| `test_wif_trust.sh` | `scripts/lib/wif-trust-repo.sh` with mocked gcloud |
| `test_check_repo_hygiene.sh` | `scripts/check-repo-hygiene.sh` |

### Python tests (`tests/test_*.py`)

- `test_wizard_defaults.py` — env parsing, merge, CLI flags
- `test_goldenpath_ops.py` — validators, WIF, config I/O
- `test_goldenpath_ops_helpers.py` — catalog, template hints, service paths, display-name clamp, token repair
- `test_goldenpath_dryrun.py` — wizard dry-run audit structure
- `test_mcp_*.py` — MCP validate, content, config, auth, audit
- `test_mcp_gcp.py` — GCP helper parsing, deploy status, service config (mocked gcloud)
- `test_mcp_gcp_adc.py` — ADC / `run_v2` client path (mocked)
- `test_catalog_schema.py` — `templates/catalog.json` schema + template directory parity
- `test_mcp_github_ops.py` — workflow dispatch errors (mocked)
- `test_mcp_server_tools.py` — `scaffold_service`, `trigger_deploy` guards
- `test_validator_parity.py` — Python vs bash project ID validators

Integration tests live under `tests/integration/` and are excluded from default pytest (`-m "not integration"`).

First run creates `tests/.venv` and installs `tests/requirements-test.txt` plus editable `mcp/`.

### Pester tests (`goldenpath-setup.tests.ps1`)

Unit tests for PowerShell wizard validation, config roundtrip, WIF checks, and `--help` CLI surface. Uses `$TestDrive` — never touches your real `.goldenpath-setup.local.json`.

```powershell
pwsh ./tests/Run-SetupWizardTests.ps1
pwsh ./tests/Run-SetupWizardTests.ps1 -Detailed
pwsh ./tests/Run-SetupWizardTests.ps1 -NoCoverage
pwsh ./tests/bootstrap-module.tests.ps1
pwsh ./tests/ps-wizard-modules.smoke.ps1
```

## CI

| Workflow | Tier | Trigger |
|----------|------|---------|
| `.github/workflows/tests.yml` | 1 | Every PR / push to `main` |
| `.github/workflows/integration-tests.yml` | 2 | Release tags `v*` + `workflow_dispatch` |

## Release acceptance

Before promoting a **customer-facing** build:

1. Tier 1 green on `main`
2. Tier 2 green on the release tag (sandbox project, WIF, `GH_TOKEN`)
3. Platform hygiene: `./scripts/check-repo-hygiene.sh`

Configure GitHub **environment** `goldenpath-sandbox` with:

- `GCP_SANDBOX_PROJECT`, `GCP_WIF_PROVIDER`, `GCP_WIF_SERVICE_ACCOUNT`
- `GITHUB_ORG`, `GITHUB_TOKEN`
- Optional variable `GCP_REGION` (default `us-central1`)

## Pre-release checklist (Tier 1 spot checks)

| Check | Command |
|-------|---------|
| All templates scaffold clean | `bash tests/bash/test_shop_scaffold.sh` |
| Publish preflight | `bash tests/bash/test_shop_publish_guards.sh` |
| Doctor diagnostics | `bash tests/bash/test_shop_doctor.sh` |
| Health verify contract | `bash tests/bash/test_verify_deployment.sh` |
| Teardown safety | `bash tests/bash/test_teardown_safety.sh` |
| Skill path traversal | `pytest tests/test_mcp_content.py -k traversal` |
| MCP write-tool gates | `pytest tests/test_mcp_server_tools.py` |

## Out of Tier 1 scope (separate tracks)

| Area | Track |
|------|-------|
| Streamlit UI click paths | Manual QA or dedicated UI automation backlog |
| Interactive wizard menus | Covered by Pester validators + Tier 2 publish path |
| `platform/bootstrap` terraform apply | Tier 2 sandbox bootstrap (enterprise runbook) |

## `templates/*/tests/` — not this directory

| Template | Test file | Runner |
|----------|-----------|--------|
| `fastapi` | `tests/test_health.py` | `pytest -q` |
| `streamlit` | `tests/test_app.py` | `pytest -q` |
| `express` | `tests/health.test.js` | `node --test` |
| `nextjs` | `tests/health.test.mjs` | `node --test` |
| `react-spa` | `tests/smoke.test.js` | `node --test` |
| `svelte-spa` | `tests/smoke.test.js` | `node --test` |