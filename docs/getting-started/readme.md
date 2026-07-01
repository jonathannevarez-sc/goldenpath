# Getting started

Pick **one** onboarding path and stay on it. Do not mix CLI and wizard config files.

> **New here?** Read [**01-start-here.md**](./01-start-here.md), then [**02-pick-your-path.md**](./02-pick-your-path.md), then one path guide below.

> **Placeholders:** Examples use `YOUR_ORG` and `YOUR_GCP_SANDBOX_PROJECT` (sandbox). Replace with your values — see [`config/README.md`](../../config/README.md) and `config/enterprise.env`.

## If you want X, read Y

| You want… | Read |
|-----------|------|
| Orientation | [**01-start-here.md**](./01-start-here.md) |
| Choose CLI vs wizard vs MCP | [**02-pick-your-path.md**](./02-pick-your-path.md) |
| Shell scripts (`scripts/`, `shop`) | [**10-shell-scripts-guide.md**](./10-shell-scripts-guide.md) |
| Fastest terminal deploy | [**03-quickstart.md**](./03-quickstart.md) → [**04-journey-cli.md**](./04-journey-cli.md) |
| Guided setup (menu or Streamlit) | [**05-journey-wizard.md**](./05-journey-wizard.md) |
| Wizard menu lookup (options 1–15) | [**07-setup-wizard-usage.md**](./07-setup-wizard-usage.md) |
| Wizard PowerShell / automation | [**06-wizard-powershell-advanced.md**](./06-wizard-powershell-advanced.md) |
| Streamlit web UI (full guide) | [**09-streamlit-setup-ui.md**](./09-streamlit-setup-ui.md) |
| MCP journey in Claude | [**08-journey-mcp.md**](./08-journey-mcp.md) |
| MCP overview (local vs Cloud Run) | [**mcp/guide.md**](../../mcp/guide.md) |

## Enterprise config (all paths)

```bash
cp config/enterprise.env.example config/enterprise.env
$EDITOR config/enterprise.env
```

Variable reference: [`config/README.md`](../../config/README.md).

## All docs (1–10)

| # | File | Purpose |
|---|------|---------|
| 1 | [`01-start-here.md`](./01-start-here.md) | Entry — prerequisites, three paths, templates |
| 2 | [`02-pick-your-path.md`](./02-pick-your-path.md) | Why paths differ; do not mix config files |
| 3 | [`03-quickstart.md`](./03-quickstart.md) | CLI — 15-minute deploy |
| 4 | [`04-journey-cli.md`](./04-journey-cli.md) | CLI — full `shop` walkthrough |
| 5 | [`05-journey-wizard.md`](./05-journey-wizard.md) | Wizard — primary journey (bash, Python, PS, Streamlit) |
| 6 | [`06-wizard-powershell-advanced.md`](./06-wizard-powershell-advanced.md) | Wizard — `pwsh`, headless modules, automation |
| 7 | [`07-setup-wizard-usage.md`](./07-setup-wizard-usage.md) | Wizard — menu options 1–15, flows, troubleshooting |
| 8 | [`08-journey-mcp.md`](./08-journey-mcp.md) | MCP — Claude walkthrough |
| 9 | [`09-streamlit-setup-ui.md`](./09-streamlit-setup-ui.md) | Streamlit UI — pages and workflows |
| 10 | [`10-shell-scripts-guide.md`](./10-shell-scripts-guide.md) | **Cross-cutting** — `scripts/` + `shop` (any path; not a fourth config track) |

## CLI path

| # | File | Purpose |
|---|------|---------|
| 3 | [`03-quickstart.md`](./03-quickstart.md) | **CLI** 15-minute deploy |
| 4 | [`04-journey-cli.md`](./04-journey-cli.md) | Full `shop` CLI walkthrough |

**CLI setup (once per shell):**

```bash
cd goldenpath
export PATH="$PWD/cli:$PATH"   # then use bare shop; or ./cli/shop every time
```

## Wizard / UI path

*Table order is **recommended reading order**, not file number.*

| # | File | Purpose |
|---|------|---------|
| 5 | [`05-journey-wizard.md`](./05-journey-wizard.md) | **Primary** — wizard backends (bash, Python, PS, Streamlit) |
| 9 | [`09-streamlit-setup-ui.md`](./09-streamlit-setup-ui.md) | **Streamlit UI** — pages, workflows, efficient use |
| 7 | [`07-setup-wizard-usage.md`](./07-setup-wizard-usage.md) | Reference — menu options 1–15, flows, troubleshooting |
| 6 | [`06-wizard-powershell-advanced.md`](./06-wizard-powershell-advanced.md) | **Advanced** — `pwsh` install, headless modules, automation |

Start with **05** or **09** (Streamlit-only users). Use **07** for menu option numbers. **06** is for scripting and contributors.

## MCP path

| # | File | Purpose |
|---|------|---------|
| 8 | [`08-journey-mcp.md`](./08-journey-mcp.md) | Claude MCP walkthrough |
| — | [`mcp/guide.md`](../../mcp/guide.md) | What MCP does and doesn't; local stdio vs Cloud Run |

## Shell scripts reference

Supplement for **any** path — bootstrap, wizard launchers, hygiene, MCP deploy. Not a separate onboarding track (no own config file).

| # | File | Purpose |
|---|------|---------|
| 10 | [`10-shell-scripts-guide.md`](./10-shell-scripts-guide.md) | **`scripts/` + `shop`** — layout, workflows, troubleshooting |

## Three paths at a glance

| | **CLI** | **Wizard / UI** | **MCP** |
|---|---------|-----------------|---------|
| **Start** | `shop config init` | `./scripts/goldenpath-setup.sh` or `-{bash,py,ps,ui}.sh` | [mcp/guide.md](../../mcp/guide.md) → client config |
| **Bootstrap** | `./scripts/standup-teardown-env.sh` | Wizard menu **3** | Wizard or standup (one-time) |
| **Scaffold** | `shop new` | Wizard menu **6** | `scaffold_service` |
| **Publish** | `shop publish` | Wizard menu **7** | `shop publish` or wizard **7** |
| **Config file** | `.goldenpath-cli.local.json` | `.goldenpath-setup.local.json` | MCP env + optional wizard file |

## Sandbox setup

| Guide | When |
|-------|------|
| [sandbox-env.md](../environments/sandbox-env.md) | Isolated sandbox / single-project test (`personal_test`) |

Also see [**Repository guide**](../repository-guide.md) for the full repo map.

**Accidental files in the platform repo?** Run `./scripts/check-repo-hygiene.sh` — see [Repo hygiene](../repository-guide.md#repo-hygiene--what-to-delete-vs-keep).