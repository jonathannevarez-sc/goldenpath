# 2. Pick your path — do not mix

**Getting started · Doc 2 of 10** · [Index](./readme.md)

Golden Path has **three onboarding experiences**. Each uses different config and entry points. Choose one and stay on it.

> **Replace placeholders:** `YOUR_ORG`, `YOUR_GCP_PROJECT` — examples use `YOUR_GCP_SANDBOX_PROJECT` from the [sandbox](../environments/sandbox-env.md).

> See [repository-guide.md](../repository-guide.md) for where each path's files live in the repo.

## If you want X, read Y

| You want… | Read |
|-----------|------|
| Fastest terminal deploy | [03-quickstart.md](./03-quickstart.md) |
| Full CLI narrative | [04-journey-cli.md](./04-journey-cli.md) |
| Guided first-time setup (menu or Streamlit) | [05-journey-wizard.md](./05-journey-wizard.md) |
| Wizard menu lookup (options 1–15) | [07-setup-wizard-usage.md](./07-setup-wizard-usage.md) |
| Script `pwsh` / automation (advanced) | [06-wizard-powershell-advanced.md](./06-wizard-powershell-advanced.md) |
| AI in Claude | [08-journey-mcp.md](./08-journey-mcp.md) |
| Shell scripts (`scripts/`, `shop`) | [10-shell-scripts-guide.md](./10-shell-scripts-guide.md) |
| MCP overview (local vs Cloud Run) | [mcp/guide.md](../../mcp/guide.md) |

## 1. Comparison

| | **CLI** | **Wizard / UI** | **MCP** |
|---|---------|-----------------|---------|
| **Tool** | `shop` ([`cli/shop`](../../cli/shop)) | `./scripts/goldenpath-setup.sh` or `-{bash,py,ps,ui}.sh` | MCP server in Claude |
| **Config file** | `.goldenpath-cli.local.json` | `.goldenpath-setup.local.json` | MCP client config + env vars |
| **Bootstrap** | `./scripts/standup-teardown-env.sh` | Wizard menu **3** | Wizard or standup script (one-time) |
| **Scaffold** | `shop new <name> --output ..` | Wizard menu **6** | `scaffold_service` tool |
| **Publish + deploy** | `shop publish ../<name>` (public repo) | Wizard menu **7** (private OK) | `shop publish` or wizard **7** |
| **Diagnose issues** | `shop doctor` | Wizard menu **9** | Skill `deploy-to-shop-gcp` |
| **Best for** | Terminal power users | First-time guided setup | AI-assisted dev in editor |

## 2. CLI path

```bash
cd goldenpath
export PATH="$PWD/cli:$PATH"

./scripts/standup-teardown-env.sh --yes --skip-labels

shop config init --github-org YOUR_ORG --gcp-dev YOUR_GCP_SANDBOX_PROJECT
shop list
shop new my-app --template streamlit --output ..
shop publish ../my-app
```

(`./cli/shop` works everywhere if you skip the PATH export.)

**What `shop publish` does:** creates a **public** GitHub repo, forces default branch **`main`**, sets WIF secrets, adds per-repo IAM trust, pushes `main`, watches the workflow, verifies health (exits non-zero if unhealthy).

**Key folders:** `cli/`, `scripts/lib/`, `scripts/env/`, `templates/`

**Docs:** [03-quickstart.md](./03-quickstart.md) · [04-journey-cli.md](./04-journey-cli.md)

## 3. Wizard / UI path

**Primary doc:** [05-journey-wizard.md](./05-journey-wizard.md) — bash, Python, PowerShell, and Streamlit backends.

**Configure enterprise defaults first** ([`config/README.md`](../../config/README.md)):

```bash
cp config/enterprise.env.example config/enterprise.env
$EDITOR config/enterprise.env
```

**No PowerShell required:**

```bash
cd goldenpath
./scripts/goldenpath-setup-bash.sh    # or: -py.sh, -ps.sh, -ui.sh
```

**Auto-detect** (`pwsh` if available, else bash):

```bash
./scripts/goldenpath-setup.sh
```

**Streamlit web UI:**

```bash
./scripts/goldenpath-setup-ui.sh
```

Menu **1** = full guided setup. After scaffold, use **Publish to GitHub now** or menu **7** later.

**Key folders:** `scripts/setup/`, `config/enterprise.env`, `scripts/lib/wizard_defaults.py`

| When you need… | Read |
|----------------|------|
| Menu option numbers, flows, troubleshooting | [07-setup-wizard-usage.md](./07-setup-wizard-usage.md) |
| `pwsh` install, dot-sourcing modules, CI automation | [06-wizard-powershell-advanced.md](./06-wizard-powershell-advanced.md) |

## 4. MCP path

1. Bootstrap GCP once (wizard menu **3** or `./scripts/standup-teardown-env.sh`)
2. Configure MCP from [mcp/examples/claude-mcp.example.json](../../mcp/examples/claude-mcp.example.json)
3. In Claude: load skill `scaffold-shop-service`, call `scaffold_service`
4. Publish via wizard menu **7**, `shop publish`, or manual `gh`

**Key folders:** `mcp/`, `skills/`, `docs/` (served as MCP resources)

**Doc:** [08-journey-mcp.md](./08-journey-mcp.md)

## 5. Why mixing paths causes pain

The demo-streamlit test mixed wizard and CLI (manual `gh` secrets, manual WIF bindings). That led to:

| Symptom | Cause |
|---------|-------|
| Workflow never runs | GitHub default branch `master`, workflow listens on `main` |
| Wrong GCP project in deploy | Scaffold project ≠ bootstrap project |
| AR login 403 | Missing per-repo WIF `tokenCreator` binding |

**Going forward:**

| You are… | Use only… |
|----------|-----------|
| CLI user | `shop` + `standup-teardown-env.sh` |
| Wizard user | `goldenpath-setup.sh` or `-{bash,py,ps,ui}.sh` |
| MCP user | MCP tools + one bootstrap/publish path (wizard or `shop publish`) |

## 6. Common failures (and fixes)

| Symptom | Fix |
|---------|-----|
| Workflow never runs | `shop publish` or wizard **7** (sets `main`) |
| AR login 403 | `shop publish` adds WIF trust automatically |
| Wrong project in deploy | `shop doctor` or wizard **9**, re-scaffold with correct project |
| Unreplaced `{{tokens}}` in deploy.yml | `shop publish` auto-repairs |

## 7. Related

| # | Doc |
|---|-----|
| 1 | [01-start-here.md](./01-start-here.md) — orientation |
| 3 | [03-quickstart.md](./03-quickstart.md) — CLI quick deploy |
| — | [repository-guide.md](../repository-guide.md) — repo file map |