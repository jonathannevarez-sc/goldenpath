#!/usr/bin/env bash
# Static parity checks: PS / bash / Python wizards expose the same critical surfaces.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/assert.sh
source "${SCRIPT_DIR}/lib/assert.sh"

REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
SETUP="${REPO_ROOT}/scripts/setup"

must_contain() {
  local file="$1" pattern="$2" label="$3"
  if ! grep -q -e "$pattern" "$file"; then
    echo "parity miss: ${label} — expected '${pattern}' in ${file}" >&2
    return 1
  fi
}

test_start "menu 15 dry run in PowerShell wizard"
must_contain "${SETUP}/goldenpath-setup.ps1" '15.*Dry run' "ps menu 15"
must_contain "${SETUP}/goldenpath-setup.ps1" '--dryrun' "ps --dryrun flag"
must_contain "${SETUP}/goldenpath-setup.ps1" 'FULL MENU' "ps help full menu"
must_contain "${SETUP}/goldenpath-setup.ps1" 'TROUBLESHOOTING' "ps help troubleshooting"
test_end

test_start "menu 15 dry run in Python wizard"
must_contain "${SETUP}/goldenpath_setup.py" '15.*Dry run' "py menu 15"
must_contain "${SETUP}/goldenpath_setup.py" 'invoke_dryrun' "py invoke_dryrun"
test_end

test_start "menu 15 dry run in bash wizard"
must_contain "${SETUP}/goldenpath_setup.sh" '15.*Dry run' "bash menu 15"
must_contain "${SETUP}/goldenpath_setup.sh" 'invoke_dryrun' "bash invoke_dryrun"
test_end

test_start "launcher --dryrun flag"
must_contain "${REPO_ROOT}/scripts/goldenpath-setup.sh" '--dryrun' "launcher dryrun"
test_end

test_start "PS scaffold + repair module functions"
must_contain "${SETUP}/modules/Scaffold.ps1" 'function Invoke-GoldenPathScaffold' "Invoke-GoldenPathScaffold"
must_contain "${SETUP}/modules/Scaffold.ps1" 'function Repair-GoldenPathScaffoldTokens' "Repair-GoldenPathScaffoldTokens"
must_contain "${SETUP}/modules/Publish.ps1" 'Repair-GoldenPathScaffoldTokens' "publish repair call"
test_end

test_start "PS bootstrap display name clamp + teardown guards"
must_contain "${SETUP}/modules/Bootstrap.ps1" 'function Get-GcpProjectDisplayName' "Get-GcpProjectDisplayName"
must_contain "${SETUP}/modules/Bootstrap.ps1" 'ExpectedProjectId' "teardown project match"
must_contain "${SETUP}/modules/Bootstrap.ps1" 'ProtectedProjects' "teardown protected guard"
test_end

test_start "Python ops parity (display, repair, dryrun)"
must_contain "${SETUP}/goldenpath_ops.py" 'def normalize_project_display_name' "py normalize display"
must_contain "${SETUP}/goldenpath_ops.py" 'def repair_scaffold_tokens' "py repair tokens"
must_contain "${SETUP}/goldenpath_dryrun.py" 'def run_dryrun' "py dryrun"
test_end

test_start "bash ops parity (display normalize, shared Python ops CLI)"
must_contain "${SETUP}/goldenpath_setup_ops.sh" 'wizard_normalize_display_name' "bash normalize display"
must_contain "${SETUP}/goldenpath_setup_ops.sh" 'wizard_invoke_ops_cli' "bash ops cli delegate"
must_contain "${SETUP}/goldenpath_setup_ops.sh" 'goldenpath_ops_cli.py' "bash ops cli path"
test_end

test_start "shared ops CLI surfaces (scaffold, publish, doctor, upgrade)"
must_contain "${SETUP}/goldenpath_ops_cli.py" 'def _cmd_scaffold' "ops cli scaffold"
must_contain "${SETUP}/goldenpath_ops_cli.py" 'def _cmd_publish' "ops cli publish"
must_contain "${SETUP}/goldenpath_ops_cli.py" 'def _cmd_doctor' "ops cli doctor"
must_contain "${SETUP}/goldenpath_ops_cli.py" 'def _cmd_upgrade' "ops cli upgrade"
must_contain "${SETUP}/goldenpath_ops.py" 'def upgrade_platform_pins' "ops upgrade pins"
test_end

test_start "PowerShell upgrade pins via shared ops CLI"
must_contain "${SETUP}/modules/OpsCli.ps1" 'Invoke-GoldenPathUpgradePlatformPins' "ps upgrade helper"
must_contain "${SETUP}/modules/Scaffold.ps1" 'Invoke-GoldenPathUpgradePlatformPins' "ps scaffold upgrade"
must_contain "${SETUP}/modules/Publish.ps1" 'Invoke-GoldenPathUpgradePlatformPins' "ps publish upgrade"
test_end

test_start "shop CLI delegates to shared ops"
must_contain "${REPO_ROOT}/cli/shop" 'shop_invoke_ops' "shop ops delegate"
must_contain "${REPO_ROOT}/cli/shop" 'goldenpath_ops_cli.py' "shop ops cli path"
test_end

test_start "menu 3 prerequisites in all backends"
must_contain "${SETUP}/goldenpath-setup.ps1" 'Test-Prerequisites' "ps prerequisites"
must_contain "${SETUP}/goldenpath_setup.py" 'test_prerequisites' "py prerequisites"
must_contain "${SETUP}/goldenpath_setup.sh" 'test_prerequisites' "bash prerequisites"
test_end

test_start "display name clamp on edit settings (all backends)"
must_contain "${SETUP}/goldenpath-setup.ps1" 'Get-GcpProjectDisplayName' "ps edit clamp"
must_contain "${SETUP}/goldenpath_setup.py" 'normalize_project_display_name' "py edit clamp"
must_contain "${SETUP}/goldenpath_setup.sh" 'wizard_normalize_display_name' "bash edit clamp"
test_end

test_summary