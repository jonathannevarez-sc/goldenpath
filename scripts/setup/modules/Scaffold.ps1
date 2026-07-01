# Pure PowerShell service scaffold — no shop CLI dependency.
Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot "OpsCli.ps1")

function Get-GoldenPathCatalog([string]$RepoRoot) {
    $path = Join-Path $RepoRoot "templates/catalog.json"
    if (-not (Test-Path $path)) { throw "Missing templates/catalog.json" }
    return Get-Content $path -Raw | ConvertFrom-Json
}

function Get-ScaffoldConfigValue($Config, [string]$Key, [string]$Default = "") {
    if ($Config -is [System.Collections.IDictionary]) {
        if ($Config.Contains($Key)) {
            $val = $Config[$Key]
            if ($null -ne $val -and "$val".Length -gt 0) { return [string]$val }
        }
        return $Default
    }
    if ($Config.PSObject.Properties.Name -contains $Key) {
        $val = $Config.$Key
        if ($null -ne $val -and "$val".Length -gt 0) { return [string]$val }
    }
    return $Default
}

function Get-ScaffoldEnterpriseProfile([string]$RepoRoot) {
    $merged = @{}
    $example = Join-Path $RepoRoot "config/enterprise.env.example"
    if (Test-Path $example) {
        Get-Content $example | ForEach-Object {
            if ($_ -match '^\s*([A-Z_]+)=(.*)$') {
                $merged[$Matches[1]] = $Matches[2].Trim().Trim('"')
            }
        }
    }
    $enterprise = Join-Path $RepoRoot "config/enterprise.env"
    if (Test-Path $enterprise) {
        Get-Content $enterprise | ForEach-Object {
            if ($_ -match '^\s*([A-Z_]+)=(.*)$') {
                $merged[$Matches[1]] = $Matches[2].Trim().Trim('"')
            }
        }
    }
    return $merged
}

function Set-GoldenPathScaffoldTokens {
    param(
        [string]$TargetDir,
        [string]$ServiceName,
        $Config,
        $Meta,
        [string]$RepoRoot
    )

    $profile = Get-ScaffoldEnterpriseProfile $RepoRoot
    $devProject = Get-ScaffoldConfigValue $Config 'gcp_dev_project'
    $prodProject = Get-ScaffoldConfigValue $Config 'gcp_prod_project'
    # Workflow/module pin always follows enterprise.env — never stale wizard JSON.
    $goldenpathVersion = $profile.GOLDENPATH_VERSION
    if (-not $goldenpathVersion) {
        $goldenpathVersion = Get-ScaffoldConfigValue $Config 'goldenpath_version'
    }
    $gcpRegion = Get-ScaffoldConfigValue $Config 'gcp_region'
    if (-not $gcpRegion) { $gcpRegion = $profile.GCP_REGION }
    $platformRepo = Get-ScaffoldConfigValue $Config 'github_platform_repo'
    if (-not $platformRepo) { $platformRepo = $profile.PLATFORM_REPO }
    if (-not $platformRepo) { $platformRepo = 'goldenpath' }
    if ($platformRepo -eq $ServiceName) {
        $platformRepo = if ($profile.PLATFORM_REPO) { $profile.PLATFORM_REPO } else { 'goldenpath' }
    }

    $replacements = [ordered]@{
        '{{SERVICE_NAME}}'       = $ServiceName
        '{{GITHUB_ORG}}'         = if ($profile.GITHUB_ORG) { $profile.GITHUB_ORG } else { Get-ScaffoldConfigValue $Config 'github_org' }
        '{{PLATFORM_REPO}}'      = $platformRepo
        '{{GOLDENPATH_VERSION}}' = $goldenpathVersion
        '{{GCP_DEV_PROJECT}}'    = $devProject
        '{{GCP_PROD_PROJECT}}'   = $prodProject
        '{{GCP_REGION}}'         = $gcpRegion
        '{{ARTIFACT_REGISTRY_REPO}}' = $profile.ARTIFACT_REGISTRY_REPO
        '{{APP_RUNTIME}}'        = $Meta.app_runtime
        '{{HEALTH_CHECK_PATH}}'  = $Meta.health_check_path
        '{{CONTAINER_PORT}}'     = [string]$Meta.container_port
    }

    $skip = @('node_modules', '__pycache__', '.pytest_cache', '/.git/')
    foreach ($file in Get-ChildItem -Path $TargetDir -Recurse -File -Force) {
        if ($skip | Where-Object { $file.FullName -like "*$_*" }) { continue }
        $raw = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue
        if (-not $raw) { continue }
        if ($raw -notmatch '\{\{[A-Z_]+\}\}') { continue }

        foreach ($key in $replacements.Keys) {
            $raw = $raw.Replace([string]$key, [string]$replacements[$key])
        }
        Set-Content -Path $file.FullName -Value $raw -NoNewline -Encoding UTF8
    }
}

function Test-GoldenPathDeployWorkflow([string]$ServiceDir) {
    $deployWorkflow = Join-Path $ServiceDir ".github/workflows/deploy.yml"
    if (-not (Test-Path $deployWorkflow)) { return $null }
    $raw = Get-Content $deployWorkflow -Raw
    if ($raw -match '\{\{[A-Z_]+\}\}') { return $deployWorkflow }
    return $null
}

function Get-ServiceTemplateHint([string]$ServiceDir) {
    $req = Join-Path $ServiceDir "requirements.txt"
    if (Test-Path $req) {
        $content = Get-Content $req -Raw
        if ($content -match '(?m)^streamlit') { return 'streamlit' }
        if ($content -match '(?m)^fastapi') { return 'fastapi' }
    }
    $pkg = Join-Path $ServiceDir "package.json"
    if (Test-Path $pkg) {
        try {
            $json = Get-Content $pkg -Raw | ConvertFrom-Json
        } catch {
            return $null
        }
        $deps = @()
        if ($json.PSObject.Properties.Name -contains 'dependencies' -and $json.dependencies) {
            $deps += $json.dependencies.PSObject.Properties.Name
        }
        if ($json.PSObject.Properties.Name -contains 'devDependencies' -and $json.devDependencies) {
            $deps += $json.devDependencies.PSObject.Properties.Name
        }
        if ($deps -contains 'next') { return 'nextjs' }
        if ($deps -contains 'express') { return 'express' }
        if ($deps -contains 'react') { return 'react-spa' }
        if ($deps -contains 'svelte') { return 'svelte-spa' }
    }
    return $null
}

function Test-GoldenPathServiceName([string]$Name) {
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

function Invoke-GoldenPathScaffold {
    param(
        [string]$RepoRoot,
        [string]$ServiceName,
        [string]$Template,
        [string]$OutputDir,
        $Config
    )

    $nameErr = Test-GoldenPathServiceName $ServiceName
    if ($nameErr) { throw $nameErr }

    $catalog = Get-GoldenPathCatalog $RepoRoot
    $meta = $catalog.PSObject.Properties[$Template]
    if (-not $meta) {
        $available = ($catalog.PSObject.Properties | ForEach-Object { $_.Name }) -join ', '
        throw "Unknown template '$Template'. Available: $available"
    }
    $meta = $meta.Value

    $templateDir = Join-Path $RepoRoot "templates/$Template"
    if (-not (Test-Path $templateDir)) {
        throw "Template directory not found: $templateDir"
    }

    $targetDir = Join-Path $OutputDir $ServiceName
    if ((Test-Path $targetDir) -and @(Get-ChildItem -Path $targetDir -Force -ErrorAction SilentlyContinue).Count -eq 0) {
        # Wizard may create an empty folder before copying template files.
    } elseif ((Test-Path $targetDir) -and @(Get-ChildItem -Path $targetDir -Force -ErrorAction SilentlyContinue).Count -gt 0) {
        throw "Target already exists and is not empty: $targetDir"
    } else {
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    }

    Copy-Item -Path (Join-Path $templateDir '*') -Destination $targetDir -Recurse -Force

    Set-GoldenPathScaffoldTokens -TargetDir $targetDir -ServiceName $ServiceName `
        -Config $Config -Meta $meta -RepoRoot $RepoRoot

    Invoke-GoldenPathUpgradePlatformPins -RepoRoot $RepoRoot -ServiceDir $targetDir

    $broken = Test-GoldenPathDeployWorkflow $targetDir
    if ($broken) {
        throw "deploy.yml still has unreplaced template tokens: $broken"
    }

    if (Get-Command git -ErrorAction SilentlyContinue) {
        Push-Location $targetDir
        try {
            & git init -q -b main
            if ($LASTEXITCODE -ne 0) { throw "git init failed (exit $LASTEXITCODE)" }
            & git add .
            if ($LASTEXITCODE -ne 0) { throw "git add failed (exit $LASTEXITCODE)" }
            & git commit -q -m "chore: scaffold $ServiceName from golden path ($Template)"
            if ($LASTEXITCODE -ne 0) { throw "git commit failed (exit $LASTEXITCODE)" }
        } finally {
            Pop-Location
        }
    }

    return [PSCustomObject]@{
        ServiceDir        = (Resolve-Path $targetDir).Path
        ServiceName       = $ServiceName
        Template          = $Template
        HealthCheckPath   = [string]$meta.health_check_path
    }
}

function Repair-GoldenPathScaffoldTokens {
    param(
        [string]$RepoRoot,
        [string]$ServiceDir,
        [string]$Template,
        $Config
    )

    $catalog = Get-GoldenPathCatalog $RepoRoot
    $metaProp = $catalog.PSObject.Properties[$Template]
    if (-not $metaProp) {
        $available = ($catalog.PSObject.Properties | ForEach-Object { $_.Name }) -join ', '
        throw "Unknown template '$Template'. Available: $available"
    }

    $serviceName = Split-Path $ServiceDir -Leaf
    Set-GoldenPathScaffoldTokens -TargetDir $ServiceDir -ServiceName $serviceName `
        -Config $Config -Meta $metaProp.Value -RepoRoot $RepoRoot

    Invoke-GoldenPathUpgradePlatformPins -RepoRoot $RepoRoot -ServiceDir $ServiceDir

    $broken = Test-GoldenPathDeployWorkflow $ServiceDir
    if ($broken) {
        throw "deploy.yml still has unreplaced template tokens: $broken"
    }
    return $ServiceDir
}