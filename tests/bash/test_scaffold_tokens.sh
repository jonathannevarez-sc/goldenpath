#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/assert.sh
source "${SCRIPT_DIR}/lib/assert.sh"

REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "${TMP_ROOT}"' EXIT

SERVICE_DIR="${TMP_ROOT}/demo-service"
mkdir -p "${SERVICE_DIR}/.github/workflows"
cp "${REPO_ROOT}/templates/fastapi/.github/workflows/deploy.yml" "${SERVICE_DIR}/.github/workflows/deploy.yml"
cp "${REPO_ROOT}/templates/fastapi/requirements.txt" "${SERVICE_DIR}/requirements.txt"

die() { printf 'error: %s\n' "$*" >&2; return 1; }
log() { :; }
warn() { :; }

CATALOG="${REPO_ROOT}/templates/catalog.json"
catalog_get() {
  python3 - <<PY
import json
catalog = json.load(open("${CATALOG}"))
print(catalog["${1}"]["${2}"])
PY
}

# shellcheck source=../../scripts/lib/scaffold-tokens.sh
source "${REPO_ROOT}/scripts/lib/scaffold-tokens.sh"

# load-config.sh enables errexit when sourced inside validate_gcp_project_id
set +e

test_start "deploy_has_tokens detects unreplaced tokens"
assert_exit 0 deploy_has_tokens "${SERVICE_DIR}"
test_end

test_start "get_service_template_hint detects fastapi"
hint="$(get_service_template_hint "${SERVICE_DIR}")"
assert_eq "fastapi" "$hint"
test_end

test_start "replace_tokens substitutes workflow placeholders"
replace_tokens "${SERVICE_DIR}" "my-service" "my-org" "goldenpath" \
  "dev-project" "prod-project" "us-central1" "python" "/api/health" \
  "8000" "v0.3.8" "shop-services"
assert_exit 1 deploy_has_tokens "${SERVICE_DIR}"
workflow="$(cat "${SERVICE_DIR}/.github/workflows/deploy.yml")"
assert_match "my-service" "$workflow"
assert_match "dev-project" "$workflow"
test_end

test_start "validate_gcp_project_id rejects short ids"
assert_exit 1 validate_gcp_project_id abc
test_end

test_start "validate_gcp_project_id accepts valid id"
assert_exit 0 validate_gcp_project_id my-valid-project
test_end

test_start "validate_gcp_project_id rejects protected project when config loaded"
export REPO_ROOT="${REPO_ROOT}"
mkdir -p "${TMP_ROOT}/config"
cat > "${TMP_ROOT}/config/enterprise.env" <<'EOF'
PARENT_PROJECT_ID=billing-anchor-test
BILLING_ACCOUNT_ID=000000-000000-000000
GITHUB_ORG=test-org
PROTECTED_PROJECTS=protected-a,protected-b
EOF
export GOLDENPATH_CONFIG="${TMP_ROOT}/config/enterprise.env"
set +e
( validate_gcp_project_id protected-a ) >/dev/null 2>&1
protected_code=$?
set -e
assert_eq 1 "$protected_code"
test_end

test_start "repair_tokens_if_needed fixes stale deploy.yml"
STALE_DIR="${TMP_ROOT}/stale-service"
mkdir -p "${STALE_DIR}/.github/workflows"
cp "${REPO_ROOT}/templates/fastapi/.github/workflows/deploy.yml" "${STALE_DIR}/.github/workflows/deploy.yml"
cp "${REPO_ROOT}/templates/fastapi/requirements.txt" "${STALE_DIR}/requirements.txt"
export SHOP_GITHUB_ORG=test-org SHOP_GOLDENPATH_REPO=goldenpath SHOP_GOLDENPATH_VERSION=v0.3.8
export SHOP_GCP_DEV_PROJECT=my-valid-project SHOP_GCP_PROD_PROJECT=my-valid-project SHOP_GCP_REGION=us-central1
export SHOP_ARTIFACT_REGISTRY_REPO=shop-services ARTIFACT_REGISTRY_REPO=shop-services
set +e
( repair_tokens_if_needed "${STALE_DIR}" "stale-service" ) >/dev/null 2>&1
repair_code=$?
set -e
assert_eq 0 "$repair_code"
assert_exit 1 deploy_has_tokens "${STALE_DIR}"
test_end

test_summary