#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/assert.sh
source "${SCRIPT_DIR}/lib/assert.sh"

REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

test_start "goldenpath-setup.sh --help exits 0"
set +e
out="$("${REPO_ROOT}/scripts/goldenpath-setup.sh" --help 2>&1)"
code=$?
set -e
assert_eq 0 "$code"
assert_match "launcher" "$out"
test_end

test_start "goldenpath-setup.sh --explain-launchers exits 0"
set +e
out="$("${REPO_ROOT}/scripts/goldenpath-setup.sh" --explain-launchers 2>&1)"
code=$?
set -e
assert_eq 0 "$code"
assert_match "LAUNCHER" "$out"
test_end

test_start "goldenpath-setup-bash.sh --help exits 0"
set +e
out="$("${REPO_ROOT}/scripts/goldenpath-setup-bash.sh" --help 2>&1)"
code=$?
set -e
assert_eq 0 "$code"
assert_match "Bash Wizard" "$out"
test_end

test_start "goldenpath-setup-py.sh --help exits 0"
set +e
out="$("${REPO_ROOT}/scripts/goldenpath-setup-py.sh" --help 2>&1)"
code=$?
set -e
assert_eq 0 "$code"
assert_match "Python Wizard" "$out"
test_end

test_start "goldenpath-setup.sh rejects unknown backend"
set +e
"${REPO_ROOT}/scripts/goldenpath-setup.sh" --backend nonsense >/dev/null 2>&1
code=$?
set -e
assert_eq 1 "$code"
test_end

test_summary