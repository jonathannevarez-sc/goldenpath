# 7. Wizard — menu reference

**Getting started · Doc 7 of 10** · [Index](./readme.md) · **Primary wizard doc:** [05-journey-wizard.md](./05-journey-wizard.md)

Menu option lookup, typical flows, and troubleshooting for the setup wizard. Read **05** first for the end-to-end narrative; use **07** when you need option numbers or a specific flow spelled out.

Four terminal backends + Streamlit — identical menu (options 1–15):

| Backend | Command | Requires |
|---------|---------|----------|
| **Auto** (default) | `./scripts/goldenpath-setup.sh` | `pwsh` if available, else bash |
| **Bash** | `./scripts/goldenpath-setup-bash.sh` | `bash`, gcloud, terraform, gh, `python3` |
| **Python** | `./scripts/goldenpath-setup-py.sh` | `python3`, gcloud, terraform, gh |
| **PowerShell** | `./scripts/goldenpath-setup-ps.sh` | `pwsh` |
| **Streamlit web UI** | `./scripts/goldenpath-setup-ui.sh` | `streamlit`; `pwsh` only for bootstrap / verify / teardown |

**Streamlit-only users:** Full UI guide → [09-streamlit-setup-ui.md](./09-streamlit-setup-ui.md)

**Implementation:**

| File | Role |
|------|------|
| [`scripts/goldenpath-setup.sh`](../../scripts/goldenpath-setup.sh) | Unified launcher (`--backend auto\|bash\|py\|ps\|ui`) |
| [`scripts/setup/goldenpath_setup.sh`](../../scripts/setup/goldenpath_setup.sh) | Bash wizard (no PowerShell) |
| [`scripts/setup/goldenpath_setup.py`](../../scripts/setup/goldenpath_setup.py) | Python wizard (no PowerShell) |
| [`scripts/setup/goldenpath-setup.ps1`](../../scripts/setup/goldenpath-setup.ps1) | PowerShell wizard |
| [`scripts/setup/goldenpath_setup_app.py`](../../scripts/setup/goldenpath_setup_app.py) | Streamlit UI (13 pages) |
| [`scripts/setup/goldenpath_ops.py`](../../scripts/setup/goldenpath_ops.py) | Shared scaffold / publish / doctor / upgrade logic |
| [`scripts/setup/goldenpath_ops_cli.py`](../../scripts/setup/goldenpath_ops_cli.py) | CLI entry used by bash wizard, `shop`, and PS upgrade/doctor |
| [`scripts/setup/modules/`](../../scripts/setup/modules/) | Bootstrap, Scaffold, Publish, Verify, OpsCli modules |
| [`scripts/lib/wizard_defaults.py`](../../scripts/lib/wizard_defaults.py) | Defaults from `config/enterprise.env` |

**Parity:** Bash, Python, Streamlit, `shop`, and PowerShell all converge on `goldenpath_ops` for scaffold, publish, doctor, and platform-pin upgrades (`GOLDENPATH_VERSION` from `enterprise.env`, currently `v0.3.8`).

**Repo map:** [repository-guide.md](../repository-guide.md)  
**Do not mix** with CLI config — see [02-pick-your-path.md](./02-pick-your-path.md)

---

## 1. Configure enterprise settings

```bash
cp config/enterprise.env.example config/enterprise.env
$EDITOR config/enterprise.env
```

**Required** in `enterprise.env`: `PARENT_PROJECT_ID`, `BILLING_ACCOUNT_ID`, `GITHUB_ORG`. Other keys fall back to `enterprise.env.example` — see [`config/README.md`](../../config/README.md).

Wizard defaults (sandbox project, GitHub org, region) come from this file via [`scripts/lib/wizard_defaults.py`](../../scripts/lib/wizard_defaults.py).

---

## 2. Run the wizard

From the **goldenpath** repo root:

```bash
# Auto: PowerShell if pwsh exists, else bash
./scripts/goldenpath-setup.sh

# Explicit backend (no PowerShell required)
./scripts/goldenpath-setup-bash.sh
./scripts/goldenpath-setup-py.sh

# Streamlit web UI
./scripts/goldenpath-setup-ui.sh
```

### Launcher modes

| Command | What it does |
|---------|--------------|
| `./scripts/goldenpath-setup.sh` | Interactive menu (auto backend) |
| `./scripts/goldenpath-setup.sh --backend bash` | Bash wizard |
| `./scripts/goldenpath-setup.sh --backend py` | Python wizard |
| `./scripts/goldenpath-setup.sh --wizard` | Full guided setup (no menu) |
| `./scripts/goldenpath-setup.sh --dryrun` | Read-only audit (menu 15) — no GCP/GitHub changes |
| `./scripts/goldenpath-setup.sh --help` | Launcher usage |

PowerShell headless:

```bash
pwsh ./scripts/setup/goldenpath-setup.ps1 --wizard
pwsh ./scripts/setup/goldenpath-setup.ps1 --dryrun
pwsh ./scripts/setup/goldenpath-setup.ps1 -h    # comprehensive built-in help
```

---

## 3. GCP project — always prompted

Bootstrap, WIF secrets, and wizard scaffold (menu **6**) **must use the same project ID**.

The wizard prompts for project ID when you:

- Edit settings (option **12**)
- Run bootstrap (option **3**)
- Scaffold a service (option **6**)

Saved to `.goldenpath-setup.local.json`. The CLI uses a **separate** file: `.goldenpath-cli.local.json`.

Default profile: [`config/enterprise.env`](../../config/enterprise.env)

---

## 4. Choose your GCP project (menu option 12)

### 1) Sandbox (default)

- Project: `GCP_SANDBOX_PROJECT` from `config/enterprise.env`
- Preconfigured for your billing account
- Disposable — tear down with option **13**

### 2) New self-contained sandbox

**Use when you want your own isolated project you can delete later.**

1. Menu → **12) Edit settings**
2. Pick **New self-contained sandbox**
3. Enter a globally unique project ID, e.g. `my-org-gp-sandbox`
4. Menu → **3) Bootstrap GCP**

Wizard creates project, links billing, writes `terraform.tfvars`, runs Terraform.

When finished: menu **13** destroys resources and deletes the project.

**Project ID rules:** 6–30 chars, lowercase, start with letter, no protected names (`YOUR_BILLING_ANCHOR_PROJECT`, etc.)

### 3) Custom existing project

- Use a GCP project that already exists
- Teardown option **13** asks for extra confirmation

---

## 5. Menu reference

```
 1   Full guided setup (new users)
 2   Check prerequisites (gcloud, terraform, git, gh)
 3   Bootstrap GCP in your chosen project
 4   Show GitHub WIF secrets (Terraform or gcloud auto-detect)
 5   Set WIF secrets on a repo via gh
 6   Scaffold a new service (wizard — not shop CLI)
 7   Publish service to GitHub (repo + secrets + deploy)
 8   Verify deployment (health check)
 9   Doctor — diagnose deploy blockers
10   Generate Claude MCP config
11   Show current status
12   Edit settings — pick project profile / name
13   Tear down current sandbox project
14   Fresh start (reset local wizard state)
15   Dry run — read-only audit (no deploy / no changes)
 h   Help / usage (same as -h on PS backend)
 0   Exit
```

Streamlit UI mirrors these as 13 sidebar pages — see [09-streamlit-setup-ui.md](./09-streamlit-setup-ui.md) for the full page map and efficient workflows.

---

## 6. Typical flows

### New user — first time

```
./scripts/goldenpath-setup.sh
→ 1 (full guided setup)
→ pick profile
→ bootstrap runs
→ save WIF secrets
→ optional scaffold
→ optional MCP config (option 10)
```

### Your own disposable sandbox

```
./scripts/goldenpath-setup.sh
→ 12 → New self-contained sandbox → gp-mytest-2026
→ 3  → Bootstrap
→ 6  → Scaffold hello-golden
→ … push to GitHub, deploy …
→ 13 → Tear down when done
```

### Resume later

```
./scripts/goldenpath-setup.sh
→ 11 (current project + Cloud Run services)
→ 4  (WIF secrets again)
```

---

## 7. What gets saved

File: `.goldenpath-setup.local.json` (gitignored)

| Field | Example |
|-------|---------|
| `profile` | `sandbox` |
| `gcp_project` | `my-org-gp-sandbox` |
| `sandbox_disposable` | `true` |
| `github_org` | `YOUR_GITHUB_ORG` |
| `wif_provider` | `projects/.../providers/github-provider` |
| `last_service` | `hello-golden` |

---

## 8. Scripts the wizard calls

| Wizard step | Underlying script / module |
|-------------|---------------------------|
| Bootstrap | [`scripts/env/standup-teardown-env.sh`](../../scripts/env/standup-teardown-env.sh); bash/Python via ops; PS via `modules/Bootstrap.ps1` |
| Scaffold | `goldenpath_ops.scaffold()` — bash via `goldenpath_ops_cli.py`; Python/Streamlit import ops directly; PS via `Scaffold.ps1` + `OpsCli.ps1` upgrade |
| Publish | `goldenpath_ops.publish()` — same paths; PS orchestrates via `Publish.ps1` |
| Doctor / upgrade pins | `goldenpath_ops.service_doctor()` / `upgrade_platform_pins()` — shared across all backends |
| Verify | `goldenpath_ops.verify_deployment()` or `modules/Verify.ps1` |
| Dry run (15) | [`scripts/setup/goldenpath_dryrun.py`](../../scripts/setup/goldenpath_dryrun.py) |
| Teardown | [`scripts/env/teardown-personal-test.sh`](../../scripts/env/teardown-personal-test.sh) |
| MCP config | Writes `mcp/claude-mcp.generated.json` from [`mcp/examples/`](../../mcp/examples/) |

Wizard menus **6–7** do not call `cli/shop` (different config file). `shop` uses the same `goldenpath_ops_cli.py` under the hood.

---

## 9. Teardown safety

Option **13** never deletes projects listed in `PROTECTED_PROJECTS` in [`config/enterprise.env`](../../config/enterprise.env) (always includes `PARENT_PROJECT_ID` when configured).

Enforced by [`scripts/lib/teardown-safety.sh`](../../scripts/lib/teardown-safety.sh).

Manual teardown:

```bash
ALLOWED_TEARDOWN_PROJECTS=gp-mytest-2026 \
  ./scripts/teardown-personal-test.sh --delete-project gp-mytest-2026 --yes
```

---

## 10. Standup script (used by wizard option 3)

```bash
./scripts/standup-teardown-env.sh \
  --project-id my-org-gp-sandbox \
  --project-name "My Golden Path Sandbox" \
  --github-org YOUR_GITHUB_ORG \
  --region "${GCP_REGION}" \
  --yes
```

Requires `ARTIFACT_REGISTRY_REPO` in [`config/enterprise.env`](../../config/enterprise.env) — standup writes `artifact_registry_id` into `platform/bootstrap/terraform.tfvars`.

Root launcher delegates to [`scripts/env/standup-teardown-env.sh`](../../scripts/env/standup-teardown-env.sh).

---

## 11. Troubleshooting

| Issue | Fix |
|-------|-----|
| `pwsh: command not found` | Use `./scripts/goldenpath-setup-bash.sh` or `-py.sh` |
| Project ID rejected | Lowercase, 6–30 chars, start with letter |
| WIF secrets empty | Run option **3** first, then **4** |
| `gh account ≠ GITHUB_ORG` | `gh auth switch --user YOUR_GITHUB_ORG` |
| Stale deploy.yml pin (v0.3.0–v0.3.6) | Run menu **7** (publish auto-upgrades) or `shop upgrade <dir>` |
| Teardown blocked | Project must match saved config; not protected |
| Bootstrap fails on billing | Ensure billing access on the account |

---

## 12. Tests

| Suite | File | What it covers |
|-------|------|----------------|
| Pester | [`tests/goldenpath-setup.tests.ps1`](../../tests/goldenpath-setup.tests.ps1) | PS wizard validation, config, `-h` / `--dryrun` CLI |
| Bash parity | [`tests/bash/test_wizard_parity.sh`](../../tests/bash/test_wizard_parity.sh) | Cross-backend menu 15, ops CLI, upgrade pins |
| pytest | [`tests/test_goldenpath_ops_helpers.py`](../../tests/test_goldenpath_ops_helpers.py) | `goldenpath_ops` scaffold, repair, upgrade |

```powershell
pwsh ./tests/Run-SetupWizardTests.ps1          # default includes code coverage
pwsh ./tests/Run-SetupWizardTests.ps1 -NoCoverage   # skip coverage.xml artifact
```

`coverage.xml` (Pester JaCoCo report) is gitignored — safe to delete locally.

See [tests/README.md](../../tests/README.md).

---

## 13. Related docs

| # | Doc | Content |
|---|-----|---------|
| 5 | [05-journey-wizard.md](./05-journey-wizard.md) | End-to-end narrative |
| 6 | [06-wizard-powershell-advanced.md](./06-wizard-powershell-advanced.md) | Install `pwsh`, run scripts, headless modules |
| 4 | [04-journey-cli.md](./04-journey-cli.md) | Terminal-only path |
| 8 | [08-journey-mcp.md](./08-journey-mcp.md) | Claude AI path |
| 9 | [09-streamlit-setup-ui.md](./09-streamlit-setup-ui.md) | Streamlit wizard UI |
| 10 | [10-shell-scripts-guide.md](./10-shell-scripts-guide.md) | Shell scripts reference |
| — | [sandbox-env.md](../environments/sandbox-env.md) | Sandbox details |
| — | [repository-guide.md](../repository-guide.md) | Full repo map |
