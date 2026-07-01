#!/usr/bin/env bash
# Golden Path setup wizard — unified launcher (pick backend or auto-detect).
#
# Usage:
#   ./scripts/goldenpath-setup.sh                    # auto: pwsh → ps, else bash
#   ./scripts/goldenpath-setup.sh --backend bash     # bash wizard (no pwsh)
#   ./scripts/goldenpath-setup.sh --backend py       # Python wizard
#   ./scripts/goldenpath-setup.sh --backend ps       # PowerShell wizard
#   ./scripts/goldenpath-setup.sh --backend ui       # Streamlit browser UI
#   ./scripts/goldenpath-setup.sh --wizard|--help    # passed to the wizard
#
# Aliases (same behavior): goldenpath-setup-{bash,py,ui,ps}.sh
# Implementation lives in scripts/setup/ — this file is a thin router only.
# Docs: docs/getting-started/07-setup-wizard-usage.md
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SETUP_DIR="${SCRIPT_DIR}/setup"
BACKEND="auto"
WIZARD_ARGS=()

usage() {
  cat <<EOF
Golden Path setup wizard — launcher (not the implementation).

Usage:
  ./scripts/goldenpath-setup.sh [--backend MODE] [wizard args...]

Backends:
  auto     Pick ps if pwsh exists, else bash (default)
  ps       PowerShell → setup/goldenpath-setup.ps1
  bash     Bash CLI  → setup/goldenpath_setup.sh
  py       Python    → setup/goldenpath_setup.py
  ui       Streamlit → setup/goldenpath_setup_app.py

Wizard args (forwarded): --wizard, --help, -h
  --dryrun      Read-only audit — same as wizard menu 15 (no deploy)

Shortcuts:
  ./scripts/goldenpath-setup-bash.sh   (= --backend bash)
  ./scripts/goldenpath-setup-py.sh     (= --backend py)
  ./scripts/goldenpath-setup-ui.sh     (= --backend ui)
  ./scripts/goldenpath-setup-ps.sh     (= --backend ps)

Layout:  ./scripts/check-repo-hygiene.sh --explain
Docs:    docs/getting-started/07-setup-wizard-usage.md
EOF
}

has_pwsh() {
  command -v pwsh >/dev/null 2>&1 || command -v powershell >/dev/null 2>&1
}

run_ps() {
  local ps1="${SETUP_DIR}/goldenpath-setup.ps1"
  if command -v pwsh >/dev/null 2>&1; then
    if [[ ${#WIZARD_ARGS[@]} -gt 0 ]]; then
      exec pwsh -File "${ps1}" "${WIZARD_ARGS[@]}"
    else
      exec pwsh -File "${ps1}"
    fi
  fi
  if command -v powershell >/dev/null 2>&1; then
    if [[ ${#WIZARD_ARGS[@]} -gt 0 ]]; then
      exec powershell -File "${ps1}" "${WIZARD_ARGS[@]}"
    else
      exec powershell -File "${ps1}"
    fi
  fi
  cat <<'EOF'
PowerShell backend requires pwsh.

  macOS:   brew install powershell
  Or use:  ./scripts/goldenpath-setup.sh --backend bash

EOF
  exit 1
}

run_bash() {
  local sh="${SETUP_DIR}/goldenpath_setup.sh"
  chmod +x "${sh}" 2>/dev/null || true
  if [[ ${#WIZARD_ARGS[@]} -gt 0 ]]; then
    exec bash "${sh}" "${WIZARD_ARGS[@]}"
  else
    exec bash "${sh}"
  fi
}

run_py() {
  local py="${SETUP_DIR}/goldenpath_setup.py"
  if ! command -v python3 >/dev/null 2>&1; then
    echo "Python backend requires python3." >&2
    exit 1
  fi
  if [[ ${#WIZARD_ARGS[@]} -gt 0 ]]; then
    exec python3 "${py}" "${WIZARD_ARGS[@]}"
  else
    exec python3 "${py}"
  fi
}

run_ui() {
  local app="${SETUP_DIR}/goldenpath_setup_app.py"
  if ! command -v streamlit >/dev/null 2>&1; then
    cat <<'EOF'
Streamlit backend requires: pip install streamlit
EOF
    exit 1
  fi
  if [[ ${#WIZARD_ARGS[@]} -gt 0 ]]; then
    exec streamlit run "${app}" "${WIZARD_ARGS[@]}"
  else
    exec streamlit run "${app}"
  fi
}

resolve_auto() {
  if has_pwsh; then
    echo "ps"
  else
    echo "bash"
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dryrun)
      if ! command -v python3 >/dev/null 2>&1; then
        echo "python3 required for --dryrun" >&2
        exit 1
      fi
      exec python3 "${SETUP_DIR}/goldenpath_dryrun.py" "${@:2}"
      ;;
    --backend)
      BACKEND="${2:?--backend requires ps|bash|py|ui|auto}"
      shift 2
      ;;
    --backend=*)
      BACKEND="${1#*=}"
      shift
      ;;
    --explain-launchers)
      exec "${SCRIPT_DIR}/check-repo-hygiene.sh" --explain
      ;;
    -h|--help)
      if [[ ${#WIZARD_ARGS[@]} -eq 0 && "$BACKEND" == "auto" ]]; then
        usage
        exit 0
      fi
      WIZARD_ARGS+=("$1")
      shift
      ;;
    *)
      WIZARD_ARGS+=("$1")
      shift
      ;;
  esac
done

case "${BACKEND}" in
  auto) BACKEND="$(resolve_auto)" ;;
  powershell|pwsh|ps1|ps) BACKEND="ps" ;;
  python|py3|py) BACKEND="py" ;;
  streamlit|ui) BACKEND="ui" ;;
  bash|sh) BACKEND="bash" ;;
  ps|bash|py|ui) ;;
  *)
    echo "Unknown backend: ${BACKEND} (use ps|bash|py|ui|auto)" >&2
    exit 1
    ;;
esac

if [[ "$BACKEND" == "auto" ]]; then
  BACKEND="$(resolve_auto)"
fi

case "${BACKEND}" in
  ps)   run_ps ;;
  bash) run_bash ;;
  py)   run_py ;;
  ui)   run_ui ;;
esac