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

test_summary