#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/assert.sh
source "${SCRIPT_DIR}/lib/assert.sh"

REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
SHOP="${REPO_ROOT}/cli/shop"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "${TMP_ROOT}"' EXIT

test_start "shop list prints catalog templates"
set +e
out="$("${SHOP}" list 2>&1)"
code=$?
set -e
assert_eq 0 "$code"
assert_match "fastapi" "$out"
assert_match "nextjs" "$out"
test_end

test_start "shop without args prints usage"
set +e
out="$("${SHOP}" 2>&1)"
code=$?
set -e
assert_eq 1 "$code"
assert_match "Golden Path CLI" "$out"
test_end

test_start "shop config rejects unknown subcommand"
set +e
out="$("${SHOP}" config bogus 2>&1)"
code=$?
set -e
assert_eq 1 "$code"
assert_match "usage: shop config" "$out"
test_end

test_start "shop new --dry-run prints target path"
set +e
out="$(
  SHOP_GITHUB_ORG=test-org \
  SHOP_GCP_DEV_PROJECT=my-valid-project \
  SHOP_GCP_PROD_PROJECT=my-valid-project \
  SHOP_GCP_REGION=us-central1 \
  SHOP_GOLDENPATH_REPO=goldenpath \
  SHOP_GOLDENPATH_VERSION=v0.3.7 \
  "${SHOP}" new my-dry-run-svc --template fastapi --dry-run --output "${TMP_ROOT}" 2>&1
)"
code=$?
set -e
assert_eq 0 "$code"
assert_match "would create" "$out"
assert_match "my-dry-run-svc" "$out"
test_end

test_start "shop new --print-config emits a ServiceConfig JSON"
set +e
out="$(
  SHOP_GITHUB_ORG=test-org \
  SHOP_GCP_DEV_PROJECT=my-valid-project \
  SHOP_GCP_PROD_PROJECT=my-valid-project \
  SHOP_GCP_REGION=us-central1 \
  SHOP_GOLDENPATH_REPO=goldenpath \
  SHOP_GOLDENPATH_VERSION=v0.3.7 \
  "${SHOP}" new --print-config --template fastapi 2>&1
)"
code=$?
set -e
assert_eq 0 "$code"
assert_match "service_name" "$out"
assert_match "cloud_sql" "$out"
test_end

test_start "shop new --config composes a service with Cloud SQL"
conf="${TMP_ROOT}/svc.json"
cat > "$conf" <<'JSON'
{
  "service_name": "compose-svc",
  "template": "fastapi",
  "runtime": "python",
  "deployment_mode": "server",
  "data_stores": [{"id": "cloud_sql", "config": {"engine": "postgresql", "ip_mode": "public"}}],
  "environments": ["dev", "prod"]
}
JSON
set +e
out="$(
  SHOP_GITHUB_ORG=test-org \
  SHOP_GCP_DEV_PROJECT=my-valid-project \
  SHOP_GCP_PROD_PROJECT=my-valid-project \
  SHOP_GCP_REGION=us-central1 \
  SHOP_GOLDENPATH_REPO=goldenpath \
  SHOP_GOLDENPATH_VERSION=v0.3.7 \
  "${SHOP}" new --config "$conf" --output "${TMP_ROOT}" 2>&1
)"
code=$?
set -e
assert_eq 0 "$code"
assert_match "compose-svc" "$out"
assert_file_exists "${TMP_ROOT}/compose-svc/infra/data-stores.tf"
assert_file_exists "${TMP_ROOT}/compose-svc/app/db.py"
test_end

test_summary