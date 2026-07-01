---
name: goldenpath-setup-wizard
phase: 2
description: >
  Run the Golden Path setup wizard end-to-end — bootstrap, WIF secrets,
  scaffold, publish, verify, doctor, teardown. Use when the user mentions
  goldenpath-setup.ps1, setup wizard, wizard menu, full guided setup,
  goldenpath-setup.sh, bootstrap sandbox, or .goldenpath-setup.local.json.
  Do NOT use for shop CLI path (.goldenpath-cli.local.json) or headless
  shop new/publish without wizard context.
distribution: mcp-resources
status: implemented
---

# Golden Path setup wizard

Interactive onboarding for **goldenpath** — from zero GCP bootstrap to a live Cloud Run service. Equivalent to all wizard backends (`goldenpath-setup.ps1`, `goldenpath_setup.sh`, `goldenpath_setup.py`, Streamlit UI).

## When to use

- User wants the **wizard path** (not `cli/shop`)
- User asks to bootstrap a sandbox, run setup wizard, or follow menu options 1–15
- User references `goldenpath-setup.ps1`, `.goldenpath-setup.local.json`, or sandbox teardown
- New user needs profile → bootstrap → WIF → scaffold → publish in order

## When NOT to use

- User chose **CLI path** → use `scaffold-shop-service` + `.goldenpath-cli.local.json`
- User only needs MCP tools with no local bootstrap → `08-journey-mcp.md` flow
- User already bootstrapped and only wants deploy help → `deploy-to-shop-gcp`

## Read first

- Resource: `goldenpath://docs/getting-started/07-setup-wizard-usage.md`
- Resource: `goldenpath://docs/getting-started/05-journey-wizard.md`
- Enterprise config: `config/enterprise.env` (copy from `config/enterprise.env.example`)
- Wizard state: `.goldenpath-setup.local.json` (gitignored, wizard-only)

**Never mix** wizard config with CLI config (`.goldenpath-cli.local.json`).

---

## Choose a backend

| Backend | Command | Needs |
|---------|---------|-------|
| **Auto** | `./scripts/goldenpath-setup.sh` | `pwsh` if available, else bash |
| **PowerShell** | `./scripts/goldenpath-setup-ps.sh` | `pwsh` |
| **Bash** | `./scripts/goldenpath-setup-bash.sh` | `bash`, gcloud, terraform, gh |
| **Python** | `./scripts/goldenpath-setup-py.sh` | `python3`, gcloud, terraform, gh |
| **Streamlit** (browser) | `./scripts/goldenpath-setup-ui.sh` | `streamlit`; `pwsh` only for bootstrap / verify / teardown |

Headless full wizard (no menu):

```bash
./scripts/goldenpath-setup.sh --wizard          # auto backend
./scripts/goldenpath-setup-bash.sh --wizard     # Bash
./scripts/goldenpath-setup-py.sh --wizard       # Python
```

Help: any launcher + `--help` · dry run: `--dryrun` or menu **15** · PS comprehensive help: `pwsh ./scripts/setup/goldenpath-setup.ps1 -h`

---

## Prerequisites (menu 2)

Required: `gcloud`, `terraform`, `git`, `gh`

Optional: `python3`, `docker`, `pwsh` (if using PowerShell backend)

Enterprise config before bootstrap:

```bash
cp config/enterprise.env.example config/enterprise.env
$EDITOR config/enterprise.env
```

Auth before bootstrap:

```bash
gcloud auth login
gcloud auth application-default login
gh auth login
```

Verify: `./scripts/check-repo-hygiene.sh` (platform repo layout only)

---

## GCP project profiles (menu 12)

Bootstrap, WIF, and wizard scaffold **must share the same project ID**.

| Profile | Use case | Disposable (menu 13) |
|---------|----------|----------------------|
| **sandbox** | Defaults from `config/enterprise.env` (`GCP_SANDBOX_PROJECT`) | yes |
| **sandbox** (new) | User picks new project ID, e.g. `gp-sandbox-20260616` | yes |
| **custom** | Existing GCP project | no (extra teardown confirm) |

**Project ID rules:** 6–30 chars, lowercase, start with letter, no `--`, not in `PROTECTED_PROJECTS`.

Default profile env: `config/enterprise.env`

---

## Menu map → agent actions

| # | Menu | Agent action |
|---|------|----------------|
| **1** | Full guided setup | Run `--wizard` launcher OR steps 12→2→3→4→5→6→7→10 in sequence |
| **2** | Prerequisites | Check tools + gcloud ADC; install missing CLIs |
| **3** | Bootstrap | Create/link project + `terraform apply` in `platform/bootstrap/` |
| **4** | WIF secrets | Read terraform outputs or gcloud IAM |
| **5** | Set GitHub secrets | `gh secret set GCP_WIF_PROVIDER` and `GCP_WIF_SERVICE_ACCOUNT` |
| **6** | Scaffold | Copy `templates/<template>/` outside repo; replace `{{TOKENS}}`; `git init -b main` |
| **7** | Publish | `gh repo create`, set secrets, WIF trust, `git push`, watch deploy workflow |
| **8** | Verify | Cloud Run URL + health path from template catalog |
| **9** | Doctor | Branch `main`, tfvars project match, GitHub secrets, no `{{TOKENS}}` in deploy.yml |
| **10** | MCP config | Write `mcp/claude-mcp.generated.json` |
| **11** | Status | `gcloud projects describe`, Artifact Registry, WIF, `gcloud run services list` |
| **12** | Edit settings | Update `.goldenpath-setup.local.json`; clear WIF if project changes |
| **13** | Teardown | `terraform destroy` + optional `gcloud projects delete` |
| **14** | Fresh start | Reset `.goldenpath-setup.local.json` to enterprise defaults |
| **15** | Dry run | Read-only audit via `goldenpath_dryrun.py` — no GCP/GitHub changes |

Shared ops: `goldenpath_ops.py` / `goldenpath_ops_cli.py` (scaffold, publish, doctor, upgrade pins).

---

## Bootstrap (menu 3)

From `config/enterprise.env`:

- `PARENT_PROJECT_ID`, `BILLING_ACCOUNT_ID` — project create + billing link
- `ARTIFACT_REGISTRY_REPO` — written to `platform/bootstrap/terraform.tfvars` as `artifact_registry_id`
- `GITHUB_ORG`, `PLATFORM_REPO` — WIF trust and tfvars

Standup/wizard generates tfvars and runs `terraform apply` in `platform/bootstrap/`.

Alternate script:

```bash
./scripts/standup-teardown-env.sh --yes --skip-labels
```

---

## Scaffold (menu 6)

- Output **outside** platform repo (default: parent of `goldenpath/`)
- Templates: `list_templates()` or `templates/catalog.json` (`nextjs` default)
- Token placeholders: `{{SERVICE_NAME}}`, `{{GITHUB_ORG}}`, `{{PLATFORM_REPO}}`, etc.

**Not** `shop new` — that is the CLI path.

---

## Publish (menu 7)

Reusable workflow: `YOUR_ORG/goldenpath/.github/workflows/deploy.yml@<GOLDENPATH_VERSION>`

1. Ensure `infra/dev.tfvars` `project_id` matches wizard project
2. `gh repo create` (match platform repo visibility)
3. Set WIF secrets (+ `GOLDENPATH_MODULE_TOKEN` if platform repo is private)
4. WIF trust: `scripts/lib/wif-trust-repo.sh <project> <org> <repo>`
5. `git push -u origin main`
6. `gh run watch` on `deploy.yml`

---

## Teardown (menu 13)

Sandbox only (`personal_test = true`). Enterprises bootstrap once and rarely tear down.

```bash
# Destroy bootstrap resources — GCP project remains
./scripts/teardown-personal-test.sh --yes

# Also delete the GCP project (irreversible)
./scripts/teardown-personal-test.sh --delete-project <project-id> --yes
```

Protected projects (`PROTECTED_PROJECTS` in `enterprise.env`) are blocked on `--delete-project`.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `pwsh: command not found` | Use `./scripts/goldenpath-setup-bash.sh` or `-py.sh` |
| Missing enterprise config | `cp config/enterprise.env.example config/enterprise.env` |
| Project ID rejected | Lowercase, 6–30 chars, not in `PROTECTED_PROJECTS` |
| WIF secrets empty | Bootstrap (3) before WIF (4) |
| Deploy workflow fails | Doctor (9); re-publish (7) |
| `project_id` mismatch | Re-scaffold after fixing project in menu 12 |
| Mixed CLI/wizard config | Use only `.goldenpath-setup.local.json` on wizard path |

---

## Implementation files

| File | Role |
|------|------|
| `scripts/goldenpath-setup.sh` | Unified launcher |
| `scripts/setup/goldenpath-setup.ps1` | PowerShell wizard |
| `scripts/setup/goldenpath_setup.sh` | Bash wizard |
| `scripts/setup/goldenpath_setup.py` | Python wizard |
| `scripts/setup/goldenpath_setup_app.py` | Streamlit UI |
| `scripts/setup/goldenpath_ops.py` | Shared scaffold / publish / doctor / upgrade |
| `scripts/setup/goldenpath_ops_cli.py` | CLI for bash wizard, `shop`, PS upgrade/doctor |
| `scripts/lib/wizard_defaults.py` | Defaults from `enterprise.env` |
| `scripts/setup/modules/*.ps1` | Bootstrap, Scaffold, Publish, Verify, OpsCli |

---

## Definition of done

- `config/enterprise.env` configured for the enterprise
- Bootstrap applied in chosen GCP project
- WIF secrets on platform repo (and service repo if scaffolded)
- Service scaffolded **outside** platform repo with matching `project_id`
- Push to `main` → dev deploy succeeds → health check passes
- Config saved in `.goldenpath-setup.local.json` for resume