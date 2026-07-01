# Shared Python ops CLI helpers for PowerShell wizard modules.
Set-StrictMode -Version Latest

function Invoke-GoldenPathUpgradePlatformPins {
    param(
        [string]$RepoRoot,
        [string]$ServiceDir
    )

    $cli = Join-Path $RepoRoot "scripts/setup/goldenpath_ops_cli.py"
    if (-not (Test-Path $cli)) { return }

    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & python3 $cli upgrade $ServiceDir 2>&1 | ForEach-Object {
            if ($_ -is [System.Management.Automation.ErrorRecord]) {
                Write-Host $_.ToString() -ForegroundColor DarkGray
            } else {
                Write-Host $_ -ForegroundColor DarkGray
            }
        }
        $exit = if ($null -ne $LASTEXITCODE) { $LASTEXITCODE } else { 0 }
        if ($exit -ne 0) {
            throw "upgrade platform pins failed (exit $exit)"
        }
    } finally {
        $ErrorActionPreference = $prev
    }
}