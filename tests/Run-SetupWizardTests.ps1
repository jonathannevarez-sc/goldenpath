#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Convenience runner for the Golden Path Setup Wizard Pester tests.

.DESCRIPTION
    Ensures Pester is available, then runs tests/goldenpath-setup.tests.ps1
    with clear output. Safe to run from the repo root.

.EXAMPLE
    pwsh ./tests/Run-SetupWizardTests.ps1
#>

[CmdletBinding()]
param(
    [switch]$Detailed,
    [switch]$NoCoverage
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$TestFile = Join-Path $RepoRoot 'tests/goldenpath-setup.tests.ps1'

Write-Host ''
Write-Host 'Golden Path Setup Wizard — Test Runner' -ForegroundColor Cyan
Write-Host '=======================================' -ForegroundColor DarkCyan
Write-Host ''

# ── Ensure Pester is available ────────────────────────────────────────────────
$pester = Get-Module -ListAvailable -Name Pester | Sort-Object Version -Descending | Select-Object -First 1

if (-not $pester) {
    Write-Host 'Pester module not found. Installing for current user...' -ForegroundColor Yellow
    try {
        Install-Module -Name Pester -Force -SkipPublisherCheck -Scope CurrentUser -MinimumVersion 5.0 -ErrorAction Stop
        Write-Host 'Pester installed successfully.' -ForegroundColor Green
    } catch {
        Write-Error "Failed to install Pester: $_`nPlease run manually: Install-Module Pester -Force -SkipPublisherCheck -Scope CurrentUser"
        exit 1
    }
    $pester = Get-Module -ListAvailable -Name Pester | Sort-Object Version -Descending | Select-Object -First 1
}

Write-Host "Using Pester $($pester.Version)" -ForegroundColor DarkGray

# Import the latest Pester
Import-Module Pester -MinimumVersion 5.0 -Force -ErrorAction Stop

# ── Run the tests (using Pester 5+ Configuration for reliability) ─────────────
$config = New-PesterConfiguration
$config.Run.Path = $TestFile
$config.Output.Verbosity = if ($Detailed) { 'Detailed' } else { 'Normal' }
$config.Run.PassThru = $true

if (-not $NoCoverage) {
    $config.CodeCoverage.Enabled = $true
    $config.CodeCoverage.Path = 'scripts/setup/goldenpath-setup.ps1'
}

Write-Host ''
Write-Host "Running: Invoke-Pester $($TestFile | Split-Path -Leaf)" -ForegroundColor DarkGray
Write-Host ''

$results = Invoke-Pester -Configuration $config
$failed = $results.FailedCount

$bootstrapTests = Join-Path $RepoRoot 'tests/bootstrap-module.tests.ps1'
if (Test-Path $bootstrapTests) {
    Write-Host ''
    Write-Host "Running: Invoke-Pester bootstrap-module.tests.ps1" -ForegroundColor DarkGray
    $bootstrapConfig = New-PesterConfiguration
    $bootstrapConfig.Run.Path = $bootstrapTests
    $bootstrapConfig.Output.Verbosity = if ($Detailed) { 'Detailed' } else { 'Normal' }
    $bootstrapConfig.Run.PassThru = $true
    $bootstrapResults = Invoke-Pester -Configuration $bootstrapConfig
    $failed += $bootstrapResults.FailedCount
}

Write-Host ''
if ($failed -eq 0) {
    Write-Host "All wizard Pester tests passed!" -ForegroundColor Green
} else {
    Write-Host "$failed test(s) failed." -ForegroundColor Red
    exit 1
}

exit 0
