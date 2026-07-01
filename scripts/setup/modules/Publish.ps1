# Pure PowerShell GitHub publish + WIF trust + deploy watch.
Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot "OpsCli.ps1")

function Get-GoldenPathPlatformRepoVisibility {
    param(
        [string]$GithubOrg,
        [string]$PlatformRepo,
        [scriptblock]$InvokeExternal
    )

    $fullPlatformRepo = "$GithubOrg/$PlatformRepo"
    $result = & $InvokeExternal "gh" @("repo", "view", $fullPlatformRepo, "--json", "visibility", "-q", ".visibility")
    if ($result.ExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($result.StdOut.Trim())) {
        return "PUBLIC"
    }
    return $result.StdOut.Trim().ToUpperInvariant()
}

function Get-GoldenPathRepoCreateVisibilityFlag {
    param([string]$Visibility)
    switch ($Visibility) {
        "PRIVATE" { return "--private" }
        "INTERNAL" { return "--internal" }
        default { return "--public" }
    }
}

function Get-ServiceProjectFromTfvars([string]$ServiceDir) {
    $devTf = Join-Path $ServiceDir "infra/dev.tfvars"
    if (-not (Test-Path $devTf)) { return $null }
    $content = Get-Content $devTf -Raw
    if ($content -match 'project_id\s*=\s*"([^"]+)"') { return $Matches[1] }
    return $null
}

function Test-WifSaBinding {
    param([string]$PolicyJson, [string]$Member, [string]$Role)
    if ([string]::IsNullOrWhiteSpace($PolicyJson)) { return $false }
    $policy = $PolicyJson | ConvertFrom-Json
    foreach ($binding in @($policy.bindings)) {
        if ($binding.role -eq $Role -and $Member -in @($binding.members)) { return $true }
    }
    return $false
}

function Add-GoldenPathWifTrust {
    param(
        [string]$GcpProject,
        [string]$GithubOrg,
        [string]$RepoName,
        [scriptblock]$InvokeExternal
    )

    $sa = "github-actions@${GcpProject}.iam.gserviceaccount.com"
    $num = (& $InvokeExternal "gcloud" @("projects", "describe", $GcpProject, "--format=value(projectNumber)")).StdOut.Trim()
    if (-not $num) { throw "Could not get project number for $GcpProject" }
    $pool = (& $InvokeExternal "gcloud" @(
        "iam", "workload-identity-pools", "list",
        "--project=$GcpProject", "--location=global", "--format=value(name)"
    )).StdOut.Trim() -split "`n" | Select-Object -First 1
    if (-not $pool) { throw "No WIF pool in $GcpProject" }
    $poolId = $pool -replace '.*/workloadIdentityPools/', ''
    $member = "principalSet://iam.googleapis.com/projects/$num/locations/global/workloadIdentityPools/$poolId/attribute.repository/${GithubOrg}/${RepoName}"

    foreach ($role in @("roles/iam.workloadIdentityUser", "roles/iam.serviceAccountTokenCreator")) {
        $policy = (& $InvokeExternal "gcloud" @(
            "iam", "service-accounts", "get-iam-policy", $sa,
            "--project=$GcpProject", "--format=json"
        )).StdOut
        if (Test-WifSaBinding $policy $member $role) { continue }
        $bind = & $InvokeExternal "gcloud" @(
            "iam", "service-accounts", "add-iam-policy-binding", $sa,
            "--project=$GcpProject", "--role=$role", "--member=$member", "--quiet"
        )
        if ($bind.ExitCode -ne 0) { throw "WIF binding failed for $role" }
    }
}

function Get-GoldenPathLatestDeployRun {
    param([string]$FullRepo, [scriptblock]$InvokeExternal)

    $raw = (& $InvokeExternal "gh" @(
        "run", "list", "--repo", $FullRepo, "--workflow=deploy.yml",
        "--limit", "1", "--json", "databaseId,conclusion,status,event"
    )).StdOut.Trim()
    if (-not $raw) { return $null }
    try {
        return (@($raw | ConvertFrom-Json))[0]
    } catch {
        return $null
    }
}

function Test-GoldenPathWorkflowStartupFailure {
    param(
        [string]$FullRepo,
        $Run,
        [scriptblock]$InvokeExternal
    )

    if (-not $Run -or $Run.conclusion -ne "failure") { return $false }
    $jobCount = (& $InvokeExternal "gh" @(
        "api", "repos/$FullRepo/actions/runs/$($Run.databaseId)/jobs", "--jq", ".total_count"
    )).StdOut.Trim()
    return ($jobCount -eq "0")
}

function Start-GoldenPathDeployWorkflow {
    param(
        [string]$FullRepo,
        [scriptblock]$InvokeExternal,
        [string]$Environment = "dev"
    )

    Write-Host "  Triggering deploy via workflow_dispatch ($Environment) — first push on new repos often fails workflow validation" -ForegroundColor DarkGray
    & $InvokeExternal "gh" @(
        "workflow", "run", "deploy.yml", "--repo", $FullRepo, "-f", "environment=$Environment"
    ) | Out-Null
}

function Resolve-GoldenPathDeployRunId {
    param(
        [string]$FullRepo,
        [scriptblock]$InvokeExternal,
        [int]$InitialDelaySeconds = 8
    )

    Start-Sleep -Seconds $InitialDelaySeconds
    $latest = Get-GoldenPathLatestDeployRun -FullRepo $FullRepo -InvokeExternal $InvokeExternal
    if (-not $latest) {
        Start-GoldenPathDeployWorkflow -FullRepo $FullRepo -InvokeExternal $InvokeExternal
        Start-Sleep -Seconds 5
        $latest = Get-GoldenPathLatestDeployRun -FullRepo $FullRepo -InvokeExternal $InvokeExternal
        if ($latest) { return [string]$latest.databaseId }
        return $null
    }

    if (Test-GoldenPathWorkflowStartupFailure -FullRepo $FullRepo -Run $latest -InvokeExternal $InvokeExternal) {
        Start-GoldenPathDeployWorkflow -FullRepo $FullRepo -InvokeExternal $InvokeExternal
        Start-Sleep -Seconds 5
        $latest = Get-GoldenPathLatestDeployRun -FullRepo $FullRepo -InvokeExternal $InvokeExternal
        if ($latest) { return [string]$latest.databaseId }
        return $null
    }

    return [string]$latest.databaseId
}

function Wait-GoldenPathDeployRun {
    param(
        [string]$FullRepo,
        [scriptblock]$InvokeExternal,
        [int]$InitialDelaySeconds = 8
    )

    $runId = Resolve-GoldenPathDeployRunId -FullRepo $FullRepo -InvokeExternal $InvokeExternal `
        -InitialDelaySeconds $InitialDelaySeconds
    if (-not $runId) { return $false }

    Write-Host "  Watching deploy: https://github.com/$FullRepo/actions/runs/$runId" -ForegroundColor DarkGray
    Write-Host "  (live workflow output below — may take several minutes)" -ForegroundColor DarkGray
    Write-Host ""
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & gh run watch $runId --repo $FullRepo --exit-status 2>&1 | ForEach-Object {
        if ($_ -is [System.Management.Automation.ErrorRecord]) {
            Write-Host $_.ToString() -ForegroundColor Yellow
        } else {
            Write-Host $_
        }
    }
    $exit = if ($null -ne $LASTEXITCODE) { $LASTEXITCODE } else { 0 }
    $ErrorActionPreference = $prev
    Write-Host ""
    return ($exit -eq 0)
}

function Test-GhAuthMatchesOrg {
    param([string]$GithubOrg, [scriptblock]$InvokeExternal)
    $status = & $InvokeExternal "gh" @("auth", "status")
    $text = "$($status.StdOut)$($status.StdErr)"
    if ($status.ExitCode -ne 0) { throw "not logged in to GitHub — run: gh auth login" }
    if ($text -match 'account (\S+)') {
        $active = $Matches[1]
        if ($active -ne $GithubOrg) {
            throw "active gh account is '$active' but GITHUB_ORG is '$GithubOrg' — run: gh auth switch --user $GithubOrg"
        }
    }
}

function Invoke-GoldenPathPublish {
    param(
        [string]$ServiceDir,
        [string]$RepoRoot,
        [hashtable]$Config,
        [string]$WifProvider,
        [string]$WifServiceAccount,
        [scriptblock]$InvokeExternal,
        [switch]$WatchDeploy
    )

    if (-not (Test-Path $ServiceDir)) { throw "Service directory not found: $ServiceDir" }
    Test-GhAuthMatchesOrg -GithubOrg $Config.github_org -InvokeExternal $InvokeExternal
    $serviceDir = (Resolve-Path $ServiceDir).Path
    $serviceName = Split-Path $serviceDir -Leaf
    $fullRepo = "$($Config.github_org)/$serviceName"
    $gcpProject = $Config.gcp_dev_project

    $tfProject = Get-ServiceProjectFromTfvars $serviceDir
    if ($tfProject -and $tfProject -ne $gcpProject) {
        throw "infra/dev.tfvars has '$tfProject' but config has '$gcpProject'"
    }

    Invoke-GoldenPathUpgradePlatformPins -RepoRoot $RepoRoot -ServiceDir $serviceDir

    $brokenDeploy = Test-GoldenPathDeployWorkflow $serviceDir
    if ($brokenDeploy) {
        $template = Get-ServiceTemplateHint $serviceDir
        if (-not $template) { throw "deploy.yml has unreplaced {{tokens}} — re-scaffold or specify template for repair" }
        Repair-GoldenPathScaffoldTokens -RepoRoot $RepoRoot -ServiceDir $serviceDir -Template $template -Config $Config | Out-Null
    }

    Push-Location $serviceDir
    try {
        if (-not (Test-Path ".git")) { throw "Not a git repo: $serviceDir" }

        $branch = (& $InvokeExternal "git" @("branch", "--show-current")).StdOut.Trim()
        if ($branch -ne "main") {
            & $InvokeExternal "git" @("branch", "-M", "main") | Out-Null
        }

        if (-not $WifProvider -or -not $WifServiceAccount) {
            throw "WIF credentials missing — bootstrap first, then show WIF secrets"
        }

        $enterprise = Get-EnterpriseEnv $RepoRoot
        $platformRepo = if ($Config.github_platform_repo) {
            $Config.github_platform_repo
        } else {
            $enterprise.PLATFORM_REPO
        }
        if (-not $platformRepo) { $platformRepo = 'goldenpath' }
        if ($platformRepo -eq $serviceName) {
            $platformRepo = if ($enterprise.PLATFORM_REPO) { $enterprise.PLATFORM_REPO } else { 'goldenpath' }
        }
        $platformVisibility = Get-GoldenPathPlatformRepoVisibility $Config.github_org $platformRepo $InvokeExternal

        $remote = & $InvokeExternal "git" @("remote", "get-url", "origin")
        $repoExisted = ($remote.ExitCode -eq 0)
        if (-not $repoExisted) {
            $visibilityFlag = Get-GoldenPathRepoCreateVisibilityFlag $platformVisibility
            Write-Host "  [1/5] Creating GitHub repo $fullRepo ($platformVisibility) ..." -ForegroundColor DarkGray
            $create = & $InvokeExternal "gh" @(
                "repo", "create", $fullRepo,
                $visibilityFlag, "--source=.", "--remote=origin"
            )
            if ($create.ExitCode -ne 0) { throw "gh repo create failed — run: gh auth login" }
        } else {
            Write-Host "  [1/5] GitHub repo exists: $fullRepo" -ForegroundColor DarkGray
        }

        Write-Host "  [2/5] Setting GitHub secrets (WIF) ..." -ForegroundColor DarkGray
        & $InvokeExternal "gh" @("api", "repos/$fullRepo", "-X", "PATCH", "-f", "default_branch=main") | Out-Null

        $s1 = & $InvokeExternal "gh" @("secret", "set", "GCP_WIF_PROVIDER", "--body", $WifProvider, "--repo", $fullRepo)
        $s2 = & $InvokeExternal "gh" @("secret", "set", "GCP_WIF_SERVICE_ACCOUNT", "--body", $WifServiceAccount, "--repo", $fullRepo)
        if ($s1.ExitCode -ne 0 -or $s2.ExitCode -ne 0) { throw "Failed to set GitHub secrets" }

        if ($platformVisibility -eq "PRIVATE") {
            $moduleToken = (& $InvokeExternal "gh" @("auth", "token")).StdOut.Trim()
            if ($moduleToken) {
                Write-Host "  Setting GOLDENPATH_MODULE_TOKEN (private platform repo) ..." -ForegroundColor DarkGray
                $s3 = & $InvokeExternal "gh" @(
                    "secret", "set", "GOLDENPATH_MODULE_TOKEN", "--body", $moduleToken, "--repo", $fullRepo
                )
                if ($s3.ExitCode -ne 0) { throw "Failed to set GOLDENPATH_MODULE_TOKEN for private module fetch" }
            } else {
                throw "Platform repo is private — run 'gh auth login' so GOLDENPATH_MODULE_TOKEN can be set"
            }
        }

        Write-Host "  [3/5] Adding WIF trust for $fullRepo ..." -ForegroundColor DarkGray
        $wifTrust = Join-Path $RepoRoot "scripts/lib/wif-trust-repo.sh"
        if (Test-Path $wifTrust) {
            $wif = & $InvokeExternal "bash" @($wifTrust, $gcpProject, $Config.github_org, $serviceName)
            if ($wif.ExitCode -ne 0) { throw "WIF trust script failed" }
        } else {
            Add-GoldenPathWifTrust $gcpProject $Config.github_org $serviceName $InvokeExternal
            Start-Sleep -Seconds 45
        }

        Write-Host "  [4/5] Pushing main branch ..." -ForegroundColor DarkGray
        $push = & $InvokeExternal "git" @("push", "-u", "origin", "main")
        if ($push.ExitCode -ne 0) { throw "git push failed" }

        if ($WatchDeploy) {
            Write-Host "  [5/5] Waiting for deploy workflow ..." -ForegroundColor DarkGray
        }

        $deployOk = $null
        if ($WatchDeploy) {
            $deployOk = Wait-GoldenPathDeployRun -FullRepo $fullRepo -InvokeExternal $InvokeExternal
            if (-not $deployOk) {
                $latest = Get-GoldenPathLatestDeployRun -FullRepo $fullRepo -InvokeExternal $InvokeExternal
                if ($latest -and $latest.conclusion -eq 'failure') {
                    $failedId = [string]$latest.databaseId
                    if ($failedId -and -not (Test-GoldenPathWorkflowStartupFailure -FullRepo $fullRepo -Run $latest -InvokeExternal $InvokeExternal)) {
                        $rerun = & $InvokeExternal "gh" @("run", "rerun", $failedId, "--repo", $fullRepo)
                        if ($rerun.ExitCode -eq 0) {
                            $deployOk = Wait-GoldenPathDeployRun -FullRepo $fullRepo -InvokeExternal $InvokeExternal -InitialDelaySeconds 10
                        }
                    }
                }
                if (-not $deployOk) {
                    Start-GoldenPathDeployWorkflow -FullRepo $fullRepo -InvokeExternal $InvokeExternal
                    $deployOk = Wait-GoldenPathDeployRun -FullRepo $fullRepo -InvokeExternal $InvokeExternal -InitialDelaySeconds 10
                }
            }
            if (-not $deployOk) {
                Write-Host "  GitHub deploy failed — attempting local Terraform recovery ..." -ForegroundColor DarkGray
                $recover = Join-Path $RepoRoot "scripts/lib/deploy-recover-local.sh"
                if (Test-Path $recover) {
                    $rec = & $InvokeExternal "bash" @($recover, $serviceDir, "dev")
                    if ($rec.ExitCode -eq 0) { $deployOk = $true }
                }
            }
        }

        return [PSCustomObject]@{
            Repo         = $fullRepo
            ServiceDir   = $serviceDir
            GcpProject   = $gcpProject
            DeployOk     = $deployOk
        }
    } finally {
        Pop-Location
    }
}

function Test-GoldenPathServiceDoctor {
    param(
        [string]$ServiceDir,
        [hashtable]$Config,
        [scriptblock]$InvokeExternal,
        [string]$RepoRoot = ""
    )

    $issues = [System.Collections.Generic.List[string]]::new()
    if (-not (Test-Path $ServiceDir)) {
        $issues.Add("Service directory not found: $ServiceDir")
        return $issues
    }

    if (-not $RepoRoot) {
        $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../../..")).Path
    }

    $cli = Join-Path $RepoRoot "scripts/setup/goldenpath_ops_cli.py"
    if (Test-Path $cli) {
        $resolved = (Resolve-Path $ServiceDir).Path
        $doc = & $InvokeExternal "python3" @($cli, "doctor", $resolved)
        foreach ($line in @($doc.StdOut -split "`n")) {
            if ($line -match '^ISSUE=(.+)$') {
                $issues.Add($Matches[1])
            }
        }
        if ($issues.Count -gt 0 -or $doc.ExitCode -eq 0) {
            return $issues
        }
    }

    # Fallback when Python CLI is unavailable
    $serviceName = Split-Path (Resolve-Path $ServiceDir).Path -Leaf
    $fullRepo = "$($Config.github_org)/$serviceName"
    $ghAvailable = $null -ne (Get-Command gh -ErrorAction SilentlyContinue)

    Push-Location $ServiceDir
    try {
        $branch = (& $InvokeExternal "git" @("branch", "--show-current")).StdOut.Trim()
        if ($branch -ne "main") { $issues.Add("Local branch is '$branch' — run: git branch -M main") }

        $tfProject = Get-ServiceProjectFromTfvars $ServiceDir
        if ($tfProject -ne $Config.gcp_dev_project) {
            $issues.Add("project_id mismatch: tfvars='$tfProject' config='$($Config.gcp_dev_project)'")
        }

        if ($ghAvailable) {
            $defaultBranch = (& $InvokeExternal "gh" @("api", "repos/$fullRepo", "--jq", ".default_branch")).StdOut.Trim()
            if ($defaultBranch -and $defaultBranch -ne "main") {
                $issues.Add("GitHub default branch is '$defaultBranch' (should be main)")
            }

            $secrets = (& $InvokeExternal "gh" @("secret", "list", "--repo", $fullRepo)).StdOut
            foreach ($s in @("GCP_WIF_PROVIDER", "GCP_WIF_SERVICE_ACCOUNT")) {
                if ($secrets -notmatch $s) { $issues.Add("Missing GitHub secret: $s") }
            }
        } else {
            $issues.Add("gh CLI not found — skipping GitHub secret checks")
        }

        $brokenDeploy = Test-GoldenPathDeployWorkflow $ServiceDir
        if ($brokenDeploy) {
            $issues.Add("deploy.yml has unreplaced template tokens ({{...}}) — publish will auto-repair, or re-run menu 6")
        }
    } finally {
        Pop-Location
    }

    return $issues
}