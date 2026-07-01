#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/assert.sh
source "${SCRIPT_DIR}/lib/assert.sh"

REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "${TMP_ROOT}"' EXIT

mkdir -p "${TMP_ROOT}/config"
cp "${REPO_ROOT}/config/enterprise.env.example" "${TMP_ROOT}/config/enterprise.env"
sed -i '' 's/^GITHUB_ORG=.*/GITHUB_ORG=test-org/' "${TMP_ROOT}/config/enterprise.env" 2>/dev/null \
  || sed -i 's/^GITHUB_ORG=.*/GITHUB_ORG=test-org/' "${TMP_ROOT}/config/enterprise.env"
sed -i '' 's/^PARENT_PROJECT_ID=.*/PARENT_PROJECT_ID=billing-anchor-test/' "${TMP_ROOT}/config/enterprise.env" 2>/dev/null \
  || sed -i 's/^PARENT_PROJECT_ID=.*/PARENT_PROJECT_ID=billing-anchor-test/' "${TMP_ROOT}/config/enterprise.env"
sed -i '' 's/^BILLING_ACCOUNT_ID=.*/BILLING_ACCOUNT_ID=000000-000000-000000/' "${TMP_ROOT}/config/enterprise.env" 2>/dev/null \
  || sed -i 's/^BILLING_ACCOUNT_ID=.*/BILLING_ACCOUNT_ID=000000-000000-000000/' "${TMP_ROOT}/config/enterprise.env"
sed -i '' 's/^PROTECTED_PROJECTS=.*/PROTECTED_PROJECTS=protected-a,protected-b/' "${TMP_ROOT}/config/enterprise.env" 2>/dev/null \
  || sed -i 's/^PROTECTED_PROJECTS=.*/PROTECTED_PROJECTS=protected-a,protected-b/' "${TMP_ROOT}/config/enterprise.env"

# shellcheck source=../../scripts/lib/load-config.sh
source "${REPO_ROOT}/scripts/lib/load-config.sh"

test_start "load_goldenpath_config exports SHOP_* vars"
export GOLDENPATH_CONFIG="${TMP_ROOT}/config/enterprise.env"
load_goldenpath_config "${REPO_ROOT}"
assert_eq "test-org" "${GITHUB_ORG}"
assert_eq "test-org" "${SHOP_GITHUB_ORG}"
test_end

test_start "goldenpath_is_protected_project detects protected ids"
export PROTECTED_PROJECTS="protected-a,protected-b"
assert_exit 0 goldenpath_is_protected_project protected-a
assert_exit 1 goldenpath_is_protected_project my-sandbox-123
test_end

test_start "load_goldenpath_config fails on missing file"
unset GOLDENPATH_CONFIG
assert_exit 1 load_goldenpath_config "${TMP_ROOT}/missing-root"
test_end

test_summary