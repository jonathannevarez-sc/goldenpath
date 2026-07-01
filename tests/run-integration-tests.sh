#!/usr/bin/env bash
# Tier 2 enterprise integration tests (sandbox GitHub + GCP).
# Required for customer-facing releases — see tests/README.md § Release acceptance.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

: "${INTEGRATION_TEST_ENABLED:?Set INTEGRATION_TEST_ENABLED=1 for Tier 2 integration}"
: "${SHOP_GITHUB_ORG:?Required}"
: "${SHOP_GCP_DEV_PROJECT:?Required}"
: "${GCP_REGION:?Required}"
: "${GH_TOKEN:?Required (or GITHUB_TOKEN)}"

export GITHUB_TOKEN="${GITHUB_TOKEN:-${GH_TOKEN}}"

VENV="${SCRIPT_DIR}/.venv"
if [[ ! -x "${VENV}/bin/python" ]]; then
  python3 -m venv "${VENV}"
  "${VENV}/bin/pip" install -q -r "${SCRIPT_DIR}/requirements-test.txt"
  "${VENV}/bin/pip" install -q -e "${REPO_ROOT}/mcp"
fi

echo "Tier 2 integration: sandbox deploy spine"
"${VENV}/bin/python" -m pytest "${SCRIPT_DIR}/integration" -m integration -q --tb=short
echo "Tier 2 integration passed."