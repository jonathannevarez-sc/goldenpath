#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/assert.sh
source "${SCRIPT_DIR}/lib/assert.sh"

REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
SHOP="${REPO_ROOT}/cli/shop"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "${TMP_ROOT}"' EXIT

CATALOG="${REPO_ROOT}/templates/catalog.json"
TEMPLATES="$(python3 -c "import json; print(' '.join(json.load(open('${CATALOG}'))))")"

shop_env() {
  SHOP_GITHUB_ORG=test-org \
  SHOP_GCP_DEV_PROJECT=my-valid-project \
  SHOP_GCP_PROD_PROJECT=my-valid-project \
  SHOP_GCP_REGION=us-central1 \
  SHOP_GOLDENPATH_REPO=goldenpath \
  SHOP_GOLDENPATH_VERSION=v0.3.7 \
  SHOP_ARTIFACT_REGISTRY_REPO=shop-services \
  "$@"
}

for template in ${TEMPLATES}; do
  svc="test-${template}-svc"
  test_start "shop new scaffolds ${template} without template tokens"
  rm -rf "${TMP_ROOT}/${svc}"
  set +e
  out="$(shop_env "${SHOP}" new "${svc}" --template "${template}" --output "${TMP_ROOT}" 2>&1)"
  code=$?
  set -e
  assert_eq 0 "$code" "${template} scaffold failed: ${out}"
  assert_dir_has_no_tokens "${TMP_ROOT}/${svc}"
  assert_file_exists "${TMP_ROOT}/${svc}/.github/workflows/deploy.yml"
  assert_file_exists "${TMP_ROOT}/${svc}/infra/dev.tfvars"
  test_end
done

test_start "shop new rejects unknown template"
set +e
out="$(shop_env "${SHOP}" new bad-svc --template not-real --output "${TMP_ROOT}" 2>&1)"
code=$?
set -e
assert_eq 1 "$code"
assert_match "unknown template" "$out"
test_end

test_start "shop new rejects invalid service name"
set +e
out="$(shop_env "${SHOP}" new ab --template fastapi --output "${TMP_ROOT}" 2>&1)"
code=$?
set -e
assert_eq 1 "$code"
assert_match "service name" "$out"
test_end

test_summary