# shop CLI

Bash CLI for Golden Path onboarding on the **terminal path**. Separate from the setup wizard — uses a different config file.

| | **CLI (`shop`)** | **Wizard** |
|---|------------------|------------|
| **Entry** | `./cli/shop` or `export PATH="$PWD/cli:$PATH"` | [`./scripts/goldenpath-setup.sh`](../scripts/goldenpath-setup.sh) or `-{bash,py,ps,ui}.sh` |
| **Config** | `.goldenpath-cli.local.json` (repo root) | `.goldenpath-setup.local.json` |
| **Scaffold** | `shop new <name> --output ..` | Wizard menu **6** (does not call `shop`) |
| **Publish** | `shop publish [dir]` (always **public** repo) | Wizard menu **7** (respects platform visibility) |

**Do not mix** config files. See [02-pick-your-path.md](../docs/getting-started/02-pick-your-path.md).

## File

| File | Purpose |
|------|---------|
| [`shop`](./shop) | Single bash script — all subcommands in one file |

## Commands

| Command | Purpose |
|---------|---------|
| `shop list` | Show templates from `templates/catalog.json` |
| `shop config init` | Create `.goldenpath-cli.local.json` (defaults `github_org` from `gh api user` when logged in) |
| `shop config set` | Update saved config (same flags as `init`) |
| `shop config show` | Print saved config |
| `shop new <name> [options]` | Scaffold a service repo (should be **outside** the platform repo; use `--output ../`) |
| `shop publish [dir] [options]` | Create **public** GitHub repo, WIF secrets, IAM trust, push `main`, watch deploy, verify health (fails if unhealthy) |
| `shop verify [dir]` | Poll Cloud Run URL + health (retries cold start) |
| `shop doctor [dir]` | Diagnose deploy blockers (branch, secrets, pins, gh account) |
| `shop upgrade [dir]` | Bump deploy.yml + infra pins to `GOLDENPATH_VERSION` in `enterprise.env` |

`[dir]` defaults to the current directory. Run `shop --help` for full flag list.

`shop new`, `publish`, `doctor`, and `upgrade` delegate to [`goldenpath_ops_cli.py`](../scripts/setup/goldenpath_ops_cli.py) — same logic as wizard menus **6–7** and **9** (different config file).

### Common flags

| Flag | Commands | Purpose |
|------|----------|---------|
| `--template <name>` | `new` | Template from catalog (default: `nextjs`) |
| `--output <dir>` | `new` | Parent directory for scaffold (default: `.`) |
| `--github-org`, `--gcp-dev`, `--gcp-prod`, `--region` | `new`, `publish`, `config` | Override config / enterprise.env |
| `--goldenpath-repo`, `--goldenpath-version` | `config` | Platform repo name and workflow pin |
| `--dry-run` | `new` | Print target path only |
| `--no-watch` | `publish` | Push without `gh run watch` |

Config and env also support `SHOP_*` overrides (see `shop --help`). Saved JSON includes `artifact_registry_repo` (from `ARTIFACT_REGISTRY_REPO` in `enterprise.env`).

## Dependencies

Sources helpers from `scripts/lib/`:

- `load-config.sh` — merges `config/enterprise.env` when present
- `wizard_defaults.py` — platform defaults from `enterprise.env.example` when CLI JSON is incomplete
- `scaffold-tokens.sh` — `{{TOKEN}}` replacement, `deploy.yml` token checks
- `wif-credentials.sh` — resolve WIF provider + SA for publish
- `wif-trust-repo.sh` — per-repo WIF IAM (`shop publish`)
- `verify-deployment.sh` — health polling (`shop verify`; publish uses ops CLI)
- `goldenpath_ops_cli.py` — shared scaffold / publish / doctor / upgrade

**External tools:** `gh` (required for `publish`), `gcloud` (WIF credential lookup), `git` (optional for `shop new` initial commit).

Bootstrap is **not** built into `shop` — run [`./scripts/standup-teardown-env.sh`](../scripts/standup-teardown-env.sh) first (wizard menu **3** does the same via the guided path).

## Docs

- [04-journey-cli.md](../docs/getting-started/04-journey-cli.md) — full walkthrough
- [03-quickstart.md](../docs/getting-started/03-quickstart.md) — fast path
- [repository-guide.md](../docs/repository-guide.md) — repo map