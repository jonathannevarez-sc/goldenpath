#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Proper Pester tests for scripts/setup/goldenpath-setup.ps1

.DESCRIPTION
    Unit tests for the core testable logic in the Golden Path Setup Wizard:
    - Project ID and Service Name validation
    - Configuration loading, defaults, and persistence
    - WIF staleness detection

    These tests run without side effects on your real .goldenpath-setup.local.json
    or your actual GCP project.

.USAGE
    # Install Pester once (if needed):
    pwsh -Command "Install-Module Pester -Force -SkipPublisherCheck -Scope CurrentUser"

    # Run from repo root:
    Invoke-Pester tests/goldenpath-setup.tests.ps1 -Output Detailed

    # Or with code coverage (Pester 5+):
    Invoke-Pester tests/goldenpath-setup.tests.ps1 -Output Detailed -CodeCoverage scripts/setup/goldenpath-setup.ps1
#>

[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ── Pester Tests ───────────────────────────────────────────────────────────────

BeforeAll {
    $Script:RepoRoot   = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
    $Script:WizardPath = Join-Path $Script:RepoRoot 'scripts/setup/goldenpath-setup.ps1'
    $Script:TestEnterpriseEnv = Join-Path $TestDrive 'enterprise.env'
    @'
PARENT_PROJECT_ID=billing-anchor-test
BILLING_ACCOUNT_ID=000000-000000-000000
GCP_DEV_PROJECT=my-gp-dev-test
GCP_PROD_PROJECT=my-gp-prod-test
GCP_SANDBOX_PROJECT=my-gp-sandbox-test
GITHUB_ORG=my-github-org
PLATFORM_REPO=goldenpath
PROTECTED_PROJECTS=protected-name-test,billing-anchor-test
'@ | Set-Content -Path $Script:TestEnterpriseEnv -Encoding UTF8

    Write-Verbose "Dot-sourcing wizard (for test) from $Script:WizardPath"
    . $Script:WizardPath
    $Script:EnterpriseEnv = $Script:TestEnterpriseEnv
    $Script:ProtectedProjects = Get-ProtectedProjectsFromEnv

    # Promote the wizard functions into global scope so Pester It blocks can see them
    # (Pester has scope isolation between discovery/execution and It blocks).
    $functionsToExport = @(
        'Test-ProjectId'
        'Test-ServiceName'
        'Get-DefaultConfig'
        'Get-Config'
        'Save-Config'
        'Test-WifCredentialsStale'
        'Test-GoldenPathWifProvider'
        'Test-GoldenPathWifServiceAccount'
    )

    Get-Command -CommandType Function -Name $functionsToExport -ErrorAction SilentlyContinue |
        ForEach-Object {
            Set-Item -Path "Function:\global:$($_.Name)" -Value $_.ScriptBlock -Force
        }

    # Capture original for cleanup (best effort)
    $script:OriginalConfigPath = if (Get-Variable -Name ConfigPath -Scope Script -ErrorAction SilentlyContinue) {
        $Script:ConfigPath
    } else { $null }
}

AfterAll {
    if ($script:OriginalConfigPath) {
        $Script:ConfigPath = $script:OriginalConfigPath
    }
}

Describe 'Golden Path Setup Wizard' -Tag 'Unit' {

    Context 'Test-ProjectId' {

        It 'returns $null for a valid project id' {
            Test-ProjectId 'my-valid-project-123' | Should -Be $null
        }

        It 'rejects too-short project id (< 6 chars)' {
            Test-ProjectId 'abc' | Should -Match '6–30 characters'
        }

        It 'rejects too-long project id (> 30 chars)' {
            $long = 'a' * 31
            Test-ProjectId $long | Should -Match '6–30 characters'
        }

        It 'rejects project id that does not start with a letter' {
            Test-ProjectId '1myproject' | Should -Match 'start with a letter'
        }

        It 'rejects project id ending with a hyphen' {
            Test-ProjectId 'valid-project-' | Should -Match 'not end with a hyphen'
        }

        It 'rejects project id with consecutive hyphens' {
            Test-ProjectId 'my--project' | Should -Match 'consecutive hyphens'
        }

        It 'rejects protected project names' {
            Test-ProjectId 'protected-name-test' | Should -Match 'protected'
            Test-ProjectId 'billing-anchor-test' | Should -Match 'protected'
        }

        It 'accepts valid kebab-case style project ids' {
            Test-ProjectId 'my-gp-sandbox-test' | Should -Be $null
            Test-ProjectId 'my-cool-sandbox-42' | Should -Be $null
        }
    }

    Context 'Test-ServiceName' {

        It 'returns $null for a valid service name' {
            Test-ServiceName 'my-streamlit-app' | Should -Be $null
            Test-ServiceName 'fastapi-backend' | Should -Be $null
        }

        It 'rejects too-short service name (< 3 chars)' {
            Test-ServiceName 'ab' | Should -Match '3–40 characters'
        }

        It 'rejects too-long service name (> 40 chars)' {
            $long = 'a' * 41
            Test-ServiceName $long | Should -Match '3–40 characters'
        }

        It 'rejects service name ending with hyphen' {
            Test-ServiceName 'my-app-' | Should -Match 'no trailing hyphen'
        }

        It 'rejects service name with consecutive hyphens' {
            Test-ServiceName 'my--app' | Should -Match 'consecutive hyphens'
        }

        It 'rejects names that do not start with a letter' {
            Test-ServiceName '123-service' | Should -Match 'start with a letter'
        }

        It 'accepts valid kebab-case service names' {
            Test-ServiceName 'nextjs-frontend' | Should -Be $null
            Test-ServiceName 'express-api-v2' | Should -Be $null
        }
    }

    Context 'Get-DefaultConfig' {

        It 'returns an ordered hashtable with expected keys' {
            $cfg = Get-DefaultConfig
            $cfg | Should -BeOfType 'System.Collections.Specialized.OrderedDictionary'
            $cfg.profile | Should -Be 'sandbox'
            $cfg.gcp_project | Should -Not -BeNullOrEmpty
            $cfg.sandbox_disposable | Should -Be $true
        }

        It 'loads distinct sandbox, dev, and prod projects from enterprise.env' {
            $cfg = Get-DefaultConfig
            $cfg.gcp_project | Should -Be 'my-gp-sandbox-test'
            $cfg.gcp_dev_project | Should -Be 'my-gp-dev-test'
            $cfg.gcp_prod_project | Should -Be 'my-gp-prod-test'
        }
    }

    Context 'Config load/save (isolated temp file)' {

        BeforeEach {
            # Use Pester's built-in $TestDrive for perfect isolation (auto-cleaned)
            $script:TempConfig = Join-Path $TestDrive "gp-test-config.json"
            if (Test-Path $script:TempConfig) { Remove-Item $script:TempConfig -Force }

            # Override in multiple scopes — the wizard uses bare $ConfigPath in Get-Config/Save-Config
            $ConfigPath        = $script:TempConfig
            $Script:ConfigPath = $script:TempConfig
            $global:ConfigPath = $script:TempConfig
        }

        It 'Get-Config returns defaults when no config file exists' {
            if (Test-Path $ConfigPath) { Remove-Item $ConfigPath -Force }
            $cfg = Get-Config
            $cfg.profile | Should -Be 'sandbox'
            $cfg.gcp_project | Should -Be 'my-gp-sandbox-test'
        }

        It 'Save-Config + Get-Config roundtrips values correctly' {
            $enterprise = Get-EnterpriseProfile
            $original = Get-Config
            $original.sandbox_disposable = $false
            $original.last_service = 'my-cool-service'

            Save-Config $original

            $loaded = Get-Config
            # enterprise.env owns team pins — wizard JSON cannot override them
            if ($enterprise.GCP_DEV_PROJECT) {
                $loaded.gcp_dev_project | Should -Be $enterprise.GCP_DEV_PROJECT
            }
            $loaded.sandbox_disposable | Should -Be $false
            $loaded.last_service | Should -Be 'my-cool-service'
        }

        It 'preserves boolean types on roundtrip' {
            $cfg = Get-Config
            $cfg.sandbox_disposable = $false
            Save-Config $cfg

            $loaded = Get-Config
            $loaded.sandbox_disposable | Should -BeOfType 'bool'
            $loaded.sandbox_disposable | Should -Be $false
        }
    }

    Context 'Test-WifCredentialsStale' {

        It 'returns true when service account belongs to a different project' {
            $cfg = [ordered]@{
                gcp_dev_project     = 'new-project-123'
                wif_service_account = 'github-actions@old-project-999.iam.gserviceaccount.com'
            }
            Test-WifCredentialsStale $cfg | Should -Be $true
        }

        It 'returns false when service account matches the dev project' {
            $cfg = [ordered]@{
                gcp_dev_project     = 'my-project-abc'
                wif_service_account = 'github-actions@my-project-abc.iam.gserviceaccount.com'
            }
            Test-WifCredentialsStale $cfg | Should -Be $false
        }

        It 'returns false when there is no wif_service_account yet' {
            $cfg = [ordered]@{
                gcp_dev_project     = 'any-project'
                wif_service_account = ''
            }
            Test-WifCredentialsStale $cfg | Should -Be $false
        }

        It 'returns true when WIF values are terraform warning garbage' {
            $cfg = [ordered]@{
                gcp_dev_project     = 'my-gp-sandbox-test'
                wif_provider        = "Warning: No outputs found"
                wif_service_account = "Warning: No outputs found"
            }
            Test-WifCredentialsStale $cfg | Should -Be $true
        }
    }

    Context 'WIF value validation' {

        It 'rejects terraform warning text as WIF provider' {
            Test-GoldenPathWifProvider 'Warning: No outputs found' | Should -Be $false
        }

        It 'accepts a real WIF provider resource name' {
            $provider = 'projects/123456789/locations/global/workloadIdentityPools/github-pool/providers/github'
            Test-GoldenPathWifProvider $provider | Should -Be $true
        }

        It 'accepts the expected github-actions service account format' {
            Test-GoldenPathWifServiceAccount 'github-actions@my-gp-sandbox-test.iam.gserviceaccount.com' | Should -Be $true
        }
    }

    Context 'Script invocation (CLI surface)' {

        It 'exits 0 and prints usage when invoked with --help' {
            $result = & pwsh -NoProfile -File $Script:WizardPath --help 2>&1
            $LASTEXITCODE | Should -Be 0
            $output = $result -join "`n"
            $output | Should -Match 'Golden Path GCP — PowerShell Setup Wizard'
            $output | Should -Match 'FULL MENU'
            $output | Should -Match '--wizard'
            $output | Should -Match '--dryrun'
        }

        It 'exits 0 and prints usage when invoked with -h' {
            $result = & pwsh -NoProfile -File $Script:WizardPath -h 2>&1
            $LASTEXITCODE | Should -Be 0
            $output = $result -join "`n"
            $output | Should -Match 'RECOMMENDED JOURNEYS'
            $output | Should -Match 'TROUBLESHOOTING'
        }
    }
}

# ── Optional: allow direct execution to give a helpful message ────────────────
if ($MyInvocation.InvocationName -ne '.') {
    Write-Host ''
    Write-Host 'This is a Pester test file.' -ForegroundColor Cyan
    Write-Host 'Run it with:' -ForegroundColor DarkGray
    Write-Host '  Invoke-Pester tests/goldenpath-setup.tests.ps1 -Output Detailed' -ForegroundColor White
    Write-Host ''
}