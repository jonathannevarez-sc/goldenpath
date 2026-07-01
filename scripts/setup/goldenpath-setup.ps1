#!/usr/bin/env pwsh
# Golden Path GCP — Interactive Setup Wizard (PowerShell backend)
# Usage: pwsh ./scripts/setup/goldenpath-setup.ps1 [-h|--help] [--wizard] [--dryrun]
#        ./scripts/goldenpath-setup.sh              # auto launcher (pwsh → this script)
#        ./scripts/goldenpath-setup-ps.sh           # same as --backend ps
# Docs:  docs/getting-started/07-setup-wizard-usage.md
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Script:RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
$Script:ConfigPath = Join-Path $RepoRoot ".goldenpath-setup.local.json"
$Script:ModulesDir = Join-Path $PSScriptRoot "modules"
. (Join-Path $Script:ModulesDir "Scaffold.ps1")
. (Join-Path $Script:ModulesDir "Bootstrap.ps1")
. (Join-Path $Script:ModulesDir "Publish.ps1")
. (Join-Path $Script:ModulesDir "Verify.ps1")
$Script:BootstrapDir = Join-Path $RepoRoot "platform/bootstrap"
$Script:EnterpriseEnv = Join-Path $RepoRoot "config/enterprise.env"

# ── UI helpers ────────────────────────────────────────────────────────────────

function Write-Banner {
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "  ║    Golden Path GCP — PowerShell Wizard (not shop CLI)    ║" -ForegroundColor Cyan
    Write-Host "  ╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step([int]$Number, [int]$Total, [string]$Title) {
    Write-Host ""
    Write-Host "  ── Step $Number of $Total : $Title ──" -ForegroundColor Yellow
    Write-Host ""
}

function Write-Ok([string]$Message) { Write-Host "  ✓ $Message" -ForegroundColor Green }
function Write-Warn([string]$Message) { Write-Host "  ! $Message" -ForegroundColor Yellow }
function Write-Err([string]$Message) { Write-Host "  ✗ $Message" -ForegroundColor Red }

function Read-Choice([string]$Prompt, [string[]]$Options, [int]$Default = 0) {
    for ($i = 0; $i -lt $Options.Length; $i++) {
        $mark = if ($i -eq $Default) { "*" } else { " " }
        Write-Host "  [$mark] $($i + 1)) $($Options[$i])"
    }
    $raw = Read-Host "  $Prompt [default=$($Default + 1)]"
    if ([string]::IsNullOrWhiteSpace($raw)) { return $Default }
    $n = 0
    if (-not [int]::TryParse($raw, [ref]$n) -or $n -lt 1 -or $n -gt $Options.Length) {
        Write-Warn "Invalid choice — using default."
        return $Default
    }
    return $n - 1
}

function Read-Input([string]$Prompt, [string]$Default = "") {
    if ($Default) {
        $raw = Read-Host "  $Prompt [$Default]"
        if ([string]::IsNullOrWhiteSpace($raw)) { return $Default }
        return $raw.Trim()
    }
    do {
        $raw = Read-Host "  $Prompt"
    } while ([string]::IsNullOrWhiteSpace($raw))
    return $raw.Trim()
}

function Confirm([string]$Prompt, [bool]$DefaultYes = $true) {
    $hint = if ($DefaultYes) { "Y/n" } else { "y/N" }
    $raw = Read-Host "  $Prompt [$hint]"
    if ([string]::IsNullOrWhiteSpace($raw)) { return $DefaultYes }
    return $raw -match '^[Yy]'
}

function Press-Enter([string]$Message = "Press Enter to continue...") {
    Read-Host "  $Message" | Out-Null
}

function Invoke-ExternalLive([string]$Exe, [string[]]$ArgumentList, [string]$WorkDir = $RepoRoot) {
    Push-Location $WorkDir
    $prev = $ErrorActionPreference
    try {
        Write-Host "  (live output below)" -ForegroundColor DarkGray
        Write-Host ""
        try {
            $ErrorActionPreference = "Continue"
            & $Exe @ArgumentList 2>&1 | ForEach-Object {
                if ($_ -is [System.Management.Automation.ErrorRecord]) {
                    Write-Host $_.ToString() -ForegroundColor Yellow
                } else {
                    Write-Host $_
                }
            }
        } finally {
            $ErrorActionPreference = $prev
        }
        $exit = if ($null -ne $LASTEXITCODE) { $LASTEXITCODE } else { 0 }
        return [PSCustomObject]@{ ExitCode = $exit; StdOut = ""; StdErr = "" }
    } finally {
        Pop-Location
    }
}

function Invoke-External([string]$Exe, [string[]]$ArgumentList, [string]$WorkDir = $RepoRoot) {
    Push-Location $WorkDir
    $prev = $ErrorActionPreference
    try {
        try {
            $ErrorActionPreference = "Continue"
            $merged = & $Exe @ArgumentList 2>&1
        } finally {
            $ErrorActionPreference = $prev
        }
        $exit = if ($null -ne $LASTEXITCODE) { $LASTEXITCODE } else { 0 }

        $stdout = @()
        $stderr = @()
        foreach ($line in @($merged)) {
            if ($line -is [System.Management.Automation.ErrorRecord]) {
                $stderr += $line.ToString()
            } else {
                $stdout += [string]$line
            }
        }
        return [PSCustomObject]@{
            ExitCode = $exit
            StdOut   = ($stdout -join "`n")
            StdErr   = ($stderr -join "`n")
        }
    } finally {
        Pop-Location
    }
}

function Test-Command([string]$Name) {
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

# ── Config persistence ────────────────────────────────────────────────────────

$Script:ProtectedProjects = @()

function Show-Usage {
    Write-Host @"

  ╔══════════════════════════════════════════════════════════════════════════╗
  ║         Golden Path GCP — PowerShell Setup Wizard (-h / --help)          ║
  ╚══════════════════════════════════════════════════════════════════════════╝

  WHAT THIS IS
    Interactive wizard for Golden Path on GCP: bootstrap a project, get GitHub
    deploy credentials (WIF), scaffold a service from a template, publish to
    GitHub, watch deploy, and verify Cloud Run + health.

    This is the PowerShell backend. Same menu exists in bash, Python, and
    Streamlit — they share goldenpath_ops so scaffold/publish/doctor behave
    the same. Do NOT mix this wizard with ./cli/shop (separate config file).

  ── HOW TO RUN ────────────────────────────────────────────────────────────

    From the goldenpath repo root:

      ./scripts/goldenpath-setup.sh                 # auto (uses pwsh if installed)
      ./scripts/goldenpath-setup-ps.sh              # this script explicitly
      pwsh ./scripts/setup/goldenpath-setup.ps1     # direct

    Other backends (no pwsh required):
      ./scripts/goldenpath-setup-bash.sh
      ./scripts/goldenpath-setup-py.sh
      ./scripts/goldenpath-setup-ui.sh              # Streamlit browser UI

  ── COMMAND-LINE FLAGS ──────────────────────────────────────────────────────

    (no args)       Interactive menu (default)
    --wizard        Full guided setup — 6 steps, no menu (best for new users)
    --dryrun        Read-only audit (menu 15) — no GCP/GitHub changes
    -h, --help, -?  This help (also type h at the main menu)

  ── BEFORE YOU START ─────────────────────────────────────────────────────────

    1. Copy and edit team settings:
         cp config/enterprise.env.example config/enterprise.env

       Required keys: PARENT_PROJECT_ID, BILLING_ACCOUNT_ID, GITHUB_ORG
       Team-owned pins (version, org, GCP) always come from enterprise.env.

    2. Install tools (menu 2 checks these):
         gcloud, terraform, git, gh  — required
         python3                     — dry run, upgrade pins, shared ops
         docker, pwsh                — optional (MCP / Docker)

    3. Log in:
         gcloud auth login
         gcloud auth application-default login
         gh auth login
         gh auth switch --user YOUR_GITHUB_ORG   # must match enterprise.env

  ── FULL MENU (type the number at the prompt) ───────────────────────────────

     1   Full guided setup (recommended first time)
         Profile → prerequisites → bootstrap → WIF → scaffold/publish → MCP

     2   Check prerequisites (gcloud, terraform, git, gh, python3)
     3   Bootstrap GCP — create/link project, terraform apply, WIF pool
     4   Show GitHub WIF secrets (auto-detect from Terraform or gcloud)
     5   Set WIF secrets on a repo via gh (platform or service repo)
     6   Scaffold a new service (template → folder outside platform repo)
     7   Publish service — GitHub repo, secrets, WIF trust, push, deploy watch
     8   Verify deployment — Cloud Run URL + health check (retries cold start)
     9   Doctor — diagnose blockers (branch, secrets, pins, gh account)
    10   Generate Claude MCP config (mcp/claude-mcp.generated.json)
    11   Show current status (project, WIF, last service, Cloud Run list)
    12   Edit settings — project profile, org, region, platform repo
    13   Tear down sandbox (destroy resources; optional project delete)
    14   Fresh start — reset .goldenpath-setup.local.json to defaults
    15   Dry run — read-only audit of what the wizard would do
     h   Help / usage (same as -h)
     0   Exit

  ── PROJECT PROFILES (menu 12 — Edit settings) ──────────────────────────────

     1) Sandbox profile
        Uses GCP_SANDBOX_PROJECT from config/enterprise.env.
        Disposable — tear down with menu 13.

     2) New self-contained sandbox
        You pick a globally unique project ID (e.g. my-org-gp-sandbox-2026).
        Wizard creates the project, links billing, runs bootstrap.
        Delete everything later with menu 13.

     3) Custom existing project
        Use a GCP project that already exists (you manage lifecycle).

    Project ID rules: 6–30 chars, lowercase, start with a letter, no trailing
    hyphen. Protected projects (PARENT_PROJECT_ID, etc.) cannot be sandboxes.

    IMPORTANT: Bootstrap (3), WIF (4), and scaffold (6) must use the SAME
    project ID. If you change project in menu 12, re-run bootstrap and menu 4.

  ── RECOMMENDED JOURNEYS ────────────────────────────────────────────────────

    Brand-new user (fastest path):
      ./scripts/goldenpath-setup.sh --wizard
      OR menu 1 → follow prompts through bootstrap, WIF, optional scaffold

    Your own disposable sandbox:
      menu 12 → profile 2 → enter project ID
      menu 3  → bootstrap
      menu 6  → scaffold (e.g. demo-streamlit)
      menu 7  → publish (or say yes when scaffold asks)
      menu 13 → tear down when finished

    Resume after a break:
      menu 11 → see current project + services
      menu 4  → refresh WIF secrets if needed
      menu 7  → publish or retry deploy

    Something failed:
      menu 9  → doctor lists blockers
      menu 7  → publish again (auto-repairs pins, WIF trust, deploy rerun)
      menu 8  → verify health after deploy succeeds

    Audit without changes:
      --dryrun  OR  menu 15

  ── SCAFFOLD & PUBLISH (menus 6–7) ──────────────────────────────────────────

    Scaffold creates a folder NEXT TO the platform repo (not inside it):
      ../<service-name>/   by default

    Templates: nextjs (default), fastapi, streamlit, express, react-spa, svelte-spa
    Pins workflow to GOLDENPATH_VERSION from enterprise.env (currently v0.3.7).

    Publish does (in order):
      [1/5] Create GitHub repo (visibility matches platform repo)
      [2/5] Set GCP_WIF_PROVIDER + GCP_WIF_SERVICE_ACCOUNT secrets
      [3/5] Add WIF IAM trust for the service repo
      [4/5] Push main branch
      [5/5] Watch deploy.yml workflow + verify Cloud Run health

    Active gh account must match GITHUB_ORG or publish will stop with a fix hint.

  ── SAVED SETTINGS ──────────────────────────────────────────────────────────

    Wizard state:  .goldenpath-setup.local.json  (gitignored, repo root)
    Team defaults: config/enterprise.env           (committed by you, not secrets)

    enterprise.env wins for: goldenpath_version, github_org, platform repo,
    gcp_dev_project, gcp_prod_project, gcp_region.

    Shop CLI uses a SEPARATE file: .goldenpath-cli.local.json — do not mix.

  ── TROUBLESHOOTING (quick fixes) ───────────────────────────────────────────

    "WIF credentials missing"        → menu 3 (bootstrap), then menu 4
    "gh account ≠ GITHUB_ORG"        → gh auth switch --user YOUR_GITHUB_ORG
    "deploy workflow failed"         → menu 7 retry; check GitHub Actions logs
    "health check not ready"         → wait 30s, menu 8; cold start is normal
    "deploy.yml wrong version/org"   → publish auto-upgrades pins; or menu 7 again
    "project_id mismatch"            → menu 12 fix project, re-scaffold or menu 7
    "protected project"              → pick a different ID in menu 12 profile 2

    Teardown (menu 13) never deletes PROTECTED_PROJECTS from enterprise.env.

  ── NOT THIS WIZARD? ────────────────────────────────────────────────────────

    Headless / CI-style CLI (bash only):
      ./cli/shop list
      ./cli/shop new <name> --template fastapi
      ./cli/shop publish <dir>
      ./cli/shop doctor <dir>

    Docs (read in order for full story):
      docs/getting-started/05-journey-wizard.md       — end-to-end narrative
      docs/getting-started/07-setup-wizard-usage.md   — menu reference (all backends)
      docs/getting-started/06-wizard-powershell-advanced.md — PS-specific depth

"@
}

function Test-ProjectId([string]$ProjectId) {
    if ($ProjectId.Length -lt 6 -or $ProjectId.Length -gt 30) {
        return "Project ID must be 6–30 characters."
    }
    if ($ProjectId -notmatch '^[a-z][a-z0-9-]*[a-z0-9]$') {
        return "Use lowercase letters, numbers, and hyphens; must start with a letter and not end with a hyphen."
    }
    if ($ProjectId -match '--') {
        return "Project ID cannot contain consecutive hyphens."
    }
    if ($Script:ProtectedProjects -contains $ProjectId) {
        return "Project '$ProjectId' is protected and cannot be used as a sandbox."
    }
    return $null
}

function Get-ProtectedProjectsFromEnv {
    if (-not (Test-Path $EnterpriseEnv)) { return @() }
    $csv = ""
    Get-Content $EnterpriseEnv | ForEach-Object {
        if ($_ -match '^\s*PROTECTED_PROJECTS=(.*)$') { $csv = $Matches[1].Trim() }
    }
    if ([string]::IsNullOrWhiteSpace($csv)) { return @() }
    return @($csv.Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ })
}

function Get-EnterpriseProfile {
    $merged = @{}
    $example = Join-Path $RepoRoot "config/enterprise.env.example"
    if (Test-Path $example) {
        Get-Content $example | ForEach-Object {
            if ($_ -match '^\s*([A-Z_]+)=(.*)$') {
                $merged[$Matches[1]] = $Matches[2].Trim().Trim('"')
            }
        }
    }
    if (Test-Path $EnterpriseEnv) {
        Get-Content $EnterpriseEnv | ForEach-Object {
            if ($_ -match '^\s*([A-Z_]+)=(.*)$') {
                $merged[$Matches[1]] = $Matches[2].Trim().Trim('"')
            }
        }
    }
    return $merged
}

function Get-DefaultConfig {
    $p = Get-EnterpriseProfile
    $sandbox = if ($p.GCP_SANDBOX_PROJECT) { $p.GCP_SANDBOX_PROJECT }
               elseif ($p.GCP_DEV_PROJECT) { $p.GCP_DEV_PROJECT } else { "" }
    $dev = if ($p.GCP_DEV_PROJECT) { $p.GCP_DEV_PROJECT } else { $sandbox }
    $prod = if ($p.GCP_PROD_PROJECT) { $p.GCP_PROD_PROJECT } else { $dev }

    $cfg = [ordered]@{
        profile              = "sandbox"
        gcp_project          = $sandbox
        project_display_name = $p.SANDBOX_PROJECT_NAME
        gcp_region           = $p.GCP_REGION
        github_org           = $p.GITHUB_ORG
        github_platform_repo = $p.PLATFORM_REPO
        goldenpath_version   = $p.GOLDENPATH_VERSION
        gcp_dev_project      = $dev
        gcp_prod_project     = $prod
        sandbox_disposable   = $true
        wif_provider         = ""
        wif_service_account  = ""
        last_service         = ""
        last_service_dir     = ""
    }

    $Script:ProtectedProjects = Get-ProtectedProjectsFromEnv
    return $cfg
}

function Get-ScaffoldOutputDir {
    return Split-Path $RepoRoot -Parent
}

function Get-DefaultServiceDir($Config) {
    if (-not $Config.last_service) { return $null }
    if ($Config.last_service_dir -and (Test-Path $Config.last_service_dir)) {
        return $Config.last_service_dir
    }
    $outside = Join-Path (Get-ScaffoldOutputDir) $Config.last_service
    if (Test-Path $outside) { return $outside }
    $inside = Join-Path $RepoRoot $Config.last_service
    if (Test-Path $inside) { return $inside }
    return $outside
}

function Get-Config {
    $defaults = Get-DefaultConfig
    if (-not (Test-Path $ConfigPath)) { return $defaults }

    try {
        $raw = Get-Content $ConfigPath -Raw
        $saved = $raw | ConvertFrom-Json
        foreach ($key in @($defaults.Keys)) {
            $val = if ($saved.PSObject.Properties.Name -contains $key) { $saved.$key } else { $null }
            if ($null -eq $val) { continue }
            if ($val -is [bool]) {
                $defaults[$key] = $val
            } elseif ("$val".Length -gt 0) {
                $defaults[$key] = "$val"
            }
        }
    } catch {
        Write-Warn "Could not read saved config — using defaults."
    }

    if ($defaults.profile -in @('teardown', 'enterprise')) {
        $defaults.profile = 'sandbox'
    }

    if (($defaults.wif_provider -and -not (Test-GoldenPathWifProvider $defaults.wif_provider)) -or
        ($defaults.wif_service_account -and -not (Test-GoldenPathWifServiceAccount $defaults.wif_service_account))) {
        Write-Warn "Saved WIF credentials are invalid — clearing (run bootstrap, then menu 4)."
        $defaults.wif_provider = ""
        $defaults.wif_service_account = ""
        if (Test-Path $ConfigPath) {
            [System.IO.File]::WriteAllText($ConfigPath, ($defaults | ConvertTo-Json -Depth 5))
        }
    }

    $enterprise = Get-EnterpriseProfile
    foreach ($pair in @(
        @{ cfg = 'goldenpath_version'; env = 'GOLDENPATH_VERSION' },
        @{ cfg = 'github_org'; env = 'GITHUB_ORG' },
        @{ cfg = 'github_platform_repo'; env = 'PLATFORM_REPO' },
        @{ cfg = 'gcp_dev_project'; env = 'GCP_DEV_PROJECT' },
        @{ cfg = 'gcp_prod_project'; env = 'GCP_PROD_PROJECT' },
        @{ cfg = 'gcp_region'; env = 'GCP_REGION' }
    )) {
        if ($enterprise.($pair.env)) {
            $defaults.($pair.cfg) = $enterprise.($pair.env)
        }
    }
    if ($enterprise.GCP_SANDBOX_PROJECT -and $defaults.profile -eq 'sandbox') {
        $defaults.gcp_project = $enterprise.GCP_SANDBOX_PROJECT
    }
    return $defaults
}

function Save-Config($Config) {
    $enterprise = Get-EnterpriseProfile
    foreach ($pair in @(
        @{ cfg = 'goldenpath_version'; env = 'GOLDENPATH_VERSION' },
        @{ cfg = 'github_org'; env = 'GITHUB_ORG' },
        @{ cfg = 'github_platform_repo'; env = 'PLATFORM_REPO' },
        @{ cfg = 'gcp_dev_project'; env = 'GCP_DEV_PROJECT' },
        @{ cfg = 'gcp_prod_project'; env = 'GCP_PROD_PROJECT' },
        @{ cfg = 'gcp_region'; env = 'GCP_REGION' }
    )) {
        if ($enterprise.($pair.env)) {
            $Config.($pair.cfg) = $enterprise.($pair.env)
        }
    }
    $json = $Config | ConvertTo-Json -Depth 5
    [System.IO.File]::WriteAllText($ConfigPath, $json)
    Write-Ok "Settings saved to .goldenpath-setup.local.json"
}

# ── Prerequisites & auth ──────────────────────────────────────────────────────

function Test-Prerequisites {
    Write-Step 1 1 "Checking prerequisites"
    $required = @(
        @{ Name = "gcloud";  Install = "https://cloud.google.com/sdk/docs/install" }
        @{ Name = "terraform"; Install = "https://developer.hashicorp.com/terraform/install" }
        @{ Name = "git";     Install = "https://git-scm.com/" }
        @{ Name = "gh";      Install = "https://cli.github.com/" }
    )
    $optional = @("python3", "docker", "pwsh")

    $allOk = $true
    foreach ($tool in $required) {
        if (Test-Command $tool.Name) {
            Write-Ok "$($tool.Name) found"
        } else {
            Write-Err "$($tool.Name) missing — install: $($tool.Install)"
            $allOk = $false
        }
    }
    foreach ($tool in $optional) {
        if (Test-Command $tool) { Write-Ok "$tool found (optional)" }
        else { Write-Warn "$tool not found (optional — needed for MCP / Docker)" }
    }
    return $allOk
}

function Test-GcloudAuth {
    $acct = Invoke-External "gcloud" @("auth", "list", "--filter=status:ACTIVE", "--format=value(account)")
    if ($acct.ExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($acct.StdOut.Trim())) {
        Write-Warn "Not logged in to gcloud."
        if (Confirm "Open browser for 'gcloud auth login' now?") {
            Invoke-External "gcloud" @("auth", "login") | Out-Null
        } else { return $false }
    } else {
        Write-Ok "gcloud account: $($acct.StdOut.Trim())"
    }

    $adc = Invoke-External "gcloud" @("auth", "application-default", "print-access-token")
    if ($adc.ExitCode -ne 0) {
        Write-Warn "Application Default Credentials not set (Terraform needs these)."
        if (Confirm "Run 'gcloud auth application-default login' now?") {
            Invoke-External "gcloud" @("auth", "application-default", "login") | Out-Null
        } else { return $false }
    } else {
        Write-Ok "Application Default Credentials OK"
    }
    return $true
}

# ── WIF credentials (terraform → gcloud fallback) ─────────────────────────────

function Get-TerraformBootstrapProjectId {
    $proj = Invoke-External "terraform" @("output", "-raw", "project_id") -WorkDir $BootstrapDir
    if ($proj.ExitCode -eq 0 -and $proj.StdOut.Trim()) {
        return $proj.StdOut.Trim()
    }

    $tfvars = Join-Path $BootstrapDir "terraform.tfvars"
    if (Test-Path $tfvars) {
        $content = Get-Content $tfvars -Raw
        if ($content -match 'test_project_id\s*=\s*"([^"]+)"') {
            return $Matches[1]
        }
    }
    return $null
}

function Test-GoldenPathWifProvider([string]$Value) {
    if ([string]::IsNullOrWhiteSpace($Value)) { return $false }
    if ($Value -match 'Warning:|No outputs found') { return $false }
    return ($Value -match '^projects/[0-9]+/locations/global/workloadIdentityPools/[^/]+/providers/')
}

function Test-GoldenPathWifServiceAccount([string]$Value) {
    if ([string]::IsNullOrWhiteSpace($Value)) { return $false }
    if ($Value -match 'Warning:|No outputs found') { return $false }
    return ($Value -match '^github-actions@[a-z][a-z0-9-]*\.iam\.gserviceaccount\.com$')
}

function Get-WifFromTerraform([string]$ProjectId) {
    if (-not (Test-Path (Join-Path $BootstrapDir "terraform.tfvars"))) { return $null }

    $stateFiles = @(
        (Join-Path $BootstrapDir "terraform.tfstate"),
        (Join-Path $BootstrapDir ".terraform/terraform.tfstate")
    )
    $hasState = $stateFiles | Where-Object { Test-Path $_ }
    if (-not $hasState) { return $null }

    if (-not (Test-Path (Join-Path $BootstrapDir ".terraform"))) {
        Invoke-External "terraform" @("init", "-input=false") -WorkDir $BootstrapDir | Out-Null
    }

    $stateProject = Get-TerraformBootstrapProjectId
    if ($stateProject -and $stateProject -ne $ProjectId) {
        return $null
    }

    $provider = Invoke-External "terraform" @("output", "-raw", "dev_github_wif_provider_name") -WorkDir $BootstrapDir
    $sa = Invoke-External "terraform" @("output", "-raw", "dev_github_actions_sa_email") -WorkDir $BootstrapDir

    $providerValue = $provider.StdOut.Trim()
    $saValue = $sa.StdOut.Trim()
    if ($provider.ExitCode -eq 0 -and $sa.ExitCode -eq 0 -and
        (Test-GoldenPathWifProvider $providerValue) -and (Test-GoldenPathWifServiceAccount $saValue)) {
        return [PSCustomObject]@{
            Provider      = $providerValue
            ServiceAccount = $saValue
            Source        = "terraform"
        }
    }
    return $null
}

function Get-WifFromGcloud([string]$ProjectId) {
    $sa = Invoke-External "gcloud" @(
        "iam", "service-accounts", "list",
        "--project=$ProjectId",
        "--filter=email:github-actions@",
        "--format=value(email)"
    )
    if ($sa.ExitCode -ne 0 -or -not $sa.StdOut.Trim()) { return $null }

    $pool = Invoke-External "gcloud" @(
        "iam", "workload-identity-pools", "list",
        "--project=$ProjectId", "--location=global",
        "--format=value(name)"
    )
    if ($pool.ExitCode -ne 0 -or -not $pool.StdOut.Trim()) { return $null }

    $poolName = ($pool.StdOut.Trim() -split "`n" | Select-Object -First 1) -replace ".*/workloadIdentityPools/", ""
    $provider = Invoke-External "gcloud" @(
        "iam", "workload-identity-pools", "providers", "list",
        "--project=$ProjectId", "--location=global",
        "--workload-identity-pool=$poolName",
        "--format=value(name)"
    )
    if ($provider.ExitCode -ne 0 -or -not $provider.StdOut.Trim()) { return $null }

    return [PSCustomObject]@{
        Provider       = ($provider.StdOut.Trim() -split "`n" | Select-Object -First 1)
        ServiceAccount = ($sa.StdOut.Trim() -split "`n" | Select-Object -First 1)
        Source         = "gcloud"
    }
}

function Get-WifCredentials([string]$ProjectId) {
    Write-Host "  Looking up GitHub deploy credentials for project: $ProjectId" -ForegroundColor DarkGray

    $fromTf = Get-WifFromTerraform $ProjectId
    if ($fromTf) {
        Write-Ok "Found via Terraform state"
        return $fromTf
    }

    Write-Warn "No matching Terraform state for '$ProjectId' — trying gcloud API instead..."
    $fromGc = Get-WifFromGcloud $ProjectId
    if ($fromGc) {
        Write-Ok "Found via gcloud"
        return $fromGc
    }

    Write-Err "Could not find WIF credentials. Run bootstrap first (menu option 3)."
    return $null
}

function Test-WifCredentialsStale($Config) {
    $provider = Get-ScaffoldConfigValue $Config 'wif_provider'
    $sa = Get-ScaffoldConfigValue $Config 'wif_service_account'
    if ($provider -and -not (Test-GoldenPathWifProvider $provider)) { return $true }
    if ($sa -and -not (Test-GoldenPathWifServiceAccount $sa)) { return $true }
    if (-not $sa) { return $false }
    $expected = "github-actions@$($Config.gcp_dev_project).iam.gserviceaccount.com"
    return ($sa -ne $expected)
}

function Ensure-WifCredentials($Config) {
    if (Test-WifCredentialsStale $Config) {
        Write-Warn "WIF credentials are for a different project — clearing and re-looking up"
        $Config.wif_provider = ""
        $Config.wif_service_account = ""
        Save-Config $Config
    }
    if (-not $Config.wif_provider -or -not $Config.wif_service_account) {
        Show-WifSecrets $Config | Out-Null
    }
    return $Config
}

function Show-WifSecrets($Config) {
    $wif = Get-WifCredentials $Config.gcp_dev_project
    if (-not $wif) { return $false }

    $Config.wif_provider = $wif.Provider
    $Config.wif_service_account = $wif.ServiceAccount
    Save-Config $Config

    Write-Host ""
    Write-Host "  ┌─────────────────────────────────────────────────────────┐" -ForegroundColor Cyan
    Write-Host "  │  GitHub secrets — add these to your repos               │" -ForegroundColor Cyan
    Write-Host "  └─────────────────────────────────────────────────────────┘" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Secret name                  Value" -ForegroundColor White
    Write-Host "  ─────────────────────────────────────────────────────────" -ForegroundColor DarkGray
    Write-Host "  GCP_WIF_PROVIDER" -ForegroundColor Yellow -NoNewline
    Write-Host "             $($wif.Provider)"
    Write-Host "  GCP_WIF_SERVICE_ACCOUNT" -ForegroundColor Yellow -NoNewline
    Write-Host "      $($wif.ServiceAccount)"
    Write-Host ""
    Write-Host "  Source: $($wif.Source)  |  Project: $($Config.gcp_project)" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  Add to:" -ForegroundColor White
    Write-Host "    • Platform repo:  $($Config.github_org)/$($Config.github_platform_repo)"
    Write-Host "    • Each service repo you scaffold"
    Write-Host ""
    Write-Host "  Also enable reusable workflows on the platform repo:" -ForegroundColor White
    Write-Host "    GitHub → $($Config.github_platform_repo) → Settings → Actions → General"
    Write-Host "    → Allow reusable workflows from this repository"
    Write-Host ""
    return $true
}

function Set-GitHubSecrets($Config, [string]$Repo) {
    if (-not (Test-Command "gh")) {
        Write-Err "gh CLI required. Install: https://cli.github.com/"
        return
    }

    $Config = Ensure-WifCredentials $Config
    if (-not $Config.wif_provider -or -not $Config.wif_service_account) { return }

    $fullRepo = if ($Repo -match "/") { $Repo } else { "$($Config.github_org)/$Repo" }
    Write-Host "  Setting secrets on $fullRepo ..." -ForegroundColor DarkGray

    $r1 = Invoke-External "gh" @("secret", "set", "GCP_WIF_PROVIDER", "--body", $Config.wif_provider, "--repo", $fullRepo)
    $r2 = Invoke-External "gh" @("secret", "set", "GCP_WIF_SERVICE_ACCOUNT", "--body", $Config.wif_service_account, "--repo", $fullRepo)

    if ($r1.ExitCode -eq 0 -and $r2.ExitCode -eq 0) {
        Write-Ok "Secrets set on $fullRepo"
    } else {
        Write-Err "Failed to set secrets. Run: gh auth login"
        if ($r1.StdErr) { Write-Host $r1.StdErr -ForegroundColor Red }
        if ($r2.StdErr) { Write-Host $r2.StdErr -ForegroundColor Red }
    }
}

# ── Bootstrap ─────────────────────────────────────────────────────────────────

function Get-InvokeExternalAdapter() {
    return {
        param([string]$Exe, [string[]]$ArgumentList, [string]$WorkDir = "")
        if ([string]::IsNullOrWhiteSpace($WorkDir)) {
            $WorkDir = (Get-Location).Path
        }
        Push-Location $WorkDir
        $prev = $ErrorActionPreference
        try {
            try {
                $ErrorActionPreference = "Continue"
                $merged = & $Exe @ArgumentList 2>&1
            } finally {
                $ErrorActionPreference = $prev
            }
            $exit = if ($null -ne $LASTEXITCODE) { $LASTEXITCODE } else { 0 }

            $stdout = @()
            $stderr = @()
            foreach ($line in @($merged)) {
                if ($line -is [System.Management.Automation.ErrorRecord]) {
                    $stderr += $line.ToString()
                } else {
                    $stdout += [string]$line
                }
            }
            return [PSCustomObject]@{
                ExitCode = $exit
                StdOut   = ($stdout -join "`n")
                StdErr   = ($stderr -join "`n")
            }
        } finally {
            Pop-Location
        }
    }.GetNewClosure()
}

function Invoke-BootstrapStandup($Config) {
    $Config = Prompt-GcpProject $Config "bootstrap"

    $err = Test-ProjectId $Config.gcp_project
    if ($err) {
        Write-Err $err
        return $false
    }

    Write-Host ""
    Write-Host "  Project:  $($Config.gcp_project)" -ForegroundColor White
    Write-Host "  Profile:  $($Config.profile)" -ForegroundColor White
    if ($Config.sandbox_disposable -eq $true) {
        Write-Host "  Teardown: menu option 13 can delete this project when you are done" -ForegroundColor DarkGray
    }
    Write-Host ""

    if (-not (Confirm "Run bootstrap in project '$($Config.gcp_project)'? (gcloud + terraform)")) {
        Write-Warn "Skipped bootstrap."
        return $false
    }

    Write-Host ""
    Write-Host "  Bootstrap via PowerShell (gcloud + terraform)..." -ForegroundColor DarkGray
    Write-Host ""

    try {
        $adapter = Get-InvokeExternalAdapter
        Invoke-GoldenPathBootstrap -RepoRoot $RepoRoot -Config $Config -InvokeExternal $adapter | Out-Null
    } catch {
        Write-Err "Bootstrap failed: $_"
        return $false
    }

    Write-Ok "Bootstrap complete"
    Show-WifSecrets $Config | Out-Null
    return $true
}

# ── Scaffold ──────────────────────────────────────────────────────────────────

function Show-TemplateList($RepoRoot) {
    try {
        $catalog = Get-GoldenPathCatalog $RepoRoot
        Write-Host "  Template       Runtime  Port   Health" -ForegroundColor White
        Write-Host "  ────────────────────────────────────────" -ForegroundColor DarkGray
        foreach ($prop in $catalog.PSObject.Properties) {
            $m = $prop.Value
            $isDefault = $m.PSObject.Properties.Name -contains 'default' -and $m.default
            $def = if ($isDefault) { " (default)" } else { "" }
            Write-Host "  $($prop.Name.PadRight(14)) $($m.app_runtime.PadRight(8)) $($m.container_port.ToString().PadRight(6)) $($m.health_check_path)$def"
        }
        Write-Host ""
    } catch {
        Write-Warn "Could not load template catalog: $_"
    }
}

function Test-ServiceName([string]$Name) {
    if ($Name.Length -lt 3 -or $Name.Length -gt 40) {
        return "Service name must be 3–40 characters."
    }
    if ($Name -notmatch '^[a-z][a-z0-9-]*[a-z0-9]$') {
        return "Use lowercase kebab-case; start with a letter, no trailing hyphen (e.g. my-streamlit-app)."
    }
    if ($Name -match '--') {
        return "Service name cannot contain consecutive hyphens."
    }
    return $null
}

function Invoke-ScaffoldService($Config) {
    $outcome = [ordered]@{
        ServiceName = ""
        ServiceDir  = ""
        Template    = ""
        Published   = $false
        Publish     = $null
        Verify      = $null
    }

    Write-Host ""
    $name = ""
    while ($true) {
        $name = Read-Input "Service name (e.g. demo-streamlit)"
        $nameErr = Test-ServiceName $name
        if (-not $nameErr) { break }
        Write-Err $nameErr
    }

    $scaffoldParent = Get-ScaffoldOutputDir
    $targetDir = Join-Path $scaffoldParent $name
    if ((Test-Path $targetDir) -and @(Get-ChildItem -Path $targetDir -Force -ErrorAction SilentlyContinue).Count -gt 0) {
        Write-Err "Folder already exists and is not empty: $targetDir"
        return $outcome
    }
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    $Config.last_service = $name
    $Config.last_service_dir = $targetDir
    Save-Config $Config
    Write-Ok "Folder created: $targetDir"
    Write-Host "  (outside platform repo: $scaffoldParent)" -ForegroundColor DarkGray
    Write-Host "  (open in Finder/VS Code now — template files copy next)" -ForegroundColor DarkGray
    Write-Host ""

    if ($Config.gcp_dev_project) {
        Write-Host "  Using project: $($Config.gcp_dev_project)" -ForegroundColor DarkGray
        if (-not (Confirm "Scaffold into project '$($Config.gcp_dev_project)'?" $true)) {
            $Config = Prompt-GcpProject $Config "scaffold + deploy"
        }
    } else {
        $Config = Prompt-GcpProject $Config "scaffold + deploy"
    }

    Show-TemplateList $RepoRoot
    $catalog = Get-GoldenPathCatalog $RepoRoot
    $template = ""
    while ($true) {
        $template = Read-Input "Template (nextjs, fastapi, streamlit, ...)" "nextjs"
        if ($catalog.PSObject.Properties[$template]) { break }
        $available = ($catalog.PSObject.Properties | ForEach-Object { $_.Name }) -join ', '
        Write-Err "Unknown template '$template'. Available: $available"
    }

    Write-Host ""
    Write-Host "  Scaffolding $template into $name ..." -ForegroundColor DarkGray
    try {
        $result = Invoke-GoldenPathScaffold -RepoRoot $RepoRoot -ServiceName $name -Template $template `
            -OutputDir $scaffoldParent -Config $Config
    } catch {
        Write-Err "Scaffold failed: $_"
        return $outcome
    }

    $serviceDir = $result.ServiceDir
    $Config.last_service = $name
    $Config.last_service_dir = $serviceDir
    Save-Config $Config
    $outcome.ServiceName = $name
    $outcome.ServiceDir = $serviceDir
    $outcome.Template = $template

    Write-Ok "Scaffolded: $serviceDir (branch: main)"
    Test-ScaffoldProjectMatch $Config $serviceDir
    Write-Host ""
    Write-Host "  project_id = $($Config.gcp_dev_project) in infra/*.tfvars" -ForegroundColor DarkGray
    Write-Host "  health path  = $($result.HealthCheckPath)" -ForegroundColor DarkGray
    Write-Host ""

    if (Confirm "Publish to GitHub now? (creates repo, secrets, WIF trust, deploy)") {
        $pub = Invoke-PublishService $Config $serviceDir
        if ($pub) {
            $outcome.Published = $true
            $outcome.Publish = $pub
            $outcome.Verify = $pub.Verify
        }
    } else {
        Write-Host "  When ready: menu option 7 → Publish service to GitHub" -ForegroundColor White
        Write-Host ""
    }
    return $outcome
}

function Invoke-PublishService($Config, [string]$ServiceDir = "") {
    if (-not $ServiceDir) {
        $defaultDir = if (Get-DefaultServiceDir $Config) {
            Get-DefaultServiceDir $Config
        } else { Get-ScaffoldOutputDir }
        $ServiceDir = Read-Input "Service directory" $defaultDir
    }

    $Config = Ensure-WifCredentials $Config
    if (-not $Config.wif_provider -or -not $Config.wif_service_account) {
        Write-Err "WIF credentials missing — bootstrap project $($Config.gcp_dev_project) first (menu 3), then menu 4"
        return $null
    }

    $adapter = Get-InvokeExternalAdapter

    try {
        if (-not (Test-Path $ServiceDir)) { throw "Service directory not found: $ServiceDir" }
        $ServiceDir = (Resolve-Path $ServiceDir).Path
        $serviceName = Split-Path $ServiceDir -Leaf
        $cloudRunSvc = "$serviceName-dev"

        Write-Host ""
        Write-Host "  Publishing $serviceName (GitHub → secrets → WIF → push → deploy watch)..." -ForegroundColor DarkGray
        Write-Host ""
        $pub = Invoke-GoldenPathPublish -ServiceDir $ServiceDir -RepoRoot $RepoRoot -Config $Config `
            -WifProvider $Config.wif_provider -WifServiceAccount $Config.wif_service_account `
            -InvokeExternal $adapter -WatchDeploy

        Write-Ok "Published: $($pub.Repo)"
        Write-Host "  https://github.com/$($pub.Repo)" -ForegroundColor DarkGray

        $verify = $null
        if ($null -ne $pub.DeployOk -and -not $pub.DeployOk) {
            Write-Err "GitHub deploy workflow failed — repo was created but Cloud Run is not live yet."
            Write-Host "  Actions: https://github.com/$($pub.Repo)/actions" -ForegroundColor DarkGray
            Write-Host "  Retry:   menu 7 (Publish) — WIF trust + deploy rerun are automatic." -ForegroundColor DarkGray
            Write-Host "  Doctor:  menu 9 to list blockers" -ForegroundColor DarkGray
        } else {
            if ($pub.DeployOk) {
                Write-Ok "Deploy workflow succeeded"
            } else {
                Write-Warn "Deploy watch skipped — checking Cloud Run directly"
            }
            Write-Host ""
            Write-Host "  Verifying Cloud Run + health (may take ~1 min on cold start)..." -ForegroundColor DarkGray
            $verify = Invoke-GoldenPathVerifyDeployment -CloudRunService $cloudRunSvc `
                -ServiceDir $ServiceDir -RepoRoot $RepoRoot -Config $Config -InvokeExternal $adapter
            Show-DeploymentResult -Verify $verify -Repo $pub.Repo -Verbose

            if ($verify.HealthOk) {
                Write-Ok "Service is live and healthy"
            } elseif ($verify.Url) {
                Write-Warn "Service URL exists but health check not ready — wait 30s and run menu 8"
            } else {
                Write-Warn "Cloud Run service not visible yet — check Actions or run menu 8 shortly"
            }
        }

        $Config.last_service = $serviceName
        $Config.last_service_dir = $ServiceDir
        Save-Config $Config

        return [PSCustomObject]@{
            Repo         = $pub.Repo
            ServiceDir   = $ServiceDir
            ServiceName  = $serviceName
            CloudRunSvc  = $cloudRunSvc
            DeployOk     = $pub.DeployOk
            Verify       = $verify
        }
    } catch {
        Write-Err "Publish failed: $_"
        Write-Host "  Run menu option 9 (Doctor) to diagnose." -ForegroundColor DarkGray
        return $null
    }
}

function Invoke-ServiceDoctor($Config) {
    $defaultDir = if (Get-DefaultServiceDir $Config) {
        Get-DefaultServiceDir $Config
    } else { Get-ScaffoldOutputDir }
    $dir = Read-Input "Service directory" $defaultDir
    $adapter = Get-InvokeExternalAdapter
    $issues = Test-GoldenPathServiceDoctor -ServiceDir $dir -Config $Config -InvokeExternal $adapter -RepoRoot $RepoRoot
    Write-Host ""
    if ($issues.Count -eq 0) {
        Write-Ok "No issues found"
    } else {
        Write-Host "  Issues:" -ForegroundColor Yellow
        foreach ($i in $issues) { Write-Host "    • $i" -ForegroundColor Yellow }
        Write-Host ""
        Write-Host "  Fix with menu option 7 (Publish service)" -ForegroundColor White
    }
    Write-Host ""
}

# ── Verify & status ───────────────────────────────────────────────────────────

function Test-Deployment($Config) {
    $service = Read-Input "Cloud Run service name" $(if ($Config.last_service) { "$($Config.last_service)-dev" } else { "my-service-dev" })
    $serviceDir = if (Get-DefaultServiceDir $Config) { Get-DefaultServiceDir $Config } else { "" }
    $adapter = Get-InvokeExternalAdapter

    $verify = Invoke-GoldenPathVerifyDeployment -CloudRunService $service `
        -ServiceDir $serviceDir -RepoRoot $RepoRoot -Config $Config -InvokeExternal $adapter

    if ($verify.Error -and -not $verify.Url) {
        Write-Err $verify.Error
        Write-Host "  List services: menu 11 (Show status)" -ForegroundColor DarkGray
        return
    }

    $repo = if ($Config.last_service -and $Config.github_org) {
        "$($Config.github_org)/$($Config.last_service)"
    } else { "" }
    Show-DeploymentResult -Verify $verify -Repo $repo -Verbose

    if (-not $verify.HealthOk) {
        Write-Err "No health endpoint responded."
        if ($repo) {
            Write-Host "  Deploy logs: https://github.com/$repo/actions" -ForegroundColor DarkGray
        }
    }
}

function Invoke-DryRunWizard {
    Write-Host ""
    Write-Host "  Running read-only wizard audit (no GCP/GitHub changes)..." -ForegroundColor DarkGray
    Write-Host ""
    if (-not (Test-Command "python3")) {
        Write-Err "python3 required for dry run"
        return $false
    }
    $dryRunScript = Join-Path $PSScriptRoot "goldenpath_dryrun.py"
    $ok = Invoke-ExternalLive "python3" @($dryRunScript)
    if (-not $ok) {
        Write-Warn "Dry run reported blockers — review output above before bootstrap or publish"
    }
    return $ok
}

function Show-Status($Config) {
    Write-Host ""
    Write-Host "  ┌─ Current configuration ─────────────────────────────────┐" -ForegroundColor Cyan
    $disposable = if ($Config.sandbox_disposable -eq $true) { 'yes (option 13)' } else { 'no' }
    $lastSvc = if ($Config.last_service) { $Config.last_service } else { '(none)' }
    foreach ($line in @(
        "Profile         $($Config.profile)"
        "GCP project     $($Config.gcp_project)"
        "Region          $($Config.gcp_region)"
        "GitHub org      $($Config.github_org)"
        "Platform repo   $($Config.github_platform_repo)"
        "Disposable      $disposable"
        "Last service    $lastSvc"
        "Config file     $ConfigPath"
    )) {
        Write-Host ("  │  " + $line.PadRight(55) + "│")
    }
    Write-Host "  └───────────────────────────────────────────────────────────┘" -ForegroundColor Cyan

    $proj = Invoke-External "gcloud" @("projects", "describe", $Config.gcp_project, "--format=value(lifecycleState)")
    if ($proj.ExitCode -eq 0) {
        Write-Ok "GCP project exists ($($proj.StdOut.Trim()))"
    } else {
        Write-Warn "GCP project not found — run bootstrap (option 3)"
    }

    $ar = Invoke-External "gcloud" @(
        "artifacts", "repositories", "list",
        "--project=$($Config.gcp_project)", "--format=value(name)"
    )
    if ($ar.ExitCode -eq 0 -and $ar.StdOut.Trim()) {
        Write-Ok "Artifact Registry configured"
    } else {
        Write-Warn "No Artifact Registry — bootstrap may not have run"
    }

    $wif = Get-WifCredentials $Config.gcp_project
    if ($wif) {
        Write-Ok "WIF credentials available (via $($wif.Source))"
    } else {
        Write-Warn "WIF credentials not found"
    }

    $services = Invoke-External "gcloud" @(
        "run", "services", "list",
        "--project=$($Config.gcp_project)", "--region=$($Config.gcp_region)",
        "--format=table(SERVICE,REGION,URL)"
    )
    if ($services.ExitCode -eq 0 -and $services.StdOut.Trim()) {
        Write-Host ""
        Write-Host $services.StdOut
    }
    Write-Host ""
}

function New-McpClaudeConfig($Config) {
    $mcpDir = Join-Path $RepoRoot "mcp"
    $venvPython = Join-Path $mcpDir ".venv/bin/python"
    if ($IsWindows) { $venvPython = Join-Path $mcpDir ".venv/Scripts/python.exe" }

    if (-not (Test-Path $venvPython)) {
        Write-Warn "MCP venv not found at $venvPython"
        if (Confirm "Create venv and install MCP dependencies now?") {
            if (-not (Test-Command "python3")) {
                Write-Err "python3 required"
                return
            }
            Invoke-External "python3" @("-m", "venv", (Join-Path $mcpDir ".venv")) | Out-Null
            $pip = if ($IsWindows) { Join-Path $mcpDir ".venv/Scripts/pip" } else { Join-Path $mcpDir ".venv/bin/pip" }
            Invoke-External $pip @("install", "-r", (Join-Path $mcpDir "requirements.txt")) | Out-Null
            Write-Ok "MCP venv created"
        } else { return }
    }

    $outPath = Join-Path $mcpDir "claude-mcp.generated.json"
    $defaults = Get-DefaultConfig
    $goldenpathVersion = $defaults.goldenpath_version
    $cfg = @{
        mcpServers = @{
            "goldenpath-local" = @{
                command = $venvPython
                args    = @("-m", "goldenpath_mcp")
                env     = @{
                    GOLDENPATH_ROOT    = $RepoRoot
                    GOLDENPATH_CHANNEL = "stable"
                    GOLDENPATH_VERSION = $goldenpathVersion
                    GCP_PROJECT        = $Config.gcp_project
                    GCP_REGION         = $Config.gcp_region
                }
            }
        }
    }
    ($cfg | ConvertTo-Json -Depth 6) | Set-Content $outPath -Encoding UTF8

    Write-Ok "Wrote $outPath"
    Write-Host ""
    Write-Host "  Paste the contents into Claude Desktop → Settings → Developer → MCP" -ForegroundColor White
    Write-Host "  Or merge 'goldenpath-local' into your existing MCP config."
    Write-Host ""
    Get-Content $outPath
    Write-Host ""
}

# ── Profile & full wizard ─────────────────────────────────────────────────────

function Read-ValidatedProjectId([string]$Prompt, [string]$Default = "") {
    while ($true) {
        $id = Read-Input $Prompt $Default
        $id = $id.ToLower()
        $err = Test-ProjectId $id
        if (-not $err) { return $id }
        Write-Err $err
    }
}

function Prompt-GcpProject($Config, [string]$Purpose, [string]$DefaultProject = "") {
    $previousDevProject = [string]$Config.gcp_dev_project
    if (-not $previousDevProject) { $previousDevProject = [string]$Config.gcp_project }

    Write-Host ""
    Write-Host "  ┌─ GCP project: $Purpose ──────────────────────────────────┐" -ForegroundColor Cyan
    Write-Host "  │  Bootstrap, WIF secrets, and scaffold MUST use the same     │" -ForegroundColor Cyan
    Write-Host "  │  same project ID — or deploy will fail.                  │" -ForegroundColor Cyan
    Write-Host "  └───────────────────────────────────────────────────────────┘" -ForegroundColor Cyan
    Write-Host ""
    if ($previousDevProject) {
        Write-Host "  Saved project: $previousDevProject" -ForegroundColor DarkGray
    }

    $default = if ($DefaultProject) { $DefaultProject }
               elseif ($previousDevProject) { $previousDevProject }
               elseif ($Config.gcp_project) { $Config.gcp_project }
               else { "" }
    $project = Read-ValidatedProjectId "GCP project ID" $default

    if ($previousDevProject -and $previousDevProject -ne $project) {
        $Config.wif_provider = ""
        $Config.wif_service_account = ""
        Write-Warn "Project changed — WIF credentials cleared (use menu 4 after bootstrap)"
    }

    $Config.gcp_project = $project
    $Config.gcp_dev_project = $project
    if (Confirm "Use '$project' for both dev and prod deploys?" $true) {
        $Config.gcp_prod_project = $project
    } else {
        $Config.gcp_prod_project = Read-ValidatedProjectId "GCP prod project ID" $project
    }

    Save-Config $Config
    Write-Ok "Locked in: bootstrap + scaffold → $($Config.gcp_dev_project)"
    return $Config
}

function Test-ScaffoldProjectMatch($Config, [string]$ServiceDir) {
    $devTf = Join-Path $ServiceDir "infra/dev.tfvars"
    if (-not (Test-Path $devTf)) { return }
    $content = Get-Content $devTf -Raw
    if ($content -match 'project_id\s*=\s*"([^"]+)"') {
        $found = $Matches[1]
        if ($found -ne $Config.gcp_dev_project) {
            Write-Err "Scaffold project_id is '$found' but wizard has '$($Config.gcp_dev_project)'"
            Write-Warn "Re-run scaffold after setting the correct project in menu option 12 or 6."
        } else {
            Write-Ok "infra/dev.tfvars project_id matches wizard ($found)"
        }
    }
}

function Edit-Config($Config) {
    Write-Host ""
    $choice = Read-Choice "Choose setup profile" @(
        "Sandbox — defaults from config/enterprise.env",
        "New self-contained sandbox — pick a project name, tear down later",
        "Custom existing project — use a GCP project you already have"
    ) 0

    if ($choice -eq 0) {
        $defaults = Get-DefaultConfig
        foreach ($key in $defaults.Keys) { $Config[$key] = $defaults[$key] }
        $Config.profile = "sandbox"
        $Config.sandbox_disposable = $true
        Write-Host ""
        Write-Host "  Sandbox defaults come from config/enterprise.env — confirm or enter your project." -ForegroundColor DarkGray
        $Config = Prompt-GcpProject $Config "sandbox"
    } elseif ($choice -eq 1) {
        $Config.profile = "sandbox"
        $Config.sandbox_disposable = $true
        Write-Host ""
        Write-Host "  Pick a globally unique GCP project ID (6–30 chars, lowercase)." -ForegroundColor White
        Write-Host "  Example: gp-demo-$(whoami 2>$null | ForEach-Object { $_ -replace '[^a-z0-9]', '' } | Select-Object -First 1)" -ForegroundColor DarkGray
        Write-Host "  This project will be yours alone — delete it anytime via menu option 13." -ForegroundColor DarkGray
        Write-Host ""
        $suggested = "gp-sandbox-$(Get-Date -Format 'yyyyMMdd')"
        $Config = Prompt-GcpProject $Config "new self-contained sandbox" $suggested
        $displayInput = Read-Input "Project display name (max 30 chars)" $Config.gcp_project
        $Config.project_display_name = Get-GcpProjectDisplayName -DisplayName $displayInput -ProjectId $Config.gcp_project
        $Config.gcp_region = Read-Input "GCP region" $Config.gcp_region
        $Config.github_org = Read-Input "GitHub org or username" $Config.github_org
        $Config.github_platform_repo = Read-Input "Platform repo name" $Config.github_platform_repo
    } else {
        $Config.profile = "custom"
        $Config.sandbox_disposable = $false
        $Config = Prompt-GcpProject $Config "existing GCP project"
        $displayInput = Read-Input "Project display name (max 30 chars)" $Config.gcp_project
        $Config.project_display_name = Get-GcpProjectDisplayName -DisplayName $displayInput -ProjectId $Config.gcp_project
        $Config.gcp_region = Read-Input "GCP region" $Config.gcp_region
        $Config.github_org = Read-Input "GitHub org or username" $Config.github_org
        $Config.github_platform_repo = Read-Input "Platform repo name" $Config.github_platform_repo
    }

    Save-Config $Config

    Write-Host ""
    Write-Host "  Your settings:" -ForegroundColor White
    Write-Host "    Profile:        $($Config.profile)"
    Write-Host "    GCP project:    $($Config.gcp_project)"
    Write-Host "    Region:         $($Config.gcp_region)"
    Write-Host "    GitHub:         $($Config.github_org)/$($Config.github_platform_repo)"
    if ($Config.sandbox_disposable -eq $true) {
        Write-Host "    Disposable:     yes — tear down with menu option 13" -ForegroundColor DarkGray
    }
    Write-Host ""
    return $Config
}

function Reset-WizardState {
    Write-Host ""
    Write-Host "  Resets .goldenpath-setup.local.json to defaults." -ForegroundColor DarkGray
    Write-Host "  Does NOT delete GCP projects, GitHub repos, or Cloud Run services." -ForegroundColor DarkGray
    Write-Host "  Use menu 13 to tear down the GCP sandbox if you want that too." -ForegroundColor DarkGray
    Write-Host ""
    if (-not (Confirm "Reset local wizard state for a fresh start?")) { return $null }

    $fresh = Get-DefaultConfig
    Save-Config $fresh
    Write-Ok "Wizard state reset — profile: sandbox, project: $($fresh.gcp_project)"
    Write-Host ""
    Write-Host "  Next: option 1 (full guided setup) or --wizard" -ForegroundColor White
    Write-Host ""
    return $fresh
}

function Invoke-TeardownSandbox($Config) {
    $err = Test-ProjectId $Config.gcp_project
    if ($err) {
        Write-Err "Cannot tear down: $err"
        return
    }

    if ($Config.sandbox_disposable -ne $true -and $Config.profile -ne "sandbox") {
        Write-Warn "Current profile '$($Config.profile)' is not marked disposable."
        if (-not (Confirm "Continue teardown anyway?")) { return }
    }

    Write-Host ""
    Write-Host "  This will DESTROY all Golden Path resources in:" -ForegroundColor Yellow
    Write-Host "    $($Config.gcp_project)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Steps: terraform destroy → delete GCP project (irreversible)" -ForegroundColor DarkGray
    Write-Host "  Protected projects (YOUR_BILLING_ANCHOR_PROJECT, etc.) cannot be deleted." -ForegroundColor DarkGray
    Write-Host ""

    if (-not (Confirm "Destroy bootstrap resources in '$($Config.gcp_project)'?")) { return }
    $deleteProject = Confirm "DELETE entire GCP project '$($Config.gcp_project)'?"

    try {
        $adapter = Get-InvokeExternalAdapter
        Invoke-GoldenPathTeardown -RepoRoot $RepoRoot -DeleteProject:$deleteProject -InvokeExternal $adapter `
            -ExpectedProjectId $Config.gcp_project -ProtectedProjects (Get-ProtectedProjectsFromEnv)
    } catch {
        Write-Err "Teardown failed: $_"
        return
    }

    Write-Ok "Sandbox '$($Config.gcp_project)' torn down."
    Write-Host "  Pick a new project in menu option 12 to stand up again." -ForegroundColor DarkGray
}

function Show-WizardCompletion($Config, $WizardState) {
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "  ║                    Setup wizard complete!                ║" -ForegroundColor Green
    Write-Host "  ╚══════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "  What you set up:" -ForegroundColor White
    Write-Host "    Profile        $($Config.profile) → $($Config.gcp_project) ($($Config.gcp_region))"
    if ($WizardState.BootstrapRan) {
        Write-Host "    Bootstrap      ✓ GCP project + Terraform + Artifact Registry" -ForegroundColor Green
    } else {
        Write-Host "    Bootstrap      skipped — run menu 3 when ready" -ForegroundColor DarkGray
    }
    if ($Config.wif_provider) {
        Write-Host "    WIF secrets    ✓ ready for GitHub Actions deploys" -ForegroundColor Green
    }

    if ($WizardState.ServiceName) {
        Write-Host "    Service        $($WizardState.ServiceName) ($($WizardState.Template))" -ForegroundColor Green
        if ($WizardState.Published -and $WizardState.Publish) {
            Write-Host "    GitHub         https://github.com/$($WizardState.Publish.Repo)" -ForegroundColor Green
            if ($WizardState.Verify -and $WizardState.Verify.Url) {
                Write-Host "    Cloud Run      $($WizardState.Verify.Url)" -ForegroundColor Green
                if ($WizardState.Verify.HealthOk) {
                    Write-Host "    Health         $($WizardState.Verify.HealthPath) → HTTP $($WizardState.Verify.StatusCode)" -ForegroundColor Green
                }
            } elseif ($WizardState.Publish.DeployOk -eq $false) {
                Write-Host "    Deploy         ✗ workflow failed — see Actions tab" -ForegroundColor Yellow
            }
        } elseif (-not $WizardState.Published) {
            Write-Host "    Publish        not yet — menu 7 when ready" -ForegroundColor DarkGray
        }
    } else {
        Write-Host "    Service        none yet — menu 6 to scaffold" -ForegroundColor DarkGray
    }

    Write-Host ""
    if ($WizardState.Verify -and $WizardState.Verify.Url -and $WizardState.Verify.HealthOk) {
        Write-Host "  Your app is live. Open it now:" -ForegroundColor White
        Write-Host "    $($WizardState.Verify.Url)" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  To ship changes:" -ForegroundColor White
        Write-Host "    cd $($WizardState.ServiceDir)"
        Write-Host "    # edit your code, then:"
        Write-Host '    git add . && git commit -m "your change" && git push'
        Write-Host "    → GitHub Actions deploys to $($WizardState.Publish.CloudRunSvc) automatically"
    } elseif ($WizardState.Published -and $WizardState.Publish -and $WizardState.Publish.DeployOk -eq $false) {
        Write-Host "  Next steps (deploy failed):" -ForegroundColor White
        Write-Host "    1. Open https://github.com/$($WizardState.Publish.Repo)/actions"
        Write-Host "    2. Fix the error, or run menu 9 (Doctor)"
        Write-Host "    3. Re-run menu 7 (Publish) to retry deploy + verify"
    } elseif ($WizardState.ServiceName -and -not $WizardState.Published) {
        Write-Host "  Next step:" -ForegroundColor White
        Write-Host "    Menu 7 — Publish $($WizardState.ServiceName) to GitHub (repo + deploy + verify)"
    } elseif (-not $WizardState.ServiceName) {
        Write-Host "  Next step:" -ForegroundColor White
        Write-Host "    Menu 6 — Scaffold your first service, then menu 7 to publish"
    } else {
        Write-Host "  Next step:" -ForegroundColor White
        Write-Host "    Menu 8 — Verify deployment, or wait a minute and re-run publish (menu 7)"
    }

    Write-Host ""
    Write-Host "  Wizard menu:  pwsh ./scripts/setup/goldenpath-setup.ps1" -ForegroundColor DarkGray
    Write-Host "  All services: menu 11  |  Tear down sandbox: menu 13" -ForegroundColor DarkGray
    Write-Host ""
}

function Start-FullWizard {
    Write-Banner
    Write-Host "  This wizard walks you through Golden Path setup one step at a time."
    Write-Host "  You can stop anytime and resume from the main menu."
    Write-Host ""

    $Config = Get-Config
    $total = 6
    $wizardState = [ordered]@{
        BootstrapRan = $false
        ServiceName  = ""
        ServiceDir   = ""
        Template     = ""
        Published    = $false
        Publish      = $null
        Verify       = $null
    }

    Write-Step 1 $total "Choose your profile"
    $Config = Edit-Config $Config

    Write-Step 2 $total "Check tools & login"
    if (-not (Test-Prerequisites)) {
        Write-Err "Fix missing tools, then run the wizard again."
        Press-Enter
        return
    }
    if (-not (Test-GcloudAuth)) {
        Write-Err "GCP auth required before continuing."
        Press-Enter
        return
    }
    Press-Enter

    Write-Step 3 $total "Bootstrap GCP (one-time)"
    Write-Host "  Creates the project (if needed) and runs Terraform bootstrap."
    Write-Host "  Project: $($Config.gcp_project) ($($Config.profile))"
    if ($Config.sandbox_disposable -eq $true) {
        Write-Host "  Disposable — tear down later with menu option 13."
    }
    Write-Host "  Does not modify protected projects (e.g. YOUR_BILLING_ANCHOR_PROJECT)."
    Write-Host ""
    if (Confirm "Run bootstrap now?") {
        $wizardState.BootstrapRan = [bool](Invoke-BootstrapStandup $Config)
    } else {
        Write-Warn "Skipped — you can run it later from the main menu (option 3)."
    }
    $Config = Get-Config
    Press-Enter

    Write-Step 4 $total "GitHub deploy credentials"
    Show-WifSecrets $Config | Out-Null
    if (Confirm "Set WIF secrets on platform repo '$($Config.github_platform_repo)' via gh?") {
        Set-GitHubSecrets $Config $Config.github_platform_repo
    }
    $Config = Get-Config
    Press-Enter

    Write-Step 5 $total "Scaffold + publish your first service"
    Write-Host "  Creates a service folder, copies a template, publishes to GitHub,"
    Write-Host "  watches the deploy workflow, then verifies Cloud Run + health."
    Write-Host ""
    if (Confirm "Scaffold and publish a service now?") {
        $scaffold = Invoke-ScaffoldService $Config
        if ($scaffold.ServiceName) {
            $wizardState.ServiceName = $scaffold.ServiceName
            $wizardState.ServiceDir = $scaffold.ServiceDir
            $wizardState.Template = $scaffold.Template
            $wizardState.Published = $scaffold.Published
            $wizardState.Publish = $scaffold.Publish
            $wizardState.Verify = $scaffold.Verify
        }
    } else {
        Write-Host "  Skip for now — menu 6 (scaffold) and menu 7 (publish) later."
    }
    Press-Enter

    Write-Step 6 $total "MCP for Claude (optional)"
    if (Confirm "Generate Claude MCP config?") {
        New-McpClaudeConfig $Config
    } else {
        Write-Host "  Skipped — menu 10 anytime."
    }

    Show-WizardCompletion $Config $wizardState
    Press-Enter "Press Enter to return to the main menu..."
}

function Show-MainMenu {
    $Config = Get-Config

    while ($true) {
        Write-Banner
        Write-Host "  GCP: $($Config.gcp_project)  |  GitHub: $($Config.github_org)/$($Config.github_platform_repo)" -ForegroundColor DarkGray
        Write-Host ""
        Write-Host "  What would you like to do?"
        Write-Host ""
        Write-Host "    1) Full guided setup (recommended for new users)"
        Write-Host "    2) Check prerequisites"
        Write-Host "    3) Bootstrap GCP (stand up / terraform apply)"
        Write-Host "    4) Show GitHub WIF secrets"
        Write-Host "    5) Set GitHub WIF secrets on a repo"
        Write-Host "    6) Scaffold a new service (PowerShell — not shop CLI)"
        Write-Host "    7) Publish service to GitHub (repo + secrets + deploy)"
        Write-Host "    8) Verify a deployment (health check)"
        Write-Host "    9) Doctor — diagnose deploy blockers"
        Write-Host "   10) Generate Claude MCP config"
        Write-Host "   11) Show current status"
        Write-Host "   12) Edit settings (project, org, region)"
        Write-Host "   13) Tear down current sandbox project"
        Write-Host "   14) Fresh start (reset local wizard state)"
        Write-Host "   15) Dry run — audit wizard (no deploy / no changes)"
        Write-Host "    h) Help / usage"
        Write-Host "    0) Exit"
        Write-Host ""

        $pick = Read-Input "Choice" "1"

        switch ($pick) {
            "1" { Start-FullWizard }
            "2" { Test-Prerequisites | Out-Null; Press-Enter }
            "3" {
                if (Test-Prerequisites) {
                    if (Test-GcloudAuth) { Invoke-BootstrapStandup $Config | Out-Null }
                }
                Press-Enter
            }
            "4" { Show-WifSecrets $Config | Out-Null; Press-Enter }
            "5" {
                $repo = Read-Input "Repo (name or org/name)" $Config.github_platform_repo
                Set-GitHubSecrets $Config $repo
                Press-Enter
            }
            "6" { Invoke-ScaffoldService $Config; Press-Enter }
            "7" { Invoke-PublishService $Config; Press-Enter }
            "8" { Test-Deployment $Config; Press-Enter }
            "9" { Invoke-ServiceDoctor $Config; Press-Enter }
            "10" { New-McpClaudeConfig $Config; Press-Enter }
            "11" { Show-Status $Config; Press-Enter }
            "12" { $Config = Edit-Config $Config; Press-Enter }
            "13" { Invoke-TeardownSandbox $Config; Press-Enter }
            "14" {
                $reset = Reset-WizardState
                if ($reset) { $Config = $reset }
                Press-Enter
            }
            "15" { Invoke-DryRunWizard | Out-Null; Press-Enter }
            { $_ -in @("h", "H", "help", "?") } { Show-Usage; Press-Enter }
            "0" { Write-Host "  Bye!" -ForegroundColor Cyan; return }
            default { Write-Warn "Unknown option — type h for help"; Start-Sleep -Seconds 1 }
        }

        $Config = Get-Config
        Clear-Host
    }
}

# ── Entry ─────────────────────────────────────────────────────────────────────

# Only execute the interactive entry point when the script is run directly.
# When dot-sourced (e.g. from tests), we define functions but skip the menu.
if ($MyInvocation.InvocationName -ne '.') {
    Set-Location $RepoRoot
    if ($args -contains "--help" -or $args -contains "-h" -or $args -contains "-?") {
        Show-Usage
    } elseif ($args -contains "--dryrun") {
        Invoke-DryRunWizard | Out-Null
    } elseif ($args -contains "--wizard") {
        Start-FullWizard
    } else {
        Show-MainMenu
    }
}