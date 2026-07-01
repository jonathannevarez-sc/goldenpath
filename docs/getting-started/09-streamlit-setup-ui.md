# 9. Streamlit setup UI — guide

**Getting started · Doc 9 of 10** · [Index](./readme.md)

Complete guide to the **Golden Path Streamlit Setup UI**: what it does, who it is for, and how to use it efficiently from zero to a live Cloud Run service.

> **Related docs:** End-to-end wizard journey → [05-journey-wizard.md](./05-journey-wizard.md). Menu lookup (all backends) → [07-setup-wizard-usage.md](./07-setup-wizard-usage.md). Choose wizard vs CLI → [02-pick-your-path.md](./02-pick-your-path.md).

---

## What this app is

The Streamlit app is a **browser-based setup wizard** for Golden Path. It mirrors the terminal wizard menu as a visual UI with sidebar navigation, status panels, and one-click actions.

| | Streamlit UI | Terminal wizard (bash / Python / PS) |
|---|--------------|--------------------------------------|
| **Start** | `./scripts/goldenpath-setup-ui.sh` | `./scripts/goldenpath-setup.sh` or `-{bash,py,ps}.sh` |
| **Interface** | Web pages in the browser | Terminal menu (options 1–15) |
| **Config file** | `.goldenpath-setup.local.json` | Same file |
| **Defaults** | `config/enterprise.env` + `enterprise.env.example` fallbacks | Same via `wizard_defaults.py` |
| **Scaffold / publish / doctor** | Python `goldenpath_ops` (no pwsh) | Same ops via menu 6–7 / 9 or `goldenpath_ops_cli.py` |
| **Bootstrap / verify / teardown** | PowerShell modules via `pwsh` | Same modules or bash/Python equivalents |

**Implementation:** [`scripts/setup/goldenpath_setup_app.py`](../../scripts/setup/goldenpath_setup_app.py)  
**Launcher:** [`scripts/goldenpath-setup-ui.sh`](../../scripts/goldenpath-setup-ui.sh)

The app is **not** your deployed service and **not** a Cloud Run dashboard. It is an **onboarding and operations tool** on your laptop: bootstrap GCP, scaffold a service repo, publish to GitHub, verify health, tear down sandboxes, and generate Claude MCP config.

---

## Who should use it

| Use Streamlit when… | Use something else when… |
|---------------------|---------------------------|
| You prefer buttons and forms over a terminal menu | You want the fastest scripted path → [03-quickstart.md](./03-quickstart.md) (`shop` CLI) |
| You want quick links to GCP Console and GitHub Actions | You use Claude and want MCP tools → [08-journey-mcp.md](./08-journey-mcp.md) |
| You are walking a teammate through setup screen-by-screen | You are automating headless setup → [06-wizard-powershell-advanced.md](./06-wizard-powershell-advanced.md) |

You can switch between Streamlit and any terminal wizard backend anytime — they share the same config file. For a fully pwsh-free path, use bash or Python backends (`goldenpath-setup-bash.sh` / `-py.sh`).

---

## Prerequisites

Install **before** opening the UI:

| Tool | Required for | Install |
|------|----------------|---------|
| **Python 3** | Streamlit | Preinstalled on most Macs |
| **Streamlit** | Running the UI | `pip install streamlit` |
| **pwsh** | Bootstrap, verify, teardown only | macOS: `brew install powershell` |
| **python3** | Scaffold, publish, doctor (via `goldenpath_ops`) | Preinstalled on most Macs |
| **gcloud** | GCP project, bootstrap, verify | [Cloud SDK](https://cloud.google.com/sdk/docs/install) |
| **terraform** | Bootstrap / teardown | [HashiCorp install](https://developer.hashicorp.com/terraform/install) |
| **git** | Scaffold commits | [git-scm.com](https://git-scm.com/) |
| **gh** | Publish, WIF secrets, doctor | [cli.github.com](https://cli.github.com/) |

**Auth (once per machine):**

```bash
gcloud auth login
gcloud auth application-default login
gh auth login
```

Use the **🔍 Prerequisites** page in the app to confirm everything before bootstrap.

> **Important:** Scaffold, publish, and doctor use **Python** (`goldenpath_ops`) — no `pwsh` required. Bootstrap, verify, and teardown still call **PowerShell modules** (`Bootstrap.ps1`, `Verify.ps1`, teardown). For a fully pwsh-free path, use bash or Python terminal backends (`goldenpath-setup-bash.sh` / `-py.sh`). Dry run has no Streamlit page — use `./scripts/goldenpath-setup.sh --dryrun` or terminal menu **15**.

---

## Run the app

From the **goldenpath** repo root:

```bash
cd goldenpath
./scripts/goldenpath-setup-ui.sh
```

Your browser opens (default `http://localhost:8501`). The sidebar shows current profile, GCP project, region, GitHub org, and WIF status.

**Stop the server:** `Ctrl+C` in the terminal where Streamlit is running.

---

## Pages at a glance

The sidebar has **13 pages**. They map to the terminal wizard menu as follows:

| Streamlit page | PS menu | Purpose |
|----------------|---------|---------|
| 🏠 Dashboard | 11 (status) | Overview, quick GCP/WIF checks, console links |
| 🧙 Full Guided Wizard | 1 | Step-by-step path for new users (7 steps) |
| 🔍 Prerequisites | 2 | Tool and auth checks |
| 🚀 Bootstrap GCP | 3 | Create project, link billing, Terraform bootstrap |
| 🔑 WIF Secrets | 4, 5 | Look up WIF credentials; set GitHub secrets via `gh` |
| 🏗️ Scaffold Service | 6 | Copy a template into a **new folder outside** this repo |
| 📤 Publish Service | 7 | GitHub repo, secrets, push, deploy watch |
| ✅ Verify Deployment | 8 | Cloud Run URL + template-aware health check |
| 🩺 Doctor | 9 | Diagnose publish/deploy blockers |
| 🤖 MCP Config | 10 | Generate `mcp/claude-mcp.generated.json` for Claude |
| ⚙️ Edit Settings | 12 | Profile, project ID, region, GitHub org/repo |
| 💣 Sandbox Teardown | 13 | `terraform destroy` + optional project delete |
| 🔄 Fresh Start | 14 | Reset local wizard JSON only (no GCP/GitHub delete) |

---

## What each page does (detail)

### 🏠 Dashboard

Your home screen after the app loads.

- Shows profile, project, region from saved config.
- **Check GCP project exists** — quick `gcloud projects describe`.
- **Check WIF credentials** — terraform output or gcloud fallback.
- **List Cloud Run services** — services in your configured project/region.
- Links to GCP Console, Cloud Run, Artifact Registry, GitHub repo, and last scaffolded service.

**Use when:** Resuming work, confirming bootstrap succeeded, or jumping to cloud consoles.

---

### 🧙 Full Guided Wizard

Linear onboarding for **first-time users**. Seven steps with a progress bar:

1. Edit Settings (pick profile)
2. Prerequisites
3. Bootstrap GCP
4. WIF Secrets
5. Scaffold a service
6. Publish service
7. MCP Config (optional)

**Use when:** You have never run Golden Path on this machine. Complete each step before **Next →**.

After step 7, use **✅ Verify Deployment** and **🏠 Dashboard** to confirm the app is live.

---

### 🔍 Prerequisites

Runs version checks for `gcloud`, `terraform`, `git`, `gh`, and `pwsh`, plus gcloud and Application Default Credentials.

**Use when:** Before bootstrap, or after installing new tools. Fix anything marked ❌ in your terminal, then re-run checks.

---

### 🚀 Bootstrap GCP

One-time (per sandbox project) setup:

- Creates the GCP project if missing
- Links billing (from [`config/enterprise.env`](../../config/enterprise.env) — see [`config/README.md`](../../config/README.md))
- Writes `platform/bootstrap/terraform.tfvars` with `personal_test = true`
- Runs `terraform init` + `terraform apply` (Artifact Registry, WIF pool, GitHub OIDC, deploy SA)

Confirm the checkbox, then **Run Bootstrap**. Expect several minutes.

**Use when:** New sandbox or new custom project. **Same project ID** must be used for scaffold and publish.

Protected projects (`YOUR_BILLING_ANCHOR_PROJECT`, etc.) are blocked.

---

### 🔑 WIF Secrets

Workload Identity Federation lets GitHub Actions deploy without JSON keys.

1. **Look up WIF credentials** — reads Terraform state or gcloud.
2. Copy `GCP_WIF_PROVIDER` and `GCP_WIF_SERVICE_ACCOUNT` into GitHub repo secrets (platform repo + each service repo).
3. Optionally **Set secrets via gh CLI** for a repo you specify.

Also reminds you to enable **reusable workflows** on the platform repo (Settings → Actions → General).

**Use when:** After bootstrap, before publish. Credentials are cached in `.goldenpath-setup.local.json`.

---

### 🏗️ Scaffold Service

Creates a new service from one of six templates:

`nextjs` · `fastapi` · `streamlit` · `express` · `react-spa` · `svelte-spa`

| Field | Guidance |
|-------|----------|
| **Service name** | 3–40 chars, lowercase kebab-case (e.g. `demo-streamlit`) |
| **Output directory** | Default: **parent of `goldenpath`** (e.g. `../demo-streamlit`) |
| **GCP project** | Must match bootstrap project |

**Do not scaffold into the platform repo.** The UI warns and blocks output inside `goldenpath`. Services belong in a sibling folder or separate directory — see [Repo hygiene](../repository-guide.md#repo-hygiene--what-to-delete-vs-keep).

Scaffold runs `Invoke-GoldenPathScaffold` (same as PS menu 6): copies template, replaces tokens, `git init` + initial commit.

**Use when:** You need a new app repo before publish.

---

### 📤 Publish Service

End-to-end publish for a scaffolded directory:

- Creates GitHub repo under your org
- Sets WIF secrets
- Adds WIF trust policy
- Pushes `main`
- Watches the deploy workflow

Default service directory comes from `last_service_dir` in config (set at scaffold time).

**Requires:** WIF credentials from **🔑 WIF Secrets**. Publish can take several minutes.

**Use when:** Service folder exists locally and you want it on GitHub + Cloud Run.

---

### ✅ Verify Deployment

Checks a Cloud Run service (default: `{last_service}-dev`) in your project/region.

Uses `Verify.ps1` to try the correct health path per template (`/api/health`, `/_stcore/health`, `/health`, etc.) with retries.

**Use when:** After publish, or when the service may still be cold-starting (wait 30s and retry).

---

### 🩺 Doctor

Runs `Test-GoldenPathServiceDoctor` on a service directory. Typical findings:

- `gh` / gcloud not authenticated
- Missing WIF secrets on GitHub
- `infra/dev.tfvars` project_id mismatch vs wizard config
- Wrong git branch or GitHub default branch

**Use when:** Publish failed or deploy workflow is red. Fix issues, then **📤 Publish** again.

---

### 🤖 MCP Config

Generates local Claude MCP config at `mcp/claude-mcp.generated.json`.

**Requires:** MCP venv at `mcp/.venv` (create with `cd mcp && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`).

Optionally shows hosted MCP URL if `mcp-server-dev` is deployed on Cloud Run.

**Use when:** You want Golden Path tools inside Claude after bootstrap. See [08-journey-mcp.md](./08-journey-mcp.md).

---

### ⚙️ Edit Settings

Choose how GCP is used:

| Setup mode | Profile | Meaning |
|------------|---------|---------|
| **Sandbox — defaults from enterprise.env** | `sandbox` | Preconfigured from `config/enterprise.env` ([sandbox-env.md](../environments/sandbox-env.md)) |
| **New self-contained sandbox** | `sandbox` | Your own disposable project ID (suggested `gp-sandbox-YYYYMMDD`) |
| **Custom existing project** | `custom` | Existing project; not auto-marked disposable |

Also set region, GitHub org, platform repo name, Golden Path version tag.

Changing **GCP project** clears cached WIF credentials — re-run bootstrap and WIF lookup.

**Use when:** Before bootstrap, or when switching sandboxes.

---

### 💣 Sandbox Teardown

Destroys Golden Path Terraform resources in the current project. Optional: delete the entire GCP project.

Safety checks (via `Bootstrap.ps1`):

- Requires `personal_test = true` in `terraform.tfvars`
- Blocks protected project IDs

**Use when:** You are done with a disposable sandbox. **Irreversible** if you delete the project.

---

### 🔄 Fresh Start

Resets `.goldenpath-setup.local.json` to defaults. Does **not** delete GCP projects, GitHub repos, or Cloud Run services.

**Use when:** Local wizard state is confused. Use **💣 Teardown** if you also want GCP cleanup.

---

## Efficient workflows

### Path A — First time (fastest for new users)

```
./scripts/goldenpath-setup-ui.sh
→ 🧙 Full Guided Wizard (all 7 steps)
→ ✅ Verify Deployment
→ 🏠 Dashboard (open live URL)
```

Estimated time: 20–40 minutes (mostly bootstrap + first deploy).

---

### Path B — Disposable sandbox, minimal clicks

For [`YOUR_GCP_SANDBOX_PROJECT`](../environments/sandbox-env.md) with defaults already in `enterprise.env`:

```
→ ⚙️ Edit Settings → sandbox mode (defaults from enterprise.env)
→ 🔍 Prerequisites → Run checks
→ 🚀 Bootstrap GCP
→ 🔑 WIF Secrets → Look up → Set on platform repo
→ 🏗️ Scaffold Service (name: my-app, output: ..)
→ 📤 Publish Service
→ ✅ Verify Deployment
```

---

### Path C — Resume tomorrow

Config persists in `.goldenpath-setup.local.json`.

```
→ 🏠 Dashboard (sanity check project + WIF)
→ Continue where you left off (e.g. 📤 Publish if only scaffolded)
```

Streamlit reloads config from disk on each interaction — safe to run PS wizard and Streamlit alternately.

---

### Path D — Second service (skip bootstrap)

Same GCP project and WIF already configured:

```
→ 🏗️ Scaffold Service (new name, same output parent dir)
→ 📤 Publish Service
→ ✅ Verify Deployment
```

No need to re-bootstrap unless you changed project in **⚙️ Edit Settings**.

---

### Path E — Deploy failed

```
→ 🩺 Doctor (read issues)
→ Fix in terminal (gh auth, secrets, tfvars) or ⚙️ Edit Settings
→ 📤 Publish Service (retry)
→ ✅ Verify Deployment
```

GitHub Actions link is on verify/dashboard and in publish output.

---

### Path F — Done with sandbox

```
→ 💣 Sandbox Teardown (destroy + optional project delete)
→ 🔄 Fresh Start (optional — reset local JSON)
```

---

## Config file

**Path:** `.goldenpath-setup.local.json` (gitignored, repo root)

| Field | Purpose |
|-------|---------|
| `profile` | `sandbox` \| `custom` |
| `gcp_project` | Bootstrap / deploy target |
| `gcp_region` | From `GCP_REGION` in [`config/enterprise.env`](../../config/enterprise.env) |
| `github_org` | GitHub org or username |
| `github_platform_repo` | Usually `goldenpath` |
| `wif_provider` / `wif_service_account` | Cached after WIF lookup |
| `last_service` | Last scaffolded service name |
| `last_service_dir` | Absolute path to service folder (for publish/doctor) |
| `sandbox_disposable` | Whether teardown is expected |

**Do not mix** with CLI config `.goldenpath-cli.local.json` — see [02-pick-your-path.md](./02-pick-your-path.md).

---

## Rules for efficient, safe use

1. **One project ID** for bootstrap, scaffold tokens, and publish — mismatch is the #1 deploy failure.
2. **Scaffold outside `goldenpath`** — default output `../<service-name>`. If unsure, run `./scripts/check-repo-hygiene.sh`.
3. **WIF before publish** — always run **🔑 WIF Secrets** after bootstrap.
4. **Enable reusable workflows** on the platform GitHub repo before service deploys.
5. **Prerequisites once** — auth and tool versions rarely change; bootstrap is once per sandbox.
6. **Doctor before re-bootstrap** — many issues are secrets or tfvars, not Terraform.
7. **Keep the terminal open** — Streamlit runs there; errors appear in page expanders and the terminal.

---

## What the app does not do

| Expectation | Reality |
|-------------|---------|
| Run without `pwsh` | Bootstrap/scaffold/publish/teardown need PowerShell modules |
| Replace `shop` CLI | CLI path uses `.goldenpath-cli.local.json` — separate workflow |
| Scaffold into platform repo | Blocked by design; use parent directory |
| Delete GitHub repos on teardown | Teardown is GCP/Terraform only |
| Manage production multi-env | Wizard targets dev sandbox (`*-dev` Cloud Run) first |

---

## Troubleshooting

| Symptom | Where to go |
|---------|-------------|
| Bootstrap fails on billing | Confirm [`enterprise.env`](../../config/enterprise.env) billing ID; check `gcloud` permissions |
| Publish fails immediately | **🩺 Doctor** — usually WIF secrets or project mismatch |
| Health check fails but URL works | Wait 30–60s (cold start); **✅ Verify** retries automatically |
| `pwsh` not found | `brew install powershell`; re-run **🔍 Prerequisites** |
| Junk files in `goldenpath` root | `./scripts/check-repo-hygiene.sh` — [Repo hygiene](../repository-guide.md#repo-hygiene--what-to-delete-vs-keep) |
| Menu option number needed | [07-setup-wizard-usage.md](./07-setup-wizard-usage.md) |

---

## See also

- [05-journey-wizard.md](./05-journey-wizard.md) — wizard journey (PS + Streamlit narrative)
- [07-setup-wizard-usage.md](./07-setup-wizard-usage.md) — wizard menu reference (all backends)
- [repository-guide.md](../repository-guide.md) — what each repo folder is for
- [sandbox-env.md](../environments/sandbox-env.md) — shared test project setup
- [`scripts/README.md`](../../scripts/README.md) — script entry points
