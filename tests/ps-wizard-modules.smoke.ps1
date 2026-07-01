# Smoke tests for PowerShell wizard modules (no GCP/network).
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Tmp = Join-Path ([System.IO.Path]::GetTempPath()) "gp-ps-smoke-$(Get-Random)"
New-Item -ItemType Directory -Path $Tmp -Force | Out-Null

try {
    . (Join-Path $RepoRoot 'scripts/setup/modules/Scaffold.ps1')
    . (Join-Path $RepoRoot 'scripts/setup/modules/Bootstrap.ps1')
    . (Join-Path $RepoRoot 'scripts/setup/modules/Publish.ps1')

    $Config = @{
        github_org           = 'test-org'
        github_platform_repo = 'goldenpath'
        goldenpath_version   = 'v0.3.7'
        gcp_dev_project      = 'gp-test-smoke-01'
        gcp_prod_project     = 'gp-test-smoke-01'
        gcp_region           = 'us-central1'
    }

    # 1) Display name clamp
    $clamped = Get-GcpProjectDisplayName -DisplayName 'Golden Path Sandbox gp-test-smoke-01' -ProjectId 'gp-test-smoke-01'
    if ($clamped.Length -gt 30) { throw "display name not clamped: $clamped ($($clamped.Length))" }
    Write-Host "PASS display name clamp -> '$clamped'"

    # 2) Scaffold express
    $result = Invoke-GoldenPathScaffold -RepoRoot $RepoRoot -ServiceName 'smoke-express' `
        -Template 'express' -OutputDir $Tmp -Config $Config
    if (-not (Test-Path (Join-Path $result.ServiceDir 'package.json'))) {
        throw 'scaffold missing package.json'
    }
    $tokenHits = Select-String -Path (Join-Path $result.ServiceDir '.github/workflows/deploy.yml') -Pattern '\{\{[A-Z_]+\}\}' -AllMatches
    if ($tokenHits) { throw "scaffold left tokens in deploy.yml" }
    Write-Host "PASS scaffold express -> $($result.ServiceDir)"

    # 3) Repair tokens after deliberate break
    $deploy = Join-Path $result.ServiceDir '.github/workflows/deploy.yml'
    $raw = Get-Content $deploy -Raw
    Set-Content -Path $deploy -Value ($raw + "`n# {{SERVICE_NAME}}") -NoNewline -Encoding UTF8
    Repair-GoldenPathScaffoldTokens -RepoRoot $RepoRoot -ServiceDir $result.ServiceDir `
        -Template 'express' -Config $Config | Out-Null
    $tokenHits2 = Select-String -Path $deploy -Pattern '\{\{[A-Z_]+\}\}' -AllMatches
    if ($tokenHits2) { throw 'repair did not clear tokens' }
    Write-Host 'PASS repair scaffold tokens'

    # 4) Doctor on valid scaffold
    $adapter = {
        param($Exe, $ArgumentList, $WorkDir)
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $Exe
        $psi.Arguments = ($ArgumentList -join ' ')
        $psi.WorkingDirectory = if ($WorkDir) { $WorkDir } else { (Get-Location).Path }
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.UseShellExecute = $false
        $p = [System.Diagnostics.Process]::Start($psi)
        $p.WaitForExit()
        [PSCustomObject]@{ ExitCode = $p.ExitCode; StdOut = $p.StandardOutput.ReadToEnd(); StdErr = $p.StandardError.ReadToEnd() }
    }
    $issues = @(Test-GoldenPathServiceDoctor -ServiceDir $result.ServiceDir -Config $Config -InvokeExternal $adapter)
    $hard = @($issues | Where-Object {
            $_ -notmatch 'gh CLI not found|Missing GitHub secret|Not Found|404'
        })
    if ($hard.Count -gt 0) { throw "doctor unexpected issues: $($hard -join '; ')" }
    Write-Host "PASS doctor (soft issues only: $($issues.Count))"

    # 5) Teardown guard without terraform apply
    $tfvars = Join-Path $RepoRoot 'platform/bootstrap/terraform.tfvars'
    $hadTfvars = Test-Path $tfvars
    $orig = if ($hadTfvars) { Get-Content $tfvars -Raw } else { $null }
    try {
        @"
personal_test        = true
test_project_id      = "other-project-id"
region               = "us-central1"
github_org           = "test-org"
github_repo          = "goldenpath"
artifact_registry_id = "containers"
"@ | Set-Content -Path $tfvars -Encoding UTF8

        $threw = $false
        try {
            Invoke-GoldenPathTeardown -RepoRoot $RepoRoot -DeleteProject:$false `
                -InvokeExternal $adapter -ExpectedProjectId 'gp-test-smoke-01' -ProtectedProjects @() | Out-Null
        } catch {
            if ($_.Exception.Message -notmatch 'terraform.tfvars targets') { throw }
            $threw = $true
        }
        if (-not $threw) { throw 'teardown should refuse config/tfvars project mismatch' }
        Write-Host 'PASS teardown project mismatch guard'
    } finally {
        if ($hadTfvars) { Set-Content -Path $tfvars -Value $orig -NoNewline -Encoding UTF8 }
        elseif (Test-Path $tfvars) { Remove-Item $tfvars -Force }
    }

    Write-Host ''
    Write-Host 'All PS module smoke tests passed.' -ForegroundColor Green
} finally {
    Remove-Item -Recurse -Force $Tmp -ErrorAction SilentlyContinue
}