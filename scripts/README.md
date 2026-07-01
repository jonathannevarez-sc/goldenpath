# Golden Path scripts

> **User guide:** [10-shell-scripts-guide.md](../docs/getting-started/10-shell-scripts-guide.md) — what to run, when, and why.

Scripts are grouped by purpose under subfolders. **Launchers** at `scripts/*.sh` preserve familiar entry points; implementations live in subfolders.

```
scripts/
├── goldenpath-setup.sh              # unified wizard router (auto backend)
├── goldenpath-setup-{bash,py,ps,ui}.sh
├── goldenpath-setup.ps1             # PowerShell shim → setup/
├── standup-teardown-env.sh          # launcher → env/
├── teardown-personal-test.sh        # launcher → env/
├── deploy-mcp-cloudrun.sh           # launcher → deploy/
├── import-mcp-infra-state.sh        # launcher → deploy/
├── check-repo-hygiene.sh            # platform layout + wizard file checks
├── setup/                           # wizard implementations
│   ├── goldenpath-setup.ps1         # PowerShell wizard
│   ├── goldenpath_setup.sh          # Bash wizard (no pwsh)
│   ├── goldenpath_setup.py          # Python wizard (no pwsh)
│   ├── goldenpath_setup_ops.sh      # Bash ops (delegates scaffold/publish/doctor to ops CLI)
│   ├── goldenpath_ops.py            # Shared Python ops (scaffold, publish, doctor, upgrade)
│   ├── goldenpath_ops_cli.py        # CLI entry for bash, shop, PS upgrade/doctor
│   ├── goldenpath_setup_app.py      # Streamlit web UI
│   └── modules/                     # PowerShell building blocks (+ OpsCli.ps1)
├── env/                             # GCP project lifecycle
├── deploy/                          # MCP Cloud Run deploy
└── lib/                             # shared helpers
    ├── load-config.sh               # enterprise.env loader
    ├── wizard_defaults.py           # wizard defaults from enterprise.env
    ├── scaffold-tokens.sh
    ├── wif-credentials.sh
    ├── wif-trust-repo.sh
    ├── verify-deployment.sh
    └── teardown-safety.sh
```

## Setup wizard (`setup/`)

Four terminal backends + Streamlit UI — same menu (1–15), same `.goldenpath-setup.local.json`.

| Backend | Launcher | Implementation |
|---------|----------|----------------|
| Auto | `./scripts/goldenpath-setup.sh` | pwsh if available, else bash |
| Bash | `./scripts/goldenpath-setup-bash.sh` | `setup/goldenpath_setup.sh` |
| Python | `./scripts/goldenpath-setup-py.sh` | `setup/goldenpath_setup.py` |
| PowerShell | `./scripts/goldenpath-setup-ps.sh` | `setup/goldenpath-setup.ps1` |
| Streamlit | `./scripts/goldenpath-setup-ui.sh` | `setup/goldenpath_setup_app.py` |

**Enterprise defaults:** `config/enterprise.env` via `lib/wizard_defaults.py`

**Docs:** [07-setup-wizard-usage.md](../docs/getting-started/07-setup-wizard-usage.md) · [05-journey-wizard.md](../docs/getting-started/05-journey-wizard.md)

**No `pwsh`?** Use `./scripts/goldenpath-setup-bash.sh` or `-py.sh`.

Streamlit uses Python `goldenpath_ops` for scaffold/publish/doctor; PowerShell modules remain for bootstrap, verify, and teardown. Dry run: `./scripts/goldenpath-setup.sh --dryrun` or menu **15**.

## Environment (`env/`)

| Script | Purpose |
|--------|---------|
| [standup-teardown-env.sh](./env/standup-teardown-env.sh) | Create GCP project + bootstrap (reads `config/enterprise.env`) |
| [teardown-personal-test.sh](./env/teardown-personal-test.sh) | Sandbox only: destroy bootstrap; `--delete-project` removes GCP project |

## Deploy (`deploy/`)

| Script | Purpose |
|--------|---------|
| [deploy-mcp-cloudrun.sh](./deploy/deploy-mcp-cloudrun.sh) | Build + deploy MCP to Cloud Run |
| [import-mcp-infra-state.sh](./deploy/import-mcp-infra-state.sh) | Import existing MCP infra into Terraform state |

## Library (`lib/`)

| Script | Purpose |
|--------|---------|
| [load-config.sh](./lib/load-config.sh) | Load `config/enterprise.env` (or `GOLDENPATH_CONFIG`) |
| [wizard_defaults.py](./lib/wizard_defaults.py) | Wizard default config from enterprise.env |
| [scaffold-tokens.sh](./lib/scaffold-tokens.sh) | Replace `{{TOKENS}}` in scaffolds |
| [wif-credentials.sh](./lib/wif-credentials.sh) | Resolve WIF provider + SA (`shop publish`) |
| [wif-trust-repo.sh](./lib/wif-trust-repo.sh) | Per-repo WIF IAM bindings |
| [verify-deployment.sh](./lib/verify-deployment.sh) | Cloud Run health polling |
| [teardown-safety.sh](./lib/teardown-safety.sh) | Protected-project checks |

## Tests

Setup wizard tests live in [`tests/`](../tests/) (Pester for PowerShell wizard).

**Explain script layout:** `./scripts/check-repo-hygiene.sh --explain`