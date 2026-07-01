# Golden Path MCP — What It Is, What It Isn't, How to Use It

The Golden Path MCP server (`goldenpath_mcp`) connects AI assistants (Claude Desktop, Claude Code, etc.) to the **goldenpath platform repo**: official docs, skills, templates, and a small set of GCP/GitHub actions.

**Same codebase, two ways to run it:**

| Mode | Default? | Transport | Best for |
|------|----------|-----------|----------|
| **Local** | Yes | `stdio` (process spawned by your editor) | Day-to-day development on your machine |
| **Cloud Run** | Optional | `streamable-http` at `/mcp` | Team-wide docs/skills/GCP reads without a local venv |

---

## What MCP does

### Serves knowledge (Resources)

Read-only content from the repo — skills are **not** copied to your machine; the client fetches them over MCP.

| Resource URI | Content |
|--------------|---------|
| `goldenpath://docs/{path}` | Files under `docs/` (e.g. `getting-started/03-quickstart.md`) |
| `goldenpath://skills/{name}/SKILL.md` | Agent playbooks under `skills/` |
| `goldenpath://meta/version` | Release channel + version metadata |

Helper tools (for clients with weak Resource support): `list_docs`, `get_doc`, `list_skills`, `get_skill`.

### Answers platform questions (Read tools)

| Tool | Purpose |
|------|---------|
| `list_templates` | Service templates from `templates/catalog.json` |
| `get_version` | Channel and version info |
| `list_services` | Cloud Run services (Golden Path labels) |
| `get_deploy_status` | URL, ready state, image for `{name}-{environment}` |
| `get_service_config` | Cloud Run spec summary |
| `get_cost_estimate` | Cost notes + console link |
| `validate_service_repo` | Check a directory matches Golden Path layout |

### Performs guarded actions (Write tools — audited)

| Tool | Purpose |
|------|---------|
| `scaffold_service` | Runs `cli/shop new` — creates a service repo on disk from a template |
| `trigger_deploy` | Dispatches a GitHub Actions workflow (`confirm=true` + `GITHUB_TOKEN`) |

Write tools emit JSON audit lines to **stderr** (`audit.py`).

### Uses your credentials (local) or a service account (hosted)

- **Local:** GCP tools use your Application Default Credentials (`gcloud auth application-default login`). `trigger_deploy` uses your `GITHUB_TOKEN` / `GH_TOKEN`.
- **Cloud Run:** GCP read tools use the runtime service account. Optional `GITHUB_TOKEN` can be injected at deploy time for `trigger_deploy`.

---

## What MCP does **not** do

These stay in **scripts, the setup wizard, or `cli/shop`** — by design.

| Task | Where to do it |
|------|----------------|
| Bootstrap GCP (billing, WIF, Artifact Registry) | `./scripts/standup-teardown-env.sh` or wizard menu **3** |
| Publish to GitHub + wire secrets + push `main` | `shop publish` or wizard menu **7** |
| Tear down a sandbox project | `./scripts/teardown-personal-test.sh` or wizard menu **13** |
| Full wizard onboarding | `./scripts/goldenpath-setup.sh` |
| Mix wizard config with CLI config | Don't — wizard uses `.goldenpath-setup.local.json`, CLI uses `.goldenpath-cli.local.json` |

**Typical flow:** MCP scaffolds and guides → you run `shop publish` in a terminal to go live.

---

## Local MCP (stdio)

### Prerequisites

1. **Enterprise config** (once per org):

   ```bash
   cp config/enterprise.env.example config/enterprise.env
   $EDITOR config/enterprise.env
   ```

2. **GCP bootstrapped** at least once (so GCP tools return useful data):

   ```bash
   ./scripts/standup-teardown-env.sh
   # or wizard menu 3
   ```

3. **gcloud ADC** (for GCP tools):

   ```bash
   gcloud auth application-default login
   ```

### Install and run

```bash
cd mcp
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

export GOLDENPATH_ROOT="$(cd .. && pwd)"
export GCP_PROJECT=your-gcp-sandbox-project   # optional; defaults from GCP_SANDBOX_PROJECT or GCP_DEV_PROJECT in enterprise.env
export GCP_REGION=us-central1               # from enterprise.env

python -m goldenpath_mcp
```

The process speaks **stdio** — it waits for an MCP client to connect. Ctrl+C stops it.

Optional: copy `mcp/config.example.env` to `mcp/.env` and load it before starting.

### Connect your AI client

**Claude Desktop / Claude Code** — copy and edit an example config (use **absolute** paths):

- [`examples/claude-mcp.example.json`](./examples/claude-mcp.example.json)
- [`examples/claude-desktop-config.example.json`](./examples/claude-desktop-config.example.json)

```json
{
  "mcpServers": {
    "goldenpath-local": {
      "command": "/absolute/path/to/goldenpath/mcp/.venv/bin/python",
      "args": ["-m", "goldenpath_mcp"],
      "env": {
        "GOLDENPATH_ROOT": "/absolute/path/to/goldenpath",
        "GCP_PROJECT": "your-gcp-sandbox-project",
        "GCP_REGION": "us-central1"
      }
    }
  }
}
```

Restart the client after saving.

**Wizard shortcut:** menu **10** generates `mcp/claude-mcp.generated.json` (gitignored) with paths filled in.

### Local tips

- **`scaffold_service` output:** Default `output_dir` is `..` (parent of platform repo) so the service sits **outside** `goldenpath` — same rule as `shop new --output ..`.
- **`trigger_deploy`:** Set `GITHUB_TOKEN` or `GH_TOKEN` in the client `env` block if you use prod dispatch from MCP.
- **Skills:** Load `scaffold-shop-service`, `deploy-to-shop-gcp`, or `goldenpath-setup-wizard` via `get_skill` before complex tasks.

---

## Cloud Run MCP (hosted)

Deploy the **same server** as an HTTPS endpoint for remote clients. Production uses **streamable-http** at **`/mcp`** (not raw SSE — Cloud Run returns HTTP 421 on `/sse` behind the load balancer).

### Deploy

From the **repo root** (reads `config/enterprise.env` when present):

```bash
chmod +x scripts/deploy-mcp-cloudrun.sh
./scripts/deploy-mcp-cloudrun.sh
```

This builds the Docker image, pushes to Artifact Registry, and applies `mcp/infra/` Terraform. Outputs include the service URL and API key (Terraform output or Secret Manager).

Infrastructure sets:

- `MCP_TRANSPORT=streamable-http`
- `GOLDENPATH_ROOT=/app` (repo baked into the image)
- `MCP_API_KEY` from Secret Manager
- GCP read access via the Cloud Run service account

### Auth

| Route | Auth |
|-------|------|
| `/health` | Open (Cloud Run probe) |
| `/mcp` and other MCP routes | `Authorization: Bearer <MCP_API_KEY>` or `X-MCP-API-Key: <key>` |

Retrieve the key after deploy:

```bash
cd mcp/infra && terraform output
# or Secret Manager in your GCP project
```

### Connect your AI client (remote)

Copy [`examples/claude-mcp-remote.example.json`](./examples/claude-mcp-remote.example.json):

```json
{
  "mcpServers": {
    "goldenpath-remote": {
      "url": "https://YOUR-SERVICE-XXXX.run.app/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_MCP_API_KEY"
      }
    }
  }
}
```

Restart the client.

### Hosted limitations

| Capability | Local | Cloud Run |
|------------|-------|-----------|
| Docs, skills, templates | Yes | Yes |
| GCP read tools | Your `gcloud` credentials | Runtime service account |
| `scaffold_service` | Writes to **your disk** | Container filesystem only — use local MCP or `shop new` |
| `shop publish` | Run in terminal | **Not available** — always use local `cli/shop` |
| `trigger_deploy` | Your `GITHUB_TOKEN` | Only if token was configured at deploy |

**Cloud Run MCP** is best for shared **documentation, skills, and deploy status**. **Local MCP** is required for scaffolding on your machine and publishing services.

### Local Docker smoke test (optional)

Mirrors hosted HTTP without deploying:

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

---

## Environment variables (quick reference)

| Variable | Default | Purpose |
|----------|---------|---------|
| `GOLDENPATH_ROOT` | Parent of `mcp/` | Repo root |
| `GOLDENPATH_CONFIG` | `config/enterprise.env` | Override enterprise config path |
| `GCP_PROJECT` | `GCP_SANDBOX_PROJECT` or `GCP_DEV_PROJECT` from enterprise.env | Default project for GCP tools |
| `GCP_REGION` | from enterprise.env | Region for GCP tools and scaffold |
| `MCP_TRANSPORT` | `stdio` | `stdio` \| `sse` \| `streamable-http` |
| `MCP_API_KEY` | — | **Required** for `sse` and `streamable-http` |
| `MCP_PORT` / `PORT` | `8080` | HTTP listen port (hosted) |
| `GITHUB_TOKEN` / `GH_TOKEN` | — | `trigger_deploy` |
| `SHOP_CLI` | `{repo}/cli/shop` | Override shop path for `scaffold_service` |

See [`config.example.env`](./config.example.env) and [`config/README.md`](../config/README.md).

---

## End-to-end workflow (local)

```
1. Bootstrap GCP          →  standup script or wizard
2. Install local MCP      →  venv + client config (this guide)
3. Read docs / load skill →  get_doc / get_skill
4. list_templates         →  pick fastapi, nextjs, etc.
5. scaffold_service       →  creates service on disk
6. shop publish           →  terminal (NOT an MCP tool)
7. get_deploy_status      →  confirm live URL
8. (optional) trigger_deploy(confirm=true)  →  prod
```

---

## Related docs

| Doc | Topic |
|-----|-------|
| [README.md](./README.md) | Full MCP reference (tools, auth, Phase 2 notes) |
| [08-journey-mcp.md](../docs/getting-started/08-journey-mcp.md) | Step-by-step journey with Claude |
| [07-setup-wizard-usage.md](../docs/getting-started/07-setup-wizard-usage.md) | Wizard (bootstrap, publish, MCP config gen) |
| [cli/README.md](../cli/README.md) | `shop` CLI (`publish`, `verify`, `doctor`) |
| [sandbox-env.md](../docs/environments/sandbox-env.md) | Personal GCP sandbox |