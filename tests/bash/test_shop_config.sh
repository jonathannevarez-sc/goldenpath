#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/assert.sh
source "${SCRIPT_DIR}/lib/assert.sh"

REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
SHOP="${REPO_ROOT}/cli/shop"
CLI_CONFIG="${REPO_ROOT}/.goldenpath-cli.local.json"
trap 'rm -f "${CLI_CONFIG}"' EXIT

test_start "shop config set roundtrips via show"
set +e
out="$(
  SHOP_GITHUB_ORG=config-org \
  SHOP_GCP_DEV_PROJECT=my-valid-project \
  SHOP_GCP_PROD_PROJECT=my-valid-project \
  SHOP_GCP_REGION=europe-west1 \
  SHOP_GOLDENPATH_REPO=goldenpath \
  SHOP_GOLDENPATH_VERSION=v0.3.8 \
  "${SHOP}" config set \
    --github-org config-org \
    --gcp-dev my-valid-project \
    --gcp-prod my-valid-project \
    --region europe-west1 2>&1
)"
code=$?
set -e
assert_eq 0 "$code" "config set failed: ${out}"
assert_file_exists "${CLI_CONFIG}"
saved="$(cat "${CLI_CONFIG}")"
assert_match "config-org" "$saved"
assert_match "europe-west1" "$saved"

set +e
show_out="$("${SHOP}" config show 2>&1)"
show_code=$?
set -e
assert_eq 0 "$show_code"
assert_match "config-org" "$show_out"
test_end

test_summary