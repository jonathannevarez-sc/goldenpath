# 1. Start here

**Getting started · Doc 1 of 10** · [Index](./readme.md)

Golden Path is **enterprise-agnostic**. Before anything else, configure your GCP account and GitHub org.

## 1. Enterprise config

```bash
cp config/enterprise.env.example config/enterprise.env
$EDITOR config/enterprise.env
```

**Required** (bash standup scripts fail without these):

- `PARENT_PROJECT_ID` — billing anchor (Golden Path never deploys here)
- `BILLING_ACCOUNT_ID`
- `GITHUB_ORG`

**Recommended** for sandbox testing:

- `GCP_SANDBOX_PROJECT` (or `GCP_DEV_PROJECT` / `GCP_PROD_PROJECT` for multi-env)
- `PROTECTED_PROJECTS` — projects teardown scripts must never delete

Optional keys fall back to `enterprise.env.example`. Full variable list: [`config/README.md`](../../config/README.md).

## 2. Pick your path

| Path | Guide |
|------|-------|
| CLI | [04-journey-cli.md](./04-journey-cli.md) |
| Setup wizard (bash, Python, PS, or Streamlit) | [05-journey-wizard.md](./05-journey-wizard.md) |
| MCP (Claude) | [08-journey-mcp.md](./08-journey-mcp.md) |
| Shell scripts overview | [10-shell-scripts-guide.md](./10-shell-scripts-guide.md) |

**Wizard quick start (no PowerShell):**

```bash
./scripts/goldenpath-setup-bash.sh
```

## 3. Bootstrap GCP

**Sandbox (recommended for first test):**

```bash
gcloud auth application-default login
./scripts/standup-teardown-env.sh --yes --skip-labels
```

**Production (dev + prod projects):**

Follow [../platform/getting-started-platform.md](../platform/getting-started-platform.md).

## 4. Scaffold and deploy (CLI path)

```bash
export PATH="$PWD/cli:$PATH"   # or use ./cli/shop for each command

shop config init --github-org YOUR_ORG --gcp-dev YOUR_DEV --gcp-prod YOUR_PROD
shop new hello --template nextjs --output ..
shop publish ../hello
```

Wizard users: start with [05-journey-wizard.md](./05-journey-wizard.md) instead — do not mix CLI and wizard config files.

## Next

- [02-pick-your-path.md](./02-pick-your-path.md) — CLI vs wizard vs MCP
- [03-quickstart.md](./03-quickstart.md) — shortest path
- [config/README.md](../../config/README.md) — all config variables