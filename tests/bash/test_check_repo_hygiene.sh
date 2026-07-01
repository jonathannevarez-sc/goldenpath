#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/assert.sh
source "${SCRIPT_DIR}/lib/assert.sh"

REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

test_start "check-repo-hygiene.sh passes on platform repo"
set +e
out="$("${REPO_ROOT}/scripts/check-repo-hygiene.sh" 2>&1)"
code=$?
set -e
assert_eq 0 "$code"
assert_match "OK" "$out"
test_end

test_start "check-repo-hygiene.sh --explain prints layout guide"
set +e
out="$("${REPO_ROOT}/scripts/check-repo-hygiene.sh" --explain 2>&1)"
code=$?
set -e
assert_eq 0 "$code"
assert_match "Scripts layout" "$out"
test_end

test_summary