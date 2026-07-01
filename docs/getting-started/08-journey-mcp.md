# 8. Golden Path — the whole journey (MCP)

**Getting started · Doc 8 of 10** · [Index](./readme.md)

How a new user goes from zero to a live Cloud Run service using the **Golden Path MCP server** in Claude.

> **Replace placeholders:** `YOUR_ORG`, `YOUR_GCP_PROJECT` — examples use `YOUR_GCP_SANDBOX_PROJECT` ([sandbox](../environments/sandbox-env.md)).

**Platform repo:** `goldenpath`  
**MCP release:** `GOLDENPATH_VERSION` from [`config/enterprise.env`](../../config/enterprise.env)  
**Test sandbox:** `YOUR_GCP_SANDBOX_PROJECT`  
**Repo map:** [repository-guide.md](../repository-guide.md)

MCP gives you **docs, skills, and GCP lookups inside your editor**. It does **not** replace bootstrap or publish — you still run standup / wizard for GCP, and `shop publish` (or wizard menu **7**) for GitHub + deploy.

> **Overview:** [mcp/guide.md](../../mcp/guide.md) — what MCP does and doesn't do, local vs Cloud Run.

---

## 1. The journey in one picture

```
Bootstrap GCP (standup script or wizard menu 3)
        ↓
Install local MCP venv + connect Claude
        ↓
Read goldenpath://docs/getting-started/01-start-here.md
        ↓
Load skill: scaffold-shop-service
        ↓
Tool: list_templates  →  pick template
        ↓
Tool: scaffold_service  →  runs ./cli/shop new on disk
        ↓
shop publish  OR  wizard menu 7  (repo + WIF + push main + deploy)
        ↓
Tool: get_deploy_status  →  confirm live
        ↓
Daily: edit code → git push main → MCP checks status
        ↓
Tool: trigger_deploy(confirm=true)  →  prod (optional)
```

---

## 2. MCP vs CLI — what changes?

| Step | CLI | MCP |
|------|-----|-----|
| Bootstrap | `./scripts/standup-teardown-env.sh` | Same (MCP has no bootstrap tool) |
| Scaffold | `./cli/shop new` | `scaffold_service` (calls `./cli/shop new`) |
| List templates | `./cli/shop list` | `list_templates` |
| Read docs | open files | `get_doc` / `goldenpath://docs/*` |
| Read skills | N/A | `get_skill` / `goldenpath://skills/*` |
| Publish | `shop publish` | Same — **not an MCP tool** |
| Deploy status | `gcloud` / `gh` | `get_deploy_status` |
| List services | `gcloud run services list` | `list_services` |
| Prod deploy | `gh workflow run` | `trigger_deploy` (needs `GITHUB_TOKEN`) |
| Troubleshooting | read docs | load skill `deploy-to-shop-gcp` |

Skills live in [`skills/`](../../skills/) — five official playbooks served as MCP resources, not installed locally. For full wizard onboarding via MCP, load skill `goldenpath-setup-wizard`.

---

## 3. Step-by-step

### 1. Prerequisites

Run from the **repo root**.

**Enterprise config** (once per org):

```bash
cp config/enterprise.env.example config/enterprise.env
$EDITOR config/enterprise.env
```

See [`config/README.md`](../../config/README.md) for required vs optional variables.

| Tool | Purpose |
|------|---------|
| `gcloud` | Auth + GCP lookups (MCP GCP tools use your credentials) |
| `terraform` | Bootstrap (standup script runs it) |
| `git` | Version control |
| `gh` | Needed for `shop publish` |
| Python 3.11+ | Local MCP venv |

```bash
cd goldenpath
export PATH="$PWD/cli:$PATH"   # for shop publish; or use ./cli/shop

gcloud auth login
gcloud auth application-default login
gcloud auth application-default set-quota-project YOUR_GCP_SANDBOX_PROJECT
```

**Bootstrap** (one-time, before any deploy):

```bash
./scripts/standup-teardown-env.sh --yes --skip-labels
```

Or wizard menu **3** — see [05-journey-wizard.md](./05-journey-wizard.md).

---

### 2. Install local MCP (stdio)

```bash
cd goldenpath/mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Smoke test (runs until you Ctrl+C):

```bash
export GOLDENPATH_ROOT="$(cd .. && pwd)"
export GCP_PROJECT=YOUR_GCP_SANDBOX_PROJECT   # optional — defaults from enterprise.env
export GCP_REGION="${GCP_REGION}"   # from config/enterprise.env
python -m goldenpath_mcp
```

Package: [`mcp/goldenpath_mcp/`](../../mcp/goldenpath_mcp/)

---

### 3. Connect Claude

Edit [mcp/examples/claude-mcp.example.json](../../mcp/examples/claude-mcp.example.json) — replace `/ABSOLUTE/PATH/TO/goldenpath` with your repo path:

| Field | Set to |
|-------|--------|
| `command` | `…/goldenpath/mcp/.venv/bin/python` |
| `GOLDENPATH_ROOT` | `…/goldenpath` (repo root) |
| `GCP_PROJECT` | `YOUR_GCP_SANDBOX_PROJECT` (optional — defaults from `GCP_SANDBOX_PROJECT` or `GCP_DEV_PROJECT` in `config/enterprise.env`) |

If you moved the repo after creating the venv, recreate it (step 2) so `command` points at a valid interpreter.

Merge into Claude Desktop → Settings → Developer → MCP. Restart Claude Desktop. Confirm **`goldenpath-local`** appears.

**Or** generate config via wizard menu **10** → writes `mcp/claude-mcp.generated.json` (gitignored).

**Remote (optional):** deploy with `./scripts/deploy-mcp-cloudrun.sh`, then use [claude-mcp-remote.example.json](../../mcp/examples/claude-mcp-remote.example.json):

```json
"url": "https://YOUR-SERVICE.run.app/mcp"
```

Use **`/mcp`** (streamable-http), not `/sse` — raw SSE fails behind Cloud Run's load balancer. See [mcp/README.md](../../mcp/README.md).

---

### 4. Orient with docs and skills

| Resource URI | Content |
|--------------|---------|
| `goldenpath://docs/getting-started/01-start-here.md` | Orientation |
| `goldenpath://docs/getting-started/08-journey-mcp.md` | This guide |
| `goldenpath://docs/repository-guide.md` | Repo file map |
| `goldenpath://docs/environments/sandbox-env.md` | Sandbox setup |
| `goldenpath://skills/scaffold-shop-service/SKILL.md` | Scaffold skill |

Tools: `list_docs`, `get_doc`, `list_skills`, `get_skill`.

---

### 5. Scaffold via MCP

Load skill **`scaffold-shop-service`**, then call **`scaffold_service`**:

| Parameter | Required | Example |
|-----------|----------|---------|
| `name` | Yes | `hello-golden` |
| `template` | No (default `nextjs`) | `nextjs` |
| `github_org` | Yes | `YOUR_GITHUB_ORG` |
| `gcp_dev_project` | Yes | `YOUR_GCP_SANDBOX_PROJECT` |
| `gcp_prod_project` | Yes | `YOUR_GCP_SANDBOX_PROJECT` |
| `region` | No (default from `GCP_REGION` in enterprise.env) | `YOUR_GCP_REGION` |
| `output_dir` | No (default `..`) | `..` (sibling of platform repo) or another parent path |

Example:

```
scaffold_service(
  name="hello-golden",
  template="nextjs",
  github_org="YOUR_GITHUB_ORG",
  gcp_dev_project="YOUR_GCP_SANDBOX_PROJECT",
  gcp_prod_project="YOUR_GCP_SANDBOX_PROJECT"
)
```

MCP runs [`cli/shop`](../../cli/shop) `new` with `GOLDENPATH_ROOT` as working directory.

> **Hosted MCP on Cloud Run** can read docs and check GCP status, but `scaffold_service` writes inside the container filesystem — use **local MCP** for scaffolding.

---

### 6. Publish to GitHub (not an MCP tool)

MCP has no publish tool. Use one of:

```bash
cd goldenpath
shop publish ../hello-golden
```

Or wizard menu **7**, which does the same: creates repo, sets WIF secrets, adds IAM trust, pushes **`main`**, watches deploy, verifies health.

**Manual alternative:** `gh repo create` + WIF secrets + `git push origin main` — see [04-journey-cli.md](./04-journey-cli.md).

If you used `shop publish`, **deploy to dev is already triggered** — skip a separate push.

---

### 7. Check deploy status

In Claude:

```
get_deploy_status(
  service_name="hello-golden",
  environment="dev",
  project="YOUR_GCP_SANDBOX_PROJECT"
)
```

`service_name` is the **logical name** (e.g. `hello-golden`). MCP resolves the Cloud Run service as `hello-golden-dev`.

Before first deploy, `get_deploy_status` returns an error — that is expected. Use `list_services` to see already-deployed services, or publish first.

Or: `list_services(project="YOUR_GCP_SANDBOX_PROJECT")` for all Golden Path services.

For subsequent code changes: `git push origin main` → auto-deploy to dev.

---

### 8. Verify health

`get_deploy_status` returns `url`, `ready`, and `image`. Template health paths:

| Template | Path |
|----------|------|
| nextjs, fastapi, express | `/api/health` |
| streamlit | `/_stcore/health` |
| react-spa, svelte-spa | `/health` |

Or: `shop verify ../hello-golden`

---

### 9. Daily workflow

```
Edit in Claude  →  git push main  →  get_deploy_status in MCP
```

Load skill **`deploy-to-shop-gcp`** when CI or WIF fails.

---

### 10. Promote to prod

```
trigger_deploy(
  github_repo="YOUR_GITHUB_ORG/hello-golden",
  environment="prod",
  confirm=true
)
```

Requires `GITHUB_TOKEN` or `GH_TOKEN` in MCP env (Claude config `env` block).

Without a token: `gh workflow run deploy.yml -f environment=prod` or GitHub Actions UI.

---

### 11. Official skills

| Skill | When to load |
|-------|--------------|
| `scaffold-shop-service` | Creating a new service |
| `deploy-to-shop-gcp` | Publish/deploy failures, WIF, workflow issues |
| `goldenpath-setup-wizard` | Full wizard onboarding via AI |
| `shop-terraform-conventions` | Extending `infra/` safely |
| `shop-observability` | Logs, metrics, alerts |

---

## 4. MCP tools reference

**13 tools** total — bootstrap and `shop publish` are intentionally not MCP tools.

### Read

| Tool | Purpose |
|------|---------|
| `list_templates` | Template catalog from `templates/catalog.json` |
| `list_skills` / `get_skill` | Official agent skills |
| `list_docs` / `get_doc` | Documentation from `docs/` |
| `get_version` | Release channel + version metadata |
| `list_services` | Cloud Run services with `managed_by=goldenpath` label |
| `get_deploy_status` | URL, ready state, image for `{name}-{environment}` |
| `get_service_config` | Cloud Run spec |
| `get_cost_estimate` | Cost notes + console link |
| `validate_service_repo` | Check directory layout |

GCP tools use **your** `gcloud` credentials locally, or the runtime service account when hosted.

### Write (audited — logged to stderr)

| Tool | Purpose |
|------|---------|
| `scaffold_service` | Run `./cli/shop new` |
| `trigger_deploy` | GitHub Actions `workflow_dispatch` |

**Not MCP tools:** bootstrap, `shop publish`, teardown — use scripts or wizard.

---

## 5. Local vs hosted MCP

| Capability | Local (stdio) | Cloud Run (streamable-http) |
|------------|---------------|----------------------------|
| Docs / skills / templates | Yes | Yes |
| `list_services`, `get_deploy_status` | Your `gcloud` | MCP runtime SA |
| `scaffold_service` | Writes to your disk | Container filesystem only |
| `trigger_deploy` | Your `GITHUB_TOKEN` | Optional secret at deploy |

Deploy hosted: `./scripts/deploy-mcp-cloudrun.sh` → [`mcp/infra/`](../../mcp/infra/)

---

## 6. Key repo folders

| Folder | Role |
|--------|------|
| [`mcp/`](../../mcp/) | MCP server package |
| [`mcp/examples/`](../../mcp/examples/) | Claude config samples |
| [`skills/`](../../skills/) | Agent instructions (MCP resources) |
| [`docs/`](../../docs/) | Human docs (also MCP resources) |
| [`cli/shop`](../../cli/shop) | Called by `scaffold_service` and `shop publish` |

---

## 7. When to use MCP

| Good fit | Not a fit |
|----------|-----------|
| AI reads docs/skills while you work | Replacing bootstrap (use standup / wizard) |
| `get_deploy_status` without leaving Claude | Replacing `shop publish` |
| Troubleshooting with `deploy-to-shop-gcp` skill | Scaffolding on hosted MCP only |

**Related:** [05-journey-wizard.md](./05-journey-wizard.md) (bootstrap + publish menu) · [04-journey-cli.md](./04-journey-cli.md) (terminal path) · [mcp/README.md](../../mcp/README.md) (server details)

---

## 8. Troubleshooting (from live testing)

| Symptom | Cause | Fix |
|---------|-------|-----|
| `get_deploy_status` → service not found | Service not deployed yet (normal after scaffold) | Run `shop publish` first |
| `list_services` works but publish fails | GCP project exists but local bootstrap/tfvars missing | `./scripts/standup-teardown-env.sh --yes --skip-labels` |
| Claude MCP won't start | Stale paths in config after moving the repo | Edit `command` + `GOLDENPATH_ROOT`; or recreate venv (below) |
| `pip` broken in `mcp/.venv` | venv created at an old repo path | `cd mcp && rm -rf .venv && python3 -m venv .venv && pip install -r requirements.txt` |
| `trigger_deploy` → token required | No `GITHUB_TOKEN` in MCP env | Add to Claude config `env`, or use `gh workflow run` |
| `scaffold_service` → missing params | Omitted required fields | Pass `github_org`, `gcp_dev_project`, `gcp_prod_project` |
| Remote MCP connection fails on `/sse` | Cloud Run needs streamable-http | Use URL ending in **`/mcp`** |

**Optional:** add `GITHUB_TOKEN` to the Claude `env` block if you want `trigger_deploy` from MCP:

```json
"env": {
  "GOLDENPATH_ROOT": "/your/path/goldenpath",
  "GCP_PROJECT": "YOUR_GCP_SANDBOX_PROJECT",
  "GITHUB_TOKEN": "ghp_..."
}
```
