#!/usr/bin/env bash
# Run all Golden Path platform tests (bash + Python + Pester when available).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

FAILED=0

run_step() {
  local name="$1"
  shift
  echo ""
  echo "==> ${name}"
  echo "----------------------------------------"
  if "$@"; then
    echo "PASS: ${name}"
  else
    echo "FAIL: ${name}"
    FAILED=$((FAILED + 1))
  fi
}

run_step "Bash tests" bash "${SCRIPT_DIR}/bash/run-bash-tests.sh"

if command -v python3 >/dev/null 2>&1; then
  VENV="${SCRIPT_DIR}/.venv"
  STAMP="${VENV}/.deps-stamp"
  NEED_INSTALL=false
  if [[ ! -x "${VENV}/bin/python" ]]; then
    NEED_INSTALL=true
  elif [[ "${SCRIPT_DIR}/requirements-test.txt" -nt "${STAMP}" ]]; then
    NEED_INSTALL=true
  elif [[ "${REPO_ROOT}/mcp/pyproject.toml" -nt "${STAMP}" ]]; then
    NEED_INSTALL=true
  fi
  if [[ "${NEED_INSTALL}" == "true" ]]; then
    echo "Installing/updating test virtualenv at tests/.venv ..."
    python3 -m venv "${VENV}"
    "${VENV}/bin/pip" install -q -r "${SCRIPT_DIR}/requirements-test.txt"
    "${VENV}/bin/pip" install -q -e "${REPO_ROOT}/mcp"
    touch "${STAMP}"
  fi
  run_step "Python tests" "${VENV}/bin/python" -m pytest "${SCRIPT_DIR}" -q --tb=short
else
  echo "SKIP: Python tests (python3 not found)"
  FAILED=$((FAILED + 1))
fi

if command -v pwsh >/dev/null 2>&1; then
  run_step "Pester tests" pwsh -NoProfile -File "${SCRIPT_DIR}/Run-SetupWizardTests.ps1" -NoCoverage
else
  echo "SKIP: Pester tests (pwsh not found)"
fi

echo ""
if [[ "$FAILED" -gt 0 ]]; then
  echo "Some test suites failed (${FAILED})."
  exit 1
fi
echo "All requested test suites passed."
exit 0