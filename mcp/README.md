# Golden Path MCP server

**Phase:** 2 — AI-assisted developer experience (Layer B)  
**Release:** `v0.3.7`  
**Status:** Implemented

> **Start here:** [guide.md](./guide.md) — what MCP does and doesn't do, local vs Cloud Run setup.

MCP server with **3 resources** (skills, docs, version metadata) and **13 tools** (11 read, 2 audited write). Skills carry knowledge; MCP carries live lookups and guarded actions.

**Not MCP tools:** GCP bootstrap (`scripts/standup-teardown-env.sh` / wizard menu **3**), `shop publish` (GitHub repo + WIF + push `main`), teardown. After `scaffold_service`, run `shop publish` or wizard menu **7** — see [08-journey-mcp.md](../docs/getting-started/08-journey-mcp.md).

## Architecture

```
skills/  docs/  templates/     cli/shop
         │
         ▼
Golden Path MCP Server (goldenpath_mcp)
  Resources: goldenpath://skills/*  goldenpath://docs/*  goldenpath://meta/version
  Tools:     13 total (list_templates, scaffold_service, get_deploy_status, …)
         │
         ▼
Claude Desktop / Claude Code — stdio (local) or streamable-http /mcp (hosted)
```

**Skills are not installed locally** — clients read them via MCP Resources (`get_skill` / `goldenpath://skills/{name}/SKILL.md`).

Defaults for `GOLDENPATH_VERSION`, `GCP_REGION`, and `MCP_SERVICE_NAME` merge from `config/enterprise.env.example` + `config/enterprise.env` via `goldenpath_mcp/enterprise.py` when env vars are unset. See [`config/README.md`](../config/README.md).

## Quick start (local — stdio)

**Prerequisites:** Bootstrap GCP once (`./scripts/standup-teardown-env.sh`) before GCP tools return useful data.

```bash
cd mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export GOLDENPATH_ROOT="$(cd .. && pwd)"
export GCP_PROJECT=your-gcp-sandbox-project   # or dev project
export GCP_REGION=us-central1                 # or from config/enterprise.env

python -m goldenpath_mcp
```

Smoke test runs until Ctrl+C. Package entry: `python -m goldenpath_mcp` or `goldenpath-mcp` (see `pyproject.toml`).

### Claude Desktop / Claude Code

Copy a config example and set **absolute** paths:

- [claude-mcp.example.json](./examples/claude-mcp.example.json)
- [claude-desktop-config.example.json](./examples/claude-desktop-config.example.json)

Or generate config via wizard menu **10** → `mcp/claude-mcp.generated.json` (gitignored).

For an isolated sandbox, set `GCP_PROJECT` to `GCP_SANDBOX_PROJECT` from [`config/enterprise.env`](../config/enterprise.env) — see [sandbox-env.md](../docs/environments/sandbox-env.md).

Optional client `env` for prod dispatch from MCP:

```json
"GITHUB_TOKEN": "ghp_..."
```

## Hosted (streamable-http on Cloud Run)

Deploy via **Artifact Registry → Cloud Run** with **streamable-http + API key** (Secret Manager). `/health` is unauthenticated; MCP routes require `Authorization: Bearer <key>` or `X-MCP-API-Key`.

> **Cloud Run:** Raw SSE (`/sse`) returns HTTP 421 behind the load balancer. Production hosting uses **streamable-http** at **`/mcp`**.

```bash
# from goldenpath repo root (reads config/enterprise.env when present)
chmod +x scripts/deploy-mcp-cloudrun.sh
./scripts/deploy-mcp-cloudrun.sh
```

Uses `MCP_SERVICE_NAME` and `ARTIFACT_REGISTRY_REPO` from enterprise config when set. Outputs: service URL, API key (`cd mcp/infra && terraform output`, or Secret Manager).

**API key:** Terraform bootstrap creates a placeholder secret version (`{}`). `scripts/deploy/deploy-mcp-cloudrun.sh` seeds a random key and rolls the Cloud Run revision automatically. To rotate later:

```bash
openssl rand -hex 24 | gcloud secrets versions add SERVICE-dev-mcp-api-key \
  --project=PROJECT --data-file=-
gcloud run services update SERVICE-dev --project=PROJECT --region=REGION
```

### Claude — remote MCP

Copy [claude-mcp-remote.example.json](./examples/claude-mcp-remote.example.json):

```json
{
  "mcpServers": {
    "goldenpath-remote": {
      "url": "https://goldenpath-mcp-dev-XXXX.run.app/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_MCP_API_KEY"
      }
    }
  }
}
```

Restart Claude Desktop. Remote MCP gives docs, skills, templates, and GCP read tools without a local venv — not local disk scaffold.

### Hosted vs local

| Capability | Local (stdio) | Cloud Run (streamable-http) |
|------------|---------------|----------------------------|
| Docs / skills / templates | Yes | Yes |
| `list_services`, `get_deploy_status` | Your `gcloud` ADC | Runtime service account |
| `scaffold_service` | Writes to your disk | Container FS only — use local MCP or `shop new` |
| `trigger_deploy` | Your `GITHUB_TOKEN` | Optional `GITHUB_TOKEN` at deploy |
| `shop publish` | Run in terminal | Not available — use local `cli/shop` |

### Local Docker smoke test

```bash
export MCP_API_KEY="$(openssl rand -hex 24)"
docker build -f mcp/Dockerfile -t goldenpath-mcp .
docker run -p 8080:8080 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_API_KEY="$MCP_API_KEY" \
  -e GCP_PROJECT=YOUR_GCP_SANDBOX_PROJECT \
  goldenpath-mcp
curl http://localhost:8080/health
```

(`MCP_TRANSPORT=sse` works for local Docker; use `streamable-http` to mirror Cloud Run.)

## Resources

| URI | Content |
|-----|---------|
| `goldenpath://meta/version` | Channel + version metadata |
| `goldenpath://docs/{path}` | Path under `docs/`, e.g. `getting-started/03-quickstart.md`, `repository-guide.md` |
| `goldenpath://skills/{name}/SKILL.md` | Official agent skills |

Helper tools when the client has weak Resource support: `list_docs`, `get_doc`, `list_skills`, `get_skill`.

## Tools (13 total)

### Read (11)

| Tool | Purpose |
|------|---------|
| `list_templates` | Template catalog (`templates/catalog.json`) |
| `list_skills` / `get_skill` | Official skills |
| `list_docs` / `get_doc` | Documentation under `docs/` |
| `get_version` | Release metadata |
| `list_services` | Cloud Run services (Golden Path labels) |
| `get_deploy_status` | URL, ready state, image for `{name}-{environment}` |
| `get_service_config` | Cloud Run spec summary |
| `get_cost_estimate` | Cost notes + console link |
| `validate_service_repo` | Check directory layout (no audit log) |

### Write — audited (2)

| Tool | Purpose |
|------|---------|
| `scaffold_service` | Runs `cli/shop new` (requires `github_org`, `gcp_dev_project`, `gcp_prod_project`; optional `region`, `output_dir` default `..`) |
| `trigger_deploy` | GitHub Actions `workflow_dispatch` (`confirm=true`, `GITHUB_TOKEN` or `GH_TOKEN`) |

`scaffold_service` and `trigger_deploy` emit JSON audit lines to **stderr** via `audit.py`.

**Scaffold path:** default `output_dir` is `..` (parent of platform repo). Response includes `next_step: shop publish <path>` and warns if the scaffold landed inside `GOLDENPATH_ROOT`.

## Auth model

- **No privilege escalation** — GCP tools use the caller's credentials locally; hosted mode uses the runtime service account for reads
- **GCP tools (local)** — Application Default Credentials / `gcloud auth application-default login`
- **trigger_deploy** — caller's `GITHUB_TOKEN` or `GH_TOKEN`; must pass `confirm=true`
- **Hosted HTTP** — `MCP_API_KEY` required (`auth.py` `ApiKeyMiddleware` on SSE and streamable-http); `/health` is open
- **Future:** orgs may add SSO/OIDC in front of hosted MCP (reverse proxy) — not built into this package today

## Environment

See [config.example.env](./config.example.env). Override enterprise file path: `GOLDENPATH_CONFIG` (same as platform scripts).

| Variable | Default | Purpose |
|----------|---------|---------|
| `GOLDENPATH_ROOT` | auto-detect (`mcp/` parent) | Repo root |
| `GOLDENPATH_CONFIG` | `config/enterprise.env` | Alternate enterprise env path |
| `GOLDENPATH_CHANNEL` | `stable` | Release channel (resources metadata) |
| `GOLDENPATH_VERSION` | from `enterprise.env` / example | Pin version in metadata |
| `GCP_PROJECT` | `GCP_SANDBOX_PROJECT` or `GCP_DEV_PROJECT` from enterprise.env | Default project for GCP tools |
| `GCP_REGION` | from `enterprise.env` / example | Default region; required for `scaffold_service` if `region` omitted |
| `MCP_TRANSPORT` | `stdio` | `stdio` \| `sse` \| `streamable-http` |
| `MCP_HOST` | `0.0.0.0` | Bind address (hosted) |
| `MCP_PORT` / `PORT` | `8080` | Listen port (hosted; Cloud Run sets `PORT`) |
| `MCP_API_KEY` | — | **Required** for `sse` and `streamable-http` |
| `MCP_SERVICE_NAME` | from `enterprise.env` / example | Hosted Cloud Run service name |
| `GITHUB_TOKEN` / `GH_TOKEN` | — | `trigger_deploy` |
| `SHOP_CLI` | `{repo}/cli/shop` | Override shop path for `scaffold_service` |

## Skills (official — 5)

| Skill | Purpose |
|-------|---------|
| `goldenpath-setup-wizard` | Full wizard onboarding playbook |
| `scaffold-shop-service` | Create new service |
| `deploy-to-shop-gcp` | Publish/deploy failures, WIF, workflows |
| `shop-terraform-conventions` | Extend infra safely |
| `shop-observability` | Logs, metrics, alerts |

## Phase 2 exit criterion

> Developer on a fresh machine with MCP configured can **scaffold** via skills + `scaffold_service`, then **`shop publish`** (or wizard menu **7**) to reach a live `dev` deploy — guided by official skills, without mixing CLI and wizard config files.

## Related

- [08-journey-mcp.md](../docs/getting-started/08-journey-mcp.md) — end-to-end MCP walkthrough
- [repository-guide.md](../docs/repository-guide.md) — `mcp/` folder map
- [config/README.md](../config/README.md) — enterprise env + `MCP_SERVICE_NAME`
- [cli/README.md](../cli/README.md) — `shop publish` (not an MCP tool)
- [MCP evolution proposal](../docs/design/golden-path-mcp-evolution-proposal.md)
- [platform/architecture.md](../docs/platform/architecture.md) — MCP in system context
