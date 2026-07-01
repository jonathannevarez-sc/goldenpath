# Cloud Run URL lookup + health verification for wizard publish flow.
Set-StrictMode -Version Latest

function Get-ServiceHealthPaths {
    param(
        [string]$ServiceDir,
        [string]$RepoRoot
    )

    $paths = [System.Collections.Generic.List[string]]::new()
    $template = Get-ServiceTemplateHint $ServiceDir
    if ($template) {
        $catalog = Get-GoldenPathCatalog $RepoRoot
        if ($template -in $catalog.PSObject.Properties.Name) {
            $paths.Add([string]$catalog.$template.health_check_path)
        }
    }

    $deployWorkflow = Join-Path $ServiceDir ".github/workflows/deploy.yml"
    if (Test-Path $deployWorkflow) {
        $raw = Get-Content $deployWorkflow -Raw
        if ($raw -match 'health[_-]?check[_-]?path["\s:=]+([/\w-]+)') {
            $hint = $Matches[1]
            if ($hint -and $hint -notin $paths) { $paths.Add($hint) }
        }
    }

    foreach ($fallback in @("/api/health", "/health", "/_stcore/health")) {
        if ($fallback -notin $paths) { $paths.Add($fallback) }
    }
    return $paths
}

function Get-CloudRunServiceUrl {
    param(
        [string]$ServiceName,
        [string]$Project,
        [string]$Region,
        [scriptblock]$InvokeExternal
    )

    $result = & $InvokeExternal "gcloud" @(
        "run", "services", "describe", $ServiceName,
        "--project=$Project", "--region=$Region",
        "--format=value(status.url)"
    )
    if ($result.ExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($result.StdOut.Trim())) {
        return $null
    }
    return $result.StdOut.Trim()
}

function Invoke-GoldenPathVerifyDeployment {
    param(
        [string]$CloudRunService,
        [string]$ServiceDir = "",
        [string]$RepoRoot = "",
        [hashtable]$Config,
        [scriptblock]$InvokeExternal,
        [int]$MaxAttempts = 8,
        [int]$RetryDelaySeconds = 8,
        [switch]$Quiet
    )

    $project = $Config.gcp_project
    $region = $Config.gcp_region
    $url = $null
    $paths = if ($ServiceDir -and $RepoRoot) {
        Get-ServiceHealthPaths -ServiceDir $ServiceDir -RepoRoot $RepoRoot
    } else {
        [string[]]@("/api/health", "/health", "/_stcore/health")
    }

    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        if (-not $Quiet -and $attempt -gt 1) {
            Write-Host "  Waiting for Cloud Run ($attempt/$MaxAttempts)..." -ForegroundColor DarkGray
        }
        $url = Get-CloudRunServiceUrl -ServiceName $CloudRunService -Project $project -Region $region -InvokeExternal $InvokeExternal
        if ($url) { break }
        if ($attempt -lt $MaxAttempts) { Start-Sleep -Seconds $RetryDelaySeconds }
    }

    if (-not $url) {
        return [PSCustomObject]@{
            CloudRunService = $CloudRunService
            Url             = $null
            HealthOk        = $false
            HealthPath      = $null
            StatusCode      = $null
            ResponsePreview = ""
            Error           = "Service '$CloudRunService' not found in $project ($region)"
        }
    }

    $healthOk = $false
    $healthPath = $null
    $statusCode = $null
    $preview = ""

    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        foreach ($path in $paths) {
            try {
                $resp = Invoke-WebRequest -Uri "$url$path" -UseBasicParsing -TimeoutSec 20
                $healthOk = $true
                $healthPath = $path
                $statusCode = [int]$resp.StatusCode
                $preview = $resp.Content.Substring(0, [Math]::Min(200, $resp.Content.Length))
                break
            } catch {
                if (-not $Quiet) {
                    Write-Host "  Health $path → not ready yet" -ForegroundColor DarkGray
                }
            }
        }
        if ($healthOk) { break }
        if ($attempt -lt $MaxAttempts) { Start-Sleep -Seconds $RetryDelaySeconds }
    }

    return [PSCustomObject]@{
        CloudRunService = $CloudRunService
        Url             = $url
        HealthOk        = $healthOk
        HealthPath      = $healthPath
        StatusCode      = $statusCode
        ResponsePreview = $preview
        Error           = if ($healthOk) { $null } else { "No health endpoint responded on $url" }
    }
}

function Show-DeploymentResult {
    param(
        $Verify,
        [string]$Repo = "",
        [switch]$Verbose
    )

    Write-Host ""
    Write-Host "  ┌─ Deployment summary ──────────────────────────────────────┐" -ForegroundColor Cyan
    if ($Repo) {
        Write-Host "  │  GitHub repo     https://github.com/$Repo"
        Write-Host "  │  Actions         https://github.com/$Repo/actions"
    }
    Write-Host "  │  Cloud Run       $($Verify.CloudRunService)"
    if ($Verify.Url) {
        Write-Host "  │  Live URL        $($Verify.Url)" -ForegroundColor White
    } else {
        Write-Host "  │  Live URL        (not found yet)" -ForegroundColor Yellow
    }
    if ($Verify.HealthOk) {
        Write-Host "  │  Health          $($Verify.HealthPath) → HTTP $($Verify.StatusCode)" -ForegroundColor Green
        if ($Verbose -and $Verify.ResponsePreview) {
            Write-Host "  │  Response        $($Verify.ResponsePreview)" -ForegroundColor DarkGray
        }
    } elseif ($Verify.Url) {
        Write-Host "  │  Health          not responding yet — try menu 8 in a minute" -ForegroundColor Yellow
    }
    Write-Host "  └───────────────────────────────────────────────────────────┘" -ForegroundColor Cyan
    Write-Host ""

    if ($Verify.Url -and $Verify.HealthOk) {
        Write-Host "  Open your app:" -ForegroundColor White
        Write-Host "    $($Verify.Url)" -ForegroundColor Green
        Write-Host ""
    }
}