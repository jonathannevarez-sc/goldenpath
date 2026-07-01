# 5. Golden Path — the whole journey (Wizard)

**Getting started · Doc 5 of 10** · [Index](./readme.md)

**Primary wizard doc** — how a new user goes from zero to a live Cloud Run service using the **interactive setup wizard**.

> **Replace placeholders:** `YOUR_ORG`, `YOUR_GCP_PROJECT` — examples use `YOUR_GCP_SANDBOX_PROJECT` ([sandbox](../environments/sandbox-env.md)).

## Wizard backends

Four terminal backends + Streamlit UI share the **same menu (1–15)** and **same config file** (`.goldenpath-setup.local.json`). Defaults come from [`config/enterprise.env`](../../config/enterprise.env). Scaffold, publish, doctor, and upgrade pins share [`goldenpath_ops.py`](../../scripts/setup/goldenpath_ops.py).

| Backend | Command | Needs |
|---------|---------|-------|
| **Auto** | `./scripts/goldenpath-setup.sh` | `pwsh` if available, else bash |
| **Bash** | `./scripts/goldenpath-setup-bash.sh` | bash, gcloud, terraform, gh |
| **Python** | `./scripts/goldenpath-setup-py.sh` | python3, gcloud, terraform, gh |
| **PowerShell** | `./scripts/goldenpath-setup-ps.sh` | pwsh |
| **Streamlit** | `./scripts/goldenpath-setup-ui.sh` | streamlit; pwsh only for bootstrap / verify / teardown |

**Implementations:** [`scripts/setup/`](../../scripts/setup/) · **Defaults:** [`scripts/lib/wizard_defaults.py`](../../scripts/lib/wizard_defaults.py)  
**Repo map:** [repository-guide.md](../repository-guide.md)

Do not mix with the CLI path. See [02-pick-your-path.md](./02-pick-your-path.md).

| Also useful | When |
|-------------|------|
| [09-streamlit-setup-ui.md](./09-streamlit-setup-ui.md) | Streamlit pages and efficient workflows |
| [07-setup-wizard-usage.md](./07-setup-wizard-usage.md) | Menu lookup (options 1–15), flows |
| [06-wizard-powershell-advanced.md](./06-wizard-powershell-advanced.md) | `pwsh` automation, dot-sourcing modules (optional) |

**No `pwsh`?** Use bash or Python backends — they run bootstrap, scaffold, and publish without PowerShell.

---

## 1. The journey in one picture

```
cp config/enterprise.env.example config/enterprise.env
        ↓
./scripts/goldenpath-setup.sh  (or -bash.sh / -py.sh / -ui.sh)
        ↓
Menu option 1: Full guided setup
        ↓
Pick profile (sandbox or custom)
        ↓
Check prerequisites + gcloud login
        ↓
Bootstrap GCP (standup script + terraform)
        ↓
Auto-detect WIF secrets (terraform or gcloud)
        ↓
Optionally set GitHub secrets via gh
        ↓
Optionally scaffold first service (menu 6)
        ↓
Optionally generate Claude MCP config
        ↓
Settings saved → resume anytime from menu
        ↓
Menu 7: publish / menu 8: verify  OR  manual gh push
        ↓
git push main → dev deploys
        ↓
Menu option 11: show status anytime
```

---

## 2. How to start

**Recommended — auto-detect backend:**

```bash
cd goldenpath
cp config/enterprise.env.example config/enterprise.env
$EDITOR config/enterprise.env
./scripts/goldenpath-setup.sh
```

**No PowerShell (macOS/Linux):**

```bash
./scripts/goldenpath-setup-bash.sh
# or
./scripts/goldenpath-setup-py.sh
```

**Streamlit web UI:**

```bash
./scripts/goldenpath-setup-ui.sh
```

**Headless full wizard:**

```bash
./scripts/goldenpath-setup-bash.sh --wizard
./scripts/goldenpath-setup-py.sh --wizard
pwsh ./scripts/setup/goldenpath-setup.ps1 --wizard
```

Full menu reference: [07-setup-wizard-usage.md](./07-setup-wizard-usage.md)

---

## 3. Main menu

```
 1) Full guided setup (recommended for new users)
 2) Check prerequisites
 3) Bootstrap GCP (stand up / terraform apply)
 4) Show GitHub WIF secrets
 5) Set GitHub WIF secrets on a repo
 6) Scaffold a new service
 7) Publish service to GitHub (repo + secrets + deploy)
 8) Verify a deployment (health check)
 9) Doctor — diagnose deploy blockers
10) Generate Claude MCP config
11) Show current status
12) Edit settings (project, org, region)
13) Tear down current sandbox project
14) Fresh start (reset local wizard state)
15) Dry run — read-only audit (no deploy / no changes)
 h) Help / usage
 0) Exit
```

All backends converge on **`goldenpath_ops`** for scaffold, publish, doctor, and platform-pin upgrades. Bash and `shop` call it via [`goldenpath_ops_cli.py`](../../scripts/setup/goldenpath_ops_cli.py). Python and Streamlit import it directly. PowerShell modules orchestrate bootstrap/verify/teardown and delegate upgrade/doctor to the ops CLI.

Wizard building blocks: [`goldenpath_ops.py`](../../scripts/setup/goldenpath_ops.py), [`goldenpath_ops_cli.py`](../../scripts/setup/goldenpath_ops_cli.py), bash [`goldenpath_setup_ops.sh`](../../scripts/setup/goldenpath_setup_ops.sh), PowerShell [`modules/`](../../scripts/setup/modules/) (including `OpsCli.ps1`).

---

## 4. Full guided setup (option 1)

### Step 1 — Choose profile

| Profile | When to use |
|---------|-------------|
| **Sandbox** (default) | `GCP_SANDBOX_PROJECT` from `config/enterprise.env` |
| **New self-contained sandbox** | Your own project ID — create, use, tear down later (menu **13**) |
| **Custom existing** | A GCP project that already exists |

### Step 2 — Prerequisites and auth

Checks for `gcloud`, `terraform`, `git`, `gh` (and optionally `python3`, `docker`). Offers:

- `gcloud auth login`
- `gcloud auth application-default login`

### Step 3 — Bootstrap GCP

Runs [`scripts/env/standup-teardown-env.sh`](../../scripts/env/standup-teardown-env.sh) or wizard bootstrap which:

1. Creates sandbox project if missing
2. Links billing (does not modify `PARENT_PROJECT_ID`)
3. Writes `platform/bootstrap/terraform.tfvars` (including `artifact_registry_id` from `ARTIFACT_REGISTRY_REPO` in `config/enterprise.env`)
4. Runs `terraform init` + `terraform apply`

### Step 4 — WIF secrets (auto-detected)

Lookup order:

1. **Terraform state** → `dev_github_wif_provider_name`, `dev_github_actions_sa_email`
2. **gcloud fallback** → WIF pool + `github-actions@` service account

| Secret | Maps to |
|--------|---------|
| `GCP_WIF_PROVIDER` | WIF provider resource name |
| `GCP_WIF_SERVICE_ACCOUNT` | `github-actions@...` email |

Offers to push secrets via `gh secret set`.

### Step 5 — Scaffold (optional)

Copies a template outside the platform repo, replaces placeholders (`{{SERVICE_NAME}}`, `{{GITHUB_ORG}}`, `{{GCP_DEV_PROJECT}}`, etc.), and `git init -b main`. **Not** `cli/shop new`.

### Step 6 — MCP config (optional)

Creates `mcp/.venv`, installs requirements, writes `mcp/claude-mcp.generated.json`.

---

## 5. After the wizard — finish the deploy loop

**Option A — wizard publish (menu 7)**

Wires GitHub repo, secrets, WIF trust, and watches deploy. Menu **8** verifies health.

**Option B — manual**

```bash
cd ../hello-golden
gh repo create hello-golden --public --source=. --push
```

Then set WIF secrets (menu **5**), push to `main`, and verify (menu **8**).

---

## 6. Menu options in detail

| Option | Purpose |
|--------|---------|
| **2** | Verify `gcloud`, `terraform`, `git`, `gh` installed |
| **3** | Run standup + Terraform bootstrap |
| **4** | Show WIF secrets (terraform or gcloud fallback) |
| **5** | `gh secret set` on a service repo |
| **6** | Interactive scaffold (not shop CLI) |
| **7** | Publish to GitHub — repo, secrets, WIF trust, deploy watch |
| **8** | Poll Cloud Run URL + health paths |
| **9** | Doctor — diagnose branch, secrets, token issues |
| **10** | Write `mcp/claude-mcp.generated.json` |
| **11** | Show saved config, AR, WIF, Cloud Run services |
| **12** | Edit profile / project / org / region |
| **13** | Tear down disposable sandbox |
| **14** | Reset `.goldenpath-setup.local.json` to enterprise defaults |
| **15** | Dry run — read-only audit via `goldenpath_dryrun.py` |

---

## 7. Saved configuration

File: `.goldenpath-setup.local.json` (gitignored)

| Field | Example |
|-------|---------|
| `gcp_project` | `YOUR_GCP_SANDBOX_PROJECT` |
| `gcp_region` | `GCP_REGION` from [`config/enterprise.env`](../../config/enterprise.env) |
| `github_org` | `YOUR_GITHUB_ORG` |
| `wif_provider` | `projects/.../providers/github-provider` |
| `wif_service_account` | `github-actions@YOUR_GCP_SANDBOX_PROJECT.iam.gserviceaccount.com` |
| `last_service` | `hello-golden` |

Resume anytime — wizard remembers your settings.

---

## 8. Wizard vs CLI vs MCP

| Need | Use |
|------|-----|
| First-time onboarding | **Wizard** (this doc) |
| No PowerShell available | **Bash** or **Python** backend |
| Browser UI | **Streamlit** (`goldenpath-setup-ui.sh`) |
| Quick scaffold + `shop publish` | [CLI](./04-journey-cli.md) |
| AI-guided dev in Claude | [MCP](./08-journey-mcp.md) + skill `goldenpath-setup-wizard` |
| WIF when terraform state is gone | Wizard option **4** |
| Day-to-day code → push → deploy | git + GitHub Actions (any path) |

---

## 9. Troubleshooting

| Issue | Wizard help |
|-------|-------------|
| `terraform output` empty | Option **4** — gcloud fallback |
| Not logged into GCP | Option **1** or **2** |
| Forgot project/org settings | Option **11** (status) or **12** (edit) |
| Deploy worked? | Option **8** (verify) |
| What's running? | Option **11** (show status) |
| `pwsh: command not found` | Use `-bash.sh` or `-py.sh` |
| Missing enterprise config | `cp config/enterprise.env.example config/enterprise.env` |

Wizard tests: [`tests/goldenpath-setup.tests.ps1`](../../tests/goldenpath-setup.tests.ps1) — see [tests/README.md](../../tests/README.md)

---

## 10. Teardown

Wizard menu **13** or manually:

```bash
./scripts/teardown-personal-test.sh --delete-project YOUR_GCP_SANDBOX_PROJECT --yes
```

Safety: [`scripts/lib/teardown-safety.sh`](../../scripts/lib/teardown-safety.sh) blocks `PROTECTED_PROJECTS`.

See [sandbox-env.md](../environments/sandbox-env.md).
