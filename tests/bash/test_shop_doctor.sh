#!/usr/bin/env bash
# Contract tests for shop doctor — scaffolded service diagnostics.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/assert.sh
source "${SCRIPT_DIR}/lib/assert.sh"

REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
SHOP="${REPO_ROOT}/cli/shop"
TMP_ROOT="$(mktemp -d)"
mkdir -p "${TMP_ROOT}/empty-bin"
bash_test_install_mock_gh "${TMP_ROOT}/empty-bin"
SAFE_PATH="$(bash_test_path_without_gh "${TMP_ROOT}")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

shop_env() {
  env \
    SHOP_GITHUB_ORG=test-org \
    SHOP_GCP_DEV_PROJECT=my-valid-project \
    SHOP_GCP_PROD_PROJECT=my-valid-project \
    SHOP_GCP_REGION=us-central1 \
    SHOP_GOLDENPATH_REPO=goldenpath \
    SHOP_GOLDENPATH_VERSION=v0.3.8 \
    SHOP_ARTIFACT_REGISTRY_REPO=shop-services \
    "$@"
}

test_start "shop doctor passes on freshly scaffolded service"
set +e
out="$(shop_env "${SHOP}" new doctor-clean-svc --template fastapi --output "${TMP_ROOT}" 2>&1)"
code=$?
set -e
assert_eq 0 "$code"
svc_dir="${TMP_ROOT}/doctor-clean-svc"
set +e
out="$(shop_env env PATH="${SAFE_PATH}" "${SHOP}" doctor "${svc_dir}" 2>&1)"
doc_code=$?
set -e
assert_eq 0 "$doc_code"
assert_match "deploy.yml tokens OK" "$out"
assert_match "local branch: main" "$out"
assert_match "project_id matches config" "$out"
test_end

test_start "shop doctor fails when deploy.yml has unreplaced tokens"
shop_env "${SHOP}" new doctor-token-svc --template fastapi --output "${TMP_ROOT}" >/dev/null
svc_dir="${TMP_ROOT}/doctor-token-svc"
cp "${REPO_ROOT}/templates/fastapi/.github/workflows/deploy.yml" "${svc_dir}/.github/workflows/deploy.yml"
set +e
out="$(shop_env "${SHOP}" doctor "${svc_dir}" 2>&1)"
doc_code=$?
set -e
assert_eq 1 "$doc_code"
assert_match "unreplaced" "$out"
test_end

test_start "shop doctor fails on wrong git branch"
shop_env "${SHOP}" new doctor-branch-svc --template fastapi --output "${TMP_ROOT}" >/dev/null
svc_dir="${TMP_ROOT}/doctor-branch-svc"
git -C "${svc_dir}" checkout -q -b feature/wrong 2>/dev/null || true
set +e
out="$(shop_env "${SHOP}" doctor "${svc_dir}" 2>&1)"
doc_code=$?
set -e
assert_eq 1 "$doc_code"
assert_match "local branch" "$out"
test_end

test_summary