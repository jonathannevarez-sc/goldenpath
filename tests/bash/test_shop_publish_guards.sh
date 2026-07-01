#!/usr/bin/env bash
# Contract tests for shop publish preflight — no live GitHub/GCP calls.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/assert.sh
source "${SCRIPT_DIR}/lib/assert.sh"

REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
SHOP="${REPO_ROOT}/cli/shop"
TMP_ROOT="$(mktemp -d)"
EMPTY_BIN="${TMP_ROOT}/empty-bin"
mkdir -p "${EMPTY_BIN}"
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

scaffold_service() {
  local name="$1"
  shop_env "${SHOP}" new "${name}" --template fastapi --output "${TMP_ROOT}" >/dev/null
  printf '%s' "${TMP_ROOT}/${name}"
}

test_start "shop publish requires a git repository"
mkdir -p "${TMP_ROOT}/not-a-repo"
set +e
out="$(shop_env "${SHOP}" publish "${TMP_ROOT}/not-a-repo" 2>&1)"
code=$?
set -e
assert_eq 1 "$code"
assert_match "not a git repo" "$out"
test_end

test_start "shop publish rejects project_id mismatch in dev.tfvars"
svc_dir="$(scaffold_service publish-mismatch-svc)"
if [[ "$(uname)" == "Darwin" ]]; then
  sed -i '' 's/project_id.*=.*/project_id           = "wrong-project-99"/' "${svc_dir}/infra/dev.tfvars"
else
  sed -i 's/project_id.*=.*/project_id           = "wrong-project-99"/' "${svc_dir}/infra/dev.tfvars"
fi
printf '#!/usr/bin/env bash\nexit 1\n' > "${EMPTY_BIN}/gh"
chmod +x "${EMPTY_BIN}/gh"
set +e
out="$(shop_env env PATH="${SAFE_PATH}" "${SHOP}" publish "${svc_dir}" 2>&1)"
code=$?
set -e
rm -f "${EMPTY_BIN}/gh"
assert_eq 1 "$code"
assert_match "project mismatch" "$out"
test_end

test_start "shop publish fails without a working gh CLI"
svc_dir="$(scaffold_service publish-gh-svc)"
set +e
out="$(
  env -i \
    HOME="${HOME:-/tmp}" \
    TMPDIR="${TMPDIR:-/tmp}" \
    PATH="${SAFE_PATH}" \
    SHOP_GITHUB_ORG=test-org \
    SHOP_GCP_DEV_PROJECT=my-valid-project \
    SHOP_GCP_PROD_PROJECT=my-valid-project \
    SHOP_GCP_REGION=us-central1 \
    SHOP_GOLDENPATH_REPO=goldenpath \
    SHOP_GOLDENPATH_VERSION=v0.3.8 \
    SHOP_ARTIFACT_REGISTRY_REPO=shop-services \
    "${SHOP}" publish "${svc_dir}" 2>&1
)"
code=$?
set -e
if [[ "$code" -eq 0 ]]; then
  CURRENT_FAILED=1
  TESTS_FAILED=$((TESTS_FAILED + 1))
  printf '        expected non-zero exit when gh is unavailable\n'
  printf '        actual:   %q\n' "$code"
fi
assert_match "gh required|gh auth login|GH_TOKEN" "$out"
test_end

test_summary