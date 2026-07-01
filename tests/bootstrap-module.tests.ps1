# Pester tests for scripts/setup/modules/Bootstrap.ps1 (display name + teardown guards).
BeforeAll {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
    . (Join-Path $RepoRoot 'scripts/setup/modules/Bootstrap.ps1')
}

Describe 'Get-GcpProjectDisplayName' {
    It 'passes through short names' {
        Get-GcpProjectDisplayName -DisplayName 'Golden Path Sandbox' | Should -Be 'Golden Path Sandbox'
    }
    It 'truncates long names to 30 characters' {
        $long = 'Golden Path Sandbox gp-sandbox-20260624'
        (Get-GcpProjectDisplayName -DisplayName $long).Length | Should -Be 30
    }
    It 'falls back to project id' {
        Get-GcpProjectDisplayName -DisplayName '' -ProjectId 'gp-test-01' | Should -Be 'gp-test-01'
    }
}

Describe 'Invoke-GoldenPathTeardown guards' {
    It 'refuses config/tfvars project mismatch' {
        $adapter = { param($Exe, $ArgumentList, $WorkDir) [PSCustomObject]@{ ExitCode = 0; StdOut = ''; StdErr = '' } }
        $tfvars = Join-Path $RepoRoot 'platform/bootstrap/terraform.tfvars'
        $had = Test-Path $tfvars
        $orig = if ($had) { Get-Content $tfvars -Raw } else { $null }
        try {
            @'
personal_test        = true
test_project_id      = "other-project"
region               = "us-central1"
github_org           = "test"
github_repo          = "goldenpath"
artifact_registry_id = "containers"
'@ | Set-Content -Path $tfvars -Encoding UTF8
            { Invoke-GoldenPathTeardown -RepoRoot $RepoRoot -DeleteProject:$false -InvokeExternal $adapter -ExpectedProjectId 'gp-test-smoke-01' } |
                Should -Throw '*terraform.tfvars targets*'
        } finally {
            if ($had) { Set-Content -Path $tfvars -Value $orig -NoNewline -Encoding UTF8 }
            elseif (Test-Path $tfvars) { Remove-Item $tfvars -Force }
        }
    }
}