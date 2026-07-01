# 6. Wizard — PowerShell advanced (optional)

**Getting started · Doc 6 of 10** · [Index](./readme.md) · **Primary wizard doc:** [05-journey-wizard.md](./05-journey-wizard.md)

How to **install `pwsh`, run scripts directly, and automate** the wizard modules — for contributors, CI, and power users.

**Most users should start with [05-journey-wizard.md](./05-journey-wizard.md)** — use bash or Python backends if you do not have `pwsh`. Use **this doc** when you need dot-sourcing, headless `Invoke-GoldenPath*` calls, or Pester tests. For the bash `shop` CLI, see [04-journey-cli.md](./04-journey-cli.md).

**Config file:** `.goldenpath-setup.local.json` (gitignored) — separate from the CLI's `.goldenpath-cli.local.json`. See [02-pick-your-path.md](./02-pick-your-path.md).

**Repo map:** [repository-guide.md](../repository-guide.md)

---

## 1. The journey in one picture

```
Install pwsh  →  verify with pwsh --version
        ↓
cd goldenpath
        ↓
pwsh ./scripts/setup/goldenpath-setup.ps1 --wizard
   (or ./scripts/goldenpath-setup.sh)
        ↓
Bootstrap GCP  →  Invoke-GoldenPathBootstrap (gcloud + terraform)
        ↓
WIF secrets detected  →  saved to .goldenpath-setup.local.json
        ↓
Invoke-GoldenPathScaffold  →  service repo on disk
        ↓
Invoke-GoldenPathPublish  →  GitHub repo + secrets + WIF trust + push main
        ↓
GitHub Actions  →  dev Cloud Run
        ↓
Invoke-GoldenPathVerifyDeployment  →  health check
        ↓
Daily: edit → git push main → auto-deploy dev
        ↓
Invoke-GoldenPathTeardown  →  destroy sandbox (optional)
```

---

## Step 1 — Install PowerShell

The wizard and modules require **PowerShell 7+** (`pwsh`), not Windows PowerShell 5.1.

| OS | Install |
|----|---------|
| **macOS** | `brew install powershell` |
| **Windows** | Built into Windows 11; or [install PowerShell 7](https://learn.microsoft.com/powershell/scripting/install/installing-powershell-on-windows) |
| **Linux** | [Install PowerShell](https://learn.microsoft.com/powershell/scripting/install/installing-powershell-on-linux) |

Verify:

```bash
pwsh --version
# PowerShell 7.x.x
```

**No `pwsh`?** Use bash or Python backends: `./scripts/goldenpath-setup-bash.sh` or `-py.sh`. Streamlit UI also available: `./scripts/goldenpath-setup-ui.sh`. See [05-journey-wizard.md](./05-journey-wizard.md).

---

## Step 2 — Prerequisites (called by the scripts)

PowerShell scripts shell out to these tools. Install before bootstrap or publish:

| Tool | Purpose |
|------|---------|
| `gcloud` | GCP auth, project create, WIF lookup |
| `terraform` | Platform bootstrap (`platform/bootstrap/`) |
| `git` | Scaffold init, publish push |
| `gh` | Create repos, set GitHub secrets |

Authenticate once:

```bash
gcloud auth login
gcloud auth application-default login
gcloud auth application-default set-quota-project YOUR_GCP_SANDBOX_PROJECT
```

---

## Step 3 — How to execute PowerShell scripts

All commands assume you are in the **goldenpath** repo root.

### Recommended — bash launcher (auto-finds `pwsh`)

```bash
./scripts/goldenpath-setup.sh              # interactive menu
./scripts/goldenpath-setup.sh --wizard     # full guided setup, no menu
./scripts/goldenpath-setup.sh --help
./scripts/goldenpath-setup.sh --dryrun
```

Implementation: [`scripts/goldenpath-setup.sh`](../../scripts/goldenpath-setup.sh) → `pwsh -File scripts/setup/goldenpath-setup.ps1`

### Direct PowerShell

```bash
pwsh ./scripts/setup/goldenpath-setup.ps1
pwsh ./scripts/setup/goldenpath-setup.ps1 --wizard
pwsh ./scripts/setup/goldenpath-setup.ps1 --dryrun
pwsh ./scripts/setup/goldenpath-setup.ps1 -h          # comprehensive built-in help
```

Shim (same target):

```bash
pwsh ./scripts/goldenpath-setup.ps1 --help
```

### Run tests

```bash
pwsh ./tests/Run-SetupWizardTests.ps1
# or
pwsh -Command "Invoke-Pester tests/goldenpath-setup.tests.ps1 -Output Detailed"
```

### Dot-source modules (automation / CI)

Load functions without starting the menu:

```powershell
$RepoRoot = (Resolve-Path ".").Path
. ./scripts/setup/modules/Scaffold.ps1
. ./scripts/setup/modules/Bootstrap.ps1
. ./scripts/setup/modules/Publish.ps1
. ./scripts/setup/modules/Verify.ps1
```

Dot-sourcing `goldenpath-setup.ps1` itself also works — it defines functions but skips the menu when dot-sourced (used by Pester tests).

---

## Step 4 — PowerShell script inventory

| Script | Role |
|--------|------|
| [`scripts/setup/goldenpath-setup.ps1`](../../scripts/setup/goldenpath-setup.ps1) | Main wizard — menu, config, orchestration |
| [`scripts/goldenpath-setup.ps1`](../../scripts/goldenpath-setup.ps1) | Thin shim → `setup/goldenpath-setup.ps1` |
| [`scripts/setup/modules/Bootstrap.ps1`](../../scripts/setup/modules/Bootstrap.ps1) | `gcloud` project + billing + `terraform apply` |
| [`scripts/setup/goldenpath_ops.py`](../../scripts/setup/goldenpath_ops.py) | Shared scaffold / publish / doctor / upgrade (imported by Python + Streamlit) |
| [`scripts/setup/goldenpath_ops_cli.py`](../../scripts/setup/goldenpath_ops_cli.py) | CLI used by bash wizard, `shop`, and PS upgrade/doctor |
| [`scripts/setup/modules/OpsCli.ps1`](../../scripts/setup/modules/OpsCli.ps1) | `Invoke-GoldenPathUpgradePlatformPins` → ops CLI |
| [`scripts/setup/modules/Scaffold.ps1`](../../scripts/setup/modules/Scaffold.ps1) | Copy template, replace tokens, upgrade pins, `git init` |
| [`scripts/setup/modules/Publish.ps1`](../../scripts/setup/modules/Publish.ps1) | `gh repo create`, WIF trust, secrets, deploy watch, upgrade pins |
| [`scripts/setup/modules/Verify.ps1`](../../scripts/setup/modules/Verify.ps1) | Poll Cloud Run URL + health paths |
| [`tests/goldenpath-setup.tests.ps1`](../../tests/goldenpath-setup.tests.ps1) | Pester unit tests |
| [`tests/Run-SetupWizardTests.ps1`](../../tests/Run-SetupWizardTests.ps1) | Test runner (installs Pester if missing) |

The PowerShell wizard does **not** call `cli/shop` (separate config file). Scaffold and publish orchestrate via PS modules but share **`goldenpath_ops`** for upgrade pins and doctor checks via `goldenpath_ops_cli.py`.

---

## Step 5 — Interactive journey (menu or `--wizard`)

### Start the wizard

```bash
./scripts/goldenpath-setup.sh --wizard
```

**What `--wizard` runs (steps 1–6):**

1. Choose GCP profile (sandbox, new sandbox, or existing project)
2. Check prerequisites + offer `gcloud auth login`
3. Bootstrap — `Invoke-GoldenPathBootstrap` writes `platform/bootstrap/terraform.tfvars` and runs Terraform
4. Detect WIF secrets (terraform state, then gcloud fallback)
5. Optionally scaffold — `Invoke-GoldenPathScaffold`
6. Optionally write Claude MCP config

Settings persist to `.goldenpath-setup.local.json`. Resume anytime:

```bash
./scripts/goldenpath-setup.sh    # menu — options 3–15 for individual steps
```

Menu reference: [07-setup-wizard-usage.md](./07-setup-wizard-usage.md) · narrative: [05-journey-wizard.md](./05-journey-wizard.md)

### Finish deploy (after wizard)

| Goal | Menu option | Underlying function |
|------|-------------|---------------------|
| Publish to GitHub | **7** | `Invoke-GoldenPathPublish` |
| Verify health | **8** | `Invoke-GoldenPathVerifyDeployment` |
| Diagnose blockers | **9** | `Test-GoldenPathServiceDoctor` |
| Show status | **11** | `Show-Status` |
| Tear down sandbox | **13** | `Invoke-GoldenPathTeardown` |

---

## Step 6 — Scripted journey (headless modules)

Use this when you want repeatable automation without the interactive menu.

### Config hashtable

Match fields from `Get-DefaultConfig` in the wizard:

```powershell
$RepoRoot = (Resolve-Path ".").Path
$cfg = @{
    profile              = "sandbox"
    gcp_project          = "YOUR_GCP_SANDBOX_PROJECT"
    project_display_name = "Golden Path Sandbox"
    gcp_region           = "<GCP_REGION>"           # from config/enterprise.env
    github_org           = "YOUR_GITHUB_ORG"
    github_platform_repo = "<PLATFORM_REPO>"      # from config/enterprise.env
    goldenpath_version   = "<GOLDENPATH_VERSION>" # from config/enterprise.env
    gcp_dev_project      = "YOUR_GCP_SANDBOX_PROJECT"
    gcp_prod_project     = "YOUR_GCP_SANDBOX_PROJECT"
    sandbox_disposable   = $true
}
```

Defaults also load from [`config/enterprise.env`](../../config/enterprise.env).

### External-command adapter

Modules expect a scriptblock that runs CLI tools and returns exit code + stdout/stderr:

```powershell
$invoke = {
    param([string]$Exe, [string[]]$ArgumentList, [string]$WorkDir = "")
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        if ($WorkDir) { Push-Location $WorkDir }
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $Exe
        $psi.Arguments = ($ArgumentList -join ' ')
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.UseShellExecute = $false
        $p = [System.Diagnostics.Process]::Start($psi)
        $p.WaitForExit() | Out-Null
        [PSCustomObject]@{
            ExitCode = $p.ExitCode
            StdOut   = $p.StandardOutput.ReadToEnd()
            StdErr   = $p.StandardError.ReadToEnd()
        }
    } finally {
        if ($WorkDir) { Pop-Location }
        $ErrorActionPreference = $prev
    }
}
```

The wizard uses `Get-InvokeExternalAdapter` — same pattern.

### Bootstrap

```powershell
. ./scripts/setup/modules/Bootstrap.ps1
Invoke-GoldenPathBootstrap -RepoRoot $RepoRoot -Config $cfg -InvokeExternal $invoke
```

Creates the GCP project (if missing), links billing, writes `terraform.tfvars`, runs `terraform apply`.

### Scaffold

```powershell
. ./scripts/setup/modules/Scaffold.ps1
$result = Invoke-GoldenPathScaffold `
    -RepoRoot $RepoRoot `
    -ServiceName "my-streamlit-app" `
    -Template "streamlit" `
    -OutputDir "/tmp/services" `
    -Config $cfg
$result.ServiceDir   # path to scaffolded repo
```

### Publish (requires WIF credentials + `gh` auth)

```powershell
. ./scripts/setup/modules/Publish.ps1
# Obtain WIF from terraform or gcloud first (wizard option 4 does this)
Invoke-GoldenPathPublish `
    -ServiceDir $result.ServiceDir `
    -RepoRoot $RepoRoot `
    -Config $cfg `
    -WifProvider $wifProvider `
    -WifServiceAccount $wifSa `
    -InvokeExternal $invoke `
    -WatchDeploy
```

### Verify

```powershell
. ./scripts/setup/modules/Verify.ps1
$cloudRunName = "$($result.ServiceName)-dev"
$verify = Invoke-GoldenPathVerifyDeployment `
    -CloudRunService $cloudRunName `
    -ServiceDir $result.ServiceDir `
    -RepoRoot $RepoRoot `
    -Config $cfg `
    -InvokeExternal $invoke
$verify.Url
$verify.HealthOk
```

### Teardown

```powershell
. ./scripts/setup/modules/Bootstrap.ps1
Invoke-GoldenPathTeardown -RepoRoot $RepoRoot -DeleteProject $true -InvokeExternal $invoke
```

Safety: refuses protected project IDs (`YOUR_BILLING_ANCHOR_PROJECT`, etc.) and requires `personal_test = true` in `terraform.tfvars`.

---

## Step 7 — Run tests

Validate wizard logic without touching GCP:

```bash
pwsh ./tests/Run-SetupWizardTests.ps1
```

Covers project ID validation, service name rules, config load/save, WIF staleness detection. See [tests/README.md](../../tests/README.md).

Install Pester manually if needed:

```bash
pwsh -Command "Install-Module Pester -Force -SkipPublisherCheck -Scope CurrentUser"
```

---

## 8. Execution notes

### Working directory

`goldenpath-setup.ps1` calls `Set-Location $RepoRoot` on startup. Run it from anywhere, but relative paths in your own scripts should assume repo root.

### Execution policy

macOS/Linux installs typically allow local scripts. On Windows, if you see an execution policy error:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Or invoke with bypass:

```bash
pwsh -ExecutionPolicy Bypass -File ./scripts/setup/goldenpath-setup.ps1 --help
```

### What PowerShell does vs bash scripts

| Task | PowerShell module | Bash alternative |
|------|-------------------|------------------|
| Bootstrap | `Invoke-GoldenPathBootstrap` | `./scripts/standup-teardown-env.sh` |
| Scaffold | `Invoke-GoldenPathScaffold` | `./cli/shop new` |
| Publish | `Invoke-GoldenPathPublish` | `./cli/shop publish` |
| Teardown | `Invoke-GoldenPathTeardown` | `./scripts/teardown-personal-test.sh` |

Pick one path per workflow. PowerShell and CLI config files are not interchangeable.

---

## 9. Troubleshooting

| Issue | Fix |
|-------|-----|
| `pwsh: command not found` | `brew install powershell` (macOS) or use `./scripts/goldenpath-setup-ui.sh` |
| `Golden Path setup wizard requires PowerShell` | Same — bash launcher could not find `pwsh` or `powershell` |
| `ParserError` / module won't load | Check `scripts/setup/modules/*.ps1` syntax; run `pwsh -File ... --help` |
| `terraform apply failed` | Run `gcloud auth login`; confirm billing on project |
| `WIF credentials missing` | Run bootstrap (menu **3** or `Invoke-GoldenPathBootstrap`) first |
| `deploy.yml still has unreplaced template tokens` | Re-run scaffold or `Repair-GoldenPathScaffoldTokens` |
| `Not a git repo` | Scaffold first (menu **6** or `Invoke-GoldenPathScaffold`) |
| Mixed CLI + wizard config | Use `.goldenpath-setup.local.json` **or** `.goldenpath-cli.local.json`, not both |

---

## 10. Related docs

| # | Doc | When to read |
|---|-----|--------------|
| 5 | [05-journey-wizard.md](./05-journey-wizard.md) | Primary wizard narrative |
| 7 | [07-setup-wizard-usage.md](./07-setup-wizard-usage.md) | Menu reference (options 1–15) |
| 4 | [04-journey-cli.md](./04-journey-cli.md) | Bash `shop` CLI path |
| 8 | [08-journey-mcp.md](./08-journey-mcp.md) | Claude MCP path |
| — | [sandbox-env.md](../environments/sandbox-env.md) | Sandbox teardown details |