# Golden Path configuration

Enterprise-specific values live in **`config/enterprise.env`** (gitignored). Platform-wide defaults (region, workflow pin, resource names) ship in the committed **`enterprise.env.example`**.

**Platform team guide (recommended):** [team-env-setup.md](./team-env-setup.md) — how to maintain and share `enterprise.env.team` with developers.

## Platform team vs developers

| File | Committed? | Who maintains it |
|------|------------|------------------|
| `enterprise.env.example` | Yes | Upstream Golden Path — placeholders only |
| `enterprise.env.team.example` | Yes | Upstream — template + record-keeping headers |
| **`enterprise.env.team`** | **No (gitignored)** | **Platform / FinOps** — canonical org config, shared via vault or ticket |
| **`enterprise.env`** | **No (gitignored)** | **Each machine** — what CLI, wizard, MCP, and scripts read |

Product engineers **do not** look up billing IDs. Platform fills `enterprise.env.team` once; developers install it locally.

### Platform team (first time)

```bash
cp config/enterprise.env.team.example config/enterprise.env.team
$EDITOR config/enterprise.env.team   # FinOps: billing; platform: projects, GitHub, safety lists
./config/install-team-env.sh          # copies team file → enterprise.env for local verify
# Share enterprise.env.team via 1Password / internal vault — not git
```

Update the **Platform record** comment block at the top of `enterprise.env.team` when values change (date, owner, bootstrap status).

### Developers (onboarding)

```bash
# Receive enterprise.env.team from platform (vault, drive, or attachment)
cp config/enterprise.env.team config/enterprise.env
# or: ./config/install-team-env.sh   (if team file already in repo checkout)

gcloud auth login
gcloud auth application-default login
gh auth login
```

### Solo / no platform team yet

```bash
cp config/enterprise.env.example config/enterprise.env
$EDITOR config/enterprise.env
```

## Required variables

Bash loaders (`load-config.sh`) fail if these are missing from `enterprise.env`:

| Variable | Purpose |
|----------|---------|
| `PARENT_PROJECT_ID` | Billing anchor — Golden Path never deploys here |
| `BILLING_ACCOUNT_ID` | GCP billing account ID |
| `GITHUB_ORG` | GitHub org for service repos and WIF |

## Optional variables

Unset keys fall back to `enterprise.env.example` (see [Fallback behavior](#fallback-behavior) below).

| Variable | Purpose |
|----------|---------|
| `GCP_DEV_PROJECT` | Dev environment project |
| `GCP_PROD_PROJECT` | Prod environment project |
| `GCP_SANDBOX_PROJECT` | Isolated sandbox for testing; defaults to `GCP_DEV_PROJECT` when unset |
| `SANDBOX_PROJECT_NAME` | Display name when standup creates the sandbox |
| `SANDBOX_PROJECT_LABELS` | Comma-separated GCP labels for sandbox creation (e.g. `purpose=goldenpath,lifecycle=sandbox`) |
| `GCP_REGION` | Default region |
| `PLATFORM_REPO` | This platform repo name (example default: `goldenpath`) |
| `GOLDENPATH_VERSION` | Git tag for reusable deploy workflows (currently **`v0.3.7`** — older tags removed) |
| `ARTIFACT_REGISTRY_REPO` | Shared Artifact Registry repository ID (scaffold + deploy) |
| `MCP_SERVICE_NAME` | Cloud Run service name for hosted MCP deploy |
| `PROTECTED_PROJECTS` | Comma-separated — teardown scripts refuse to delete |
| `ALLOWED_TEARDOWN_PROJECTS` | Comma-separated allowlist (empty = any non-protected sandbox) |

## Who reads this

| Consumer | How |
|----------|-----|
| **Scripts** | `scripts/lib/load-config.sh` — standup, teardown, deploy helpers |
| **Wizard** | `scripts/lib/wizard_defaults.py` — menu defaults + `.goldenpath-setup.local.json` |
| **CLI** | `cli/shop` via `load-config.sh` and `wizard_defaults.py`; per-machine settings in [`.goldenpath-cli.local.json`](../cli/README.md) |
| **MCP** | `mcp/goldenpath_mcp/enterprise.py` — scaffold/deploy tools on the hosted server |

## Fallback behavior

| Loader | Behavior |
|--------|----------|
| **Bash** (`load-config.sh`) | Requires `enterprise.env` (or `GOLDENPATH_CONFIG`); sources it; optional keys fall back per-key to `enterprise.env.example` |
| **Python** (`wizard_defaults.py`, `enterprise.py`) | Merges `enterprise.env.example` first, then overlays `enterprise.env` (local wins) |

Python paths can use example-only defaults for optional keys; bash standup/teardown scripts require a local `enterprise.env`.

## Override path

```bash
export GOLDENPATH_CONFIG=/path/to/custom.env
./scripts/standup-teardown-env.sh
```

## Per-machine config (not enterprise.env)

| File | Path | Used by |
|------|------|---------|
| Wizard | `.goldenpath-setup.local.json` | Setup wizard / Streamlit UI |
| CLI | `.goldenpath-cli.local.json` | `shop` — see [`cli/README.md`](../cli/README.md) |

Both are gitignored at the repo root. Do not mix wizard and CLI config files.

## Related docs

- [`team-env-setup.md`](./team-env-setup.md) — platform distribution and developer onboarding
- [`docs/repository-guide.md`](../docs/repository-guide.md) — where config fits in the platform map
- [`docs/environments/sandbox-env.md`](../docs/environments/sandbox-env.md) — sandbox projects and standup
- [`mcp/README.md`](../mcp/README.md) — hosted MCP deploy and `MCP_SERVICE_NAME`
