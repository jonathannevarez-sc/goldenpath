#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/assert.sh
source "${SCRIPT_DIR}/lib/assert.sh"

REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# shellcheck source=../../scripts/lib/teardown-safety.sh
source "${REPO_ROOT}/scripts/lib/teardown-safety.sh"

teardown_exit_code() {
  set +e
  ( teardown_assert_deletable_project "$1" ) >/dev/null 2>&1
  local code=$?
  set -e
  printf '%s' "$code"
}

test_start "teardown_assert_deletable_project blocks protected project"
export PROTECTED_PROJECTS="protected-prod"
assert_eq 1 "$(teardown_exit_code protected-prod)"
test_end

test_start "teardown_assert_deletable_project enforces allowlist"
export PROTECTED_PROJECTS=""
export ALLOWED_TEARDOWN_PROJECTS="sandbox-a,sandbox-b"
assert_eq 1 "$(teardown_exit_code sandbox-c)"
test_end

test_start "teardown_assert_deletable_project allows listed sandbox"
export ALLOWED_TEARDOWN_PROJECTS="sandbox-a,sandbox-b"
assert_eq 0 "$(teardown_exit_code sandbox-a)"
test_end

test_start "teardown allowlist trims whitespace around entries"
export PROTECTED_PROJECTS=""
export ALLOWED_TEARDOWN_PROJECTS=" sandbox-a , sandbox-b "
assert_eq 0 "$(teardown_exit_code sandbox-b)"
test_end

test_summary